
"""
Unit tests for ExtractionService.

Tests deterministic indicator extraction using only stdlib parsing.
No external services, no mocks of LLM/Supabase/Neo4j needed.
"""

import asyncio
import unittest

from app.services.extraction_service import ExtractionService


class TestExtractionURLs(unittest.TestCase):
    """URL extraction tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_extracts_http_url(self):
        result = self._run(self.service.extract("Visit http://example.com for info"))
        self.assertIn("http://example.com", result["urls"])

    def test_extracts_https_url(self):
        result = self._run(self.service.extract("Go to https://secure.example.com/path?q=1"))
        self.assertTrue(any("https://secure.example.com" in u for u in result["urls"]))

    def test_extracts_multiple_urls(self):
        text = "Links: https://a.com and http://b.org/page"
        result = self._run(self.service.extract(text))
        self.assertEqual(len(result["urls"]), 2)

    def test_deduplicates_urls(self):
        text = "https://dup.com and again https://dup.com"
        result = self._run(self.service.extract(text))
        self.assertEqual(len(result["urls"]), 1)

    def test_strips_trailing_punctuation(self):
        text = "Check https://example.com/path."
        result = self._run(self.service.extract(text))
        urls = result["urls"]
        self.assertTrue(all(not u.endswith(".") for u in urls))

    def test_no_urls_in_clean_text(self):
        result = self._run(self.service.extract("This is a normal sentence."))
        self.assertEqual(result["urls"], [])


class TestExtractionDomains(unittest.TestCase):
    """Domain extraction tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_extracts_domain_from_url(self):
        result = self._run(self.service.extract("Visit https://malicious-site.com/phish"))
        self.assertIn("malicious-site.com", result["domains"])

    def test_strips_port_from_domain(self):
        result = self._run(self.service.extract("API at http://server.local:8080/api"))
        self.assertIn("server.local", result["domains"])

    def test_domains_are_lowercase(self):
        result = self._run(self.service.extract("Go to https://MyDomain.COM/page"))
        self.assertIn("mydomain.com", result["domains"])

    def test_deduplicates_domains(self):
        text = "https://same.org/a and https://same.org/b"
        result = self._run(self.service.extract(text))
        self.assertEqual(result["domains"].count("same.org"), 1)


class TestExtractionEmails(unittest.TestCase):
    """Email address extraction tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_extracts_email(self):
        result = self._run(self.service.extract("Contact admin@example.com"))
        self.assertIn("admin@example.com", result["emails"])

    def test_extracts_complex_email(self):
        result = self._run(self.service.extract("user.name+tag@sub.domain.co.uk"))
        self.assertIn("user.name+tag@sub.domain.co.uk", result["emails"])

    def test_deduplicates_emails(self):
        text = "a@b.com and A@B.COM"
        result = self._run(self.service.extract(text))
        self.assertEqual(len(result["emails"]), 1)

    def test_no_emails_in_clean_text(self):
        result = self._run(self.service.extract("Hello world, nothing here."))
        self.assertEqual(result["emails"], [])


class TestExtractionIPv4(unittest.TestCase):
    """IPv4 address extraction tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_extracts_ipv4(self):
        result = self._run(self.service.extract("Server at 192.168.1.100"))
        self.assertIn("192.168.1.100", result["ipv4_addresses"])

    def test_extracts_public_ip(self):
        result = self._run(self.service.extract("DNS: 8.8.8.8"))
        self.assertIn("8.8.8.8", result["ipv4_addresses"])

    def test_filters_version_strings(self):
        """Version numbers like 1.2.3.4 should be filtered out."""
        result = self._run(self.service.extract("Version 1.2.3.4 released"))
        self.assertEqual(result["ipv4_addresses"], [])

    def test_extracts_multiple_ips(self):
        text = "Primary: 10.0.0.1 Secondary: 10.0.0.2"
        result = self._run(self.service.extract(text))
        self.assertEqual(len(result["ipv4_addresses"]), 2)

    def test_no_ips_in_clean_text(self):
        result = self._run(self.service.extract("No network addresses here."))
        self.assertEqual(result["ipv4_addresses"], [])


