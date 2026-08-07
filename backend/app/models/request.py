"""
Pydantic models for the public API boundary.

AnalysisResult is the public-facing model returned by all /api/requests
endpoints. It is backward-compatible — all original fields are preserved.
The two new optional fields (quick_result, detailed_report) carry the
two-level analysis introduced in the v2 schema.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Psychology (unchanged — retained for backward compatibility)
# ---------------------------------------------------------------------------

class PsychologyFactors(BaseModel):
    urgency:     float = Field(..., ge=0, le=1)
    authority:   float = Field(..., ge=0, le=1)
    fear:        float = Field(..., ge=0, le=1)
    familiarity: float = Field(..., ge=0, le=1)
    intent:      float = Field(..., ge=0, le=1)


# ---------------------------------------------------------------------------
# QuickResult — lightweight card-level decision
# Populated by: LLM summary + Trust Engine scores (merged in result builder)
# ---------------------------------------------------------------------------

class QuickResult(BaseModel):
    """Lightweight summary shown on email list / cards.

    trust_score and risk_level come from the Trust Engine.
    decision is derived from trust_score thresholds.
    summary is the one-sentence AI explanation (≤ 15 words).
    """

    trust_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Final trust score from the Trust Engine (0-100).",
    )
    risk_level: str = Field(
        ...,
        description="SAFE | LOW | MEDIUM | HIGH | CRITICAL",
    )
    decision: str = Field(
        ...,
        description=(
            "SAFE_TO_OPEN | LIKELY_SAFE | VERIFY_FIRST | HIGH_RISK | DO_NOT_OPEN"
        ),
    )
    summary: str = Field(
        ...,
        description="One concise AI-generated sentence (max 15 words).",
    )


# ---------------------------------------------------------------------------
# DetailedReport — full analysis shown in the drill-down view
# Populated by: LLM signals + Trust Engine confidence + server timestamp
# ---------------------------------------------------------------------------

class DetailedReport(BaseModel):
    """Complete analysis shown when the user opens the report view.

    confidence comes from the Trust Engine.
    All signal/reasoning fields come from the LLM.
    analysis_timestamp is set by the server at result-build time.
    """

    confidence: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Evidence reliability score from the Trust Engine (0-100).",
    )
    positive_signals: List[str] = Field(
        default_factory=list,
        description="Clean/safe indicators found (e.g. 'SPF Passed', 'Valid SSL').",
    )
    negative_signals: List[str] = Field(
        default_factory=list,
        description="Warning indicators found (e.g. 'Newly registered domain').",
    )
    threats_detected: List[str] = Field(
        default_factory=list,
        description="Active threat categories (e.g. 'BEC attempt', 'Malware URL').",
    )
    recommendation: str = Field(
        default="",
        description="Human-readable action (e.g. 'Safe to interact.').",
    )
    reasoning: str = Field(
        default="",
        description="AI explanation of the decision (2–5 sentences).",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description=(
            "Concrete evidence items from TI/Extraction/Graph "
            "(e.g. 'VirusTotal: Clean', 'SPF Passed', 'WHOIS Age: 11 years')."
        ),
    )
    analysis_timestamp: str = Field(
        default="",
        description="ISO-8601 timestamp when analysis was completed.",
    )


# ---------------------------------------------------------------------------
# AnalysisResult — public API model (backward-compatible)
# ---------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    """Public analysis result returned by all /api/requests endpoints.

    Backward-compatible: all v1 fields are preserved unchanged.
    v2 additions (quick_result, detailed_report) are Optional so existing
    consumers that do not read them are unaffected.
    """

    # ── v1 fields (unchanged) ────────────────────────────────────────────────
    risk_score:            float            = Field(..., ge=0, le=100)
    risk_level:            str
    psychology:            PsychologyFactors
    flags:                 List[str]
    explanation:           str
    trust_score:           float            = Field(default=50.0, ge=0, le=100)
    confidence_score:      float            = Field(default=0.0, ge=0, le=100)
    verification_required: bool             = False
    recommendation:        str              = "Pending analysis"

    # ── v2 fields (additive, optional) ──────────────────────────────────────
    quick_result:    Optional[QuickResult]    = None
    detailed_report: Optional[DetailedReport] = None


# ---------------------------------------------------------------------------
# BusinessRequest — container returned by all /api/requests routes
# ---------------------------------------------------------------------------

class BusinessRequest(BaseModel):
    id:         str
    title:      str
    content:    str
    requester:  str
    created_at: datetime
    status:     str
    analysis:   Optional[AnalysisResult] = None
