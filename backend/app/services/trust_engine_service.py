"""
Trust Engine Service for TrustGuardianAI.

Pure, offline, deterministic scoring engine that consumes evidence
dictionaries and produces final risk, trust, confidence, verification,
and recommendation decisions.

Makes NO network, database, LLM, or framework calls.

Scoring architecture:
    Confidence  = LLM confidence + Threat-intel confidence + Graph confidence
    Content     = LLM risk_score (optionally halved when identity+history both low)
    Identity    = VirusTotal + email-auth + domain-age signals
    Historical  = trust-pattern changes + inactivity decay
    Fusion      = 0.40*content + 0.35*identity + 0.25*historical

Recommendation matrix:
    High trust + High confidence  → Proceed
    High trust + Low confidence   → Unverified
    Low trust  + High confidence  → Block
    Low trust  + Low confidence   → Block + escalate to SOC

Payment-change circuit breaker:
    Detects bank-account / routing / beneficiary / wire keywords in extraction.
    Overrides recommendation to MANDATORY VERIFICATION.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Confidence weights
_LLM_CONFIDENCE_MAX = 40.0
_THREAT_INTEL_CONFIDENCE_MAX = 30.0
_GRAPH_CONFIDENCE_MAX = 30.0
_GRAPH_CONFIDENCE_PER_INTERACTION = 3.0

# Threat-intel: maximum number of independent checks
_THREAT_INTEL_TOTAL_CHECKS = 2  # VirusTotal + email auth

# Fusion weights
_CONTENT_WEIGHT = 0.40
_IDENTITY_WEIGHT = 0.35
_HISTORICAL_WEIGHT = 0.25

# Thresholds
_HIGH_TRUST_THRESHOLD = 70.0
_HIGH_CONFIDENCE_THRESHOLD = 70.0

# Identity-risk contributions
_VT_MALICIOUS_PENALTY = 40.0
_EMAIL_AUTH_FAIL_PENALTY = 15.0
_DOMAIN_AGE_YOUNG_PENALTY = 10.0   # < 30 days
_DOMAIN_AGE_NEW_PENALTY = 5.0      # 30–180 days

# Historical-risk contributions
_TRUST_DROP_PENALTY = 30.0
_GOOD_HISTORY_BONUS = -10.0

# Inactivity decay
_INACTIVITY_FULL_CUTOFF_DAYS = 365
_INACTIVITY_DECAY_START_DAYS = 90

# Content-risk halving threshold
_LOW_RISK_THRESHOLD = 20.0

# Payment circuit-breaker phrases (matched against ExtractionService keys)
_PAYMENT_CIRCUIT_BREAKER_PHRASES: list[re.Pattern[str]] = [
    re.compile(r"\bbank[- ]?account\b", re.IGNORECASE),
    re.compile(r"\brouting[- ]?number\b", re.IGNORECASE),
    re.compile(r"\bbeneficiary\b", re.IGNORECASE),
    re.compile(r"\bnew[- ]?payment\b", re.IGNORECASE),
    re.compile(r"\bwire[- ]?transfer\b", re.IGNORECASE),
    re.compile(r"\bwire\b", re.IGNORECASE),
    re.compile(r"\baccount[- ]?number\b", re.IGNORECASE),
    re.compile(r"\bdirect[- ]?deposit\b", re.IGNORECASE),
    re.compile(r"\bswift[- ]?code\b", re.IGNORECASE),
    re.compile(r"\biban\b", re.IGNORECASE),
]


@dataclass
class TrustEngineResult:
    """Output of the TrustEngineService.

    All scores are on a 0–100 scale.
    risk_score + trust_score = 100 (always).
    confidence_score is independent of risk/trust.
    """

    risk_score: float
    trust_score: float
    confidence_score: float
    risk_level: str
    verification_required: bool
    recommendation: str


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp a value to [low, high]."""
    return max(low, min(high, value))


