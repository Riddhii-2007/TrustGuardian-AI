from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.api.deps import verify_token
from app.models.auth import TokenPayload
from app.models.request import BusinessRequest
from app.models.common import APIResponse, PaginatedResponse
from app.services.analyzer_service import analyzer_service
from app.services.email_service import email_service
from app.models.scan import ScanRequest, ScanType
from datetime import datetime

router = APIRouter()

class AnalyzeRequestPayload(BaseModel):
    text: str
    requester_email: Optional[str] = "unknown@example.com"
    subject: Optional[str] = "No Subject"

@router.post("/analyze", response_model=APIResponse[BusinessRequest])
async def analyze_request(payload: AnalyzeRequestPayload, token: TokenPayload = Depends(verify_token)):
    # 1. Send the text to the AI analyzer forwarding subject and requester_email metadata
    scan_req = ScanRequest(
        content=payload.text,
        metadata={
            "subject": payload.subject or "No Subject",
            "requester_email": payload.requester_email or "unknown@example.com"
        }
    )
    analysis = await analyzer_service.scan(scan_req)
    
    # 2. Package it into a BusinessRequest
    request = BusinessRequest(
        id=f"req-{datetime.now().timestamp()}",
        title=payload.subject,
        content=payload.text,
        requester=payload.requester_email,
        created_at=datetime.now(),
        status="Analyzed",
        analysis=analysis
    )
    
    return APIResponse(success=True, data=request)

@router.get("/", response_model=APIResponse[PaginatedResponse[BusinessRequest]])
async def list_requests(token: TokenPayload = Depends(verify_token)):
    # Mock data for now, would come from database
    requests = [
        BusinessRequest(
            id="req-101",
            title="Urgent Wire Transfer: Project X",
            content="John, I need you to wire $50,000 to the attached vendor immediately. I'm in a meeting and can't take calls.",
            requester="ceo@trustguardian.ai",
            created_at=datetime.now(),
            status="Pending Analysis"
        ),
        BusinessRequest(
            id="req-102",
            title="Update Payroll Details",
            content="Hi HR, please update my direct deposit to the new routing number below.",
            requester="employee@trustguardian.ai",
            created_at=datetime.now(),
            status="Pending Analysis"
        )
    ]
    data = PaginatedResponse(items=requests, total=2, page=1, size=10)
    return APIResponse(success=True, data=data)

@router.get("/{id}", response_model=APIResponse[BusinessRequest])
async def get_request(id: str, token: TokenPayload = Depends(verify_token)):
    # Mock specific request fetch + run analysis on it
    mock_email = "John, I need you to wire $50,000 to the attached vendor immediately. I'm in a meeting and can't take calls."
    analysis = await analyzer_service.scan(ScanRequest(content=mock_email))
    
    request = BusinessRequest(
        id=id,
        title="Urgent Wire Transfer: Project X",
        content=mock_email,
        requester="ceo@trustguardian.ai",
        created_at=datetime.now(),
        status="Analyzed",
        analysis=analysis
    )
    return APIResponse(success=True, data=request)


class FetchGmailPayload(BaseModel):
    access_token: str
    max_results: Optional[int] = 5


@router.post("/fetch-gmail", response_model=APIResponse[List[BusinessRequest]])
async def fetch_gmail_requests(
    payload: FetchGmailPayload,
    token: TokenPayload = Depends(verify_token)
):
    # 1. Fetch raw parsed emails from Gmail API using the access token
    raw_emails = await email_service.fetch_latest_emails(
        access_token=payload.access_token,
        max_results=payload.max_results
    )
    
    # 2. Loop through each email, run trust analysis, and package into BusinessRequest
    business_requests = []
    for raw in raw_emails:
        # Create a ScanRequest
        scan_req = ScanRequest(
            content=raw["content"],
            scan_type=ScanType.EMAIL,
            metadata={
                "subject": raw["subject"],
                "sender": raw["sender"],
                "headers": raw["headers"]
            }
        )
        
        # Run orchestrator pipeline
        analysis = await analyzer_service.scan(scan_req)
        
        request = BusinessRequest(
            id=raw["id"],
            title=raw["subject"],
            content=raw["content"],
            requester=raw["sender"],
            created_at=datetime.now(),
            status="Analyzed",
            analysis=analysis
        )
        business_requests.append(request)
        
    return APIResponse(success=True, data=business_requests)
