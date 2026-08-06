"""
Pydantic models for the LLM communication layer.

These models define the structured request/response contracts
between LLMService, providers, and callers (e.g. analyzer_service).
"""

from pydantic import BaseModel, Field


class LLMProviderResult(BaseModel):
    """Raw result returned by a provider's call() method.

    This is the internal contract between BaseLLMProvider implementations
    and LLMService. Callers should not depend on this model directly.
    """

    content: str = Field(
        ...,
        description="Raw text content returned by the LLM.",
    )
    tokens_used: int = Field(
        default=0,
        description="Total tokens consumed (prompt + completion).",
    )
    raw_response: dict = Field(
        default_factory=dict,
        description="Provider-specific metadata (model version, finish reason, etc.).",
    )


class LLMResponse(BaseModel):
    """Structured response returned by LLMService.analyze().

    This is the public contract for all callers of the LLM service.
    """

    analysis: dict | str = Field(
        ...,
        description="Parsed JSON analysis or raw text from the LLM.",
    )
    confidence: float | None = Field(
        default=None,
        description=(
            "Confidence score for the analysis. This field is NOT populated "
            "by the LLM provider. It is a placeholder to be filled by the "
            "Trust Score Engine or other downstream consumers."
        ),
    )
    provider: str = Field(
        ...,
        description="Name of the LLM provider that generated this response (e.g. 'gemini', 'groq').",
    )
    latency_ms: int = Field(
        default=0,
        description="Round-trip time for the LLM call in milliseconds.",
    )
    tokens_used: int = Field(
        default=0,
        description="Total tokens consumed by the LLM call.",
    )
    raw_response: dict = Field(
        default_factory=dict,
        description="Pass-through of provider-specific raw response metadata.",
    )