class TestExtractionUrgency(unittest.TestCase):
    """Urgency phrase detection tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_detects_immediately(self):
        result = self._run(self.service.extract("Process this immediately"))
        self.assertIn("immediately", result["urgency_phrases"])

    def test_detects_asap(self):
        result = self._run(self.service.extract("Need this done ASAP"))
        self.assertIn("asap", result["urgency_phrases"])

    def test_detects_urgent(self):
        result = self._run(self.service.extract("This is an urgent matter"))
        self.assertIn("urgent", result["urgency_phrases"])

    def test_detects_act_now(self):
        result = self._run(self.service.extract("You must act now before it's too late"))
        self.assertIn("act now", result["urgency_phrases"])

    def test_no_urgency_in_calm_text(self):
        result = self._run(self.service.extract("Please review at your convenience."))
        self.assertEqual(result["urgency_phrases"], [])


class TestExtractionPayment(unittest.TestCase):
    """Payment/financial term detection tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_detects_wire_transfer(self):
        result = self._run(self.service.extract("Please send a wire transfer"))
        self.assertIn("wire transfer", result["payment_terms"])

    def test_detects_routing_number(self):
        result = self._run(self.service.extract("Update the routing number below"))
        self.assertIn("routing number", result["payment_terms"])

    def test_detects_gift_card(self):
        result = self._run(self.service.extract("Buy a gift card for $500"))
        self.assertIn("gift card", result["payment_terms"])

    def test_detects_invoice(self):
        result = self._run(self.service.extract("Attached is the invoice for payment"))
        self.assertIn("invoice", result["payment_terms"])

    def test_no_payment_in_clean_text(self):
        result = self._run(self.service.extract("Let's meet for coffee tomorrow."))
        self.assertEqual(result["payment_terms"], [])


class TestExtractionImpersonation(unittest.TestCase):
    """Impersonation/authority term detection tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_detects_ceo(self):
        result = self._run(self.service.extract("Message from the CEO"))
        self.assertIn("ceo", result["impersonation_terms"])

    def test_detects_on_behalf_of(self):
        result = self._run(self.service.extract("I am writing on behalf of the director"))
        self.assertIn("on behalf of", result["impersonation_terms"])
        self.assertIn("director", result["impersonation_terms"])

    def test_detects_cfo(self):
        result = self._run(self.service.extract("The CFO approved this request"))
        self.assertIn("cfo", result["impersonation_terms"])

    def test_no_authority_in_clean_text(self):
        result = self._run(self.service.extract("The weather is nice today."))
        self.assertEqual(result["impersonation_terms"], [])


class TestExtractionMetadata(unittest.TestCase):
    """Metadata (sender/subject) extraction tests."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_includes_sender_from_metadata(self):
        result = self._run(self.service.extract(
            "Hello",
            metadata={"sender": "boss@company.com"},
        ))
        self.assertEqual(result["sender"], "boss@company.com")

    def test_includes_subject_from_metadata(self):
        result = self._run(self.service.extract(
            "Hello",
            metadata={"subject": "Urgent Wire Transfer"},
        ))
        self.assertEqual(result["subject"], "Urgent Wire Transfer")

    def test_uses_requester_email_as_sender(self):
        result = self._run(self.service.extract(
            "Hello",
            metadata={"requester_email": "user@example.com"},
        ))
        self.assertEqual(result["sender"], "user@example.com")

    def test_no_metadata_keys_when_absent(self):
        result = self._run(self.service.extract("Hello"))
        self.assertNotIn("sender", result)
        self.assertNotIn("subject", result)


class TestExtractionBECScenario(unittest.TestCase):
    """End-to-end test with a realistic BEC email."""

    def setUp(self):
        self.service = ExtractionService()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_bec_wire_transfer_email(self):
        """The built-in suspicious wire-transfer example from the Analyzer page."""
        content = (
            "Hi John, I need you to wire $50,000 to the attached vendor "
            "immediately. I'm in a meeting and can't take calls. Please "
            "process this urgently so we don't lose the contract. - CEO"
        )
        result = self._run(self.service.extract(
            content,
            metadata={"sender": "ceo@trustguardian.ai", "subject": "Urgent Wire Transfer"},
        ))

        # Should detect urgency signals
        self.assertTrue(len(result["urgency_phrases"]) >= 2)
        self.assertIn("immediately", result["urgency_phrases"])
        self.assertIn("urgently", result["urgency_phrases"])

        # Should detect payment terms
        self.assertTrue(len(result["payment_terms"]) >= 1)
        self.assertIn("wire", result["payment_terms"])

        # Should detect impersonation/authority
        self.assertTrue(len(result["impersonation_terms"]) >= 1)
        self.assertIn("ceo", result["impersonation_terms"])

        # Should include metadata
        self.assertEqual(result["sender"], "ceo@trustguardian.ai")
        self.assertEqual(result["subject"], "Urgent Wire Transfer")


if __name__ == "__main__":
    unittest.main()
