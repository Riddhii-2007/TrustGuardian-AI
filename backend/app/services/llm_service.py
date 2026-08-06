import json
from groq import AsyncGroq
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """
    Client for interacting with Groq API for fast LLM inference using Llama 3.
    """
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant" # Updated to supported model

    async def generate_json(self, prompt: str, system_prompt: str = "") -> dict:
        """
        Calls Groq API and guarantees a JSON response.
        """
        try:
            if not settings.GROQ_API_KEY:
                logger.warning("GROQ_API_KEY is missing. Using fallback mock data.")
                return self._fallback_analysis()

            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            content = chat_completion.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> dict:
        """Safe fallback if the API fails or key is missing."""
        return {
            "risk_score": 50,
            "risk_level": "Medium",
            "psychology": {
                "urgency": 0.5,
                "authority": 0.5,
                "fear": 0.1,
                "familiarity": 0.5,
                "intent": 0.5
            },
            "flags": ["Analysis failed. Showing fallback data."],
            "explanation": "The AI analysis engine is currently unavailable."
        }

llm_service = LLMService()
