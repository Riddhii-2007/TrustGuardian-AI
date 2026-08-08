import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.analyzer_service import AnalyzerService
from app.models.scan import ScanRequest

@pytest.mark.asyncio
async def test_circuit_breaker_triggers_mandatory_verification():
    # Construct AnalyzerService with a mocked LLM service to avoid real API calls
    mock_llm = MagicMock()
    mock_llm.analyze = AsyncMock(return_value=MagicMock(analysis={
        "risk_score": 10.0,
        "risk_level": "Safe",
        "psychology": {
            "urgency": 0.1,
            "authority": 0.1,
            "fear": 0.1,
            "familiarity": 0.1,
            "intent": 0.1
        },
        "flags": [],
        "summary": "Low risk content",
        "positive_signals": [],
        "negative_signals": [],
        "threats_detected": [],
        "recommendation": "ALLOW",
        "reasoning": "Standard request."
    }))
    
    analyzer = AnalyzerService(llm_service=mock_llm)
    
    # Test email content that matches circuit breaker pattern 1
    content = "please update our bank account number for future payments"
    request = ScanRequest(content=content)
    
    result = await analyzer.scan(request)
    
    # Assert circuit breaker was triggered
    assert result.verification_required is True
    assert "MANDATORY VERIFICATION" in result.recommendation
    assert result.risk_score == 10.0  # Kept unchanged from trust engine / llm analysis (not dampened since other signals are absent)
