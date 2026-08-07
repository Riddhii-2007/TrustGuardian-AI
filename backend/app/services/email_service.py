import base64
import logging
import re
import httpx

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service to handle fetching and parsing email data from Gmail API.
    """

    def __init__(self):
        self.gmail_messages_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

    async def fetch_latest_emails(self, access_token: str, max_results: int = 5) -> list[dict]:
        """
        Fetch the latest emails from Gmail API using a Google OAuth access token.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. Fetch message list
                list_url = f"{self.gmail_messages_url}?maxResults={max_results}"
                response = await client.get(list_url, headers=headers)
                response.raise_for_status()
                data = response.json()

                messages = data.get("messages", [])
                if not messages:
                    logger.info("No Gmail messages found.")
                    return []

                # 2. Fetch details for each message
                parsed_emails = []
                for msg in messages:
                    msg_id = msg.get("id")
                    if not msg_id:
                        continue

                    detail_url = f"{self.gmail_messages_url}/{msg_id}?format=full"
                    detail_res = await client.get(detail_url, headers=headers)
                    detail_res.raise_for_status()
                    detail_data = detail_res.json()

                    parsed = self.parse_gmail_message(detail_data)
                    parsed_emails.append(parsed)

                return parsed_emails

        except httpx.HTTPStatusError as e:
            logger.error(f"Gmail API request failed with status {e.response.status_code}: {e.response.text}")
            raise ValueError(f"Gmail API error: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching emails from Gmail API: {e}")
            raise ValueError(f"Failed to fetch Gmail data: {str(e)}")

    def parse_gmail_message(self, message_data: dict) -> dict:
        """
        Parse raw Gmail message resource structure into a flat dict.
        """
        msg_id = message_data.get("id", "")
        payload = message_data.get("payload", {})
        headers_list = payload.get("headers", [])

        # Map headers list to case-insensitive dict
        headers_dict = {h.get("name", "").lower(): h.get("value", "") for h in headers_list}

        # Extract specific header fields
        from_val = headers_dict.get("from", "unknown@example.com")
        subject = headers_dict.get("subject", "No Subject")
        date_str = headers_dict.get("date", "")
        auth_results = headers_dict.get("authentication-results", "")

        # Parse sender email address out of the From header
        sender_email = self._extract_email_address(from_val)

        # Extract message body content
        content = self._extract_body(payload)

        # Build clean headers dict to pass to ThreatIntelService
        headers_to_pass = {}
        if auth_results:
            headers_to_pass["Authentication-Results"] = auth_results

        return {
            "id": msg_id,
            "subject": subject,
            "sender": sender_email,
            "date": date_str,
            "content": content,
            "headers": headers_to_pass
        }

    @staticmethod
    def _extract_email_address(from_header: str) -> str:
        """Extract plain email address (e.g. 'john@example.com') from From header value."""
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
        if email_match:
            return email_match.group(0).lower().strip()
        return from_header.strip()

    def _extract_body(self, payload: dict) -> str:
        """
        Recursively extract plain text body content from Gmail MIME payload.
        """
        body = payload.get("body", {})
        data = body.get("data", "")
        mime_type = payload.get("mimeType", "")

        # If data is present directly at this level and is plain text, decode it
        if data and mime_type == "text/plain":
            return self._decode_base64url(data)

        # If this is a multipart message, recursively search parts
        parts = payload.get("parts", [])
        text_content = ""
        html_content = ""

        for part in parts:
            part_mime = part.get("mimeType", "")
            part_body = part.get("body", {})
            part_data = part_body.get("data", "")

            if part_data:
                decoded = self._decode_base64url(part_data)
                if part_mime == "text/plain":
                    text_content += decoded
                elif part_mime == "text/html":
                    html_content += decoded
            
            # Recurse if there are subparts
            if "parts" in part:
                recurse_content = self._extract_body(part)
                if recurse_content:
                    text_content += recurse_content

        # Prefer plain text content, fallback to html content
        return text_content.strip() or html_content.strip()

    @staticmethod
    def _decode_base64url(base64_str: str) -> str:
        """Decode base64url encoded strings safely, restoring padding if missing."""
        try:
            # Add back missing padding characters
            padding = len(base64_str) % 4
            if padding:
                base64_str += "=" * (4 - padding)
            decoded_bytes = base64.urlsafe_b64decode(base64_str.encode('utf-8'))
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to decode base64url content: {e}")
            return ""


email_service = EmailService()

