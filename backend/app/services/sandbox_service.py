from app.models.sandbox import SimulationRequest, SimulationResult, OutcomeScenario
import uuid

class SandboxService:
    """
    Decision Sandbox logic.
    """

    async def simulate_outcome(self, request: SimulationRequest) -> SimulationResult:
        # Apply safe defaults to prevent crashes
        trust_score = request.trust_score if request.trust_score is not None else 82.0
        confidence_score = request.confidence_score if request.confidence_score is not None else 85.0
        rec = (request.recommendation or "ALLOW").upper()
        flags = request.flags or []

        scenarios = []

        # Substring/contains checks to match target recommendation buckets
        if "BLOCK" in rec:
            primary_desc = "Request is blocked per Trust Engine recommendation"
            primary_prob = 0.9
            primary_impact = 100.0 - trust_score
            
            secondary_desc = "If manually overridden and approved"
            secondary_prob = 0.1
            secondary_impact = min(100.0, max(0.0, 50.0 + 10.0 * len(flags)))
            
            scenarios = [
                OutcomeScenario(
                    scenario_id="s1",
                    description=primary_desc,
                    probability=primary_prob,
                    impact_score=round(primary_impact, 2)
                ),
                OutcomeScenario(
                    scenario_id="s2",
                    description=secondary_desc,
                    probability=secondary_prob,
                    impact_score=round(secondary_impact, 2)
                )
            ]
            plain_rec = f"MANDATORY BLOCK: Request blocked per trust engine recommendation."
        elif "VERIFY" in rec:
            primary_desc = "Verification completed, request proceeds safely"
            primary_prob = 0.7
            primary_impact = 10.0
            
            secondary_desc = "Verification skipped, request proceeds unverified"
            secondary_prob = 0.3
            secondary_impact = min(100.0, max(0.0, 70.0 + (100.0 - confidence_score) / 5.0))
            
            scenarios = [
                OutcomeScenario(
                    scenario_id="s1",
                    description=primary_desc,
                    probability=primary_prob,
                    impact_score=round(primary_impact, 2)
                ),
                OutcomeScenario(
                    scenario_id="s2",
                    description=secondary_desc,
                    probability=secondary_prob,
                    impact_score=round(secondary_impact, 2)
                )
            ]
            plain_rec = f"VERIFICATION REQUIRED: Confirm details via secondary channel before proceeding."
        else: # ALLOW (or other)
            primary_desc = "Request proceeds normally"
            primary_prob = 0.95
            primary_impact = 5.0
            
            secondary_desc = "Undetected compromise"
            secondary_prob = 0.05
            secondary_impact = 95.0
            
            scenarios = [
                OutcomeScenario(
                    scenario_id="s1",
                    description=primary_desc,
                    probability=primary_prob,
                    impact_score=round(primary_impact, 2)
                ),
                OutcomeScenario(
                    scenario_id="s2",
                    description=secondary_desc,
                    probability=secondary_prob,
                    impact_score=round(secondary_impact, 2)
                )
            ]
            plain_rec = "ALLOW TRANSACTION: The request appears safe to proceed."

        return SimulationResult(
            simulation_id=str(uuid.uuid4()),
            request_id=request.request_id,
            scenarios=scenarios,
            recommendation=plain_rec
        )

    async def get_simulation_results(self, sim_id: str) -> SimulationResult:
        # Backward-compatible endpoint fallback
        return await self.simulate_outcome(
            SimulationRequest(
                request_id="req-123",
                action="approve",
                parameters={},
                trust_score=82.0,
                confidence_score=85.0,
                recommendation="ALLOW"
            )
        )

sandbox_service = SandboxService()
