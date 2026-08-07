import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.email_service import email_service


def test_extract_email_address():
    # Test typical "Name <email>" headers
    assert email_service._extract_email_address("Jane Doe <jane.doe@example.com>") == "jane.doe@example.com"
    assert email_service._extract_email_address("<ceo@company.org>") == "ceo@company.org"
    
    # Test plain email addresses
    assert email_service._extract_email_address("support@trustguardian.ai") == "support@trustguardian.ai"
    assert email_service._extract_email_address("   SPACEY@domain.co.uk  ") == "spacey@domain.co.uk"


def test_decode_base64url():
    # Test safe base64url decoding with different padding lengths
    test_str_url = "SGVsbG8gV29ybGQ"   # "Hello World" base64url without padding
    assert email_service._decode_base64url(test_str_url) == "Hello World"


def test_parse_gmail_message_multipart():
    # Construct a nested MIME multipart payload
    mock_payload = {
        "id": "msg-12345",
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "Subject", "value": "Urgent Invoice Request"},
                {"name": "From", "value": "Vendor Accounts <billing@vendor-inc.com>"},
                {"name": "Date", "value": "Fri, 7 Aug 2026 12:00:00 +0000"},
                {"name": "Authentication-Results", "value": "mx.google.com; spf=pass dkim=pass dmarc=pass"}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": "UGxlYXNlIHBheSB0aGlzIGludm9pY2UgaW1tZWRpYXRlbHku"  # "Please pay this invoice immediately."
                    }
                },
                {
                    "mimeType": "text/html",
                    "body": {
                        "data": "PHA+UGxlYXNlIHBheSB0aGlzIGludm9pY2UgaW1tZWRpYXRlbHkuPC9wPg=="
                    }
                }
            ]
        }
    }

    parsed = email_service.parse_gmail_message(mock_payload)
    assert parsed["id"] == "msg-12345"
    assert parsed["subject"] == "Urgent Invoice Request"
    assert parsed["sender"] == "billing@vendor-inc.com"
    assert parsed["date"] == "Fri, 7 Aug 2026 12:00:00 +0000"
    assert parsed["content"] == "Please pay this invoice immediately."
    assert parsed["headers"]["Authentication-Results"] == "mx.google.com; spf=pass dkim=pass dmarc=pass"


@pytest.mark.asyncio
async def test_fetch_latest_emails_success():
    # Mock response for message list
    mock_list_response = MagicMock(spec=httpx.Response)
    mock_list_response.status_code = 200
    mock_list_response.json = lambda: {
        "messages": [
            {"id": "msg-001", "threadId": "thread-001"},
            {"id": "msg-002", "threadId": "thread-002"}
        ]
    }

    # Mock response for message details
    def get_mock_detail(url, headers):
        msg_id = url.split("/")[-1].split("?")[0]
        res = MagicMock(spec=httpx.Response)
        res.status_code = 200
        res.json = lambda: {
            "id": msg_id,
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": f"Subject for {msg_id}"},
                    {"name": "From", "value": "test@example.com"}
                ],
                "body": {
                    "data": "dGVzdCBjb250ZW50"  # "test content"
                }
            }
        }
        return res

    mock_client = MagicMock(spec=httpx.AsyncClient)
    # Ensure client context manager yields mock_client
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    mock_client.get = AsyncMock()
    mock_client.get.side_effect = lambda url, headers: (
        mock_list_response if "maxResults" in url else get_mock_detail(url, headers)
    )

    with patch("httpx.AsyncClient", return_value=mock_client):
        emails = await email_service.fetch_latest_emails(access_token="fake_token", max_results=2)
        assert len(emails) == 2
        assert emails[0]["id"] == "msg-001"
        assert emails[0]["subject"] == "Subject for msg-001"
        assert emails[0]["content"] == "test content"
        assert emails[1]["id"] == "msg-002"


@pytest.mark.asyncio
async def test_fetch_latest_emails_http_error():
    # Mock a client failure (e.g. rate limit 429 or auth error 401)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.text = "Invalid Credentials"
    
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError("Auth Error", request=MagicMock(), response=mock_response))

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError) as exc_info:
            await email_service.fetch_latest_emails(access_token="invalid_token")
        assert "Gmail API error" in str(exc_info.value)
