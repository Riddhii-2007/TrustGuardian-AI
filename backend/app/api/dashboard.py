from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from app.api.deps import verify_token
from app.models.auth import TokenPayload
from app.models.common import APIResponse

router = APIRouter()

# --- Models ---
class StatCardData(BaseModel):
    id: str
    label: str
    value: str
    change: str
    trend: str # "up", "down", "neutral"
    color: str

class ActivityItem(BaseModel):
    id: str
    type: str # "alert", "analysis", "workflow"
    title: str
    description: str
    timestamp: str
    risk_level: str

class ThreatCategory(BaseModel):
    name: str
    count: int
    color: str

class DashboardStats(BaseModel):
    cards: List[StatCardData]
    threat_overview: List[ThreatCategory]
    risk_score_trend: List[Dict[str, Any]] # e.g. [{"date": "Mon", "score": 45}]

# --- Routes ---
@router.get("/stats", response_model=APIResponse[DashboardStats])
async def get_dashboard_stats(token: TokenPayload = Depends(verify_token)):
    stats = DashboardStats(
        cards=[
            StatCardData(
                id="req-analyzed",
                label="Requests Analyzed",
                value="2,845",
                change="+12.5%",
                trend="up",
                color="text-brand-400"
            ),
            StatCardData(
                id="high-risk",
                label="High Risk Detected",
                value="47",
                change="-5.2%",
                trend="down",
                color="text-risk-critical"
            ),
            StatCardData(
                id="deviations",
                label="Workflow Deviations",
                value="18",
                change="+2.1%",
                trend="up",
                color="text-risk-medium"
            ),
            StatCardData(
                id="avg-trust",
                label="Avg Trust Score",
                value="82/100",
                change="+1.5%",
                trend="up",
                color="text-risk-safe"
            )
        ],
        threat_overview=[
            ThreatCategory(name="CEO Fraud", count=15, color="#ef4444"),
            ThreatCategory(name="Invoice Tampering", count=22, color="#f97316"),
            ThreatCategory(name="Vendor Impersonation", count=34, color="#eab308"),
            ThreatCategory(name="Credential Phishing", count=18, color="#06b6d4"),
        ],
        risk_score_trend=[
            {"date": "Mon", "score": 25},
            {"date": "Tue", "score": 38},
            {"date": "Wed", "score": 15},
            {"date": "Thu", "score": 45},
            {"date": "Fri", "score": 22},
            {"date": "Sat", "score": 10},
            {"date": "Sun", "score": 5},
        ]
    )
    return APIResponse(success=True, data=stats)

@router.get("/recent-activity", response_model=APIResponse[List[ActivityItem]])
async def get_recent_activity(token: TokenPayload = Depends(verify_token)):
    activity = [
        ActivityItem(
            id="act-001",
            type="alert",
            title="Critical Risk Detected",
            description="Wire transfer request from john.doe@partner-inc.co (Lookalike domain)",
            timestamp="10 mins ago",
            risk_level="critical"
        ),
        ActivityItem(
            id="act-002",
            type="analysis",
            title="Request Analyzed",
            description="Routine software license renewal approved. Trust score: 92/100.",
            timestamp="45 mins ago",
            risk_level="safe"
        ),
        ActivityItem(
            id="act-003",
            type="workflow",
            title="Workflow Deviation",
            description="Approval bypass attempt detected on PO-48291. Sandbox blocked execution.",
            timestamp="2 hours ago",
            risk_level="high"
        ),
        ActivityItem(
            id="act-004",
            type="alert",
            title="High Risk Detected",
            description="Unusual urgency pattern in email from CEO to Finance.",
            timestamp="5 hours ago",
            risk_level="high"
        ),
        ActivityItem(
            id="act-005",
            type="analysis",
            title="Entity Trust Updated",
            description="Trust score for 'Acme Corp' decreased due to repeated anomalous requests.",
            timestamp="1 day ago",
            risk_level="medium"
        )
    ]
    return APIResponse(success=True, data=activity)
