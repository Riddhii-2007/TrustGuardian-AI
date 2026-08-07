"""
Deterministic Evidence Extraction Service for TrustGuardianAI.

Extracts structured indicators from raw text content using only
Python standard-library parsing (re module). Never calls any
external API (Gemini, Groq, Supabase, Neo4j, etc.).

Extracted indicators:
    - URLs
    - Domains (from URLs + standalone)
    - Email addresses
    - IPv4 addresses
    - Phone numbers
    - Urgency phrases
    - Payment / financial terms
    - Impersonation / authority terms
    - Sender and subject (from optional metadata)

The output dict is designed to slot directly into
ScanEvidence.extraction for downstream consumption by
the LLM and result builder.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled regex patterns (module-level for performance)
# ---------------------------------------------------------------------------

# URLs — http(s) and ftp, stopping at whitespace / common delimiters
_URL_RE = re.compile(
    r"https?://[^\s<>\"'`,;)\]]+|ftp://[^\s<>\"'`,;)\]]+",
    re.IGNORECASE,
)

# Email addresses — standard user@domain.tld
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# IPv4 addresses — four octets 0-255
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
)

# Phone numbers — common international and US formats
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s\-]?)?"           # optional country code
    r"(?:\(?\d{2,4}\)?[\s\-]?)?"       # optional area code
    r"\d{3,4}[\s\-]?\d{3,4}"          # main number
    r"(?:\s*(?:ext|x|extension)\s*\.?\s*\d{1,5})?",  # optional extension
    re.IGNORECASE,
)

# Domain extraction from URLs
_DOMAIN_FROM_URL_RE = re.compile(
    r"https?://([^/:?\s#]+)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Signal phrase lists (case-insensitive matching via pre-compiled patterns)
# ---------------------------------------------------------------------------

_URGENCY_PHRASES: list[str] = [
    "immediately",
    "urgent",
    "urgently",
    "right away",
    "asap",
    "as soon as possible",
    "time-sensitive",
    "time sensitive",
    "don't delay",
    "do not delay",
    "act now",
    "act fast",
    "within the hour",
    "end of day",
    "deadline",
    "hurry",
    "rush",
    "critical deadline",
    "cannot wait",
    "can't wait",
    "before close of business",
    "right now",
    "without delay",
]

_PAYMENT_TERMS: list[str] = [
    "wire transfer",
    "wire",
    "bank transfer",
    "routing number",
    "account number",
    "swift code",
    "iban",
    "direct deposit",
    "payment",
    "invoice",
    "ach transfer",
    "ach",
    "venmo",
    "zelle",
    "paypal",
    "cryptocurrency",
    "bitcoin",
    "gift card",
    "prepaid card",
    "money order",
    "cashier's check",
    "cashiers check",
    "purchase order",
    "remittance",
    "funds transfer",
    "credit card",
    "debit card",
]

_IMPERSONATION_TERMS: list[str] = [
    "ceo",
    "cfo",
    "cto",
    "coo",
    "president",
    "vice president",
    "vp",
    "director",
    "executive",
    "board member",
    "chairman",
    "managing director",
    "founder",
    "partner",
    "general counsel",
    "chief",
    "on behalf of",
    "acting as",
    "authorized by",
    "per the request of",
    "as instructed by",
    "from the desk of",
    "speaking for",
    "representing",
]

# Pre-compile phrase patterns for efficient matching
def _compile_phrase_patterns(phrases: list[str]) -> list[re.Pattern[str]]:
    """Compile a list of phrases into word-boundary regex patterns."""
    return [
        re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        for phrase in phrases
    ]

_URGENCY_PATTERNS = _compile_phrase_patterns(_URGENCY_PHRASES)
_PAYMENT_PATTERNS = _compile_phrase_patterns(_PAYMENT_TERMS)
_IMPERSONATION_PATTERNS = _compile_phrase_patterns(_IMPERSONATION_TERMS)


class ExtractionService:
    """Deterministic indicator extraction from raw content.

    Uses only Python stdlib (re module). No external API calls.
    Thread-safe and stateless — safe to use as a singleton.

    Usage:
        service = ExtractionService()
        result = await service.extract(content, metadata={"sender": "...", "subject": "..."})

    Returns:
        dict with keys: urls, domains, emails, ipv4_addresses, phone_numbers,
        urgency_phrases, payment_terms, impersonation_terms, sender, subject.
    """

    async def extract(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract deterministic indicators from content.

        Args:
            content: Raw text to scan for indicators.
            metadata: Optional dict with 'sender' and/or 'subject' keys.

        Returns:
            Normalized dict of extracted indicators. All list values are
            deduplicated and sorted for deterministic output.
        """
        metadata = metadata or {}

        urls = self._extract_urls(content)
        domains = self._extract_domains(content, urls)
        emails = self._extract_emails(content)
        ipv4s = self._extract_ipv4(content)
        phones = self._extract_phones(content)
        urgency = self._match_phrases(content, _URGENCY_PATTERNS)
        payment = self._match_phrases(content, _PAYMENT_PATTERNS)
        impersonation = self._match_phrases(content, _IMPERSONATION_PATTERNS)

        result: dict[str, Any] = {
            "urls": urls,
            "domains": domains,
            "emails": emails,
            "ipv4_addresses": ipv4s,
            "phone_numbers": phones,
            "urgency_phrases": urgency,
            "payment_terms": payment,
            "impersonation_terms": impersonation,
        }

        # Include sender/subject from metadata if present
        sender = metadata.get("sender") or metadata.get("requester_email")
        subject = metadata.get("subject")
        if sender:
            result["sender"] = str(sender)
        if subject:
            result["subject"] = str(subject)

        indicator_count = sum(
            len(v) for v in result.values() if isinstance(v, list)
        )
        logger.info(
            "ExtractionService extracted %d indicators "
            "(%d urls, %d domains, %d emails, %d ips, %d phones, "
            "%d urgency, %d payment, %d impersonation)",
            indicator_count,
            len(urls),
            len(domains),
            len(emails),
            len(ipv4s),
            len(phones),
            len(urgency),
            len(payment),
            len(impersonation),
        )

        return result

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_urls(content: str) -> list[str]:
        """Extract and deduplicate URLs from content."""
        # Strip trailing punctuation that gets captured by the greedy regex
        raw = _URL_RE.findall(content)
        cleaned: list[str] = []
        for url in raw:
            url = url.rstrip(".,;:!?")
            if url not in cleaned:
                cleaned.append(url)
        return sorted(cleaned, key=str.lower)

    @staticmethod
    def _extract_domains(content: str, urls: list[str]) -> list[str]:
        """Extract unique domains from discovered URLs."""
        domains: set[str] = set()
        for url in urls:
            match = _DOMAIN_FROM_URL_RE.match(url)
            if match:
                domain = match.group(1).lower()
                # Strip port number if present
                domain = domain.split(":")[0]
                domains.add(domain)
        return sorted(domains)

    @staticmethod
    def _extract_emails(content: str) -> list[str]:
        """Extract and deduplicate email addresses."""
        raw = _EMAIL_RE.findall(content)
        unique = sorted(set(e.lower() for e in raw))
        return unique

    @staticmethod
    def _extract_ipv4(content: str) -> list[str]:
        """Extract valid IPv4 addresses (excluding obvious version strings)."""
        candidates = _IPV4_RE.findall(content)
        valid: list[str] = []
        for ip in candidates:
            octets = [int(o) for o in ip.split(".")]
            # Skip strictly ascending sequences of small numbers (version
            # strings like 1.2.3.4, 2.3.4.5). Real IPs rarely have all
            # four octets small *and* strictly ascending.
            if (
                all(o <= 9 for o in octets)
                and octets == sorted(octets)
                and len(set(octets)) == 4
            ):
                continue
            if ip not in valid:
                valid.append(ip)
        return sorted(valid)

    @staticmethod
    def _extract_phones(content: str) -> list[str]:
        """Extract phone number candidates from content."""
        raw = _PHONE_RE.findall(content)
        # Filter to strings that have enough digits to be a phone number
        phones: list[str] = []
        for phone in raw:
            phone = phone.strip()
            digit_count = sum(1 for c in phone if c.isdigit())
            if digit_count >= 7:  # minimum for a valid phone number
                if phone not in phones:
                    phones.append(phone)
        return sorted(phones)

    @staticmethod
    def _match_phrases(
        content: str,
        patterns: list[re.Pattern[str]],
    ) -> list[str]:
        """Find all matching phrases from a pre-compiled pattern list."""
        matched: list[str] = []
        for pattern in patterns:
            if pattern.search(content):
                # Extract the original phrase from the pattern
                # (strip \b anchors and unescape)
                phrase = pattern.pattern
                phrase = phrase.removeprefix(r"\b").removesuffix(r"\b")
                phrase = re.sub(r"\\(.)", r"\1", phrase)
                if phrase not in matched:
                    matched.append(phrase)
        return sorted(matched, key=str.lower)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
extraction_service = ExtractionService()
