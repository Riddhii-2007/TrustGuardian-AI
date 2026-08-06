from fastapi import APIRouter, Depends
from app.api.deps import verify_token
from app.models.auth import TokenPayload
from app.models.common import APIResponse
from app.models.graph import GraphData
from app.services.graph_service import graph_service

router = APIRouter()

@router.get("/visualize", response_model=APIResponse[GraphData])
async def get_graph_visualization(token: TokenPayload = Depends(verify_token)):
    # Automatically triggers connection and seeding if first request
    graph_data = await graph_service.get_visualize_data()
    return APIResponse(success=True, data=graph_data)
