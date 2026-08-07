"""
Threat Intelligence Service.

Responsible for:
- Parsing SPF, DKIM, and DMARC from email headers.
- Extracting URLs from email content.
- Querying VirusTotal with a TTL cache.
"""
import re
import base64
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import httpx

from app.config import settings
from app.models.threat_intel import ThreatIntelResult, VirusTotalStats

logger = logging.getLogger(__name__)

# URL Extraction Regex (excludes trailing punctuation)
URL_REGEX = re.compile(r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+(?<![.,;!?])')

# Simple in-memory TTL Cache
class VT_Cache:
    def __init__(self, ttl_hours=24):
        self.ttl = timedelta(hours=ttl_hours)
        self.cache: Dict[str, Tuple[datetime, dict]] = {}

    def get(self, url: str) -> dict | None:
        if url in self.cache:
            timestamp, data = self.cache[url]
            if datetime.now() - timestamp < self.ttl:
                return data
            else:
                del self.cache[url]
        return None

    def set(self, url: str, data: dict):
        self.cache[url] = (datetime.now(), data)

vt_cache = VT_Cache()

class ThreatIntelService:
    def __init__(self):
        self.vt_api_key = settings.VIRUSTOTAL_API_KEY
        self.vt_base_url = "https://www.virustotal.com/api/v3/urls/"

    def extract_urls(self, content: str) -> List[str]:
        if not content:
            return []
        return list(set(URL_REGEX.findall(content)))

    def parse_auth_headers(self, headers: dict) -> Tuple[str, str, str]:
        """
        Parses Authentication-Results for SPF, DKIM, DMARC.
        Returns: (spf, dkim, dmarc) as PASS/FAIL/NONE
        """
        spf, dkim, dmarc = "NONE", "NONE", "NONE"
        
        # Check standard email headers dict (case-insensitive keys)
        headers_lower = {k.lower(): v for k, v in headers.items()}
        auth_results = headers_lower.get("authentication-results", "")
        
        if not auth_results:
            return spf, dkim, dmarc
            
        # Structured parsing first: typical format `spf=pass (reason) ... dkim=pass`
        parts = auth_results.split(';')
        for part in parts:
            part_clean = part.strip().lower()
            if part_clean.startswith('spf='):
                val = part_clean.split('=', 1)[1].split()[0]
                if val == 'pass': spf = 'PASS'
                elif val in ('fail', 'softfail', 'hardfail', 'neutral', 'permerror', 'temperror'): spf = 'FAIL'
            elif part_clean.startswith('dkim='):
                val = part_clean.split('=', 1)[1].split()[0]
                if val == 'pass': dkim = 'PASS'
                elif val in ('fail', 'neutral', 'permerror', 'temperror'): dkim = 'FAIL'
            elif part_clean.startswith('dmarc='):
                val = part_clean.split('=', 1)[1].split()[0]
                if val == 'pass': dmarc = 'PASS'
                elif val in ('fail', 'bestguesspass', 'temperror', 'permerror'): dmarc = 'FAIL'
                
        # Regex fallback if structured parsing missed it
        if spf == "NONE":
            if re.search(r'\bspf=pass\b', auth_results.lower()): spf = "PASS"
            elif re.search(r'\bspf=(fail|softfail|neutral)\b', auth_results.lower()): spf = "FAIL"
        if dkim == "NONE":
            if re.search(r'\bdkim=pass\b', auth_results.lower()): dkim = "PASS"
            elif re.search(r'\bdkim=(fail|neutral)\b', auth_results.lower()): dkim = "FAIL"
        if dmarc == "NONE":
            if re.search(r'\bdmarc=pass\b', auth_results.lower()): dmarc = "PASS"
            elif re.search(r'\bdmarc=(fail)\b', auth_results.lower()): dmarc = "FAIL"
            
        return spf, dkim, dmarc

    async def _query_vt(self, url: str) -> dict:
        """
        Queries VT for a single URL.
        Returns stats dict or an 'unknown' flag if 404.
        """
        if not self.vt_api_key or self.vt_api_key == "your-virustotal-api-key":
            return {"error": "VT API key missing"}

        cached = vt_cache.get(url)
        if cached:
            return cached

        # Encode URL for VT API v3
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        api_url = f"{self.vt_base_url}{url_id}"
        
        headers = {
            "x-apikey": self.vt_api_key,
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(api_url, headers=headers)
                
                if response.status_code == 404:
                    result = {"unknown": True}
                    vt_cache.set(url, result)
                    return result
                    
                response.raise_for_status()
                data = response.json()
                
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                vt_cache.set(url, stats)
                return stats
        except httpx.TimeoutException:
            return {"error": "VT timeout"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return {"error": "VT rate limited"}
            return {"error": f"VT HTTP error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"VT internal error: {str(e)}"}

    async def analyze(self, content: str, headers: dict) -> ThreatIntelResult:
        """
        Main entrypoint for threat intel collection.
        Returns a structured ThreatIntelResult.
        """
        result = ThreatIntelResult()
        
        # 1. Email Headers
        spf, dkim, dmarc = self.parse_auth_headers(headers)
        result.spf = spf
        result.dkim = dkim
        result.dmarc = dmarc
        
        if spf == "FAIL": result.flags.append("SPF failed")
        if dkim == "FAIL": result.flags.append("DKIM failed")
        if dmarc == "FAIL": result.flags.append("DMARC failed")
        if not headers:
            result.warnings.append("Authentication-Results missing")

        # 2. VirusTotal URL check
        urls = self.extract_urls(content)
        result.urls_checked = len(urls)
        
        if urls:
            tasks = [self._query_vt(url) for url in urls]
            vt_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, vt_res in zip(urls, vt_results):
                if isinstance(vt_res, Exception):
                    result.warnings.append(f"VT task failed for {url}: {str(vt_res)}")
                    continue
                
                if "error" in vt_res:
                    result.warnings.append(f"VT error for {url}: {vt_res['error']}")
                    continue
                    
                if vt_res.get("unknown"):
                    result.urls_unknown += 1
                else:
                    result.virustotal.malicious += vt_res.get("malicious", 0)
                    result.virustotal.suspicious += vt_res.get("suspicious", 0)
                    result.virustotal.harmless += vt_res.get("harmless", 0)
                    result.virustotal.undetected += vt_res.get("undetected", 0)
                    
                    if vt_res.get("malicious", 0) > 0:
                        result.urls_malicious += 1

            if result.urls_malicious > 0:
                result.flags.append(f"{result.urls_malicious} URL(s) detected as malicious")

        return result

threat_intel_service = ThreatIntelService()
