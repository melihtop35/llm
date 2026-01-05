"""
LLM API Clients for Grand Council V11 - 6 Motorlu Hibrit Jet
Each provider has its own authentication and request format.
"""

import httpx
import os
from typing import List, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from .config import COUNCIL_MEMBERS


def _is_placeholder_api_key(value: Optional[str]) -> bool:
    if value is None:
        return True
    normalized = value.strip()
    if not normalized:
        return True
    lowered = normalized.lower()
    return (
        lowered.startswith("your_")
        or lowered.endswith("_here")
        or "replace_me" in lowered
        or "changeme" in lowered
        or "example" in lowered
        or "placeholder" in lowered
    )


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider from environment."""
    member = COUNCIL_MEMBERS.get(provider)
    if member:
        value = os.getenv(member["api_key_env"])
        return None if _is_placeholder_api_key(value) else value
    return None


# ============================================================================
# GROQ CLIENT ⚡ (OpenAI Compatible)
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
    ),
    reraise=True,
)
async def query_groq(
    messages: List[Dict[str, str]], timeout: float = 60.0
) -> Optional[Dict[str, Any]]:
    """Query Groq Cloud - Llama 3.3 70B (Dünyanın en hızlısı)."""
    api_key = get_api_key("groq")
    if not api_key:
        print("Error: GROQ_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["groq"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                config["api_url"], headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "provider": "groq",
            }
    except httpx.HTTPStatusError as e:
        print(
            f"Error querying Groq: HTTP {e.response.status_code}: {e.response.text[:500]}"
        )
        return None
    except Exception as e:
        print(f"Error querying Groq: {type(e).__name__}: {e}")
        return None


# ============================================================================
# SAMBANOVA CLIENT 🧠 (OpenAI Compatible - Chairman)
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
    ),
    reraise=True,
)
async def query_sambanova(
    messages: List[Dict[str, str]], timeout: float = 180.0
) -> Optional[Dict[str, Any]]:
    """Query SambaNova Cloud - Llama 3.1 405B (Konsey Başkanı)."""
    api_key = get_api_key("sambanova")
    if not api_key:
        print("Error: SAMBANOVA_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["sambanova"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                config["api_url"], headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "provider": "sambanova",
            }
    except httpx.HTTPStatusError as e:
        print(
            f"Error querying SambaNova: HTTP {e.response.status_code}: {e.response.text[:500]}"
        )
        return None
    except Exception as e:
        print(f"Error querying SambaNova: {type(e).__name__}: {e}")
        return None


# ============================================================================
# GOOGLE AI STUDIO CLIENT 🌐 (Gemini API)
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
    ),
    reraise=True,
)
async def query_google(
    messages: List[Dict[str, str]], timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """Query Google AI Studio - Gemini 2.0 Flash (Mantık Uzmanı)."""
    api_key = get_api_key("google")
    if not api_key:
        print("Error: GOOGLE_AI_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["google"]

    # Convert OpenAI format to Gemini format.
    # Gemini supports "user" and "model" roles; system messages should be sent via systemInstruction.
    system_parts = []
    contents = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append({"role": gemini_role, "parts": [{"text": content}]})

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        },
    }

    system_text = "\n\n".join([p for p in system_parts if p.strip()])
    if system_text:
        payload["systemInstruction"] = {
            "role": "user",
            "parts": [{"text": system_text}],
        }

    def _build_url(model_name: str) -> str:
        return f"{config['api_url']}/{model_name}:generateContent?key={api_key}"

    def _extract_content(data: Dict[str, Any]) -> str:
        return data["candidates"][0]["content"]["parts"][0]["text"]

    # Try primary model first, then optional fallbacks (on 429).
    from .config import GOOGLE_MODEL_FALLBACKS

    models_to_try = [
        config["model"],
        *[m for m in GOOGLE_MODEL_FALLBACKS if m and m != config["model"]],
    ]

    last_status: Optional[int] = None
    last_error_text: Optional[str] = None

    for model_name in models_to_try:
        url = _build_url(model_name)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                content = _extract_content(data)
                return {"content": content, "provider": "google", "model": model_name}
        except httpx.HTTPStatusError as e:
            last_status = e.response.status_code
            # Important: don't print URL here because it contains the API key query param.
            last_error_text = e.response.text[:500]
            if last_status == 429:
                # Rate-limited: try next model in chain.
                continue

            # Some models may be unavailable for an account/region, or may not support
            # this exact endpoint/config. In those cases, try the next fallback.
            if last_status in (400, 403, 404):
                text = (last_error_text or "").lower()
                looks_model_related = any(
                    s in text
                    for s in (
                        "model",
                        "not found",
                        "not supported",
                        "unsupported",
                        "permission",
                        "access",
                        "not enabled",
                        "isn't available",
                        "invalid",
                    )
                )
                if looks_model_related:
                    continue

            print(f"Error querying Google AI: HTTP {last_status}: {last_error_text}")
            return None
        except Exception as e:
            print(f"Error querying Google AI: {type(e).__name__}: {e}")
            return None

    if last_status is not None:
        print(f"Error querying Google AI: HTTP {last_status}: {last_error_text}")
    return None


# ============================================================================
# MISTRAL CLIENT 🇫🇷 (OpenAI Compatible)
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
    ),
    reraise=True,
)
async def query_mistral(
    messages: List[Dict[str, str]], timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """Query Mistral AI - Mistral Large (Kodlama ve Yaratıcı Yazarlık)."""
    api_key = get_api_key("mistral")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["mistral"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                config["api_url"], headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "provider": "mistral",
            }
    except httpx.HTTPStatusError as e:
        print(
            f"Error querying Mistral: HTTP {e.response.status_code}: {e.response.text[:500]}"
        )
        return None
    except Exception as e:
        print(f"Error querying Mistral: {type(e).__name__}: {e}")
        return None


# ============================================================================
# COHERE CLIENT 📄 (Custom API)
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
    ),
    reraise=True,
)
async def query_cohere(
    messages: List[Dict[str, str]], timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """Query Cohere - Command R+ (Analiz ve Eleştirmen)."""
    api_key = get_api_key("cohere")
    if not api_key:
        print("Error: COHERE_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["cohere"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Convert to Cohere v2 chat format
    cohere_messages = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "assistant"
        cohere_messages.append({"role": role, "content": msg["content"]})

    payload = {
        "model": config["model"],
        "messages": cohere_messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                config["api_url"], headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Cohere v2 response format
            content = data["message"]["content"][0]["text"]
            return {"content": content, "provider": "cohere"}
    except httpx.HTTPStatusError as e:
        print(
            f"Error querying Cohere: HTTP {e.response.status_code}: {e.response.text[:500]}"
        )
        return None
    except Exception as e:
        print(f"Error querying Cohere: {type(e).__name__}: {e}")
        return None


# ============================================================================
# HUGGING FACE CLIENT 🛡️ (Inference API - Failover)
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
    ),
    reraise=True,
)
async def query_huggingface(
    messages: List[Dict[str, str]], timeout: float = 180.0
) -> Optional[Dict[str, Any]]:
    """Query Hugging Face - Failover via HF Router (OpenAI-compatible)."""
    api_key = get_api_key("huggingface")
    if not api_key:
        print("Error: HUGGINGFACE_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["huggingface"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    url = config["api_url"]

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # HF Router is OpenAI-compatible
            return {
                "content": data["choices"][0]["message"]["content"],
                "provider": "huggingface",
            }
    except httpx.HTTPStatusError as e:
        print(
            f"Error querying HuggingFace: HTTP {e.response.status_code}: {e.response.text[:500]}"
        )
        return None
    except Exception as e:
        print(f"Error querying HuggingFace: {type(e).__name__}: {e}")
        return None


# ============================================================================
# OPENROUTER CLIENT 🔀 (OpenAI Compatible - Multi-Model Gateway)
# ============================================================================


async def query_openrouter(
    messages: List[Dict[str, str]], timeout: float = 180.0
) -> Optional[Dict[str, Any]]:
    """Query OpenRouter - Multi-model gateway with 200+ models."""
    api_key = get_api_key("openrouter")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        return None

    config = COUNCIL_MEMBERS["openrouter"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://llm-council.local",  # Required by OpenRouter
        "X-Title": "LLM Council",  # Optional - shows in OpenRouter dashboard
    }

    url = config["api_url"]

    # Allow overriding model via env var (handy when OpenRouter catalog changes)
    env_model = os.getenv("OPENROUTER_MODEL")
    base_model = (env_model or config.get("model") or "").strip()

    models_to_try = []
    if base_model:
        models_to_try.append(base_model)
        # If the model uses ':free' suffix, also try without it (and vice versa).
        if base_model.endswith(":free"):
            models_to_try.append(base_model[: -len(":free")])
        else:
            models_to_try.append(f"{base_model}:free")

    # De-dupe while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    last_status: Optional[int] = None
    last_text: str = ""

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                return {
                    "content": data["choices"][0]["message"]["content"],
                    "provider": "openrouter",
                    "model": model_name,
                }
        except httpx.HTTPStatusError as e:
            last_status = e.response.status_code
            last_text = e.response.text[:500]

            # If OpenRouter says the model has no endpoint (404), try next variant.
            if last_status == 404:
                continue

            print(f"Error querying OpenRouter: HTTP {last_status}: {last_text}")
            return None
        except Exception as e:
            print(f"Error querying OpenRouter: {type(e).__name__}: {e}")
            return None

    if last_status is not None:
        print(f"Error querying OpenRouter: HTTP {last_status}: {last_text}")
    else:
        print("Error querying OpenRouter: No model configured")
    return None


# ============================================================================
# UNIFIED QUERY INTERFACE
# ============================================================================

# Map provider names to their query functions
PROVIDER_CLIENTS = {
    "groq": query_groq,
    "sambanova": query_sambanova,
    "google": query_google,
    "mistral": query_mistral,
    "cohere": query_cohere,
    "huggingface": query_huggingface,
    "openrouter": query_openrouter,
}


async def query_model(
    provider: str, messages: List[Dict[str, str]], timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a model by provider name.

    Args:
        provider: Provider key (groq, sambanova, google, mistral, cohere, huggingface)
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and 'provider', or None if failed
    """
    query_func = PROVIDER_CLIENTS.get(provider)
    if query_func is None:
        print(f"Unknown provider: {provider}")
        return None

    return await query_func(messages, timeout)


