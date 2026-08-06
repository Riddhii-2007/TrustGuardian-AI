"""
Google Gemini LLM provider implementation.

Uses the official google-genai SDK to communicate with Gemini models.
Model name is read from configuration (settings.GEMINI_MODEL) — never hardcoded.
"""

import logging

from google import genai
from google.genai import types

from app.config import settings
from app.models.llm import LLMProviderResult
from app.services.exceptions import LLMProviderError
from app.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """LLM provider for Google Gemini models.

    Configuration:
        GEMINI_API_KEY: API key for Google AI Studio / Vertex AI.
        GEMINI_MODEL: Model identifier (e.g. 'gemini-2.5-flash').
    """

    def __init__(self) -> None:
        self._model = settings.GEMINI_MODEL
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize the Gemini client.

        The google-genai SDK validates the API key at Client construction time,
        so we defer creation until the first call() to avoid import-time failures
        when the key is not yet configured.
        """
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    @property
    def name(self) -> str:
        return "gemini"

    def validate(self) -> None:
        """Validate that GEMINI_API_KEY is configured.

        Raises:
            LLMProviderError: If the API key is missing or empty.
        """
        if not settings.GEMINI_API_KEY:
            raise LLMProviderError(
                "GEMINI_API_KEY is not configured. "
                "Set it in your .env file or environment variables.",
                provider=self.name,
            )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> LLMProviderResult:
        """Send prompts to Gemini and return structured result.

        Args:
            system_prompt: System-level instructions for the model.
            user_prompt: User content to process.
            temperature: Sampling temperature.

        Returns:
            LLMProviderResult with parsed content, token usage, and metadata.

        Raises:
            LLMProviderError: If the Gemini API call fails.
        """
        try:
            client = self._get_client()
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )

            content = response.text or ""
            tokens_used = 0
            if response.usage_metadata:
                tokens_used = response.usage_metadata.total_token_count or 0

            raw_response = {
                "model": self._model,
                "finish_reason": (
                    response.candidates[0].finish_reason.name
                    if response.candidates
                    and response.candidates[0].finish_reason
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
                f"Gemini API call failed: {e}",
                provider=self.name,
            ) from e
