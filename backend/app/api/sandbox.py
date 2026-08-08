from fastapi import APIRouter, Depends
from app.api.deps import verify_token
from app.models.auth import TokenPayload
from app.models.common import APIResponse
from app.models.sandbox import SimulationRequest, SimulationResult
from app.services.sandbox_service import sandbox_service

router = APIRouter()

@router.post("/simulate", response_model=APIResponse[SimulationResult])
async def simulate_outcome(request: SimulationRequest, token: TokenPayload = Depends(verify_token)):
    result = await sandbox_service.simulate_outcome(request)
    return APIResponse(success=True, data=result)

@router.get("/results/{id}", response_model=APIResponse[SimulationResult])
async def get_simulation_results(id: str, token: TokenPayload = Depends(verify_token)):
    result = await sandbox_service.get_simulation_results(id)
    return APIResponse(success=True, data=result)
