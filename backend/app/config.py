from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    APP_ENV: str = "production"
    SUPABASE_URL: str = "http://localhost:8000"
    SUPABASE_SERVICE_KEY: str = "default_key"
    GROQ_API_KEY: str = ""
    DEV_AUTH_BYPASS_TOKEN: str = ""

    # --- LLM Provider Configuration ---
    LLM_PROVIDER: str = "gemini"                # "gemini" | "groq" | future: "openai", "ollama"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"      # Configurable — no hardcoded model names
    GROQ_MODEL: str = "llama-3.1-8b-instant"    # Existing default preserved
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 3

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Threat Intel
    VIRUSTOTAL_API_KEY: str = ""

    # OpenRouter — model-agnostic AI gateway
    # Change OPENROUTER_MODEL in .env to switch models with zero code changes.
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = ""

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Multi-LLM Router
    LLM_ROUTER_COOLDOWN_SECONDS: int = 60

settings = Settings()
