"""
Unit tests for ReplayService.

Tests deterministic workflow comparison, deviation detection, and 
in-memory timeline caching.
"""

import unittest
import asyncio
from datetime import datetime

from app.models.replay import CompareWorkflowRequest, WorkflowStep
from app.services.replay_service import ReplayService

class TestReplayService(unittest.TestCase):
    def setUp(self):
        self.service = ReplayService()
        self.now = datetime.now()

    def _run(self, coro):
        return asyncio.run(coro)

    def _make_step(self, action: str, status: str = "completed") -> WorkflowStep:
        return WorkflowStep(
            step_id="test-id",
            action=action,
            actor="System",
            timestamp=self.now,
            status=status
        )

    def test_normal_low_risk_approval_flow(self):
        """Normal low-risk flow without verification has no deviations."""
        req = CompareWorkflowRequest(
            request_id="req-1",
            verification_required=False,
            recommendation="Proceed",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Approve Request")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        self.assertEqual(len(result.deviations), 0)

    def test_payment_change_request_missing_verification(self):
        """Verification required but missing generates a High severity deviation."""
        req = CompareWorkflowRequest(
            request_id="req-2",
            verification_required=True,
            recommendation="MANDATORY VERIFICATION",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Approve Request")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        deviations = result.deviations
        self.assertTrue(any(d.description == "A required verification step is missing." for d in deviations))
        self.assertTrue(any("Mandatory step skipped: 'Confirm via Secondary Channel'." in d.description for d in deviations))

    def test_verification_completed_before_approval(self):
        """Verification required and completed properly before approval generates no order deviations."""
        req = CompareWorkflowRequest(
            request_id="req-3",
            verification_required=True,
            recommendation="MANDATORY VERIFICATION",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Confirm via Secondary Channel"),
                self._make_step("Record Verification Outcome"),
                self._make_step("Approve Request")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        self.assertEqual(len(result.deviations), 0)

    def test_approval_before_verification(self):
        """Approval occurring before verification generates a Critical deviation."""
        req = CompareWorkflowRequest(
            request_id="req-4",
            verification_required=True,
            recommendation="MANDATORY VERIFICATION",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Approve Request"),
                self._make_step("Confirm via Secondary Channel"),
                self._make_step("Record Verification Outcome")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        deviations = result.deviations
        self.assertTrue(any(d.description == "Approval occurred before required verification." for d in deviations))
        self.assertTrue(any(d.description == "Out-of-order step: 'Approve Request'." for d in deviations))

    def test_blocked_request_incorrectly_marked_completed(self):
        """Request recommended to Block but Approved generates Critical deviation."""
        req = CompareWorkflowRequest(
            request_id="req-5",
            verification_required=False,
            recommendation="Block",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Approve Request", status="completed")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        deviations = result.deviations
        self.assertTrue(any(d.description == "Request was approved but recommendation was to Block." for d in deviations))

    def test_unknown_workflow_action(self):
        """An unknown workflow action generates a Medium deviation."""
        req = CompareWorkflowRequest(
            request_id="req-6",
            verification_required=False,
            recommendation="Proceed",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Random Admin Action"),
                self._make_step("Approve Request")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        deviations = result.deviations
        self.assertTrue(any(d.description == "Unknown or unexpected workflow action: 'Random Admin Action'" for d in deviations))

    def test_unknown_comparison_id(self):
        """Getting timeline for an unknown comparison ID returns None."""
        result = self._run(self.service.get_timeline("invalid-id"))
        self.assertIsNone(result)

    def test_cached_timeline_retrieval(self):
        """Getting timeline for a known comparison ID works."""
        req = CompareWorkflowRequest(
            request_id="req-7",
            verification_required=False,
            recommendation="Proceed",
            actual_steps=[
                self._make_step("Receive Request"),
                self._make_step("Run Trust Analysis"),
                self._make_step("Approve Request")
            ]
        )
        result = self._run(self.service.compare_workflow(req))
        comp_id = result.comparison_id
        
        cached = self._run(self.service.get_timeline(comp_id))
        self.assertIsNotNone(cached)
        self.assertEqual(cached.comparison_id, comp_id)

if __name__ == "__main__":
    unittest.main()
