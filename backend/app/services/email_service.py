class EmailService:
    """
    Service to handle email processing.
    In the architecture, the frontend might connect to Gmail API via OAuth,
    and send raw email data to the backend, or the backend might do it itself.
    This service will handle parsing, extracting metadata, and preparing it for analysis.
    """

    async def process_email(self, raw_email_data: dict) -> dict:
        """Mock processing of email data"""
        return {
            "processed": True,
            "subject": raw_email_data.get("subject", "Unknown"),
            "extracted_text": "Please process this invoice immediately.",
            "sender": raw_email_data.get("sender", "unknown@example.com")
        }

email_service = EmailService()
