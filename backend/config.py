"""Configuration for the LLM Council - Grand Council V11 (6 Motorlu Hibrit Jet)."""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# 🚀 GRAND COUNCIL V11 - 6 API CONFIGURATION
# ============================================================================

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# ============================================================================
# Council Members Configuration
# ============================================================================

COUNCIL_MEMBERS = {
    "groq": {
        "name": "Groq Cloud",
        "icon": "⚡",
        "model": "llama-3.3-70b-versatile",
        "role": "Hız ve Teknik Uzmanlık",
        "api_url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key_env": "GROQ_API_KEY",
    },
    "sambanova": {
        "name": "SambaNova Cloud",
        "icon": "🟠",
        "model": "Meta-Llama-3.1-8B-Instruct",
        "role": "Konsey Başkanı (Chairman)",
        "api_url": "https://api.sambanova.ai/v1/chat/completions",
        "api_key_env": "SAMBANOVA_API_KEY",
    },
    "google": {
        "name": "Google AI Studio",
        "icon": "🌐",
        "model": "gemini-2.0-flash-lite",
        "role": "Mantık ve Geniş Bağlam Uzmanı",
        "api_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "api_key_env": "GOOGLE_AI_API_KEY",
    },
    "mistral": {
        "name": "Mistral AI",
        "icon": "🌀",
        "model": "mistral-large-latest",
        "role": "Kodlama ve Yaratıcı Yazarlık",
        "api_url": "https://api.mistral.ai/v1/chat/completions",
        "api_key_env": "MISTRAL_API_KEY",
    },
    "cohere": {
        "name": "Cohere",
        "icon": "📄",
        "model": "command-a-03-2025",
        "role": "Analiz ve Eleştirmen",
        "api_url": "https://api.cohere.com/v2/chat",
        "api_key_env": "COHERE_API_KEY",
    },
    "huggingface": {
        "name": "Hugging Face",
        "icon": "🤗",
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "role": "Yedek Kuvvet (Failover)",
        "api_url": "https://router.huggingface.co/v1/chat/completions",
        "api_key_env": "HUGGINGFACE_API_KEY",
    },
    "openrouter": {
        "name": "OpenRouter",
        "icon": "🔀",
        "model": "meta-llama/llama-3.1-8b-instruct",
        "role": "Çoklu Model Gateway (Failover)",
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

# ============================================================================
# Dynamic Configuration Functions
# ============================================================================


def get_council_models() -> list:
    """Get active council models from settings (dynamic)"""
    try:
        from .settings import get_active_council_models

        return get_active_council_models()
    except Exception:
        return ["groq", "google", "mistral", "cohere"]  # Fallback default


def get_chairman_model() -> str:
    """Get chairman model from settings (dynamic)"""
    try:
        from .settings import get_chairman_model as get_chairman

        return get_chairman()
    except Exception:
        return "sambanova"  # Fallback default


def get_failover_models() -> list:
    """Get failover models from settings (dynamic)"""
    try:
        from .settings import get_failover_models as get_failovers

        return get_failovers()
    except Exception:
        return ["huggingface"]  # Fallback default


# Legacy constants for backward compatibility (will be overridden by functions)
COUNCIL_MODELS = ["groq", "google", "mistral", "cohere"]
CHAIRMAN_MODEL = "sambanova"
FAILOVER_MODEL = "huggingface"

# ============================================================================
# Google model fallback chain
# ============================================================================
# If Google returns rate-limit (HTTP 429), the client can try these models in order.
# Keep this list minimal and within models you are comfortable using.
GOOGLE_MODEL_FALLBACKS = [
    # Prefer cheap/fast text models first
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    # Experimental / preview variants (may be more limited/unstable)
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash-preview-image",
    # Then higher-capacity text models (may have different limits)
    "gemini-2.5-flash",
    "gemini-3-flash",
    # Pro models last (slower / lower RPM)
    "gemini-2.5-pro",
    "gemini-3-pro",
    # Gemma (open models). Availability can vary by account/region.
    "gemma-3-1b",
    "gemma-3-2b",
    "gemma-3-4b",
    "gemma-3-12b",
    "gemma-3-27b",
]

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "llm_council")
