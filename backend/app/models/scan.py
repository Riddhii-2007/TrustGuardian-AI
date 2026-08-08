"""
Internal scan orchestration models for AnalyzerService.

These models are NEVER exposed via the public API.
The public boundary is always AnalysisResult (app/models/request.py).

Model hierarchy:
    ScanType       - enum of supported input types
    ScanRequest    - orchestrator input (caller sets scan_type explicitly)
    ScanEvidence   - central evidence accumulator; single source of truth
    ScanResult     - internal, fully-resolved result built from ScanEvidence
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.request import PsychologyFactors, QuickResult, DetailedReport
from app.models.threat_intel import ThreatIntelResult


class ScanType(str, Enum):
    """Supported scan input types.

    The scan type is always provided explicitly by the caller.
    AnalyzerService never infers or detects it from content.

    Future clients (REST API, Browser Extension, Outlook Plugin,
    Gmail Add-on, Mobile App) are responsible for setting this field.
    """

    TEXT = "text"      # BEC / plain-text message (current default)
    EMAIL = "email"    # Full email with headers and metadata
    URL = "url"        # URL / link analysis
    VENDOR = "vendor"  # Vendor due-diligence request
    QR = "qr"          # QR code payload
    IMAGE = "image"    # Image-based phishing
    PDF = "pdf"        # Document / PDF analysis


class ScanRequest(BaseModel):
    """Input to the scan orchestrator.

    scan_type is always set explicitly by the caller.
    Defaults to ScanType.TEXT for backward compatibility with
    the existing analyze_request(content: str) callers.
    """

    content: str = Field(
        ...,
        description="Raw content to analyze.",
    )
    scan_type: ScanType = Field(
        default=ScanType.TEXT,
        description=(
            "Type of scan. Always provided explicitly by the caller. "
            "AnalyzerService never infers this from content."
        ),
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Optional caller-supplied metadata (e.g. email headers, sender info).",
    )


class ScanEvidence(BaseModel):
    """Central evidence accumulator -- the single source of truth for a scan.

    Every service that participates in a scan writes its output into a
    designated slot on this object. The result builder (_build_result_from_evidence)
    reads exclusively from ScanEvidence to produce ScanResult.

    This design makes future modules purely additive:
        1. New service populates its designated slot (e.g. evidence.threat_intel).
        2. Result builder reads that slot when computing the final result.
        3. No orchestration logic requires changes.

    Active slots (currently wired):
        llm_analysis   - LLMService
        explanation    - ExplainableService

    Future slots (pre-defined, not yet wired):
        extraction     - ExtractionService
        threat_intel   - ThreatIntelService
        graph_intel    - GraphService
        sandbox        - SandboxService
    """

    # Active slots
    llm_analysis: dict = Field(
        default_factory=dict,
        description="Parsed JSON analysis dict returned by LLMService.",
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation produced by ExplainableService.",
    )

    # Future slots -- pre-defined for additive integration
    extraction: dict = Field(
        default_factory=dict,
        description="Indicators extracted from content (ExtractionService -- future).",
    )
    threat_intel: ThreatIntelResult | None = Field(
        default=None,
        description="External threat intelligence findings (ThreatIntelService).",
    )
    graph_intel: dict = Field(
        default_factory=dict,
        description="Graph relationship data from Neo4j (GraphService -- future).",
    )
    sandbox: dict = Field(
        default_factory=dict,
        description="Behavioral sandbox results (SandboxService -- future).",
    )

    # Provenance
    services_used: List[str] = Field(
        default_factory=list,
        description="Names of services that contributed evidence in this scan.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during orchestration.",
    )


class ScanResult(BaseModel):
    """Fully resolved, internal scan result. Never exposed via the public API.

    Built exclusively from ScanEvidence by the result builder.
    Mapped to the public AnalysisResult model at the API boundary.
    """

    scan_type:             ScanType
    risk_score:            float
    risk_level:            str
    psychology:            PsychologyFactors
    flags:                 List[str]
    explanation:           str
    evidence:              ScanEvidence
    latency_ms:            int   = 0
    trust_score:           float = 50.0
    confidence_score:      float = 0.0
    verification_required: bool  = False
    recommendation:        str   = "Pending analysis"
    # v2 additions
    quick_result:          Optional[QuickResult]    = None
    detailed_report:       Optional[DetailedReport] = None