class TrustEngineService:
    """Pure, offline trust/risk/confidence scoring engine.

    Consumes evidence dictionaries produced by upstream services:
        - llm_analysis (from LLMService)
        - extraction (from ExtractionService)
        - threat_intel (from ThreatIntelService — future)
        - graph_intel (from GraphService — future)

    Thread-safe and stateless — safe to use as a singleton.
    """

    def evaluate(
        self,
        llm_analysis: dict[str, Any],
        extraction: dict[str, Any],
        threat_intel: dict[str, Any] | None = None,
        graph_intel: dict[str, Any] | None = None,
    ) -> TrustEngineResult:
        """Evaluate evidence and produce final scores + recommendation.

        Args:
            llm_analysis: Parsed LLM response dict (may be empty on failure).
            extraction: ExtractionService output dict.
            threat_intel: ThreatIntelService output dict (may be None/empty).
            graph_intel: GraphService output dict (may be None/empty).

        Returns:
            TrustEngineResult with all final scoring fields.
        """
        threat_intel = threat_intel or {}
        graph_intel = graph_intel or {}

        # --- Stage 1: Confidence ---
        confidence_score = self._compute_confidence(
            llm_analysis, threat_intel, graph_intel,
        )

        # --- Stage 2: Component risks ---
        identity_risk = self._compute_identity_risk(threat_intel)
        historical_risk = self._compute_historical_risk(graph_intel)
        content_risk = self._compute_content_risk(
            llm_analysis, identity_risk, historical_risk,
        )

        # --- Stage 3: Fusion ---
        raw_risk = (
            _CONTENT_WEIGHT * content_risk
            + _IDENTITY_WEIGHT * identity_risk
            + _HISTORICAL_WEIGHT * historical_risk
        )
        risk_score = _clamp(raw_risk)
        trust_score = 100.0 - risk_score
        confidence_score = _clamp(confidence_score)

        # --- Stage 4: Risk level ---
        risk_level = self._compute_risk_level(risk_score)

        # --- Stage 5: Recommendation ---
        high_trust = trust_score >= _HIGH_TRUST_THRESHOLD
        high_confidence = confidence_score >= _HIGH_CONFIDENCE_THRESHOLD

        if high_trust and high_confidence:
            recommendation = "Proceed"
            verification_required = False
        elif high_trust and not high_confidence:
            recommendation = (
                "Unverified — clean signals; confirm via secondary channel"
            )
            verification_required = False
        elif not high_trust and high_confidence:
            recommendation = "Block"
            verification_required = False
        else:
            recommendation = "Block + escalate to SOC"
            verification_required = False

        # --- Stage 6: Payment circuit breaker ---
        if self._check_payment_circuit_breaker(extraction):
            verification_required = True
            recommendation = (
                "MANDATORY VERIFICATION — confirm via secondary channel"
            )

        logger.info(
            "TrustEngine | risk=%.1f trust=%.1f confidence=%.1f "
            "level=%s verify=%s rec='%s'",
            risk_score, trust_score, confidence_score,
            risk_level, verification_required, recommendation,
        )

        return TrustEngineResult(
            risk_score=round(risk_score, 2),
            trust_score=round(trust_score, 2),
            confidence_score=round(confidence_score, 2),
            risk_level=risk_level,
            verification_required=verification_required,
            recommendation=recommendation,
        )

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_confidence(
        llm_analysis: dict[str, Any],
        threat_intel: dict[str, Any],
        graph_intel: dict[str, Any],
    ) -> float:
        """Compute overall evidence-completeness confidence.

        Independent of risk/trust — reflects how much evidence we have.

        LLM confidence: 40 only when valid, non-empty LLM analysis exists.
        Threat-intel:   30 * successful_checks / 2.
        Graph:          min(30, interaction_count * 3).
        """
        # LLM confidence
        llm_conf = 0.0
        if llm_analysis and isinstance(llm_analysis, dict):
            # Must have at least a risk_score to be considered valid
            if "risk_score" in llm_analysis:
                llm_conf = _LLM_CONFIDENCE_MAX

        # Threat-intel confidence
        ti_conf = 0.0
        if threat_intel:
            successful = 0
            # VirusTotal check
            vt = threat_intel.get("virustotal")
            if isinstance(vt, dict) and vt.get("status") == "completed":
                successful += 1
            # Email auth check (SPF/DKIM/DMARC)
            auth = threat_intel.get("email_auth")
            if isinstance(auth, dict) and auth.get("status") == "completed":
                successful += 1
            ti_conf = _THREAT_INTEL_CONFIDENCE_MAX * successful / _THREAT_INTEL_TOTAL_CHECKS

        # Graph confidence
        graph_conf = 0.0
        if graph_intel:
            interaction_count = graph_intel.get("interaction_count", 0)
            if isinstance(interaction_count, (int, float)) and interaction_count > 0:
                graph_conf = min(
                    _GRAPH_CONFIDENCE_MAX,
                    interaction_count * _GRAPH_CONFIDENCE_PER_INTERACTION,
                )

        return llm_conf + ti_conf + graph_conf

    # ------------------------------------------------------------------
    # Identity Risk
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_identity_risk(threat_intel: dict[str, Any]) -> float:
        """Compute identity-based risk from threat intelligence.

        VirusTotal malicious hit: +40
        SPF/DKIM/DMARC failure:  +15
        Domain age < 30 days:    +10
        Domain age 30–180 days:  +5
        Missing checks:          +0
        """
        risk = 0.0
        if not threat_intel:
            return risk

        # VirusTotal
        vt = threat_intel.get("virustotal")
        if isinstance(vt, dict):
            if vt.get("malicious", False):
                risk += _VT_MALICIOUS_PENALTY

        # Email authentication (SPF/DKIM/DMARC)
        auth = threat_intel.get("email_auth")
        if isinstance(auth, dict):
            if auth.get("pass") is False:
                risk += _EMAIL_AUTH_FAIL_PENALTY

        # Domain age
        domain_age_days = threat_intel.get("domain_age_days")
        if isinstance(domain_age_days, (int, float)):
            if domain_age_days < 30:
                risk += _DOMAIN_AGE_YOUNG_PENALTY
            elif domain_age_days < 180:
                risk += _DOMAIN_AGE_NEW_PENALTY

        return risk

    # ------------------------------------------------------------------
    # Historical Risk
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_historical_risk(graph_intel: dict[str, Any]) -> float:
        """Compute historical risk from graph intelligence.

        No prior interactions:     0 (neutral)
        Sharp trust-pattern drop: +30
        Consistent good history:  -10
        After 365 days inactive:   0
        90–365 days inactive:      linear decay to 50%
        """
        if not graph_intel:
            return 0.0

        interaction_count = graph_intel.get("interaction_count", 0)
        if not isinstance(interaction_count, (int, float)) or interaction_count <= 0:
            return 0.0

        risk = 0.0

        # Trust-pattern drop detection
        if graph_intel.get("trust_drop", False):
            risk += _TRUST_DROP_PENALTY

        # Consistent good history bonus
        if graph_intel.get("consistent_good", False):
            risk += _GOOD_HISTORY_BONUS

        # Inactivity decay
        days_since_last = graph_intel.get("days_since_last_interaction")
        if isinstance(days_since_last, (int, float)) and days_since_last > 0:
            if days_since_last >= _INACTIVITY_FULL_CUTOFF_DAYS:
                # Full cutoff — no historical influence
                risk = 0.0
            elif days_since_last >= _INACTIVITY_DECAY_START_DAYS:
                # Linear decay from 100% at 90d to 50% at 365d
                decay_range = _INACTIVITY_FULL_CUTOFF_DAYS - _INACTIVITY_DECAY_START_DAYS
                days_into_decay = days_since_last - _INACTIVITY_DECAY_START_DAYS
                decay_factor = 1.0 - 0.5 * (days_into_decay / decay_range)
                risk *= decay_factor

        return risk

    # ------------------------------------------------------------------
    # Content Risk
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_content_risk(
        llm_analysis: dict[str, Any],
        identity_risk: float,
        historical_risk: float,
    ) -> float:
        """Compute content-based risk from LLM analysis.

        When both identity and historical risk are low, the LLM risk
        gets halved to avoid urgency-only inflation.
        """
        if not llm_analysis or not isinstance(llm_analysis, dict):
            return 0.0

        raw_score = llm_analysis.get("risk_score", 0.0)
        try:
            llm_risk = float(raw_score)
        except (TypeError, ValueError):
            return 0.0

        llm_risk = _clamp(llm_risk)

        # Apply halving when both identity and historical are low
        both_low = (
            identity_risk < _LOW_RISK_THRESHOLD
            and historical_risk < _LOW_RISK_THRESHOLD
        )
        if both_low:
            return llm_risk * 0.5

        return llm_risk

    # ------------------------------------------------------------------
    # Risk Level
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_risk_level(risk_score: float) -> str:
        """Map risk_score to a human-readable risk level."""
        if risk_score >= 80:
            return "Critical"
        elif risk_score >= 60:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        elif risk_score >= 20:
            return "Low"
        else:
            return "Safe"

    # ------------------------------------------------------------------
    # Payment Circuit Breaker
    # ------------------------------------------------------------------

    @staticmethod
    def _check_payment_circuit_breaker(
        extraction: dict[str, Any],
    ) -> bool:
        """Detect payment-change indicators in extraction evidence.

        Returns True if any bank-account, routing-number, beneficiary,
        new-payment, or wire-transfer signal is detected.
        Uses the real ExtractionService output keys.
        """
        if not extraction:
            return False

        # Check payment_terms list from ExtractionService
        payment_terms: list[str] = extraction.get("payment_terms", [])
        for term in payment_terms:
            for pattern in _PAYMENT_CIRCUIT_BREAKER_PHRASES:
                if pattern.search(term):
                    return True

        # Also scan the raw content keys that ExtractionService may populate
        # (e.g., subject line mentioning wire transfers)
        for key in ("subject",):
            val = extraction.get(key, "")
            if isinstance(val, str):
                for pattern in _PAYMENT_CIRCUIT_BREAKER_PHRASES:
                    if pattern.search(val):
                        return True

        return False


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
trust_engine_service = TrustEngineService()
