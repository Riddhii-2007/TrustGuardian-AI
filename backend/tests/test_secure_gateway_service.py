import pytest
from app.services.secure_gateway_service import secure_gateway_service


def test_sanitize_emails():
    text = "Send info to test.user@company.com and ceo_mail@internal-net.org."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_EMAIL]" in sanitized
    assert "test.user@company.com" not in sanitized
    assert "ceo_mail@internal-net.org" not in sanitized


def test_sanitize_phones():
    text = "Contact support at +1 (555) 123-4567 or 555-987-6543."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_PHONE]" in sanitized
    assert "555-123-4567" not in sanitized
    assert "555-987-6543" not in sanitized


def test_sanitize_credit_cards():
    text = "Visa number: 4111 2222 3333 4444."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_CREDIT_CARD]" in sanitized
    assert "4111 2222 3333 4444" not in sanitized


def test_sanitize_aadhaar():
    text = "My Aadhaar details: 1234-5678-9012."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_AADHAAR]" in sanitized
    assert "1234-5678-9012" not in sanitized


def test_sanitize_pan():
    text = "PAN is ABCDE1234F."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_PAN]" in sanitized
    assert "ABCDE1234F" not in sanitized


def test_sanitize_employee_id():
    text = "Login for EMP-12345 or code DE-45678."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_EMPLOYEE_ID]" in sanitized
    assert "EMP-12345" not in sanitized
    assert "DE-45678" not in sanitized


def test_sanitize_internal_ips():
    text = "Connect to 10.0.0.5 or 192.168.1.100."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_INTERNAL_IP]" in sanitized
    assert "10.0.0.5" not in sanitized
    assert "192.168.1.100" not in sanitized


def test_sanitize_internal_urls():
    text = "Open http://intranet.local/index.html or https://wiki.internal:8080."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_INTERNAL_URL]" in sanitized
    assert "intranet.local" not in sanitized
    assert "wiki.internal" not in sanitized


def test_sanitize_greetings_names():
    text = "Dear John Doe, thank you for your request."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "Dear [MASKED_NAME]" in sanitized
    assert "John Doe" not in sanitized


def test_sanitize_signatures_names():
    text = "Best regards,\nJane Smith"
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "Best regards,\n[MASKED_NAME]" in sanitized
    assert "Jane Smith" not in sanitized


def test_sanitize_bank_accounts():
    text = "Bank details: Account number: 123456789012."
    sanitized = secure_gateway_service.sanitize_text(text)
    assert "[MASKED_BANK_ACCOUNT]" in sanitized
    assert "123456789012" not in sanitized


def test_sanitize_nested_data():
    data = {
        "email": "hacker@evil.com",
        "nested": {
            "phone_list": ["Call 555-555-5555", "Call 111-222-3333"],
            "ip": "10.0.0.1"
        }
    }
    sanitized = secure_gateway_service.sanitize_data(data)
    assert sanitized["email"] == "[MASKED_EMAIL]"
    assert sanitized["nested"]["phone_list"] == ["Call [MASKED_PHONE]", "Call [MASKED_PHONE]"]
    assert sanitized["nested"]["ip"] == "[MASKED_INTERNAL_IP]"
