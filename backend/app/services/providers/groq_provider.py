"""
Groq LLM provider implementation.

Preserves the existing Groq/Llama integration from the original llm_service.py.
Uses the groq SDK (AsyncGroq) which is already in requirements.txt.
Model name is read from configuration (settings.GROQ_MODEL) — never hardcoded.
"""

import logging

from groq import AsyncGroq

from app.config import settings
from app.models.llm import LLMProviderResult
from app.services.exceptions import LLMProviderError
from app.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """LLM provider for Groq inference API (Llama, Mixtral, etc.).

    Configuration:
        GROQ_API_KEY: API key for the Groq platform.
        GROQ_MODEL: Model identifier (e.g. 'llama-3.1-8b-instant').
    """

    def __init__(self) -> None:
        self._model = settings.GROQ_MODEL
        self._client: AsyncGroq | None = None

    def _get_client(self) -> AsyncGroq:
        """Lazily initialize the Groq client.

        Defers client creation until first call() to avoid import-time
        failures when GROQ_API_KEY is not yet configured.
        """
        if self._client is None:
            self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._client

    @property
    def name(self) -> str:
        return "groq"

    def validate(self) -> None:
        """Validate that GROQ_API_KEY is configured.

        Raises:
            LLMProviderError: If the API key is missing or empty.
        """
        if not settings.GROQ_API_KEY:
            raise LLMProviderError(
                "GROQ_API_KEY is not configured. "
                "Set it in your .env file or environment variables.",
                provider=self.name,
            )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> LLMProviderResult:
        """Send prompts to Groq and return structured result.

        This method preserves the original Groq integration logic
        from the pre-refactor llm_service.py.

        Args:
            system_prompt: System-level instructions for the model.
            user_prompt: User content to process.
            temperature: Sampling temperature.

        Returns:
            LLMProviderResult with parsed content, token usage, and metadata.

        Raises:
            LLMProviderError: If the Groq API call fails.
        """
        try:
            # Groq requires the word "json" in the prompt when using JSON mode
            if "json" not in system_prompt.lower() and "json" not in user_prompt.lower():
                system_prompt += "\n\nPlease return the result in JSON format."

            client = self._get_client()
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self._model,
                temperature=temperature,
                response_format={"type": "json_object"},
            )

            content = chat_completion.choices[0].message.content or ""
            tokens_used = 0
            if chat_completion.usage:
                tokens_used = chat_completion.usage.total_tokens or 0

            raw_response = {
                "model": self._model,
                "finish_reason": (
                    chat_completion.choices[0].finish_reason
                    if chat_completion.choices
                    else "unknown"
                ),
            }

            return LLMProviderResult(
                content=content,
                tokens_used=tokens_used,
                raw_response=raw_response,
            )

        except Exception as e:
            raise LLMProviderError(
                f"Groq API call failed: {e}",
                provider=self.name,
            ) from e
