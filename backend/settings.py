"""
Dynamic Settings Management for LLM Council
Manages chairman, experts, and failover models at runtime
Single source of truth: config.py COUNCIL_MEMBERS
Storage: MongoDB (async) with sync wrappers
"""

import os
import asyncio
from dotenv import load_dotenv, set_key
from pathlib import Path

# Import from single source of truth
from .config import COUNCIL_MEMBERS
from .database import MongoDB

ENV_FILE = Path(__file__).parent.parent / ".env"
SETTINGS_COLLECTION = "settings"

DEFAULT_SETTINGS = {
    "chairman": "sambanova",
    "experts": ["groq", "google", "mistral", "cohere"],
}


async def _get_settings_collection():
    """Get the settings collection from MongoDB"""
    db = MongoDB.get_database()
    if db is None:
        return None
    return db[SETTINGS_COLLECTION]


async def _get_settings_from_db() -> dict:
    """Load settings from MongoDB"""
    collection = await _get_settings_collection()
    if collection is None:
        return DEFAULT_SETTINGS.copy()

    doc = await collection.find_one({"_id": "main_settings"})
    if doc:
        # Get chairman, use default only if not in document
        chairman = doc.get("chairman")
        if chairman is None:
            chairman = DEFAULT_SETTINGS["chairman"]

        # Get experts - allow empty list (for simple LLM mode)
        # Only use default if key doesn't exist in document
        if "experts" in doc:
            experts = doc["experts"]
        else:
            experts = DEFAULT_SETTINGS["experts"]

        return {
            "chairman": chairman,
            "experts": experts,
        }
    return DEFAULT_SETTINGS.copy()


async def _save_settings_to_db(settings: dict) -> bool:
    """Save settings to MongoDB"""
    collection = await _get_settings_collection()
    if collection is None:
        return False

    try:
        # Get chairman - use default only if not provided at all
        chairman = settings.get("chairman")
        if chairman is None:
            chairman = DEFAULT_SETTINGS["chairman"]

        # Get experts - allow empty list (simple LLM mode)
        # Only use default if key doesn't exist at all
        if "experts" in settings:
            experts = settings["experts"]
        else:
            experts = DEFAULT_SETTINGS["experts"]

        await collection.update_one(
            {"_id": "main_settings"},
            {
                "$set": {
                    "chairman": chairman,
                    "experts": experts,
                }
            },
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"Error saving settings to MongoDB: {e}")
        return False


def _run_async(coro):
    """Run async coroutine in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def get_all_providers() -> dict:
    """Get all providers from config (single source)"""
    return COUNCIL_MEMBERS


def get_settings() -> dict:
    """Load current settings from MongoDB and API keys from .env"""
    # Reload .env to get latest values
    load_dotenv(ENV_FILE, override=True)

    # Get settings from MongoDB
    settings = _run_async(_get_settings_from_db())

    # Initialize api_keys
    settings["api_keys"] = {}

    # Load API keys from .env (masked for display)
    for provider_id, provider_info in COUNCIL_MEMBERS.items():
        env_key = provider_info.get("api_key_env", "")
        env_value = os.getenv(env_key) if env_key else None
        if env_value:
            # Show masked version (first 8 chars + ***)
            masked = env_value[:8] + "***" if len(env_value) > 8 else "***"
            settings["api_keys"][provider_id] = masked
            settings["api_keys"][f"{provider_id}_exists"] = True
        else:
            settings["api_keys"][f"{provider_id}_exists"] = False

    # Add provider info for frontend (from single source)
    settings["all_providers"] = COUNCIL_MEMBERS

    # Calculate failover models (providers not selected as chairman or expert)
    selected = set([settings["chairman"]] + settings["experts"])
    settings["failover_models"] = [
        p for p in COUNCIL_MEMBERS.keys() if p not in selected
    ]

    return settings


async def get_settings_async() -> dict:
    """Async version of get_settings for use in async context"""
    # Reload .env to get latest values
    load_dotenv(ENV_FILE, override=True)

    # Get settings from MongoDB
    settings = await _get_settings_from_db()

    # Initialize api_keys
    settings["api_keys"] = {}

    # Load API keys from .env (masked for display)
    for provider_id, provider_info in COUNCIL_MEMBERS.items():
        env_key = provider_info.get("api_key_env", "")
        env_value = os.getenv(env_key) if env_key else None
        if env_value:
            masked = env_value[:8] + "***" if len(env_value) > 8 else "***"
            settings["api_keys"][provider_id] = masked
            settings["api_keys"][f"{provider_id}_exists"] = True
        else:
            settings["api_keys"][f"{provider_id}_exists"] = False

    # Add provider info for frontend (from single source)
    settings["all_providers"] = COUNCIL_MEMBERS

    # Calculate failover models
    selected = set([settings["chairman"]] + settings["experts"])
    settings["failover_models"] = [
        p for p in COUNCIL_MEMBERS.keys() if p not in selected
    ]

    return settings


def save_settings(settings: dict) -> bool:
    """Save settings to MongoDB and update .env for API keys"""
    try:
        # Save to MongoDB
        success = _run_async(_save_settings_to_db(settings))
        if not success:
            print("Warning: Could not save to MongoDB")

        # Update .env file with API keys
        if settings.get("api_keys"):
            for provider_id, api_key in settings["api_keys"].items():
                # Skip _exists flags and masked values
                if "_exists" in provider_id or (api_key and "***" in api_key):
                    continue
                if api_key and provider_id in COUNCIL_MEMBERS:
                    env_key = COUNCIL_MEMBERS[provider_id].get("api_key_env", "")
                    if env_key:
                        set_key(str(ENV_FILE), env_key, api_key)

        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


async def save_settings_async(settings: dict) -> bool:
    """Async version of save_settings"""
    try:
        # Save to MongoDB
        success = await _save_settings_to_db(settings)
        if not success:
            print("Warning: Could not save to MongoDB")

        # Update .env file with API keys
        if settings.get("api_keys"):
            for provider_id, api_key in settings["api_keys"].items():
                if "_exists" in provider_id or (api_key and "***" in api_key):
                    continue
                if api_key and provider_id in COUNCIL_MEMBERS:
                    env_key = COUNCIL_MEMBERS[provider_id].get("api_key_env", "")
                    if env_key:
                        set_key(str(ENV_FILE), env_key, api_key)

        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def reload_env():
    """Reload environment variables from .env file"""
    load_dotenv(ENV_FILE, override=True)


def get_active_council_models() -> list:
    """Get list of active expert provider IDs for council"""
    settings = get_settings()
    return settings.get("experts", DEFAULT_SETTINGS["experts"])


async def get_active_council_models_async() -> list:
    """Async version for use in async context"""
    settings = await get_settings_async()
    return settings.get("experts", DEFAULT_SETTINGS["experts"])


def get_chairman_model() -> str:
    """Get the chairman provider ID"""
    settings = get_settings()
    return settings.get("chairman", DEFAULT_SETTINGS["chairman"])


async def get_chairman_model_async() -> str:
    """Async version for use in async context"""
    settings = await get_settings_async()
    return settings.get("chairman", DEFAULT_SETTINGS["chairman"])


def get_failover_models() -> list:
    """Get list of failover provider IDs (unselected providers)"""
    settings = get_settings()
    return settings.get("failover_models", ["huggingface"])
