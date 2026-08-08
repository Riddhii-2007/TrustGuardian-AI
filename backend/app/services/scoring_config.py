"""
Centralized Scoring Configuration for TrustGuardian AI Trust Engine.
All hardcoded scoring logic, weights, penalties, and thresholds must live here.
"""

# ---------------------------------------------------------------------------
# Confidence Calculation (Max 100)
# Confidence represents completeness and reliability of available evidence.
# ---------------------------------------------------------------------------
CONF_LLM_MAX = 40.0
CONF_THREAT_INTEL_MAX = 30.0
CONF_GRAPH_MAX = 30.0

CONF_GRAPH_PER_INTERACTION = 3.0
CONF_THREAT_INTEL_TOTAL_CHECKS = 2  # VirusTotal + Email Auth

# ---------------------------------------------------------------------------
# Component Weights (for calculating base Risk/Trust before clamp)
# ---------------------------------------------------------------------------
WEIGHT_CONTENT = 0.40
WEIGHT_IDENTITY = 0.35
WEIGHT_HISTORICAL = 0.25

# ---------------------------------------------------------------------------
# Scoring Adjustments (Points added to component risk)
# ---------------------------------------------------------------------------
# Identity Risk
RULE_VT_MALICIOUS_PENALTY = 40.0
RULE_EMAIL_AUTH_FAIL_PENALTY = 15.0
RULE_DOMAIN_AGE_YOUNG_PENALTY = 10.0
RULE_DOMAIN_AGE_NEW_PENALTY = 5.0

# Historical Risk
RULE_TRUST_DROP_PENALTY = 30.0
RULE_GOOD_HISTORY_BONUS = -10.0

# Time-based decay for historical risk
INACTIVITY_FULL_CUTOFF_DAYS = 365
INACTIVITY_DECAY_START_DAYS = 90

# ---------------------------------------------------------------------------
# Content Risk Overrides
# ---------------------------------------------------------------------------
LOW_RISK_THRESHOLD = 20.0
CONTENT_RISK_HALVING_FACTOR = 0.5  # If Identity and Historical risk are low

# ---------------------------------------------------------------------------
# Derived Decisions (based on Final Trust Score: 0-100)
# ---------------------------------------------------------------------------
# Trust Score = 100 - Final Risk Score

def determine_risk_level(trust_score: float) -> str:
    """Map Trust Score to Risk Level."""
    if trust_score <= 20:
        return "CRITICAL"
    elif trust_score <= 40:
        return "HIGH"
    elif trust_score <= 60:
        return "MEDIUM"
    elif trust_score <= 80:
        return "LOW"
    else:
        return "SAFE"

HIGH_TRUST_THRESHOLD = 70.0
HIGH_CONFIDENCE_THRESHOLD = 70.0

def determine_recommendation(trust_score: float, confidence_score: float) -> str:
    """Map Trust and Confidence Score to a 2D Decision Matrix."""
    high_trust = trust_score >= HIGH_TRUST_THRESHOLD
    high_confidence = confidence_score >= HIGH_CONFIDENCE_THRESHOLD
    if high_trust and high_confidence:
        return "ALLOW"
    if high_trust and not high_confidence:
        return "VERIFY_UNVERIFIED_SENDER"   # clean signals, but new/unknown — not "risky"
    if not high_trust and high_confidence:
        return "BLOCK"
    return "BLOCK_ESCALATE_SOC"             # low trust AND low confidence

