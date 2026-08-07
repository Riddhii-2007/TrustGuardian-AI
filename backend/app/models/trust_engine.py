from __future__ import annotations

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from app.models.threat_intel import ThreatIntelResult

class DecisionTrace(BaseModel):
    """Internal decision trace powering the future Explainable Report."""
    rule_name: str
    evidence_source: str
    weight_applied: float
    explanation: str

class LLMAnalysisResult(BaseModel):
    """Strongly typed model for LLM evidence consumed by the Trust Engine."""
    risk_score: float = Field(default=50.0)
    risk_level: str = Field(default="Unknown")
    
class GraphAnalysisResult(BaseModel):
    """Strongly typed model for Graph evidence consumed by the Trust Engine."""
    interaction_count: int = Field(default=0)
    trust_drop: bool = Field(default=False)
    consistent_good: bool = Field(default=False)
    days_since_last_interaction: Optional[float] = Field(default=None)


    
class ReplayResult(BaseModel):
    """Placeholder for future Trust Replay status."""
    status: str = Field(default="not_found")

class TrustEngineResult(BaseModel):
    """Strongly typed output model for the Trust Engine."""
    trust_score: float = Field(ge=0.0, le=100.0, description="Final clamped score (0-100)")
    risk_level: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL, SAFE")
    confidence_score: float = Field(ge=0.0, le=100.0, description="Reliability of available evidence")
    recommendation: str = Field(description="ALLOW, VERIFY, BLOCK")
    reasoning: List[DecisionTrace] = Field(description="Human-readable decision trace")
    evidence_used: List[str] = Field(description="Which evidence slots contributed")
    component_scores: Dict[str, float] = Field(description="Content, Identity, Historical, etc.")
