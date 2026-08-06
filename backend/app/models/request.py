from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PsychologyFactors(BaseModel):
    urgency: float = Field(..., ge=0, le=1)
    authority: float = Field(..., ge=0, le=1)
    fear: float = Field(..., ge=0, le=1)
    familiarity: float = Field(..., ge=0, le=1)
    intent: float = Field(..., ge=0, le=1)

class AnalysisResult(BaseModel):
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: str
    psychology: PsychologyFactors
    flags: List[str]
    explanation: str

class BusinessRequest(BaseModel):
    id: str
    title: str
    content: str
    requester: str
    created_at: datetime
    status: str
    analysis: Optional[AnalysisResult] = None
