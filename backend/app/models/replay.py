from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class WorkflowStep(BaseModel):
    step_id: str
    action: str
    actor: str
    timestamp: datetime
    status: str

class DeviationAlert(BaseModel):
    alert_id: str
    severity: str
    description: str
    step_id: Optional[str] = None

class WorkflowComparison(BaseModel):
    comparison_id: str
    expected_workflow: List[WorkflowStep]
    actual_workflow: List[WorkflowStep]
    deviations: List[DeviationAlert]

class CompareWorkflowRequest(BaseModel):
    request_id: str
    verification_required: bool
    recommendation: str
    actual_steps: List[WorkflowStep]
