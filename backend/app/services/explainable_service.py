class ExplainableService:
    """
    Service to generate human-readable explanations of AI decisions.
    """

    async def generate_explanation(self, context_data: dict) -> str:
        return "Based on the analysis, this request flagged high urgency and authority which is common in phishing attempts."

explainable_service = ExplainableService()
