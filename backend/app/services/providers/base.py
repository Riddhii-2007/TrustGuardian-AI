"""
Abstract base class for LLM providers.

All provider implementations must subclass BaseLLMProvider and implement
the required interface. This enables the Open/Closed Principle: new providers
can be added without modifying LLMService or existing providers.

To add a new provider:
    1. Create a new file in app/services/providers/ (e.g. openai_provider.py)
    2. Subclass BaseLLMProvider and implement name, call(), and validate()
    3. Register the provider in providers/__init__.py PROVIDER_REGISTRY
"""

from abc import ABC, abstractmethod

from app.models.llm import LLMProviderResult


class BaseLLMProvider(ABC):
    """Abstract base class defining the provider contract.

    Providers are responsible ONLY for:
        - Communicating with their specific LLM API
        - Returning structured LLMProviderResult
        - Validating their own configuration

    Providers must NOT handle:
        - Retries or timeouts (handled by LLMService)
        - Business logic (handled by callers)
        - Prompt construction (prompts are passed through as-is)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider (e.g. 'gemini', 'groq').

        Used in logging, response metadata, and provider selection.
        """
        ...

    @abstractmethod
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> LLMProviderResult:
        """Send prompts to the LLM and return a structured result.

        Args:
            system_prompt: System-level instructions for the LLM.
            user_prompt: User-facing content/query.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).

        Returns:
            LLMProviderResult containing the raw response content,
            token usage, and provider-specific metadata.

        Raises:
            LLMProviderError: If the API call fails.
        """
        ...

    @abstractmethod
    def validate(self) -> None:
        """Validate that this provider is properly configured.

        Should check for required API keys, valid model names, etc.

        Raises:
            LLMProviderError: If configuration is invalid or incomplete.
        """
        ...
