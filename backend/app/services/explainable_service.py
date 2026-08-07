import logging
from app.prompts.explainable_prompt import EXPLAINABLE_SYSTEM_PROMPT
from app.services.llm_router import llm_router

logger = logging.getLogger(__name__)


class ExplainableService:
    """
    Service to generate human-readable explanations of AI decisions.
    """

    def __init__(self, llm_service_instance=None):
        self.llm_service = llm_service_instance or llm_router

    async def generate_explanation(self, context_data: dict) -> str:
        """
        Generate a dynamic explanation of a trust scan decision using the LLM.
        """
        llm_fallback = ""
        if isinstance(context_data, dict):
            llm_analysis = context_data.get("llm_analysis") or {}
            if isinstance(llm_analysis, dict):
                llm_fallback = llm_analysis.get("explanation") or ""

        try:
            user_prompt = (
                "Based on the provided security scan evidence, generate a clear, "
                "non-technical explanation paragraph of the trust decision suitable "
                "for a business analyst.\n\n"
                "You MUST return your response as a JSON object with a single 'explanation' "
                "key containing the paragraph. Example:\n"
                '{"explanation": "This request is flagged as high risk because..."}'
            )

            response = await self.llm_service.analyze(
                system_prompt=EXPLAINABLE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                evidence=context_data,
            )

            analysis = response.analysis
            if isinstance(analysis, dict) and "explanation" in analysis:
                explanation = analysis["explanation"]
                if explanation and isinstance(explanation, str):
                    return explanation.strip()

            # If response is a string (e.g. LLM didn't return valid JSON but returned text directly)
            if isinstance(analysis, str) and analysis.strip():
                return analysis.strip()

        except Exception as e:
            logger.warning(f"Failed to generate dynamic explanation: {e}")

        # Fallback path if LLM call failed or response could not be parsed
        return llm_fallback or "Analysis completed."


explainable_service = ExplainableService()

