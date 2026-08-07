import pytest
import asyncio
from unittest.mock import MagicMock, patch
import httpx
from datetime import datetime

from app.services.threat_intel_service import ThreatIntelService, vt_cache
from app.models.threat_intel import ThreatIntelResult

@pytest.fixture
def service():
    # Clear cache before each test
    vt_cache.cache.clear()
    svc = ThreatIntelService()
    # Use a dummy key so it attempts the request
    svc.vt_api_key = "dummy-key"
    return svc

def test_extract_urls(service):
    content = "Check this out: https://evil.com and http://test.org."
    urls = service.extract_urls(content)
    assert len(urls) == 2
    assert "https://evil.com" in urls
    assert "http://test.org" in urls

def test_extract_no_urls(service):
    content = "No urls here!"
    urls = service.extract_urls(content)
    assert len(urls) == 0

def test_parse_auth_headers_all_pass(service):
    headers = {
        "Authentication-Results": "mx.google.com; dkim=pass header.i=@domain.com; spf=pass (google.com: domain of user@domain.com designates 1.2.3.4 as permitted sender); dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=domain.com"
    }
    spf, dkim, dmarc = service.parse_auth_headers(headers)
    assert spf == "PASS"
    assert dkim == "PASS"
    assert dmarc == "PASS"

def test_parse_auth_headers_all_fail(service):
    headers = {
        "Authentication-Results": "mx.google.com; dkim=fail; spf=softfail; dmarc=fail"
    }
    spf, dkim, dmarc = service.parse_auth_headers(headers)
    assert spf == "FAIL"
    assert dkim == "FAIL"
    assert dmarc == "FAIL"

def test_parse_auth_headers_missing(service):
    headers = {}
    spf, dkim, dmarc = service.parse_auth_headers(headers)
    assert spf == "NONE"
    assert dkim == "NONE"
    assert dmarc == "NONE"

def test_parse_auth_headers_regex_fallback(service):
    # Unstructured fallback text
    headers = {
        "Authentication-Results": "Some weird string where spf=pass and dkim=fail and dmarc=pass"
    }
    spf, dkim, dmarc = service.parse_auth_headers(headers)
    assert spf == "PASS"
    assert dkim == "FAIL"
    assert dmarc == "PASS"

@pytest.mark.asyncio
async def test_analyze_vt_malicious(service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 2,
                    "suspicious": 1,
                    "harmless": 88,
                    "undetected": 5
                }
            }
        }
    }
    
    async def mock_get(*args, **kwargs):
        return mock_response

    with patch('httpx.AsyncClient.get', side_effect=mock_get):
        result = await service.analyze("Look at https://malicious.com", {})
        
        assert result.urls_checked == 1
        assert result.urls_malicious == 1
        assert result.urls_unknown == 0
        assert result.virustotal.malicious == 2
        assert "1 URL(s) detected as malicious" in result.flags
        assert "Authentication-Results missing" in result.warnings

@pytest.mark.asyncio
async def test_analyze_vt_harmless(service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 0,
                    "suspicious": 0,
                    "harmless": 90,
                    "undetected": 0
                }
            }
        }
    }
    
    async def mock_get(*args, **kwargs):
        return mock_response

    with patch('httpx.AsyncClient.get', side_effect=mock_get):
        result = await service.analyze("Look at https://safe.com", {})
        
        assert result.urls_checked == 1
        assert result.urls_malicious == 0
        assert result.urls_unknown == 0
        assert result.virustotal.malicious == 0
        assert result.virustotal.harmless == 90

@pytest.mark.asyncio
async def test_analyze_vt_unknown_404(service):
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    async def mock_get(*args, **kwargs):
        return mock_response

    with patch('httpx.AsyncClient.get', side_effect=mock_get):
        result = await service.analyze("Look at https://never-scanned.com", {})
        
        assert result.urls_checked == 1
        assert result.urls_unknown == 1
        assert result.urls_malicious == 0
        assert result.virustotal.malicious == 0

@pytest.mark.asyncio
async def test_analyze_vt_timeout(service):
    with patch('httpx.AsyncClient.get', side_effect=httpx.TimeoutException("Timeout")):
        result = await service.analyze("Look at https://timeout.com", {})
        
        assert result.urls_checked == 1
        assert any("VT timeout" in w for w in result.warnings)

@pytest.mark.asyncio
async def test_cache_hit(service):
    # Manually populate cache
    vt_cache.set("https://cached.com", {"malicious": 5, "harmless": 10})
    
    # Should not make network call since we don't mock it and it would fail if it did
    result = await service.analyze("Check https://cached.com", {})
    
    assert result.urls_checked == 1
    assert result.virustotal.malicious == 5
    assert result.virustotal.harmless == 10
    assert result.urls_malicious == 1

@pytest.mark.asyncio
async def test_empty_email(service):
    result = await service.analyze("", {})
    assert result.urls_checked == 0
    assert result.spf == "NONE"
    assert result.dkim == "NONE"
    assert result.dmarc == "NONE"
