from pydantic import BaseModel
from typing import List

class OutcomeScenario(BaseModel):
    scenario_id: str
    description: str
    probability: float
    impact_score: float

class SimulationRequest(BaseModel):
    request_id: str
    action: str
    parameters: dict
    trust_score: float | None = None
    confidence_score: float | None = None
    recommendation: str | None = None
    flags: List[str] = []

class SimulationResult(BaseModel):
    simulation_id: str
    request_id: str
    scenarios: List[OutcomeScenario]
    recommendation: str
