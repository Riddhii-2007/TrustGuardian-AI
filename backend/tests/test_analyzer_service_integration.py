import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.analyzer_service import AnalyzerService
from app.models.scan import ScanRequest

@pytest.mark.asyncio
async def test_analyzer_service_integration_e2e():
    # Mock LLM service to return content-specific analysis results
    mock_llm = MagicMock()
    
    def mock_analyze(system_prompt, user_prompt, evidence=None):
        content = user_prompt.lower()
        if "update our bank account" in content:
            risk = 15.0
            rec = "Verify first"
            flags = ["Payment details mentioned"]
        elif "immediately" in content or "urgently" in content:
            risk = 85.0
            rec = "BLOCK"
            flags = ["High urgency", "Financial pressure"]
        else:
            risk = 5.0
            rec = "ALLOW"
            flags = []
            
        return MagicMock(analysis={
            "risk_score": risk,
            "risk_level": "Safe" if risk < 30 else "High" if risk > 70 else "Medium",
            "psychology": {
                "urgency": 0.9 if risk > 70 else 0.1,
                "authority": 0.8 if risk > 70 else 0.1,
                "fear": 0.1,
                "familiarity": 0.1,
                "intent": 0.7 if risk > 70 else 0.1
            },
            "flags": flags,
            "summary": "Mock analysis summary",
            "positive_signals": [],
            "negative_signals": [],
            "threats_detected": [],
            "recommendation": rec,
            "reasoning": "Mock reasoning."
        })
        
    mock_llm.analyze = AsyncMock(side_effect=mock_analyze)
    
    # Initialize analyzer service with mock LLM
    analyzer = AnalyzerService(llm_service=mock_llm)
    
    test_cases = [
        # 1. Normal safe email
        ("Hi John, here is the weekly report for your review. Thanks.", False),
        # 2. BEC email with high urgency
        ("URGENT: Wire $50,000 to vendor immediately to avoid contract cancellation. CEO.", False),
        # 3. Bank account change request (should trigger circuit breaker)
        ("please update our bank account number for future payments", True)
    ]
    
    for content, expected_cb in test_cases:
        request = ScanRequest(content=content)
        result = await analyzer.scan(request)
        
        # Verification assertions
        assert result.risk_score >= 0.0 and result.risk_score <= 100.0
        assert result.trust_score >= 0.0 and result.trust_score <= 100.0
        assert result.confidence_score >= 0.0 and result.confidence_score <= 100.0
        assert isinstance(result.verification_required, bool)
        assert result.recommendation != ""
        
        # Verify the key relation: risk_score + trust_score == 100
        assert abs((result.risk_score + result.trust_score) - 100.0) < 0.01
        
        # Verify circuit breaker trigger matching
        if expected_cb:
            assert result.verification_required is True
            assert "MANDATORY VERIFICATION" in result.recommendation
