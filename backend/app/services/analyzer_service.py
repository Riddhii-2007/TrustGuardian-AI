from app.models.request import AnalysisResult, PsychologyFactors
from app.services.llm_service import llm_service
import json

class AnalyzerService:
    """
    Orchestrates the analysis of business requests using LLMs (Groq/Llama 3).
    """

    SYSTEM_PROMPT = """
    You are an expert cybersecurity analyst specializing in Business Email Compromise (BEC) and social engineering.
    Analyze the following business request (email or message) and evaluate it across 5 psychological vectors.
    You MUST output valid JSON only, matching the exact structure below. Do not include markdown blocks or any other text.
    
    Scores must be a float between 0.0 and 1.0.
    Calculate an overall risk_score from 0 to 100 based on the manipulation tactics.
    Set risk_level to one of: "Safe", "Low", "Medium", "High", "Critical".
    Extract specific suspicious phrases or tactics into the 'flags' array.
    Provide a concise 1-2 sentence 'explanation' of your decision.

    Expected JSON format:
    {
        "risk_score": 85,
        "risk_level": "High",
        "psychology": {
            "urgency": 0.9,
            "authority": 0.8,
            "fear": 0.2,
            "familiarity": 0.1,
            "intent": 0.7
        },
        "flags": ["Urgent wire transfer", "CEO impersonation"],
        "explanation": "High urgency and authority are used to pressure the target into bypassing normal financial controls."
    }
    """

    async def analyze_request(self, content: str) -> AnalysisResult:
        """
        Sends the request content to the LLM and maps the JSON response to the AnalysisResult model.
        """
        if not content.strip():
            # Return safe default if empty
            return AnalysisResult(
                risk_score=0,
                risk_level="Safe",
                psychology=PsychologyFactors(urgency=0, authority=0, fear=0, familiarity=0, intent=0),
                flags=[],
                explanation="No content provided for analysis."
            )

        prompt = f"Analyze this business request:\n\n{content}"
        
        result_dict = await llm_service.generate_json(prompt, self.SYSTEM_PROMPT)
        
        try:
            # Map dict to Pydantic model
            psychology = PsychologyFactors(**result_dict.get("psychology", {}))
            return AnalysisResult(
                risk_score=result_dict.get("risk_score", 50),
                risk_level=result_dict.get("risk_level", "Medium"),
                psychology=psychology,
                flags=result_dict.get("flags", []),
                explanation=result_dict.get("explanation", "Analysis completed.")
            )
        except Exception as e:
            # Fallback if LLM hallucinations break the schema
            return AnalysisResult(
                risk_score=50,
                risk_level="Unknown",
                psychology=PsychologyFactors(urgency=0, authority=0, fear=0, familiarity=0, intent=0),
                flags=[f"Schema parsing error: {str(e)}"],
                explanation="The AI generated a malformed response."
            )

analyzer_service = AnalyzerService()