async def query_models_parallel(
    providers: List[str], messages: List[Dict[str, str]], use_failover: bool = True
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple providers in parallel.

    Args:
        providers: List of provider keys
        messages: List of message dicts to send to each provider
        use_failover: If True, use HuggingFace as failover for failed queries

    Returns:
        Dict mapping provider key to response dict (or None if failed)
    """
    import asyncio
    from .config import get_failover_models

    # Create tasks for all providers
    tasks = [query_model(provider, messages) for provider in providers]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map providers to their responses
    results = {provider: response for provider, response in zip(providers, responses)}

    # Check for failures and use failover if enabled
    if use_failover:
        failed_providers = [p for p, r in results.items() if r is None]
        failover_models = get_failover_models()  # DYNAMIC

        if failed_providers and failover_models:
            print(f"🛡️ Activating failover for: {failed_providers}")
            # Try each failover model until one succeeds
            failover_response = None
            failover_model_used = None
            for failover_model in failover_models:
                if failover_model not in providers:
                    failover_response = await query_model(failover_model, messages)
                    if failover_response:
                        failover_model_used = failover_model
                        break

            if failover_response:
                for provider in failed_providers:
                    results[provider] = {
                        **failover_response,
                        "is_failover": True,
                        "original_provider": provider,
                        "original_display_name": get_provider_display_name(provider),
                        "failover_model_used": failover_model_used,
                    }

    return results


def get_provider_display_name(provider: str) -> str:
    """Get the display name for a provider."""
    member = COUNCIL_MEMBERS.get(provider)
    if member:
        return member["name"]
    return provider


def get_provider_role(provider: str) -> str:
    """Get the role description for a provider."""
    member = COUNCIL_MEMBERS.get(provider)
    if member:
        return member["role"]
    return "Unknown"
