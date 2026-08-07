from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import verify_token
from app.models.auth import TokenPayload
from app.models.common import APIResponse
from app.models.replay import WorkflowComparison, CompareWorkflowRequest
from app.services.replay_service import replay_service

router = APIRouter()

@router.post("/compare", response_model=APIResponse[WorkflowComparison])
async def compare_workflows(data: CompareWorkflowRequest, token: TokenPayload = Depends(verify_token)):
    comparison = await replay_service.compare_workflow(data)
    return APIResponse(success=True, data=comparison)

@router.get("/timeline/{id}", response_model=APIResponse[WorkflowComparison])
async def get_timeline(id: str, token: TokenPayload = Depends(verify_token)):
    timeline = await replay_service.get_timeline(id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Comparison timeline not found")
    return APIResponse(success=True, data=timeline)
