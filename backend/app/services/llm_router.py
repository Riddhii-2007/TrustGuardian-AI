import asyncio
import json
import logging
import time
from typing import Any

from app.config import settings
from app.models.llm import LLMResponse
from app.services.exceptions import LLMServiceError
from app.services.providers import get_provider

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    Intelligent Multi-LLM Router that dynamically switches LLM providers (e.g. Gemini, Groq)
    when they fail (due to rate limits, timeouts, quotas, or network issues) and manages
    temporary provider cooldown states.
    """

    def __init__(self, providers_priority: list[str] | None = None) -> None:
        # Default priority order: Gemini (Primary), Groq (Secondary)
        self.priority = providers_priority or ["gemini", "groq"]
        self.cooldowns: dict[str, float] = {}

    def _is_healthy(self, provider_name: str) -> bool:
        """Check if a provider is currently out of its cooldown period."""
        cooldown_until = self.cooldowns.get(provider_name, 0.0)
        return time.time() >= cooldown_until

    def _get_healthiest_provider(self) -> str:
        """Select the first healthy provider from priority list, falling back to primary on all-cooldown."""
        for provider_name in self.priority:
            if self._is_healthy(provider_name):
                return provider_name
        
        # If all are on cooldown, log warning and use primary as best effort
        primary = self.priority[0]
        logger.warning(
            "All LLM providers %s are currently on cooldown. "
            "Falling back to primary provider: %s as best-effort.",
            self.priority,
            primary
        )
        return primary

    async def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        evidence: dict | None = None,
    ) -> LLMResponse:
        """
        Dynamically route the request to the healthiest provider, failover on error.
        """
        # Prepare context data
        full_user_prompt = user_prompt
        if evidence:
            evidence_str = json.dumps(evidence, indent=2, default=str)
            full_user_prompt = (
                f"{user_prompt}\n\n--- Evidence ---\n{evidence_str}"
            )

        last_error = None
        # Copy the priority list to attempt failover
        attempts = self.priority.copy()
        
        # Ensure we try the healthiest one first
        first_provider = self._get_healthiest_provider()
        attempts.remove(first_provider)
        attempts.insert(0, first_provider)

        for provider_name in attempts:
            start_time = time.monotonic()
            try:
                provider_instance = get_provider(provider_name)
                provider_instance.validate()

                logger.info("LLMRouter routing request to: %s", provider_name)

                provider_result = await asyncio.wait_for(
                    provider_instance.call(
                        system_prompt=system_prompt,
                        user_prompt=full_user_prompt,
                        temperature=settings.LLM_TEMPERATURE,
                    ),
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                )

                latency_ms = int((time.monotonic() - start_time) * 1000)
                analysis = self._parse_response(provider_result.content)

                logger.info(
                    "LLMRouter success: provider=%s latency_ms=%d tokens=%d",
                    provider_name,
                    latency_ms,
                    provider_result.tokens_used,
                )

                return LLMResponse(
                    analysis=analysis,
                    confidence=None,
                    provider=provider_name,
                    latency_ms=latency_ms,
                    tokens_used=provider_result.tokens_used,
                    raw_response=provider_result.raw_response,
                )

            except Exception as e:
                cooldown_until = time.time() + settings.LLM_ROUTER_COOLDOWN_SECONDS
                self.cooldowns[provider_name] = cooldown_until
                last_error = e

                logger.warning(
                    "LLMRouter provider failure: provider=%s. "
                    "Putting on cooldown for %ds. Error: %s",
                    provider_name,
                    settings.LLM_ROUTER_COOLDOWN_SECONDS,
                    str(e)
                )

        # All providers failed
        raise LLMServiceError(
            f"All configured LLM providers failed: {last_error}",
            provider="router",
            retries=len(self.priority),
        )

    async def generate_json(self, prompt: str, system_prompt: str = "") -> dict:
        """Backward-compatible prompt generation wrapper."""
        result = await self.analyze(
            system_prompt=system_prompt,
            user_prompt=prompt,
        )
        if isinstance(result.analysis, dict):
            return result.analysis
        return {"raw": result.analysis}

    @staticmethod
    def _parse_response(content: str) -> dict | str:
        """Parse LLM response content as JSON."""
        if not content or not content.strip():
            return {}
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.debug("LLM response is not valid JSON, returning raw text")
            return content


llm_router = LLMRouter()
