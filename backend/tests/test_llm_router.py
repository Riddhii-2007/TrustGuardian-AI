import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from app.services.llm_router import LLMRouter
from app.models.llm import LLMProviderResult
from app.services.exceptions import LLMServiceError


@pytest.mark.asyncio
async def test_router_primary_success():
    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.call = AsyncMock(return_value=LLMProviderResult(
        content='{"explanation": "Gemini success"}',
        tokens_used=15,
        raw_response={"model": "gemini-2.5-flash"}
    ))

    router = LLMRouter(providers_priority=["gemini", "groq"])

    with patch("app.services.llm_router.get_provider", return_value=mock_gemini):
        response = await router.analyze("system", "user")
        assert response.provider == "gemini"
        assert response.analysis == {"explanation": "Gemini success"}
        mock_gemini.call.assert_called_once()


@pytest.mark.asyncio
async def test_router_failover_to_secondary():
    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.call = AsyncMock(side_effect=Exception("Gemini quota exceeded"))

    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.call = AsyncMock(return_value=LLMProviderResult(
        content='{"explanation": "Groq fallback success"}',
        tokens_used=20,
        raw_response={"model": "llama-3.1-8b-instant"}
    ))

    # Helper function to return different mock based on name
    def get_mock_provider(name):
        if name == "gemini":
            return mock_gemini
        return mock_groq

    router = LLMRouter(providers_priority=["gemini", "groq"])

    with patch("app.services.llm_router.get_provider", side_effect=get_mock_provider):
        response = await router.analyze("system", "user")
        assert response.provider == "groq"
        assert response.analysis == {"explanation": "Groq fallback success"}
        # Gemini should be in cooldown now
        assert not router._is_healthy("gemini")
        assert router._is_healthy("groq")


@pytest.mark.asyncio
async def test_router_all_cooldown_fallback():
    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.call = AsyncMock(return_value=LLMProviderResult(
        content='{"explanation": "Gemini fallback success"}',
        tokens_used=15,
        raw_response={"model": "gemini-2.5-flash"}
    ))

    router = LLMRouter(providers_priority=["gemini", "groq"])
    # Put both on cooldown manually
    router.cooldowns["gemini"] = time.time() + 100
    router.cooldowns["groq"] = time.time() + 100

    with patch("app.services.llm_router.get_provider", return_value=mock_gemini):
        response = await router.analyze("system", "user")
        # Should fall back to trying gemini anyway
        assert response.provider == "gemini"
        assert response.analysis == {"explanation": "Gemini fallback success"}


@pytest.mark.asyncio
async def test_router_all_fail():
    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.call = AsyncMock(side_effect=Exception("Gemini error"))

    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.call = AsyncMock(side_effect=Exception("Groq error"))

    def get_mock_provider(name):
        if name == "gemini":
            return mock_gemini
        return mock_groq

    router = LLMRouter(providers_priority=["gemini", "groq"])

    with patch("app.services.llm_router.get_provider", side_effect=get_mock_provider):
        with pytest.raises(LLMServiceError) as exc_info:
            await router.analyze("system", "user")
        assert "All configured LLM providers failed" in str(exc_info.value)
        assert not router._is_healthy("gemini")
        assert not router._is_healthy("groq")
