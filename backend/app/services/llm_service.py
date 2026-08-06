"""
Provider-agnostic LLM communication layer.

This service is the ONLY interface between the application and LLM providers.
It handles prompt forwarding, retries, timeouts, and structured responses.

Responsibilities:
    ✓ Prepare requests (merge evidence into prompts)
    ✓ Call configured LLM provider
    ✓ Parse structured JSON responses
    ✓ Handle retries with exponential backoff
    ✓ Handle errors and timeouts
    ✓ Return structured LLMResponse

NOT responsible for:
    ✗ Trust score calculation
    ✗ Phishing analysis logic
    ✗ VirusTotal / Neo4j queries
    ✗ Database reads
    ✗ Report building
    ✗ Psychology scoring
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time

from app.config import settings
from app.models.llm import LLMProviderResult, LLMResponse
from app.services.exceptions import LLMProviderError, LLMServiceError
from app.services.providers import BaseLLMProvider, get_provider

logger = logging.getLogger(__name__)


class LLMService:
    """Provider-agnostic LLM service with retry logic and structured responses.

    Supports dependency injection: pass a custom provider to the constructor
    for testing or runtime provider switching. Falls back to the configured
    default provider (settings.LLM_PROVIDER) if none is supplied.

    Usage:
        # Default provider from config
        service = LLMService()

        # Explicit provider injection
        from app.services.providers import GeminiProvider
        service = LLMService(provider=GeminiProvider())

        # New public API
        result = await service.analyze(
            system_prompt="You are a security analyst.",
            user_prompt="Analyze this email...",
            evidence={"sender": "ceo@company.com"},
        )

        # Backward-compatible API (used by analyzer_service.py)
        result_dict = await service.generate_json(prompt, system_prompt)
    """

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        """Initialize the LLM service.

        Args:
            provider: Optional provider instance for dependency injection.
                If None, the provider is resolved from settings.LLM_PROVIDER
                via the provider factory.
        """
        self._provider = provider or self._resolve_provider()
        logger.info("LLMService initialized with provider: %s", self._provider.name)

    def _resolve_provider(self) -> BaseLLMProvider:
        """Resolve the provider from configuration.

        Returns:
            A validated BaseLLMProvider instance.
        """
        try:
            return get_provider()
        except LLMServiceError:
            # Re-raise configuration errors as-is
            raise
        except Exception as e:
            raise LLMServiceError(
                f"Failed to initialize LLM provider: {e}",
            ) from e

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        evidence: dict | None = None,
    ) -> LLMResponse:
        """Provider-agnostic LLM call with retries and structured response.

        This is the primary public API. The caller supplies prompts and
        optional evidence; this service forwards them to the configured
        LLM provider and returns a structured response.

        Args:
            system_prompt: System-level instructions for the LLM.
            user_prompt: User-facing content to analyze.
            evidence: Optional structured evidence dict. When provided,
                it is serialized to JSON and appended to the user prompt.

        Returns:
            LLMResponse containing the parsed analysis, provider name,
            latency, token usage, and raw response metadata.
            The 'confidence' field is None — it is a placeholder for
            the Trust Score Engine, not populated by the LLM provider.

        Raises:
            LLMServiceError: After all retry attempts are exhausted.
        """
        # Merge evidence into user prompt if provided
        full_user_prompt = user_prompt
        if evidence:
            evidence_str = json.dumps(evidence, indent=2, default=str)
            full_user_prompt = (
                f"{user_prompt}\n\n--- Evidence ---\n{evidence_str}"
            )

        start_time = time.monotonic()

        provider_result = await self._call_with_retry(
            system_prompt=system_prompt,
            user_prompt=full_user_prompt,
        )

        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Parse JSON response, fall back to raw text
        analysis = self._parse_response(provider_result.content)

        response = LLMResponse(
            analysis=analysis,
            confidence=None,  # Placeholder for Trust Score Engine
            provider=self._provider.name,
            latency_ms=latency_ms,
            tokens_used=provider_result.tokens_used,
            raw_response=provider_result.raw_response,
        )

        logger.info(
            "LLM call completed: provider=%s latency_ms=%d tokens=%d",
            response.provider,
            response.latency_ms,
            response.tokens_used,
        )

        return response

    async def generate_json(self, prompt: str, system_prompt: str = "") -> dict:
        """Backward-compatible wrapper for existing callers.

        Maps the legacy (prompt, system_prompt) signature to the new
        analyze() method and returns a plain dict for compatibility.

        Used by: analyzer_service.py
            ``result_dict = await llm_service.generate_json(prompt, self.SYSTEM_PROMPT)``

        Args:
            prompt: User prompt text.
            system_prompt: System prompt text.

        Returns:
            Parsed dict from the LLM response. If the LLM returns
            non-JSON text, wraps it as {"raw": "..."}.
        """
        result = await self.analyze(
            system_prompt=system_prompt,
            user_prompt=prompt,
        )
        if isinstance(result.analysis, dict):
            return result.analysis
        return {"raw": result.analysis}

    # ------------------------------------------------------------------
    # Internal: Retry Logic
    # ------------------------------------------------------------------

    async def _call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMProviderResult:
        """Call the provider with exponential backoff retry logic.

        Retries on transient failures with configurable max attempts.
        Each retry doubles the delay and adds random jitter to prevent
        thundering herd effects.

        Args:
            system_prompt: System-level instructions.
            user_prompt: User-facing content.

        Returns:
            LLMProviderResult from a successful provider call.

        Raises:
            LLMServiceError: After all retries are exhausted.
        """
        max_retries = settings.LLM_MAX_RETRIES
        timeout = settings.LLM_TIMEOUT_SECONDS
        base_delay = 1.0
        last_error: Exception | None = None

        # Validate provider configuration before attempting any calls
        self._provider.validate()

        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._provider.call(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=settings.LLM_TEMPERATURE,
                    ),
                    timeout=timeout,
                )
                if attempt > 0:
                    logger.info(
                        "LLM call succeeded on retry %d/%d (provider=%s)",
                        attempt,
                        max_retries,
                        self._provider.name,
                    )
                return result

            except asyncio.TimeoutError:
                last_error = LLMServiceError(
                    f"LLM call timed out after {timeout}s",
                    provider=self._provider.name,
                    retries=attempt,
                )
                logger.warning(
                    "LLM call timed out: provider=%s attempt=%d/%d timeout=%ds",
                    self._provider.name,
                    attempt + 1,
                    max_retries + 1,
                    timeout,
                )

            except LLMProviderError as e:
                last_error = e
                logger.warning(
                    "LLM provider error: provider=%s attempt=%d/%d error=%s",
                    self._provider.name,
                    attempt + 1,
                    max_retries + 1,
                    str(e),
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    "Unexpected LLM error: provider=%s attempt=%d/%d error=%s",
                    self._provider.name,
                    attempt + 1,
                    max_retries + 1,
                    str(e),
                )

            # Exponential backoff with jitter (skip delay on last attempt)
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.info(
                    "Retrying in %.1fs (attempt %d/%d, provider=%s)",
                    delay,
                    attempt + 1,
                    max_retries,
                    self._provider.name,
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise LLMServiceError(
            f"LLM call failed after {max_retries + 1} attempts: {last_error}",
            provider=self._provider.name,
            retries=max_retries,
        )

    # ------------------------------------------------------------------
    # Internal: Response Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(content: str) -> dict | str:
        """Parse LLM response content as JSON.

        Attempts to parse the response as JSON. If parsing fails,
        returns the raw text — the caller decides how to handle it.

        Args:
            content: Raw text response from the LLM.

        Returns:
            Parsed dict if valid JSON, otherwise the raw string.
        """
        if not content or not content.strip():
            return {}

        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.debug(
                "LLM response is not valid JSON, returning raw text "
                "(length=%d chars)",
                len(content),
            )
            return content


# ---------------------------------------------------------------------------
# Module-level singleton (backward compatibility)
#
# This preserves the existing import used by analyzer_service.py:
#   from app.services.llm_service import llm_service
# ---------------------------------------------------------------------------
llm_service = LLMService()
