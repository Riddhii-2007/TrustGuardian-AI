"""
OpenRouter LLM provider implementation.

OpenRouter exposes an OpenAI-compatible API that routes to hundreds of models
(GPT, Claude, Gemini, DeepSeek, Llama, Qwen, etc.) through a single endpoint.

Setting LLM_PROVIDER=openrouter and OPENROUTER_MODEL=<any-model-slug> in .env
is all that is needed to switch the entire AI Analysis layer to any model.
No code changes are required.

Configuration (backend/.env):
    OPENROUTER_API_KEY  - Your OpenRouter API key (sk-or-v1-...)
    OPENROUTER_BASE_URL - https://openrouter.ai/api/v1  (default)
    OPENROUTER_MODEL    - Model slug, e.g. deepseek/deepseek-chat-v3-0324
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.config import settings
from app.models.llm import LLMProviderResult
from app.services.exceptions import LLMProviderError
from app.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseLLMProvider):
    """LLM provider for OpenRouter — a unified gateway to 200+ models.

    Switching models requires ONLY changing OPENROUTER_MODEL in .env.
    No code modifications are needed.

    Examples of valid OPENROUTER_MODEL values:
        deepseek/deepseek-chat-v3-0324
        openai/gpt-4o
        anthropic/claude-3-5-sonnet
        google/gemini-2.5-pro
        meta-llama/llama-3.3-70b-instruct
        qwen/qwen-2.5-72b-instruct
    """

    def __init__(self) -> None:
        self._model    = settings.OPENROUTER_MODEL
        self._base_url = settings.OPENROUTER_BASE_URL or _DEFAULT_BASE_URL
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Lazily initialize the AsyncOpenAI client pointed at OpenRouter."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=self._base_url,
            )
        return self._client

    @property
    def name(self) -> str:
        return "openrouter"

    def validate(self) -> None:
        """Validate required OpenRouter configuration.

        Raises:
            LLMProviderError: If API key or model is missing.
        """
        if not settings.OPENROUTER_API_KEY:
            raise LLMProviderError(
                "OPENROUTER_API_KEY is not configured. "
                "Set it in your .env file: OPENROUTER_API_KEY=sk-or-v1-...",
                provider=self.name,
            )
        if not self._model:
            raise LLMProviderError(
                "OPENROUTER_MODEL is not configured. "
                "Set it in your .env file, e.g.: OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324",
                provider=self.name,
            )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> LLMProviderResult:
        """Send prompts to OpenRouter and return structured result.

        The model used is controlled entirely by OPENROUTER_MODEL in .env.
        Changing that value switches the AI model with zero code changes.

        Args:
            system_prompt: System-level instructions for the model.
            user_prompt:   User content to analyze.
            temperature:   Sampling temperature (0.0 = deterministic).

        Returns:
            LLMProviderResult with response content, token usage, and metadata.

        Raises:
            LLMProviderError: If the OpenRouter API call fails.
        """
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=temperature,
                # Ask for JSON output — most models on OpenRouter honour this
                response_format={"type": "json_object"},
            )

            content     = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            finish      = response.choices[0].finish_reason if response.choices else "unknown"

            logger.info(
                "OpenRouterProvider success: model=%s tokens=%d finish=%s",
                self._model, tokens_used, finish,
            )

            return LLMProviderResult(
                content=content,
                tokens_used=tokens_used,
                raw_response={
                    "model":         self._model,
                    "finish_reason": finish,
                },
            )

        except Exception as e:
            raise LLMProviderError(
                f"OpenRouter API call failed (model={self._model}): {e}",
                provider=self.name,
            ) from e
