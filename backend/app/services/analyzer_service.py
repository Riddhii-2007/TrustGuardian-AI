"""
Scan Orchestrator for TrustGuardianAI.

AnalyzerService coordinates the complete scan workflow following
an evidence-first architecture:

    ScanRequest
        → validate input
        → ScanEvidence (parallel evidence collection)
        → _build_result_from_evidence (result builder)
        → ScanResult
        → _to_analysis_result (public boundary)
        → AnalysisResult

ScanEvidence is the single source of truth for every scan.
Every service writes into its designated slot; the result builder
reads exclusively from the evidence object.

Responsibilities:
    ✓ Accept scan requests
    ✓ Validate input
    ✓ Coordinate service execution
    ✓ Aggregate evidence into ScanEvidence
    ✓ Handle partial failures gracefully
    ✓ Build ScanResult from aggregated evidence
    ✓ Return backward-compatible AnalysisResult

NOT responsible for:
    ✗ LLM SDK calls            → LLMService
    ✗ Trust score calculation   → TrustScoreService (future)
    ✗ Graph queries             → GraphService (future)
    ✗ Threat intelligence       → ThreatIntelService (future)
    ✗ Explainability generation → ExplainableService
    ✗ Prompt engineering        → app/prompts/ (future migration)
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable
from typing import TypeVar

from app.models.request import AnalysisResult, PsychologyFactors
from app.models.scan import ScanEvidence, ScanRequest, ScanResult, ScanType
from app.services.explainable_service import (
    ExplainableService,
    explainable_service as _default_explainable,
)
from app.services.llm_service import LLMService, llm_service as _default_llm

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Safe defaults applied when LLM response fields are absent or invalid
_DEFAULT_RISK_SCORE: float = 50.0
_DEFAULT_RISK_LEVEL: str = "Unknown"


class AnalyzerService:
    """Scan Orchestrator — coordinates the full TrustGuardianAI scan workflow.

    Design principles:
        Evidence-first:  ScanEvidence is the single source of truth.
                         The result builder reads only from evidence.
        Dependency injection: all services supplied via constructor.
        Graceful degradation: every service call wrapped with _run_safe().
        Async execution: independent evidence stages run concurrently.
        Open for extension: future services slot in without changing logic.

    Public API (backward compatible):
        await analyzer_service.analyze_request(content)   → AnalysisResult
        await analyzer_service.scan(ScanRequest(...))     → AnalysisResult
    """

    # BEC / Social Engineering system prompt.
    # Retained here from the original implementation.
    # Will be migrated to app/prompts/ in a dedicated future refactor.
    SYSTEM_PROMPT = """
    You are an expert cybersecurity analyst specializing in Business Email Compromise (BEC) and social engineering.
    Analyze the following business request (email or message) and evaluate it across 5 psychological vectors.
    You MUST output valid JSON only, matching the exact structure below. Do not include markdown blocks or any other text.

    Scores must be a float between 0.0 and 1.0.
    Calculate an overall risk_score from 0 to 100 based on the manipulation tactics.
    Set risk_level to one of: "Safe", "Low", "Medium", "High", "Critical".
    Extract specific suspicious phrases or tactics into the 'flags' array.
    Provide a concise 1-2 sentence 'explanation' of your decision.

    Expected JSON format:
    {
        "risk_score": 85,
        "risk_level": "High",
        "psychology": {
            "urgency": 0.9,
            "authority": 0.8,
            "fear": 0.2,
            "familiarity": 0.1,
            "intent": 0.7
        },
        "flags": ["Urgent wire transfer", "CEO impersonation"],
        "explanation": "High urgency and authority are used to pressure the target into bypassing normal financial controls."
    }
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
        explainable_service: ExplainableService | None = None,
        # ---------------------------------------------------------------
        # Future services — inject here when each is implemented.
        # Uncomment as their dedicated implementations become available.
        # ---------------------------------------------------------------
        # extraction_service: ExtractionService | None = None,
        # threat_intel_service: ThreatIntelService | None = None,
        # graph_service: GraphService | None = None,
        # trust_score_service: TrustScoreService | None = None,
    ) -> None:
        """Initialize with optional service overrides (dependency injection).

        Falls back to module-level singletons when no override is provided.
        This allows tests to inject mock services without modifying the singleton.
        """
        self.llm_service = llm_service or _default_llm
        self._explainable = explainable_service or _default_explainable
        # self._extraction = extraction_service      # future
        # self._threat_intel = threat_intel_service  # future
        # self._graph = graph_service                # future
        # self._trust_score = trust_score_service    # future

        logger.info(
            "AnalyzerService initialized | llm=%s | explainable=%s",
            type(self.llm_service).__name__,
            type(self._explainable).__name__,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_request(self, content: str) -> AnalysisResult:
        """Backward-compatible entry point.

        Called by: app/api/requests.py (lines 21 and 64).
        Delegates to scan() using the default TEXT scan type.
        This method signature is preserved exactly from the original service.
        """
        return await self.scan(ScanRequest(content=content))

    async def scan(self, request: ScanRequest) -> AnalysisResult:
        """Primary orchestrator entry point.

        The scan_type is used directly as provided in the request.
        AnalyzerService never infers or detects scan type from content.
        Future clients (REST API, browser extensions, plugins) are
        responsible for setting the correct scan_type.

        Workflow:
            ScanRequest
              → validate
              → ScanEvidence (parallel evidence collection)
              → _build_result_from_evidence (result builder)
              → ScanResult
              → _to_analysis_result (public boundary)
              → AnalysisResult

        Args:
            request: Structured scan request. scan_type is used as-is.

        Returns:
            AnalysisResult — the public-facing model, schema unchanged.
        """
        start_time = time.monotonic()

        # 1. Validate — short-circuit on empty content
        if not request.content.strip():
            logger.debug("Empty content — returning safe default result.")
            return self._safe_default_result()

        # 2. Initialize the evidence accumulator.
        #    This is the single source of truth for the entire scan.
        #    All services write into their designated slot.
        #    The result builder reads exclusively from this object.
        evidence = ScanEvidence()

        # 3. Collect evidence — parallel where services are independent.
        #    Each coroutine populates one slot of the evidence object.
        #    _run_safe() ensures a failing service never aborts the scan.
        await asyncio.gather(
            self._collect_llm_evidence(request, evidence),
            # ----------------------------------------------------------
            # Future evidence stages — add here as services are built.
            # Each runs concurrently alongside the LLM call.
            # ----------------------------------------------------------
            # self._collect_extraction_evidence(request, evidence),
            # self._collect_threat_intel_evidence(request, evidence),
            # self._collect_graph_evidence(request, evidence),
        )

        # 4. Explainability — sequential; depends on evidence.llm_analysis
        #    being populated by step 3 above.
        await self._collect_explanation(evidence)

        # 5. Build the result from evidence.
        #    The result builder is the only place that reads ScanEvidence
        #    to produce structured output.
        latency_ms = int((time.monotonic() - start_time) * 1000)
        scan_result = self._build_result_from_evidence(
            evidence=evidence,
            scan_type=request.scan_type,
            latency_ms=latency_ms,
        )

        logger.info(
            "Scan complete | type=%s risk_score=%.1f risk_level=%s "
            "latency_ms=%d services=%s warnings=%d",
            scan_result.scan_type.value,
            scan_result.risk_score,
            scan_result.risk_level,
            scan_result.latency_ms,
            evidence.services_used,
            len(evidence.warnings),
        )

        # 6. Map to the public model at the API boundary.
        #    AnalysisResult schema is never modified.
        return self._to_analysis_result(scan_result)

    # ------------------------------------------------------------------
    # Evidence Collection
    # Each method populates exactly one slot on ScanEvidence.
    # All methods are wrapped with _run_safe() for graceful degradation.
    # ------------------------------------------------------------------

    async def _collect_llm_evidence(
        self,
        request: ScanRequest,
        evidence: ScanEvidence,
    ) -> None:
        """Call LLMService and populate evidence.llm_analysis.

        Passes a filtered view of the current evidence to the LLM so
        that future services running before this stage can enrich the
        AI reasoning step. Currently all context slots are empty; as
        future services are wired in before the LLM stage, their output
        will automatically be forwarded here.
        """
        user_prompt = f"Analyze this business request:\n\n{request.content}"
        system_prompt = self._get_system_prompt(request.scan_type)

        # Build LLM context from non-empty future evidence slots.
        # Currently always empty; future services populate these before
        # the LLM call so they contribute to AI reasoning.
        context = {
            key: val
            for key, val in evidence.model_dump(
                include={"extraction", "threat_intel", "graph_intel"}
            ).items()
            if val  # omit empty dicts — no noise in the LLM prompt
        }

        async def _call() -> dict:
            result = await self.llm_service.analyze(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                evidence=context or None,
            )
            return result.analysis if isinstance(result.analysis, dict) else {}

        llm_data = await self._run_safe("llm", _call(), default={}, evidence=evidence)
        evidence.llm_analysis = llm_data
        if llm_data:
            evidence.services_used.append("llm")

    async def _collect_explanation(
        self,
        evidence: ScanEvidence,
    ) -> None:
        """Call ExplainableService and populate evidence.explanation.

        Runs after all parallel evidence stages so it receives the fullest
        available context. Falls back to the LLM's own explanation field
        if ExplainableService fails.
        """
        llm_explanation = evidence.llm_analysis.get("explanation", "")

        async def _call() -> str:
            return await self._explainable.generate_explanation(
                evidence.model_dump()
            )

        explanation = await self._run_safe(
            "explainable",
            _call(),
            default=llm_explanation or "Analysis completed.",
            evidence=evidence,
        )
        evidence.explanation = explanation
        evidence.services_used.append("explainable")

    # ------------------------------------------------------------------
    # Future evidence collection — implement in dedicated service tasks.
    #
    # Pattern each future method must follow:
    #   1. Call the dedicated service (wrapped with _run_safe).
    #   2. Populate the appropriate ScanEvidence slot.
    #   3. Append service name to evidence.services_used on success.
    #
    # Once implemented, uncomment the corresponding line in scan() step 3.
    # ------------------------------------------------------------------

    # async def _collect_extraction_evidence(
    #     self, request: ScanRequest, evidence: ScanEvidence
    # ) -> None:
    #     """TODO: ExtractionService — extract indicators from content."""
    #     ...

    # async def _collect_threat_intel_evidence(
    #     self, request: ScanRequest, evidence: ScanEvidence
    # ) -> None:
    #     """TODO: ThreatIntelService — query external threat intel sources."""
    #     ...

    # async def _collect_graph_evidence(
    #     self, request: ScanRequest, evidence: ScanEvidence
    # ) -> None:
    #     """TODO: GraphService — look up indicators in Neo4j."""
    #     ...

    # ------------------------------------------------------------------
    # Result Builder — reads exclusively from ScanEvidence
    # ------------------------------------------------------------------

    def _build_result_from_evidence(
        self,
        evidence: ScanEvidence,
        scan_type: ScanType,
        latency_ms: int,
    ) -> ScanResult:
        """Build ScanResult from the aggregated ScanEvidence.

        ScanEvidence is the single source of truth.
        This is the ONLY method that reads from evidence to produce output.
        Safe defaults are applied for any missing or malformed fields.

        Future services extend the result by populating their slot:
            evidence.threat_intel → can adjust risk_score weighting
            evidence.graph_intel  → can surface related entity risk
            evidence.sandbox      → can add behavioral context
        Each addition requires only a new read from the relevant slot here,
        with no changes to the orchestration flow.
        """
        llm = evidence.llm_analysis

        # --- Psychology factors ---
        raw_psychology = llm.get("psychology", {})
        try:
            psychology = PsychologyFactors(**raw_psychology)
        except Exception as exc:
            evidence.warnings.append(f"Psychology field parsing failed: {exc}")
            psychology = PsychologyFactors(
                urgency=0.0,
                authority=0.0,
                fear=0.0,
                familiarity=0.0,
                intent=0.0,
            )

        # --- Risk score ---
        # Reads from evidence.llm_analysis slot.
        # TODO: when TrustScoreService is available, replace with:
        #   risk_score = evidence.trust_score.get("score", _DEFAULT_RISK_SCORE)
        raw_score = llm.get("risk_score", _DEFAULT_RISK_SCORE)
        try:
            risk_score = float(raw_score)
            risk_score = max(0.0, min(100.0, risk_score))  # clamp to valid range
        except (TypeError, ValueError):
            evidence.warnings.append(
                f"Invalid risk_score value '{raw_score}' — using default."
            )
            risk_score = _DEFAULT_RISK_SCORE

        # --- Explanation ---
        # Reads from evidence.explanation slot (populated by ExplainableService).
        # Falls back to the LLM's own explanation if ExplainableService did
        # not contribute or produced an empty result.
        explanation = evidence.explanation or str(
            llm.get("explanation", "Analysis completed.")
        )

        return ScanResult(
            scan_type=scan_type,
            risk_score=risk_score,
            risk_level=str(llm.get("risk_level", _DEFAULT_RISK_LEVEL)),
            psychology=psychology,
            flags=[str(f) for f in llm.get("flags", [])],
            explanation=explanation,
            evidence=evidence,
            latency_ms=latency_ms,
        )

    def _to_analysis_result(self, scan_result: ScanResult) -> AnalysisResult:
        """Map internal ScanResult → public AnalysisResult.

        This is the backward-compatibility boundary.
        The AnalysisResult schema is never modified.
        All internal enrichment (ScanEvidence, scan_type, latency, warnings)
        remains internal and is not surfaced to API consumers.
        """
        return AnalysisResult(
            risk_score=scan_result.risk_score,
            risk_level=scan_result.risk_level,
            psychology=scan_result.psychology,
            flags=scan_result.flags,
            explanation=scan_result.explanation,
        )

    # ------------------------------------------------------------------
    # Private Utilities
    # ------------------------------------------------------------------

    async def _run_safe(
        self,
        label: str,
        coro: Awaitable[T],
        default: T,
        evidence: ScanEvidence | None = None,
    ) -> T:
        """Execute a service coroutine with graceful degradation.

        On failure: logs a warning, appends to evidence.warnings (if provided),
        and returns the default value. Never propagates an exception.

        Every service call in the orchestrator goes through this method.
        This guarantees that a single failing service cannot abort the scan.

        Args:
            label:    Human-readable service identifier for logging.
            coro:     Awaitable coroutine to execute.
            default:  Value returned when the coroutine raises.
            evidence: If provided, failure message appended to evidence.warnings.
        """
        try:
            return await coro
        except Exception as exc:
            msg = f"Service '{label}' failed — scan continues without it: {exc}"
            logger.warning(msg)
            if evidence is not None:
                evidence.warnings.append(msg)
            return default

    def _get_system_prompt(self, scan_type: ScanType) -> str:
        """Return the system prompt for the given scan type.

        Currently returns the single BEC prompt for all scan types.

        Extension point: when prompt management is refactored, replace
        this method body with a per-type dispatch:
            SCAN_PROMPTS = {ScanType.TEXT: BEC_PROMPT, ScanType.URL: URL_PROMPT, ...}
            return SCAN_PROMPTS.get(scan_type, self.SYSTEM_PROMPT)
        No other method needs to change.
        """
        # TODO: dispatch per-type prompts when prompt management is refactored
        return self.SYSTEM_PROMPT

    @staticmethod
    def _safe_default_result() -> AnalysisResult:
        """Return a safe default result for empty or invalid input."""
        return AnalysisResult(
            risk_score=0.0,
            risk_level="Safe",
            psychology=PsychologyFactors(
                urgency=0.0,
                authority=0.0,
                fear=0.0,
                familiarity=0.0,
                intent=0.0,
            ),
            flags=[],
            explanation="No content provided for analysis.",
        )


# ---------------------------------------------------------------------------
# Module-level singleton — backward compatible
#
# Preserves the existing import used by app/api/requests.py:
#   from app.services.analyzer_service import analyzer_service
# ---------------------------------------------------------------------------
analyzer_service = AnalyzerService()
