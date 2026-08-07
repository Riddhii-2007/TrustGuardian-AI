import httpx
import logging
import base64
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class GmailService:
    """Service to fetch real emails from a user's Gmail inbox using their OAuth provider token."""
    
    BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"

    async def fetch_recent_emails(self, provider_token: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not provider_token:
            logger.warning("No provider token supplied. Returning empty email list.")
            return []

        headers = {
            "Authorization": f"Bearer {provider_token}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. Fetch message IDs
                list_url = f"{self.BASE_URL}/messages?maxResults={limit}&q=in:inbox"
                list_resp = await client.get(list_url, headers=headers)
                
                if list_resp.status_code != 200:
                    logger.error(f"Failed to fetch Gmail list: {list_resp.text}")
                    return []
                
                messages = list_resp.json().get("messages", [])
                
                # 2. Fetch full message details
                emails = []
                for msg in messages:
                    msg_id = msg["id"]
                    detail_url = f"{self.BASE_URL}/messages/{msg_id}?format=full"
                    detail_resp = await client.get(detail_url, headers=headers)
                    
                    if detail_resp.status_code == 200:
                        detail_data = detail_resp.json()
                        emails.append(self._parse_message(detail_data))
                        
                return emails
                
        except Exception as e:
            logger.error(f"Error fetching emails from Gmail API: {e}")
            return []

    def _parse_message(self, msg_data: dict) -> dict:
        """Parse the raw Gmail API message format into a clean dictionary."""
        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])
        
        subject = "No Subject"
        sender = "Unknown Sender"
        date = ""
        
        for header in headers:
            name = header.get("name", "").lower()
            val = header.get("value", "")
            if name == "subject":
                subject = val
            elif name == "from":
                sender = val
            elif name == "date":
                date = val
                
        # Get body snippet or text content
        snippet = msg_data.get("snippet", "")
        
        # Try to extract full body if needed, but snippet is often enough for simple analysis
        body = snippet
        
        parts = payload.get("parts", [])
        if parts:
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data")
                    if data:
                        try:
                            # Gmail uses URL-safe base64 encoding
                            # Sometimes padding is missing
                            padding = 4 - (len(data) % 4)
                            if padding and padding != 4:
                                data += '=' * padding
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
                        except Exception as e:
                            logger.error(f"Failed to decode body: {e}")
                            pass
        
        # Truncate body length for prompt token optimization
        if len(body) > 2000:
            body = body[:2000] + "..."

        return {
            "id": msg_data.get("id"),
            "subject": subject,
            "sender": sender,
            "date": date,
            "snippet": snippet,
            "body": body,
            "content": f"From: {sender}\nSubject: {subject}\nDate: {date}\n\n{body}"
        }

gmail_service = GmailService()
