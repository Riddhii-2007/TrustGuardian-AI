import pytest
from app.models.sandbox import SimulationRequest
from app.services.sandbox_service import sandbox_service

@pytest.mark.asyncio
async def test_sandbox_substring_routing():
    # 1. Test BLOCK_ESCALATE_SOC routes to BLOCK scenario
    req_block = SimulationRequest(
        request_id="req-1",
        action="approve",
        parameters={},
        trust_score=35.0,
        confidence_score=95.0,
        recommendation="BLOCK_ESCALATE_SOC",
        flags=["Urgency check failed"]
    )
    res_block = await sandbox_service.simulate_outcome(req_block)
    assert "MANDATORY BLOCK" in res_block.recommendation
    assert len(res_block.scenarios) == 2
    # Verify primary scenario impact: 100 - trust_score = 100 - 35 = 65
    assert res_block.scenarios[0].impact_score == 65.0
    # Verify secondary scenario impact: 50 + 10 * 1 = 60
    assert res_block.scenarios[1].impact_score == 60.0

    # 2. Test VERIFY_UNVERIFIED_SENDER routes to VERIFY scenario
    req_verify = SimulationRequest(
        request_id="req-2",
        action="approve",
        parameters={},
        trust_score=75.0,
        confidence_score=40.0,
        recommendation="VERIFY_UNVERIFIED_SENDER",
        flags=[]
    )
    res_verify = await sandbox_service.simulate_outcome(req_verify)
    assert "VERIFICATION REQUIRED" in res_verify.recommendation
    assert len(res_verify.scenarios) == 2
    assert res_verify.scenarios[0].impact_score == 10.0
    # Secondary impact: 70 + (100 - 40) / 5 = 70 + 60 / 5 = 70 + 12 = 82
    assert res_verify.scenarios[1].impact_score == 82.0

@pytest.mark.asyncio
async def test_sandbox_safe_defaults():
    # Test that None/missing inputs route to ALLOW with correct defaults
    req_default = SimulationRequest(
        request_id="req-3",
        action="approve",
        parameters={}
    )
    res_default = await sandbox_service.simulate_outcome(req_default)
    assert "ALLOW TRANSACTION" in res_default.recommendation
    assert len(res_default.scenarios) == 2
    assert res_default.scenarios[0].impact_score == 5.0
    assert res_default.scenarios[1].impact_score == 95.0
