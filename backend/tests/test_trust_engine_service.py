"""
Unit tests for TrustEngineService.

Tests deterministic scoring, confidence calculation, identity/historical
risk fusion, and payment circuit breaker behavior. No network or LLM required.
"""

import unittest
from typing import Any

from app.services.trust_engine_service import TrustEngineService, TrustEngineResult


class TestTrustEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TrustEngineService()

    def test_new_clean_vendor(self):
        """New clean vendor -> high trust, low confidence."""
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 10.0},
            extraction={},
            threat_intel={"virustotal": {"status": "completed", "malicious": False}},
            graph_intel={"interaction_count": 0}
        )
        self.assertGreaterEqual(result.trust_score, 70.0)
        self.assertLess(result.confidence_score, 70.0) # LLM(40) + TI(1/2 * 30 = 15) + Graph(0) = 55
        self.assertEqual(result.recommendation, "Unverified \u2014 clean signals; confirm via secondary channel")
        self.assertFalse(result.verification_required)

    def test_malicious_evidence(self):
        """Malicious evidence -> low trust."""
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 90.0},
            extraction={},
            threat_intel={"virustotal": {"status": "completed", "malicious": True}}, # +40 identity
            graph_intel={}
        )
        self.assertLess(result.trust_score, 70.0)

    def test_missing_evidence_lowers_confidence(self):
        """Missing evidence lowers confidence but doesn't necessarily impact risk."""
        result_full = self.engine.evaluate(
            llm_analysis={"risk_score": 10.0},
            extraction={},
            threat_intel={
                "virustotal": {"status": "completed"},
                "email_auth": {"status": "completed"}
            },
            graph_intel={"interaction_count": 10}
        )
        result_missing = self.engine.evaluate(
            llm_analysis={"risk_score": 10.0},
            extraction={},
            threat_intel={},
            graph_intel={}
        )
        self.assertGreater(result_full.confidence_score, result_missing.confidence_score)
        
        # Risk should be roughly the same (or actually exactly the same since both missing and full clean have 0 identity/history risk)
        # Content risk halving might apply to both
        self.assertEqual(result_full.risk_score, result_missing.risk_score)

    def test_urgency_alone_reduced_weighting(self):
        """Urgency alone gets reduced weighting if identity/historical risk are low."""
        # High LLM risk, but no identity/historical risk -> halved
        result_halved = self.engine.evaluate(
            llm_analysis={"risk_score": 80.0},
            extraction={},
            threat_intel={},
            graph_intel={}
        )
        
        # High LLM risk, plus some identity risk -> not halved
        result_full = self.engine.evaluate(
            llm_analysis={"risk_score": 80.0},
            extraction={},
            threat_intel={"virustotal": {"status": "completed", "malicious": True}},
            graph_intel={}
        )
        
        # In result_halved, content risk is 40. raw_risk = 0.4 * 40 = 16.
        # In result_full, content risk is 80. identity is 40. raw_risk = 0.4*80 + 0.35*40 = 32 + 14 = 46.
        # We can just verify the risk score is lower when halved.
        self.assertLess(result_halved.risk_score, result_full.risk_score)
        self.assertLess(result_halved.risk_score, 20.0)

    def test_good_history_bonus(self):
        """Consistent good history lowers risk."""
        result_base = self.engine.evaluate(
            llm_analysis={"risk_score": 50.0},
            extraction={},
            threat_intel={},
            graph_intel={"interaction_count": 5}
        )
        result_bonus = self.engine.evaluate(
            llm_analysis={"risk_score": 50.0},
            extraction={},
            threat_intel={},
            graph_intel={"interaction_count": 5, "consistent_good": True}
        )
        self.assertLess(result_bonus.risk_score, result_base.risk_score)

    def test_score_clamping(self):
        """Scores are clamped to 0-100."""
        # Try to get > 100 risk
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 100.0},
            extraction={},
            threat_intel={"virustotal": {"status": "completed", "malicious": True}, "email_auth": {"pass": False}},
            graph_intel={"interaction_count": 1, "trust_drop": True}
        )
        self.assertLessEqual(result.risk_score, 100.0)
        self.assertGreaterEqual(result.risk_score, 0.0)
        
        # Try to get < 0 risk
        result_neg = self.engine.evaluate(
            llm_analysis={"risk_score": 0.0},
            extraction={},
            threat_intel={},
            graph_intel={"interaction_count": 100, "consistent_good": True}
        )
        self.assertGreaterEqual(result_neg.risk_score, 0.0)
        self.assertLessEqual(result_neg.risk_score, 100.0)

    def test_recommendation_proceed(self):
        """High trust + high confidence -> Proceed"""
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 0.0},
            extraction={},
            threat_intel={"virustotal": {"status": "completed"}, "email_auth": {"status": "completed"}},
            graph_intel={"interaction_count": 20}
        )
        self.assertEqual(result.recommendation, "Proceed")

    def test_recommendation_unverified(self):
        """High trust + low confidence -> Unverified"""
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 0.0},
            extraction={},
            threat_intel={},
            graph_intel={}
        )
        self.assertEqual(result.recommendation, "Unverified \u2014 clean signals; confirm via secondary channel")

    def test_recommendation_block(self):
        """Low trust + high confidence -> Block"""
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 100.0},
            extraction={},
            threat_intel={"virustotal": {"status": "completed", "malicious": True}, "email_auth": {"status": "completed", "pass": False}},
            graph_intel={"interaction_count": 20, "trust_drop": True}
        )
        self.assertEqual(result.recommendation, "Block")

    def test_recommendation_block_escalate(self):
        """Low trust + low confidence -> Block + escalate to SOC"""
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 100.0},
            extraction={},
            threat_intel={"virustotal": {"malicious": True}}, # Not completed status, so 0 TI confidence
            graph_intel={}
        )
        self.assertEqual(result.recommendation, "Block + escalate to SOC")

    def test_payment_circuit_breaker(self):
        """Payment/routing/bank keywords trigger verification."""
        # High trust, high confidence scenario
        extraction = {"payment_terms": ["update bank account"]}
        result = self.engine.evaluate(
            llm_analysis={"risk_score": 0.0},
            extraction=extraction,
            threat_intel={"virustotal": {"status": "completed"}, "email_auth": {"status": "completed"}},
            graph_intel={"interaction_count": 20}
        )
        self.assertTrue(result.verification_required)
        self.assertEqual(result.recommendation, "MANDATORY VERIFICATION \u2014 confirm via secondary channel")

    def test_failed_llm_zero_confidence(self):
        """Failed/missing LLM gives zero LLM confidence."""
        result_empty = self.engine.evaluate(
            llm_analysis={},
            extraction={},
            threat_intel={},
            graph_intel={}
        )
        self.assertEqual(result_empty.confidence_score, 0.0)
        
        result_no_score = self.engine.evaluate(
            llm_analysis={"explanation": "something"},
            extraction={},
            threat_intel={},
            graph_intel={}
        )
        self.assertEqual(result_no_score.confidence_score, 0.0)

if __name__ == "__main__":
    unittest.main()
