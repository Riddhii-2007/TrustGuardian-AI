import uuid
import logging
from datetime import datetime
from typing import Optional

from app.models.replay import WorkflowComparison, WorkflowStep, DeviationAlert, CompareWorkflowRequest

logger = logging.getLogger(__name__)

class ReplayService:
    """
    Trust Replay logic to compare workflows deterministically.
    """

    def __init__(self):
        # In-memory store for timelines
        self._timelines: dict[str, WorkflowComparison] = {}

    def _build_expected_workflow(self, verification_required: bool) -> list[WorkflowStep]:
        expected = []
        now = datetime.now()
        
        expected.append(WorkflowStep(
            step_id=f"exp-{uuid.uuid4().hex[:8]}",
            action="Receive Request", actor="System", timestamp=now, status="completed"
        ))
        
        expected.append(WorkflowStep(
            step_id=f"exp-{uuid.uuid4().hex[:8]}",
            action="Run Trust Analysis", actor="System", timestamp=now, status="completed"
        ))
        
        if verification_required:
            expected.append(WorkflowStep(
                step_id=f"exp-{uuid.uuid4().hex[:8]}",
                action="Confirm via Secondary Channel", actor="Analyst", timestamp=now, status="completed"
            ))
            expected.append(WorkflowStep(
                step_id=f"exp-{uuid.uuid4().hex[:8]}",
                action="Record Verification Outcome", actor="Analyst", timestamp=now, status="completed"
            ))
            
        expected.append(WorkflowStep(
            step_id=f"exp-{uuid.uuid4().hex[:8]}",
            action="Approve or Block Request", actor="System", timestamp=now, status="completed"
        ))
        
        return expected

    async def compare_workflow(self, request: CompareWorkflowRequest) -> WorkflowComparison:
        expected_steps = self._build_expected_workflow(request.verification_required)
        actual_steps = request.actual_steps
        
        deviations: list[DeviationAlert] = []
        
        # Valid known actions to map alternatives
        valid_actions = {
            "Receive Request", "Run Trust Analysis", 
            "Confirm via Secondary Channel", "Record Verification Outcome",
            "Approve or Block Request", "Approve Request", "Block Request"
        }
        
        # Track actual indices for ordering checks
        actual_indices = {step.action: idx for idx, step in enumerate(actual_steps)}
        
        # 1. Unknown/unexpected workflow actions
        for step in actual_steps:
            if step.action not in valid_actions:
                deviations.append(DeviationAlert(
                    alert_id=f"dev-{uuid.uuid4().hex[:8]}",
                    severity="Medium",
                    description=f"Unknown or unexpected workflow action: '{step.action}'",
                    step_id=step.step_id
                ))
        
        # 2. Required verification step is missing
        if request.verification_required:
            if "Confirm via Secondary Channel" not in actual_indices or "Record Verification Outcome" not in actual_indices:
                deviations.append(DeviationAlert(
                    alert_id=f"dev-{uuid.uuid4().hex[:8]}",
                    severity="High",
                    description="A required verification step is missing.",
                ))
                
        # Find approval/block step
        approval_step = next((s for s in actual_steps if s.action in ("Approve Request", "Block Request", "Approve or Block Request")), None)
        
        if approval_step:
            approval_idx = actual_indices[approval_step.action]
            
            # 3. Approval before required verification
            if request.verification_required and "Approve Request" in approval_step.action:
                verify_idx = actual_indices.get("Record Verification Outcome", -1)
                if verify_idx == -1 or approval_idx < verify_idx:
                    deviations.append(DeviationAlert(
                        alert_id=f"dev-{uuid.uuid4().hex[:8]}",
                        severity="Critical",
                        description="Approval occurred before required verification.",
                        step_id=approval_step.step_id
                    ))
                    
            # 4. Action marked completed when it should be blocked
            if "Block" in request.recommendation and "Approve Request" in approval_step.action and approval_step.status == "completed":
                deviations.append(DeviationAlert(
                    alert_id=f"dev-{uuid.uuid4().hex[:8]}",
                    severity="Critical",
                    description="Request was approved but recommendation was to Block.",
                    step_id=approval_step.step_id
                ))
                
        # 5. Skipped or out-of-order mandatory steps
        # Check basic order: Receive -> Trust Analysis -> (Verification) -> Action
        expected_order = ["Receive Request", "Run Trust Analysis"]
        if request.verification_required:
            expected_order.extend(["Confirm via Secondary Channel", "Record Verification Outcome"])
        if approval_step:
            expected_order.append(approval_step.action)
            
        last_idx = -1
        for action in expected_order:
            if action in actual_indices:
                current_idx = actual_indices[action]
                if current_idx < last_idx:
                    deviations.append(DeviationAlert(
                        alert_id=f"dev-{uuid.uuid4().hex[:8]}",
                        severity="Medium",
                        description=f"Out-of-order step: '{action}'.",
                        step_id=actual_steps[current_idx].step_id
                    ))
                last_idx = current_idx
            else:
                deviations.append(DeviationAlert(
                    alert_id=f"dev-{uuid.uuid4().hex[:8]}",
                    severity="High",
                    description=f"Mandatory step skipped: '{action}'.",
                ))

        comparison = WorkflowComparison(
            comparison_id=str(uuid.uuid4()),
            expected_workflow=expected_steps,
            actual_workflow=actual_steps,
            deviations=deviations
        )
        
        # Store in cache
        self._timelines[comparison.comparison_id] = comparison
        
        return comparison

    async def get_timeline(self, comparison_id: str) -> Optional[WorkflowComparison]:
        return self._timelines.get(comparison_id)

replay_service = ReplayService()
