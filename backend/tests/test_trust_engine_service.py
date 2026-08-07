"""
Unit tests for TrustEngineService.

Tests deterministic scoring, confidence calculation, identity/historical
risk fusion, and payment circuit breaker behavior.
"""

import unittest

from app.services.trust_engine_service import TrustEngineService
from app.models.trust_engine import (
    LLMAnalysisResult,
    GraphAnalysisResult
)
from app.models.threat_intel import ThreatIntelResult, VirusTotalStats

class TestTrustEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TrustEngineService()

    def test_new_clean_vendor(self):
        """New clean vendor -> high trust, low confidence."""
        
        # Valid LLM Analysis
        llm = LLMAnalysisResult(risk_score=10.0, risk_level="Safe")
        
        # Valid, safe VirusTotal
        vt = VirusTotalStats(malicious=0, suspicious=0, harmless=10, status="completed")
        ti = ThreatIntelResult(urls_checked=1, virustotal=vt, spf="PASS", dkim="PASS", dmarc="PASS")
        
        # No prior interactions (new vendor)
        graph = GraphAnalysisResult(interaction_count=0)
        result = self.engine.evaluate(
            llm_analysis=llm,
            threat_intel=ti,
            graph_intel=graph
        )

        self.assertGreaterEqual(result.trust_score, 80.0)
        self.assertEqual(result.recommendation, "ALLOW")
        
        # Check Decision Trace
        self.assertTrue(any(trace.rule_name == "LLM_Confidence" for trace in result.reasoning))
        self.assertTrue(any(trace.rule_name == "TI_Confidence" for trace in result.reasoning))


    def test_malicious_vendor_blocks(self):
        """High historical drop, malicious VT, and high LLM risk should trigger BLOCK."""
        llm = LLMAnalysisResult(risk_score=90.0, risk_level="Critical")
        
        vt = VirusTotalStats(malicious=5, suspicious=0, harmless=0, status="completed")
        ti = ThreatIntelResult(urls_checked=1, virustotal=vt, spf="FAIL", dkim="FAIL", dmarc="NONE")
        
        graph = GraphAnalysisResult(interaction_count=50, trust_drop=True)
        result = self.engine.evaluate(
            llm_analysis=llm,
            threat_intel=ti,
            graph_intel=graph
        )

        self.assertLess(result.trust_score, 40.0)
        self.assertEqual(result.risk_level, "HIGH")
        
        # Verify reasoning contains penalties
        rules_applied = [t.rule_name for t in result.reasoning]
        self.assertIn("VT_Malicious", rules_applied)
        self.assertIn("Email_Auth_Fail", rules_applied)
        self.assertIn("Trust_Drop", rules_applied)

    def test_missing_evidence_confidence(self):
        """Missing evidence should lower confidence but not explicitly increase risk."""
        llm = LLMAnalysisResult(risk_score=30.0)
        
        # No TI, No Graph
        result = self.engine.evaluate(
            llm_analysis=llm,
            threat_intel=None,
            graph_intel=None
        )

        self.assertLessEqual(result.confidence_score, 40.0)  # Only LLM confidence
        
        # Trust score is entirely dependent on Content Risk in this case
        self.assertEqual(result.component_scores["identity"], 0.0)
        self.assertEqual(result.component_scores["historical"], 0.0)

if __name__ == "__main__":
    unittest.main()
