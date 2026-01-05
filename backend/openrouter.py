"""
LLM API Client Module - Grand Council V11

This module re-exports the new multi-provider client functions
for backward compatibility with existing code.
"""

# Re-export all functions from the new llm_clients module
from .llm_clients import (
    query_model,
    query_models_parallel,
    get_provider_display_name,
    get_provider_role,
    get_api_key,
    PROVIDER_CLIENTS,
    # Individual provider clients (for direct access if needed)
    query_groq,
    query_sambanova,
    query_google,
    query_mistral,
    query_cohere,
    query_huggingface,
)
