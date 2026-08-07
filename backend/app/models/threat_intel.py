from typing import List, Optional
from pydantic import BaseModel, Field

class VirusTotalStats(BaseModel):
    malicious: int = 0
    suspicious: int = 0
    harmless: int = 0
    undetected: int = 0

class ThreatIntelResult(BaseModel):
    spf: str = Field(default="NONE", description="SPF result: PASS, FAIL, or NONE")
    dkim: str = Field(default="NONE", description="DKIM result: PASS, FAIL, or NONE")
    dmarc: str = Field(default="NONE", description="DMARC result: PASS, FAIL, or NONE")
    
    urls_checked: int = 0
    urls_malicious: int = 0
    urls_unknown: int = 0
    
    virustotal: VirusTotalStats = Field(default_factory=VirusTotalStats)
    
    flags: List[str] = Field(default_factory=list, description="Actual security findings")
    warnings: List[str] = Field(default_factory=list, description="Problems encountered during collection")
