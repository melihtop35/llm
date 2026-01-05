"""FastAPI backend for LLM Council."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid
import json
import asyncio
import time

from .database import MongoDB
from . import storage_mongo as db
from .council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
    simple_llm_response,
)
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL, COUNCIL_MEMBERS
from .settings import (
    get_settings,
    save_settings,
    reload_env,
    get_active_council_models,
    get_settings_async,
    save_settings_async,
    get_active_council_models_async,
)

# Track active requests for cancellation
active_requests: Dict[str, asyncio.Event] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Connect to MongoDB
    await MongoDB.connect()
    yield
    # Shutdown: Disconnect from MongoDB
    await MongoDB.disconnect()


# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="LLM Council API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/health"],
)
instrumentator.instrument(app).expose(app, include_in_schema=True)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""

    id: str
    created_at: str
    title: str | None = None
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""

    id: str
    created_at: str
    title: str | None = None
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "LLM Council API",
        "mongodb": "connected" if MongoDB.is_connected() else "disconnected",
        "version": "1.1.0",
    }


@app.get("/api/analytics")
async def get_analytics():
    """Get analytics summary for all LLM requests."""
    summary = await db.get_analytics_summary()
    return summary


@app.get("/api/analytics/errors")
async def get_analytics_errors():
    """Get recent error events."""
    errors = await db.get_recent_errors(limit=20)
    return errors


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return await db.list_conversations_mongo()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = await db.create_conversation_mongo(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = await db.get_conversation_mongo(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    deleted = await db.delete_conversation_mongo(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "message": "Conversation deleted"}


@app.post("/api/conversations/{conversation_id}/cancel")
async def cancel_request(conversation_id: str):
    """Cancel an active request for a conversation."""
    if conversation_id in active_requests:
        active_requests[conversation_id].set()  # Signal cancellation
        return {"success": True, "message": "Request cancellation signaled"}
    return {"success": False, "message": "No active request found"}


@app.post("/api/conversations/{conversation_id}/message")
@limiter.limit("20/minute")
async def send_message(conversation_id: str, request: SendMessageRequest, req: Request):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = await db.get_conversation_mongo(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    await db.add_user_message_mongo(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        await db.update_conversation_title_mongo(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content
    )

    # Add assistant message with all stages
    await db.add_assistant_message_mongo(
        conversation_id, stage1_results, stage2_results, stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata,
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = await db.get_conversation_mongo(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Create cancellation event for this request
    cancel_event = asyncio.Event()
    active_requests[conversation_id] = cancel_event

    async def check_cancelled():
        """Check if request was cancelled"""
        return cancel_event.is_set()

    async def event_generator():
        try:
            # Add user message
            await db.add_user_message_mongo(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(
                    generate_conversation_title(request.content)
                )

            # Check for cancellation
            if await check_cancelled():
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user'})}\n\n"
                return

            # Check if we're in simple LLM mode (no experts selected)
            experts = await get_active_council_models_async()

            if not experts:
                # SIMPLE LLM MODE - Only chairman responds
                yield f"data: {json.dumps({'type': 'simple_mode_start'})}\n\n"
                simple_start = time.time()

                result = await simple_llm_response(request.content)

                simple_time = (time.time() - simple_start) * 1000

                # Track analytics
                await db.track_llm_request(
                    conversation_id=conversation_id,
                    provider=result.get("model", "unknown"),
                    model=result.get("display_name", "unknown"),
                    stage="simple",
                    response_time_ms=simple_time,
                    success=True,
                )

                yield f"data: {json.dumps({'type': 'simple_mode_complete', 'data': result})}\n\n"

                # Save to conversation
                await db.add_council_response_mongo(
                    conversation_id,
                    stage1_responses=[],
                    stage2_rankings=[],
                    stage3_final=result,
                    metadata={"mode": "simple_llm"},
                )

                # Handle title
                if title_task:
                    try:
                        title = await title_task
                        await db.update_conversation_title_mongo(conversation_id, title)
                        yield f"data: {json.dumps({'type': 'title_complete', 'title': title})}\n\n"
                    except Exception as e:
                        print(f"Title generation failed: {e}")

                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                return

            # FULL COUNCIL MODE - Stage 1, 2, 3
            # Stage 1: Collect responses
            active_models = (
                await get_active_council_models_async()
            )  # Returns list of provider IDs like ["groq", "google", ...]
            model_names = [
                COUNCIL_MEMBERS.get(m, {}).get("name", m) for m in active_models
            ]
            yield f"data: {json.dumps({'type': 'stage1_start', 'models': model_names})}\n\n"
            stage1_start = time.time()
            stage1_results = await stage1_collect_responses(request.content)
            stage1_time = (time.time() - stage1_start) * 1000  # ms

            # Check for cancellation after Stage 1
            if await check_cancelled():
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user'})}\n\n"
                return

            # Track Stage 1 analytics for each provider
            for result in stage1_results:
                provider = result.get("model", "unknown")
                await db.track_llm_request(
                    conversation_id=conversation_id,
                    provider=provider,
                    model=result.get("display_name", provider),
                    stage="stage1",
                    response_time_ms=stage1_time
                    / len(stage1_results),  # Approximate per-provider
                    success=True,
                )

            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Check for cancellation before Stage 2
            if await check_cancelled():
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user'})}\n\n"
                return

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_start = time.time()
            stage2_results, label_to_model = await stage2_collect_rankings(
                request.content, stage1_results
            )
            stage2_time = (time.time() - stage2_start) * 1000  # ms

            # Check for cancellation after Stage 2
            if await check_cancelled():
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user'})}\n\n"
                return

            # Track Stage 2 analytics
            for result in stage2_results:
                provider = result.get("model", "unknown")
                await db.track_llm_request(
                    conversation_id=conversation_id,
                    provider=provider,
                    model=result.get("display_name", provider),
                    stage="stage2",
                    response_time_ms=stage2_time / len(stage2_results),
                    success=True,
                )

            aggregate_rankings = calculate_aggregate_rankings(
                stage2_results, label_to_model
            )
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Check for cancellation before Stage 3
            if await check_cancelled():
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user'})}\n\n"
                return

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_start = time.time()
            stage3_result = await stage3_synthesize_final(
                request.content, stage1_results, stage2_results
            )
            stage3_time = (time.time() - stage3_start) * 1000  # ms

            # Track Stage 3 analytics (Chairman)
            await db.track_llm_request(
                conversation_id=conversation_id,
                provider=CHAIRMAN_MODEL,
                model=stage3_result.get("display_name", CHAIRMAN_MODEL),
                stage="stage3",
                response_time_ms=stage3_time,
                success=True,
            )

            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                await db.update_conversation_title_mongo(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            await db.add_assistant_message_mongo(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result,
                aggregate_rankings,
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Track error
            await db.track_llm_request(
                conversation_id=conversation_id,
                provider="unknown",
                model="unknown",
                stage="error",
                response_time_ms=0,
                success=False,
                error_message=str(e),
            )
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Cleanup: remove from active requests
            if conversation_id in active_requests:
                del active_requests[conversation_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================


@app.get("/api/settings")
async def get_app_settings():
    """Get current application settings."""
    return await get_settings_async()


class UpdateSettingsRequest(BaseModel):
    chairman: Optional[str] = None
    experts: Optional[List[str]] = None
    api_keys: Optional[Dict[str, str]] = None


@app.post("/api/settings")
async def update_app_settings(request: UpdateSettingsRequest):
    """Update application settings."""
    settings = await get_settings_async()

    if request.chairman is not None:
        settings["chairman"] = request.chairman

    # Allow empty experts array (simple LLM mode)
    if request.experts is not None:
        settings["experts"] = request.experts

    if request.api_keys is not None:
        settings["api_keys"] = request.api_keys

    success = await save_settings_async(settings)
    if success:
        # Reload environment variables
        reload_env()
        return {"success": True, "message": "Settings updated", "data": settings}
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
