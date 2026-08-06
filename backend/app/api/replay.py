from fastapi import APIRouter, Depends
from app.api.deps import verify_token
from app.models.auth import TokenPayload
from app.models.common import APIResponse
from app.models.replay import WorkflowComparison
from app.services.replay_service import replay_service

router = APIRouter()

@router.post("/compare", response_model=APIResponse[WorkflowComparison])
async def compare_workflows(data: dict, token: TokenPayload = Depends(verify_token)):
    comparison = await replay_service.compare_workflow(data.get("request_id", ""), data.get("actual_steps", []))
    return APIResponse(success=True, data=comparison)

@router.get("/timeline/{id}", response_model=APIResponse[WorkflowComparison])
async def get_timeline(id: str, token: TokenPayload = Depends(verify_token)):
    timeline = await replay_service.get_timeline(id)
    return APIResponse(success=True, data=timeline)
