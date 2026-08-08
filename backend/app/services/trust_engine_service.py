"""
Trust Engine Service for TrustGuardianAI.

Pure, offline, deterministic scoring engine that consumes typed evidence
models and produces final risk, trust, confidence, verification,
and recommendation decisions.

Makes NO network, database, LLM, or framework calls.
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

from app.services import scoring_config as config
from app.models.trust_engine import (
    TrustEngineResult,
    LLMAnalysisResult,
    GraphAnalysisResult,
    DecisionTrace,
)
from app.models.threat_intel import ThreatIntelResult

logger = logging.getLogger(__name__)

def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))

class TrustEngineService:
    """Pure, offline trust/risk/confidence scoring engine."""

    def evaluate(
        self,
        llm_analysis: LLMAnalysisResult,
        threat_intel: ThreatIntelResult | None = None,
        graph_intel: GraphAnalysisResult | None = None,
    ) -> TrustEngineResult:
        
        reasoning: List[DecisionTrace] = []
        evidence_used: List[str] = []

        if llm_analysis and llm_analysis.risk_score > 0:
            evidence_used.append("llm_analysis")
        if threat_intel and threat_intel.urls_checked is not None:
            evidence_used.append("threat_intel")
        if graph_intel and graph_intel.interaction_count > 0:
            evidence_used.append("graph_intel")
            
        # --- Stage 1: Confidence ---
        confidence_score, conf_traces = self._compute_confidence(llm_analysis, threat_intel, graph_intel)
        reasoning.extend(conf_traces)
        
        # --- Stage 2: Component risks ---
        identity_risk, id_traces = self._compute_identity_risk(threat_intel)
        reasoning.extend(id_traces)
        
        historical_risk, hist_traces = self._compute_historical_risk(graph_intel)
        reasoning.extend(hist_traces)
        
        content_risk, cont_traces = self._compute_content_risk(llm_analysis, identity_risk, historical_risk)
        reasoning.extend(cont_traces)

        # --- Stage 3: Fusion ---
        active_weights = 0.0
        weighted_sum = 0.0

        if content_risk is not None:
            active_weights += config.WEIGHT_CONTENT
            weighted_sum += config.WEIGHT_CONTENT * content_risk
            
        if identity_risk is not None:
            active_weights += config.WEIGHT_IDENTITY
            weighted_sum += config.WEIGHT_IDENTITY * identity_risk
            
        if historical_risk is not None:
            active_weights += config.WEIGHT_HISTORICAL
            weighted_sum += config.WEIGHT_HISTORICAL * historical_risk
            
        if active_weights > 0:
            raw_risk = weighted_sum / active_weights
        else:
            raw_risk = 0.0
            
        risk_score = _clamp(raw_risk)
        trust_score = 100.0 - risk_score
        confidence_score = _clamp(confidence_score)
        
        reasoning.append(DecisionTrace(
            rule_name="Fusion",
            evidence_source="TrustEngine",
            weight_applied=0.0,
            explanation=f"Calculated Trust Score {trust_score:.2f} (Confidence: {confidence_score:.2f})"
        ))

        # --- Stage 4: Decisions ---
        risk_level = config.determine_risk_level(trust_score)
        
        recommendation = config.determine_recommendation(trust_score, confidence_score)
        
        component_scores = {}
        if content_risk is not None:
            component_scores["content"] = round(content_risk, 2)
        if identity_risk is not None:
            component_scores["identity"] = round(identity_risk, 2)
        if historical_risk is not None:
            component_scores["historical"] = round(historical_risk, 2)

        return TrustEngineResult(
            trust_score=round(trust_score, 2),
            risk_level=risk_level,
            confidence_score=round(confidence_score, 2),
            recommendation=recommendation,
            reasoning=reasoning,
            evidence_used=evidence_used,
            component_scores=component_scores
        )

    # ------------------------------------------------------------------
    # Evaluators
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_confidence(
        llm: LLMAnalysisResult, ti: ThreatIntelResult | None, graph: GraphAnalysisResult | None
    ) -> Tuple[float, List[DecisionTrace]]:
        traces = []
        conf = 0.0
        
        if llm and llm.risk_score > 0:
            conf += config.CONF_LLM_MAX
            traces.append(DecisionTrace(
                rule_name="LLM_Confidence", evidence_source="llm", weight_applied=config.CONF_LLM_MAX,
                explanation="Valid LLM analysis present."
            ))
            
        if ti:
            successful = 0
            if ti.virustotal:
                successful += 1
            if ti.spf != "NONE" or ti.dkim != "NONE" or ti.dmarc != "NONE":
                successful += 1
            if successful > 0:
                ti_conf = config.CONF_THREAT_INTEL_MAX * successful / config.CONF_THREAT_INTEL_TOTAL_CHECKS
                conf += ti_conf
                traces.append(DecisionTrace(
                    rule_name="TI_Confidence", evidence_source="threat_intel", weight_applied=ti_conf,
                    explanation=f"{successful} threat intel checks completed."
                ))
            
        if graph and graph.interaction_count > 0:
            graph_conf = min(config.CONF_GRAPH_MAX, graph.interaction_count * config.CONF_GRAPH_PER_INTERACTION)
            conf += graph_conf
            traces.append(DecisionTrace(
                rule_name="Graph_Confidence", evidence_source="graph", weight_applied=graph_conf,
                explanation=f"Based on {graph.interaction_count} prior interactions."
            ))
            
        return conf, traces

    @staticmethod
    def _compute_identity_risk(ti: ThreatIntelResult | None) -> Tuple[float | None, List[DecisionTrace]]:
        traces = []
        if not ti: return None, traces
        
        has_auth = any(status != "NONE" for status in [ti.spf, ti.dkim, ti.dmarc])
        has_urls = ti.urls_checked > 0
        if not has_auth and not has_urls:
            return None, traces
            
        risk = 0.0
        
        if ti.virustotal and ti.virustotal.malicious > 0:
            risk += config.RULE_VT_MALICIOUS_PENALTY
            traces.append(DecisionTrace(
                rule_name="VT_Malicious", evidence_source="threat_intel.virustotal", 
                weight_applied=config.RULE_VT_MALICIOUS_PENALTY, explanation="VirusTotal flagged URL/Domain as malicious."
            ))
            
        auth_failed = any(status == "FAIL" for status in [ti.spf, ti.dkim, ti.dmarc])
        if auth_failed:
            risk += config.RULE_EMAIL_AUTH_FAIL_PENALTY
            traces.append(DecisionTrace(
                rule_name="Email_Auth_Fail", evidence_source="threat_intel.email_auth", 
                weight_applied=config.RULE_EMAIL_AUTH_FAIL_PENALTY, explanation="Email authentication (SPF/DKIM/DMARC) failed."
            ))
        
        return risk, traces

    @staticmethod
    def _compute_historical_risk(graph: GraphAnalysisResult | None) -> Tuple[float | None, List[DecisionTrace]]:
        traces = []
        if not graph or graph.interaction_count <= 0: return None, traces
        
        risk = 0.0
        
        if graph.trust_drop:
            risk += config.RULE_TRUST_DROP_PENALTY
            traces.append(DecisionTrace(
                rule_name="Trust_Drop", evidence_source="graph.trust_drop", 
                weight_applied=config.RULE_TRUST_DROP_PENALTY, explanation="Sharp drop in trust pattern detected."
            ))
            
        if graph.consistent_good:
            risk += config.RULE_GOOD_HISTORY_BONUS
            traces.append(DecisionTrace(
                rule_name="Good_History", evidence_source="graph.consistent_good", 
                weight_applied=config.RULE_GOOD_HISTORY_BONUS, explanation="Consistent history of safe interactions."
            ))
            
        if graph.days_since_last_interaction is not None and graph.days_since_last_interaction > 0:
            days = graph.days_since_last_interaction
            if days >= config.INACTIVITY_FULL_CUTOFF_DAYS:
                risk = 0.0
                traces.append(DecisionTrace(
                    rule_name="Inactivity_Cutoff", evidence_source="graph.days", weight_applied=0.0,
                    explanation="Over 365 days inactive. Historical risk reset."
                ))
            elif days >= config.INACTIVITY_DECAY_START_DAYS:
                decay_range = config.INACTIVITY_FULL_CUTOFF_DAYS - config.INACTIVITY_DECAY_START_DAYS
                days_into = days - config.INACTIVITY_DECAY_START_DAYS
                factor = 1.0 - 0.5 * (days_into / decay_range)
                risk *= factor
                traces.append(DecisionTrace(
                    rule_name="Inactivity_Decay", evidence_source="graph.days", weight_applied=0.0,
                    explanation=f"Inactivity decay factor {factor:.2f} applied to historical risk."
                ))
                
        return risk, traces

    @staticmethod
    def _compute_content_risk(
        llm: LLMAnalysisResult,
        identity_risk: float | None = None,
        historical_risk: float | None = None,
    ) -> Tuple[float | None, List[DecisionTrace]]:
        traces = []
        if not llm: return None, traces

        raw = _clamp(llm.risk_score)
        other_signals_low = (
            (identity_risk is not None and identity_risk <= config.LOW_RISK_THRESHOLD)
            and (historical_risk is not None and historical_risk <= config.LOW_RISK_THRESHOLD)
        )
        if other_signals_low:
            risk = raw * config.CONTENT_RISK_HALVING_FACTOR
            traces.append(DecisionTrace(
                rule_name="Content_Risk_Dampening",
                evidence_source="llm.risk_score",
                weight_applied=risk,
                explanation="Content risk dampened — no corroborating identity or historical signal."
            ))
        else:
            risk = raw
            traces.append(DecisionTrace(
                rule_name="LLM_Content_Risk",
                evidence_source="llm.risk_score",
                weight_applied=risk,
                explanation=f"LLM base risk score: {risk:.2f}"
            ))
            
        return risk, traces

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
trust_engine_service = TrustEngineService()
