import sys
import io

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.models.trust_engine import LLMAnalysisResult, GraphAnalysisResult
from app.models.threat_intel import ThreatIntelResult, VirusTotalStats
from app.services.trust_engine_service import trust_engine_service

def create_evidence(llm_risk, has_identity, has_historical):
    # LLM Evidence (Content)
    llm = LLMAnalysisResult(risk_score=llm_risk, risk_level="Unknown")
    
    # Threat Intel Evidence (Identity)
    ti = None
    if has_identity:
        ti = ThreatIntelResult()
        # Add some basic identity evidence
        ti.urls_checked = 1
        ti.spf = "PASS"
        ti.dkim = "PASS"
        ti.dmarc = "PASS"
        # Let's say identity is clean (risk 0.0)
    
    # Graph Evidence (Historical)
    graph = None
    if has_historical:
        graph = GraphAnalysisResult(
            interaction_count=50,
            consistent_good=True
        )
        # historical risk will be -10 (clamped later)
        
    return llm, ti, graph

def run_scenario(scenario_name, llm_risk):
    print(f"========================================================")
    print(f"SCENARIO: {scenario_name} (Base Content Risk: {llm_risk})")
    print(f"========================================================")
    
    # 1. Only Content Risk available
    llm, ti, graph = create_evidence(llm_risk, False, False)
    res1 = trust_engine_service.evaluate(llm, ti, graph)
    print(f"1. Only Content Available:    Trust Score = {res1.trust_score} (Risk Level = {res1.risk_level})")
    
    # 2. Content + Identity available
    llm, ti, graph = create_evidence(llm_risk, True, False)
    res2 = trust_engine_service.evaluate(llm, ti, graph)
    print(f"2. Content + Identity:        Trust Score = {res2.trust_score} (Risk Level = {res2.risk_level})")
    
    # 3. All evidence available
    llm, ti, graph = create_evidence(llm_risk, True, True)
    res3 = trust_engine_service.evaluate(llm, ti, graph)
    print(f"3. All Evidence Available:    Trust Score = {res3.trust_score} (Risk Level = {res3.risk_level})")
    
    print()

if __name__ == "__main__":
    # Scenario 1: Safe email
    run_scenario("Safe Email", 10.0)
    
    # Scenario 2: Suspicious email
    run_scenario("Suspicious Email", 50.0)
    
    # Scenario 3: Phishing email
    run_scenario("Phishing Email", 90.0)
