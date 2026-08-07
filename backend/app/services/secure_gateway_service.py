import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class SecureGatewayService:
    """
    Secure AI Gateway Service to prevent enterprise data leakage before any external LLM receives data.
    """

    def __init__(self):
        # Ordered rules carefully (longer / more specific patterns first)
        self.patterns = [
            # Credit Card (13-16 digits)
            (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[MASKED_CREDIT_CARD]"),
            # Aadhaar Card (12 digits: XXXX XXXX XXXX or XXXXXXXXXXXX)
            (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"), "[MASKED_AADHAAR]"),
            # PAN Card (5 letters, 4 digits, 1 letter)
            (re.compile(r"\b[A-Za-z]{5}\d{4}[A-Za-z]\b"), "[MASKED_PAN]"),
            # Email Address
            (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[MASKED_EMAIL]"),
            # Phone Number
            (re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[MASKED_PHONE]"),
            # Internal IP Address
            (re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"), "[MASKED_INTERNAL_IP]"),
            # Internal URL
            (re.compile(r"\b(?:https?://)?(?:[a-zA-Z0-9-]+\.)*(?:local|internal|lan|localhost)(?::\d+)?(?:/[^\s]*)?\b"), "[MASKED_INTERNAL_URL]"),
            # Employee ID (Alpha-numeric EMP-XXXXX or custom)
            (re.compile(r"\b(?:EMP|emp|Employee|employee)[-_]?(?:ID|id)?[-_]?\d{3,6}\b"), "[MASKED_EMPLOYEE_ID]"),
            (re.compile(r"\b[A-Za-z]{2,3}-\d{4,6}\b"), "[MASKED_EMPLOYEE_ID]"),
        ]

        # Greeting name pattern
        self.greetings_re = re.compile(
            r"(?i)\b(dear|hi|hello|hey|greetings|to)\s+([A-Z][a-zA-Z]{1,15}(?:\s+[A-Z][a-zA-Z]{1,15})?)\b"
        )
        # Signature name pattern
        self.signatures_re = re.compile(
            r"(?i)\b(thanks|thank\s+you|regards|best|sincerely|respectfully|from)\b,\s*\n+([A-Z][a-zA-Z]{1,15}(?:\s+[A-Z][a-zA-Z]{1,15})?)\b"
        )
        # Bank account patterns near keywords
        self.bank_account_re = re.compile(
            r"(?i)\b(acc|account|acct|bank\s+acct|bank\s+account|routing|iban|routing\s+no|routing\s+number)\s*(?:number|no|#)?\s*[:\-\s]+(\d{9,18})\b"
        )

    def sanitize_text(self, text: str) -> str:
        """
        Detect and mask PII and internal configuration strings.
        """
        if not text:
            return text

        # 1. Mask context-dependent patterns first (Greetings, Signatures, Bank Accounts near keywords)
        # Mask names in greetings
        text = self.greetings_re.sub(lambda m: f"{m.group(1)} [MASKED_NAME]", text)

        # Mask names in signatures
        text = self.signatures_re.sub(lambda m: f"{m.group(1)},\n[MASKED_NAME]", text)

        # Mask Bank Accounts / Routing Numbers near keywords
        text = self.bank_account_re.sub(lambda m: f"{m.group(1)}: [MASKED_BANK_ACCOUNT]", text)

        # 2. Mask simple/structural context-independent patterns next (Credit Card, Aadhaar, PAN, Email, Phone, Internal IP/URL, Employee ID)
        for pattern, replacement in self.patterns:
            text = pattern.sub(replacement, text)

        return text

    def sanitize_data(self, data: Any) -> Any:
        """
        Recursively traverse lists/dicts/sets and mask PII strings in string fields.
        """
        if isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(x) for x in data]
        elif isinstance(data, set):
            return {self.sanitize_data(x) for x in data}
        elif isinstance(data, tuple):
            return tuple(self.sanitize_data(x) for x in data)
        elif isinstance(data, str):
            return self.sanitize_text(data)
        else:
            return data


secure_gateway_service = SecureGatewayService()
