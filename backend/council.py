"""3-stage LLM Council orchestration - Grand Council V11 (6 Motorlu Hibrit Jet)."""

from typing import List, Dict, Any, Tuple
from .llm_clients import (
    query_models_parallel,
    query_model,
    get_provider_display_name,
    get_provider_role,
)
from .config import COUNCIL_MEMBERS
from .settings import get_active_council_models_async, get_chairman_model_async


async def stage1_collect_responses(user_query: str) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        user_query: The user's question

    Returns:
        List of dicts with 'model', 'response', 'display_name', and 'role' keys
    """
    # System message to prevent models from revealing their identity
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful AI assistant participating in a council deliberation. "
            "IMPORTANT RULES:\\n"
            "1. Do NOT mention your name, identity, or what AI model you are.\\n"
            "2. Do NOT say things like 'As ChatGPT', 'As Claude', 'As an AI assistant', etc.\\n"
            "3. Do NOT refer to yourself by any model name or company name.\\n"
            "4. Simply answer the question directly without introducing yourself.\\n"
            "5. Focus entirely on providing a helpful, accurate response to the user's question.\\n"
            "6. Respond in the same language as the user's question."
        ),
    }

    messages = [system_message, {"role": "user", "content": user_query}]

    # Get active council models from settings (DYNAMIC)
    council_models = await get_active_council_models_async()

    # Query all models in parallel
    responses = await query_models_parallel(council_models, messages)

    # Format results
    stage1_results = []
    for provider, response in responses.items():
        if response is not None:  # Only include successful responses
            # Check if this was a failover response
            is_failover = response.get("is_failover", False)

            if is_failover:
                # Use HuggingFace display name but keep original provider info
                result = {
                    "model": "huggingface",  # Actual model used
                    "display_name": get_provider_display_name("huggingface"),
                    "role": get_provider_role("huggingface"),
                    "response": response.get("content", ""),
                    "is_failover": True,
                    "original_provider": response.get("original_provider"),
                    "original_display_name": get_provider_display_name(provider),
                }
            else:
                result = {
                    "model": provider,
                    "display_name": get_provider_display_name(provider),
                    "role": get_provider_role(provider),
                    "response": response.get("content", ""),
                }
            stage1_results.append(result)

    return stage1_results


def anonymize_response_text(text: str, model_names: List[str]) -> str:
    """
    Remove model names from response text to ensure true anonymization.
    """
    import re

    result = text

    # Common AI model names to remove
    ai_names = [
        "ChatGPT",
        "GPT-4",
        "GPT-3",
        "GPT",
        "OpenAI",
        "Claude",
        "Anthropic",
        "Gemini",
        "Bard",
        "Google AI",
        "Google",
        "Llama",
        "Meta Llama",
        "LLaMA",
        "Meta",
        "Mistral",
        "Mixtral",
        "Groq",
        "Groq Cloud",
        "Cohere",
        "Command",
        "Hugging Face",
        "HuggingFace",
        "SambaNova",
        "Samba Nova",
        "BERT",
        "T5",
        "PaLM",
        "Transformer",
        "OpenRouter",
    ]

    # Add dynamic model names from council
    all_names = ai_names + model_names

    # Remove mentions like "As [Model Name]," or "I am [Model Name]"
    for name in all_names:
        # Case insensitive replacement with word boundaries
        patterns = [
            rf"\b{re.escape(name)}\b",
            rf"(?i)as {re.escape(name)}",
            rf"(?i)i am {re.escape(name)}",
            rf"(?i){re.escape(name)} here",
        ]
        for pattern in patterns:
            result = re.sub(pattern, "[AI Model]", result, flags=re.IGNORECASE)

    return result


async def stage2_collect_rankings(
    user_query: str, stage1_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model name (using display name for UI)
    label_to_model = {
        f"Response {label}": result["display_name"]
        for label, result in zip(labels, stage1_results)
    }

    # Collect all model names for anonymization
    model_names = [result.get("display_name", "") for result in stage1_results]
    model_names += [result.get("model", "") for result in stage1_results]

    # Build the ranking prompt with ANONYMIZED responses
    responses_text = "\n\n".join(
        [
            f"Response {label}:\n{anonymize_response_text(result['response'], model_names)}"
            for label, result in zip(labels, stage1_results)
        ]
    )

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get active council models from settings (DYNAMIC)
    council_models = await get_active_council_models_async()

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(council_models, messages)

    # Format results
    stage2_results = []
    for provider, response in responses.items():
        if response is not None:
            full_text = response.get("content", "")
            parsed = parse_ranking_from_text(full_text)

            # Handle failover: use HF display name if failover happened
            is_failover = response.get("is_failover", False)
            if is_failover:
                display_name = get_provider_display_name("huggingface")
                role = get_provider_role("huggingface")
                model = "huggingface"
            else:
                display_name = get_provider_display_name(provider)
                role = get_provider_role(provider)
                model = provider

            result = {
                "model": model,
                "display_name": display_name,
                "role": role,
                "ranking": full_text,
                "parsed_ranking": parsed,
            }

            # Keep failover metadata
            if is_failover:
                result["is_failover"] = True
                result["original_provider"] = response.get("original_provider")
                result["original_display_name"] = get_provider_display_name(provider)

            stage2_results.append(result)

    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2

    Returns:
        Dict with 'model', 'display_name', 'role', and 'response' keys
    """
    # Get chairman from settings (DYNAMIC)
    chairman_model = await get_chairman_model_async()

    # Build comprehensive context for chairman
    stage1_text = "\n\n".join(
        [
            f"Model: {result['display_name']} ({result['role']})\nResponse: {result['response']}"
            for result in stage1_results
        ]
    )

    stage2_text = "\n\n".join(
        [
            f"Model: {result['display_name']} ({result['role']})\nRanking: {result['ranking']}"
            for result in stage2_results
        ]
    )

    chairman_info = COUNCIL_MEMBERS.get(chairman_model, {})

    chairman_prompt = f"""You are the Chairman of the Grand Council V11 - a prestigious council of AI models working together to provide the best possible answer.

As the Chairman ({chairman_info.get('name', 'Chairman')}), your role is to DIRECTLY ANSWER the user's question using the collective wisdom of the council.

Original Question: {user_query}

STAGE 1 - Individual Responses from Council Members:
{stage1_text}

STAGE 2 - Peer Rankings and Evaluations:
{stage2_text}

IMPORTANT INSTRUCTIONS:
1. DO NOT just evaluate which response was best or summarize the rankings.
2. DIRECTLY ANSWER the user's original question as if you are the final expert.
3. Use the BEST insights, ideas, and information from ALL council responses to craft your answer.
4. Your response should be a COMPLETE, STANDALONE answer to the user's question.
5. Do NOT mention "Response A", "Response B", etc. in your final answer.
6. Do NOT say things like "Response B was ranked highest" - the user doesn't care about internal rankings.
7. Synthesize the best parts of all responses into ONE coherent, comprehensive answer.

The council members have provided their perspectives. Now YOU must deliver the definitive answer that combines their collective wisdom.

CRITICAL LANGUAGE RULE: You MUST respond in the SAME LANGUAGE as the original question. If the question is in Turkish, your entire response must be in Turkish. If in English, respond in English. Match the user's language exactly.

Provide your comprehensive, direct answer to the user's question:"""

    messages = [{"role": "user", "content": chairman_prompt}]

    # Query the chairman model (DYNAMIC)
    response = await query_model(chairman_model, messages)

    chairman_display_name = get_provider_display_name(chairman_model)
    chairman_role = get_provider_role(chairman_model)

    if response is None:
        # Fallback if chairman fails
        return {
            "model": chairman_model,
            "display_name": chairman_display_name,
            "role": chairman_role,
            "response": "Error: Unable to generate final synthesis.",
        }

    return {
        "model": chairman_model,
        "display_name": chairman_display_name,
        "role": chairman_role,
        "response": response.get("content", ""),
    }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r"\d+\.\s*Response [A-Z]", ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [
                    re.search(r"Response [A-Z]", m).group() for m in numbered_matches
                ]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r"Response [A-Z]", ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r"Response [A-Z]", ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]], label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model display names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking["ranking"]

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append(
                {
                    "model": model,
                    "average_rank": round(avg_rank, 2),
                    "rankings_count": len(positions),
                }
            )

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x["average_rank"])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.
    Uses Groq (fastest) for quick title generation.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use Groq for title generation (fastest provider)
    response = await query_model("groq", messages, timeout=30.0)

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    title = response.get("content", "New Conversation").strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip("\"'")

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(user_query: str) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(user_query)

    # If no models responded successfully, return error
    if not stage1_results:
        return (
            [],
            [],
            {
                "model": "error",
                "response": "All models failed to respond. Please try again.",
            },
            {},
        )

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query, stage1_results
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query, stage1_results, stage2_results
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings,
    }

    return stage1_results, stage2_results, stage3_result, metadata


async def simple_llm_response(user_query: str) -> Dict[str, Any]:
    """
    Simple LLM mode - Only chairman responds (no council, no stages).
    Used when no experts are selected.

    Args:
        user_query: The user's question

    Returns:
        Dict with 'model', 'display_name', 'role', and 'response' keys
    """
    chairman_model = await get_chairman_model_async()

    messages = [{"role": "user", "content": user_query}]

    response = await query_model(chairman_model, messages)

    chairman_display_name = get_provider_display_name(chairman_model)
    chairman_role = get_provider_role(chairman_model)

    if response is None:
        return {
            "model": chairman_model,
            "display_name": chairman_display_name,
            "role": chairman_role,
            "response": "Hata: Yanıt alınamadı. Lütfen tekrar deneyin.",
        }

    return {
        "model": chairman_model,
        "display_name": chairman_display_name,
        "role": chairman_role,
        "response": response.get("content", ""),
    }
