"""
MongoDB Storage Module for LLM Council
Async storage operations using Motor driver
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from .database import MongoDB, CONVERSATIONS_COLLECTION, ANALYTICS_COLLECTION
import uuid


async def create_conversation_mongo(
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new conversation in MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return None

    conv_id = conversation_id or str(uuid.uuid4())
    now = datetime.utcnow()

    conversation = {
        "_id": conv_id,
        "id": conv_id,
        "created_at": now.isoformat() + "Z",
        "updated_at": now.isoformat() + "Z",
        "title": None,
        "messages": [],
        "metadata": {"total_tokens": 0, "total_time_ms": 0, "providers_used": []},
    }

    await collection.insert_one(conversation)
    return conversation


async def get_conversation_mongo(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get a conversation by ID from MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return None

    conversation = await collection.find_one({"_id": conversation_id})

    if conversation:
        # Transform messages to frontend format
        transformed_messages = []
        for msg in conversation.get("messages", []):
            if msg.get("role") == "assistant":
                metadata = msg.get("metadata", {})
                is_simple_mode = metadata.get("mode") == "simple_llm"

                # Convert MongoDB format to frontend format
                stage3_final = msg.get("stage3_final_response")
                transformed_msg = {
                    "role": "assistant",
                    "timestamp": msg.get("timestamp"),
                    # In simple mode we avoid stage fields entirely in UI
                    "stage1": None if is_simple_mode else msg.get("stage1_responses"),
                    "stage2": None if is_simple_mode else msg.get("stage2_rankings"),
                    "stage3": None if is_simple_mode else stage3_final,
                    "simpleResponse": stage3_final if is_simple_mode else None,
                    "metadata": {
                        "aggregate_rankings": msg.get("aggregate_rankings", []),
                        "mode": metadata.get("mode"),
                    },
                    "loading": {
                        "stage1": False,
                        "stage2": False,
                        "stage3": False,
                        "simple": False,
                    },
                }
                transformed_messages.append(transformed_msg)
            else:
                transformed_messages.append(msg)

        conversation["messages"] = transformed_messages

    return conversation


async def list_conversations_mongo(limit: int = 50) -> List[Dict[str, Any]]:
    """List all conversations from MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return []

    cursor = (
        collection.find(
            {}, {"_id": 1, "id": 1, "created_at": 1, "title": 1, "messages": 1}
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    conversations = []
    async for conv in cursor:
        conversations.append(
            {
                "id": conv["id"],
                "created_at": conv["created_at"],
                "title": conv.get("title"),
                "message_count": len(conv.get("messages", [])),
            }
        )

    return conversations


async def add_user_message_mongo(
    conversation_id: str, content: str
) -> Optional[Dict[str, Any]]:
    """Add a user message to a conversation in MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return None

    message = {
        "role": "user",
        "content": content,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    result = await collection.update_one(
        {"_id": conversation_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow().isoformat() + "Z"},
        },
    )

    if result.modified_count > 0:
        return message
    return None


async def add_assistant_message_mongo(
    conversation_id: str,
    stage1_responses: List[Dict[str, Any]],
    stage2_rankings: List[Dict[str, Any]],
    stage3_final: Dict[str, Any],
    aggregate_rankings: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Add an assistant (council) message to a conversation in MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return None

    message = {
        "role": "assistant",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stage1_responses": stage1_responses,
        "stage2_rankings": stage2_rankings,
        "aggregate_rankings": aggregate_rankings or [],
        "stage3_final_response": stage3_final,
        "metadata": metadata or {},
    }

    # Collect providers used
    providers = [r.get("model", "unknown") for r in stage1_responses]
    if stage3_final and stage3_final.get("model"):
        providers.append(stage3_final.get("model"))

    result = await collection.update_one(
        {"_id": conversation_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow().isoformat() + "Z"},
            "$addToSet": {"metadata.providers_used": {"$each": providers}},
        },
    )

    if result.modified_count > 0:
        return message
    return None


# Alias for backward compatibility
add_council_response_mongo = add_assistant_message_mongo


async def update_conversation_title_mongo(conversation_id: str, title: str) -> bool:
    """Update conversation title in MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return False

    result = await collection.update_one(
        {"_id": conversation_id},
        {"$set": {"title": title, "updated_at": datetime.utcnow().isoformat() + "Z"}},
    )

    return result.modified_count > 0


async def delete_conversation_mongo(conversation_id: str) -> bool:
    """Delete a conversation from MongoDB"""
    collection = MongoDB.get_collection(CONVERSATIONS_COLLECTION)
    if collection is None:
        return False

    result = await collection.delete_one({"_id": conversation_id})
    return result.deleted_count > 0


# ============================================================================
# ANALYTICS FUNCTIONS
# ============================================================================


async def track_llm_request(
    conversation_id: str,
    provider: str,
    model: str,
    stage: str,
    response_time_ms: float,
    tokens_used: int = 0,
    success: bool = True,
    error_message: Optional[str] = None,
) -> bool:
    """Track an LLM API request for analytics"""
    collection = MongoDB.get_collection(ANALYTICS_COLLECTION)
    if collection is None:
        return False

    analytics_event = {
        "_id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "provider": provider,
        "model": model,
        "stage": stage,  # stage1, stage2, stage3
        "response_time_ms": response_time_ms,
        "tokens_used": tokens_used,
        "success": success,
        "error_message": error_message,
        "timestamp": datetime.utcnow(),
    }

    await collection.insert_one(analytics_event)
    return True


async def get_analytics_summary() -> Dict[str, Any]:
    """Get analytics summary with provider stats"""
    collection = MongoDB.get_collection(ANALYTICS_COLLECTION)
    if collection is None:
        return {}

    # Provider başarı oranları ve ortalama yanıt süreleri
    pipeline = [
        {
            "$group": {
                "_id": "$provider",
                "total_requests": {"$sum": 1},
                "successful_requests": {"$sum": {"$cond": ["$success", 1, 0]}},
                "avg_response_time": {"$avg": "$response_time_ms"},
                "total_tokens": {"$sum": "$tokens_used"},
            }
        },
        {"$sort": {"total_requests": -1}},
    ]

    provider_stats = await collection.aggregate(pipeline).to_list(length=100)

    # Günlük istatistikler
    daily_pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "requests": {"$sum": 1},
                "avg_response_time": {"$avg": "$response_time_ms"},
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 30},
    ]

    daily_stats = await collection.aggregate(daily_pipeline).to_list(length=30)

    # Stage bazlı istatistikler
    stage_pipeline = [
        {
            "$group": {
                "_id": "$stage",
                "total_requests": {"$sum": 1},
                "avg_response_time": {"$avg": "$response_time_ms"},
            }
        },
    ]

    stage_stats = await collection.aggregate(stage_pipeline).to_list(length=10)

    return {
        "provider_stats": provider_stats,
        "daily_stats": daily_stats,
        "stage_stats": stage_stats,
    }


async def get_recent_errors(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent error events"""
    collection = MongoDB.get_collection(ANALYTICS_COLLECTION)
    if collection is None:
        return []

    cursor = collection.find({"success": False}).sort("timestamp", -1).limit(limit)
    errors = await cursor.to_list(length=limit)
    return errors
