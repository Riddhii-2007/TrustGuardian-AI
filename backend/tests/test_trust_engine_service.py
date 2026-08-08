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
        vt = VirusTotalStats(malicious=0, suspicious=0, harmless=10)
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
        
        vt = VirusTotalStats(malicious=5, suspicious=0, harmless=0)
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
        self.assertIsNone(result.component_scores.get("identity"))
        self.assertIsNone(result.component_scores.get("historical"))

    def test_content_risk_not_dampened_when_historical_evidence_absent(self):
        """Historical evidence absent -> content risk should NOT be dampened."""
        llm = LLMAnalysisResult(risk_score=85.0, risk_level="High")
        
        from app.models.threat_intel import VirusTotalStats
        vt = VirusTotalStats(malicious=0, suspicious=0, harmless=5)
        ti = ThreatIntelResult(urls_checked=1, virustotal=vt, spf="PASS", dkim="PASS", dmarc="PASS")
        
        result = self.engine.evaluate(
            llm_analysis=llm,
            threat_intel=ti,
            graph_intel=None
        )
        
        # Content risk remains 85.0 (not dampened to 42.5)
        # identity_risk = 0.0
        # raw_risk = (0.40 * 85.0 + 0.35 * 0.0) / (0.40 + 0.35) = 34.0 / 0.75 = 45.33
        # trust_score = 100.0 - 45.33 = 54.67
        self.assertEqual(result.component_scores.get("content"), 85.0)
        self.assertAlmostEqual(result.trust_score, 54.67, places=2)

    def test_content_risk_dampened_when_both_present_and_low(self):
        """Both identity and historical evidence are present and low -> content risk should be dampened."""
        llm = LLMAnalysisResult(risk_score=85.0, risk_level="High")
        
        from app.models.threat_intel import VirusTotalStats
        vt = VirusTotalStats(malicious=0, suspicious=0, harmless=5)
        ti = ThreatIntelResult(urls_checked=1, virustotal=vt, spf="PASS", dkim="PASS", dmarc="PASS")
        
        graph = GraphAnalysisResult(interaction_count=5, consistent_good=True, trust_drop=False)
        
        result = self.engine.evaluate(
            llm_analysis=llm,
            threat_intel=ti,
            graph_intel=graph
        )
        
        # Content risk is dampened to 42.5
        # identity_risk = 0.0
        # historical_risk = -10.0 (good history bonus)
        # raw_risk = (0.40 * 42.5 + 0.35 * 0.0 + 0.25 * (-10.0)) / (0.40 + 0.35 + 0.25)
        #          = (17.0 + 0 - 2.5) / 1.0 = 14.5
        # trust_score = 100.0 - 14.5 = 85.5
        self.assertEqual(result.component_scores.get("content"), 42.5)
        self.assertAlmostEqual(result.trust_score, 85.5, places=2)

if __name__ == "__main__":
    unittest.main()
