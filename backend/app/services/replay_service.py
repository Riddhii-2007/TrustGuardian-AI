from app.models.replay import WorkflowComparison, WorkflowStep, DeviationAlert
import uuid
from datetime import datetime

class ReplayService:
    """
    Trust Replay logic to compare workflows.
    """

    async def compare_workflow(self, request_id: str, actual_steps: list) -> WorkflowComparison:
        return WorkflowComparison(
            comparison_id=str(uuid.uuid4()),
            expected_workflow=[
                WorkflowStep(step_id="st1", action="Receive Request", actor="System", timestamp=datetime.now(), status="completed"),
                WorkflowStep(step_id="st2", action="Manager Approval", actor="Manager", timestamp=datetime.now(), status="pending")
            ],
            actual_workflow=[
                WorkflowStep(step_id="st1", action="Receive Request", actor="System", timestamp=datetime.now(), status="completed"),
                WorkflowStep(step_id="st3", action="Skip Approval", actor="User", timestamp=datetime.now(), status="completed")
            ],
            deviations=[
                DeviationAlert(alert_id="d1", severity="High", description="Manager approval was skipped.", step_id="st3")
            ]
        )

    async def get_timeline(self, comparison_id: str) -> WorkflowComparison:
        return await self.compare_workflow("req-123", [])

replay_service = ReplayService()
