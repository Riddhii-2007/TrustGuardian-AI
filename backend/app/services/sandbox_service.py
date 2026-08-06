from app.models.sandbox import SimulationResult, OutcomeScenario
import uuid

class SandboxService:
    """
    Decision Sandbox logic.
    """

    async def simulate_outcome(self, request_id: str, action: str, parameters: dict) -> SimulationResult:
        return SimulationResult(
            simulation_id=str(uuid.uuid4()),
            request_id=request_id,
            scenarios=[
                OutcomeScenario(
                    scenario_id="s1",
                    description="Action succeeds normally with expected results.",
                    probability=0.85,
                    impact_score=10.0
                ),
                OutcomeScenario(
                    scenario_id="s2",
                    description="Action exposes sensitive data due to misconfiguration.",
                    probability=0.15,
                    impact_score=90.0
                )
            ],
            recommendation="Proceed with caution and verify configuration."
        )

    async def get_simulation_results(self, sim_id: str) -> SimulationResult:
        return await self.simulate_outcome("req-123", "approve", {})

sandbox_service = SandboxService()
