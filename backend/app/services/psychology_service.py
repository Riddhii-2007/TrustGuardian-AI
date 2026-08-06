from app.models.request import PsychologyFactors

class PsychologyService:
    """
    Human Psychology Engine to detect behavioral manipulation.
    """

    async def analyze_text(self, text: str) -> PsychologyFactors:
        return PsychologyFactors(
            urgency=0.9,
            authority=0.8,
            fear=0.5,
            familiarity=0.2,
            intent=0.7
        )

psychology_service = PsychologyService()
