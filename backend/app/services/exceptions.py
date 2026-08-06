"""
Exceptions for the LLM service layer.

Separated from models to maintain a clean boundary:
models contain Pydantic schemas, exceptions contain error types.
"""


class LLMServiceError(Exception):
    """Raised when the LLM service encounters an unrecoverable error.

    Attributes:
        message: Human-readable error description.
        provider: Name of the provider that failed (e.g. 'gemini', 'groq').
        retries: Number of retry attempts made before raising.
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        retries: int = 0,
    ) -> None:
        self.provider = provider
        self.retries = retries
        super().__init__(message)

    def __repr__(self) -> str:
        return (
            f"LLMServiceError(message={str(self)!r}, "
            f"provider={self.provider!r}, retries={self.retries})"
        )


class LLMProviderError(LLMServiceError):
    """Raised when a specific provider fails validation or communication.

    Subclass of LLMServiceError for granular exception handling.
    """

    pass
