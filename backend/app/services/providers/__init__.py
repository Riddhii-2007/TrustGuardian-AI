"""
LLM Provider registry and factory.

Centralizes provider discovery and instantiation.
New providers are added by importing them and registering in PROVIDER_REGISTRY.
"""

from __future__ import annotations

from app.config import settings
from app.services.exceptions import LLMServiceError
from app.services.providers.base import BaseLLMProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.groq_provider import GroqProvider

# ---------------------------------------------------------------------------
# Provider Registry
#
# To add a new provider:
#   1. Create the provider class in a new file (e.g. openai_provider.py)
#   2. Import it here
#   3. Add a single entry to PROVIDER_REGISTRY
#
# No changes to LLMService or existing providers are required.
# ---------------------------------------------------------------------------
PROVIDER_REGISTRY: dict[str, type[BaseLLMProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


def get_provider(provider_name: str | None = None) -> BaseLLMProvider:
    """Factory: instantiate the configured LLM provider.

    Note: This does NOT call validate(). Validation is deferred to the
    first LLMService call so the module-level singleton can be created
    at import time without requiring API keys to be configured.

    Args:
        provider_name: Provider identifier (e.g. 'gemini', 'groq').
            Falls back to settings.LLM_PROVIDER if not specified.

    Returns:
        A BaseLLMProvider instance (not yet validated).

    Raises:
        LLMServiceError: If the provider name is unknown.
    """
    name = (provider_name or settings.LLM_PROVIDER).lower().strip()

    provider_class = PROVIDER_REGISTRY.get(name)
    if provider_class is None:
        available = ", ".join(sorted(PROVIDER_REGISTRY.keys()))
        raise LLMServiceError(
            f"Unknown LLM provider: '{name}'. "
            f"Available providers: {available}",
            provider=name,
        )

    return provider_class()


__all__ = [
    "BaseLLMProvider",
    "GeminiProvider",
    "GroqProvider",
    "PROVIDER_REGISTRY",
    "get_provider",
]
