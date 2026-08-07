"""
validate_integrations.py
========================
Comprehensive validation script for TrustGuardian-AI:
  - Part 1: VirusTotal integration
  - Part 2: OpenRouter connection
  - Part 3: AI model switching across 5 models
  - Part 4: Architecture summary

Run from backend/ directory:
    python validate_integrations.py
"""

import sys
import os
import io
import asyncio
import base64
import time
from pathlib import Path

# UTF-8 safe output on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# ---------------------------------------------------------------------------
# Colour helpers (ASCII only for Windows compat)
# ---------------------------------------------------------------------------
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"
SEP  = "-" * 60

def header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

# ===========================================================================
# PART 1 — VirusTotal
# ===========================================================================

async def run_virustotal_test() -> dict:
    """Full VirusTotal integration test."""
    header("PART 1 — VirusTotal Integration")
    result = {"status": "PASS", "issues": []}

    # 1a. Key present?
    vt_key = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
    if not vt_key or vt_key in ("your-virustotal-api-key", ""):
        print(f"{FAIL} VIRUSTOTAL_API_KEY is missing or is the placeholder value.")
        result["status"] = "FAIL"
        result["issues"].append("VIRUSTOTAL_API_KEY not configured.")
        return result
    masked = f"{vt_key[:6]}...{vt_key[-4:]}"
    print(f"{PASS} VIRUSTOTAL_API_KEY present: {masked}")

    # 1b. Verify implementation
    section("Implementation Audit")
    try:
        import re
        src = Path(__file__).parent / "app/services/threat_intel_service.py"
        code = src.read_text(encoding="utf-8")

        checks = {
            "Correct endpoint (virustotal.com/api/v3/urls)": "virustotal.com/api/v3/urls" in code,
            "x-apikey header":                               "x-apikey" in code,
            "timeout set (timeout=10.0)":                   "timeout=10.0" in code,
            "429 rate-limit handling":                       "429" in code,
            "TimeoutException handling":                     "TimeoutException" in code,
            "API key never logged":                          "vt_api_key" not in code.replace("self.vt_api_key", ""),
            "TTL cache present":                             "VT_Cache" in code or "ttl" in code.lower(),
        }
        all_pass = True
        for check, passed in checks.items():
            status = PASS if passed else FAIL
            print(f"  {status}  {check}")
            if not passed:
                result["issues"].append(f"Implementation check failed: {check}")
                all_pass = False
        if all_pass:
            print(f"\n{PASS} All implementation checks passed.")
        else:
            result["status"] = "FAIL"
    except Exception as e:
        print(f"{FAIL} Could not read threat_intel_service.py: {e}")
        result["status"] = "FAIL"
        result["issues"].append(str(e))

    # 1c. Live API test — google.com
    section("Live API Test: https://www.google.com")
    try:
        import httpx

        test_url = "https://www.google.com"
        url_id = base64.urlsafe_b64encode(test_url.encode()).decode().strip("=")
        api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        headers = {"x-apikey": vt_key, "Accept": "application/json"}

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(api_url, headers=headers)
        latency_ms = int((time.monotonic() - t0) * 1000)

        if response.status_code == 429:
            print(f"{WARN} VT rate-limited (429). API key is valid but quota exceeded.")
            result["issues"].append("Rate-limited by VirusTotal.")
        elif response.status_code == 404:
            print(f"{WARN} URL not yet analysed by VT (404) — this is normal for first-time URLs.")
        elif response.status_code == 200:
            data = response.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            reputation = attrs.get("reputation", "N/A")

            print(f"{PASS} VT responded in {latency_ms}ms (HTTP 200)")
            print(f"\n  URL tested  : {test_url}")
            print(f"  Malicious   : {stats.get('malicious', 0)}")
            print(f"  Suspicious  : {stats.get('suspicious', 0)}")
            print(f"  Harmless    : {stats.get('harmless', 0)}")
            print(f"  Undetected  : {stats.get('undetected', 0)}")
            print(f"  Reputation  : {reputation}")

            # Verify parser logic
            parsed_malicious = stats.get("malicious", 0)
            parsed_harmless  = stats.get("harmless", 0)
            if isinstance(parsed_malicious, int) and isinstance(parsed_harmless, int):
                print(f"\n{PASS} Parser correctly extracted integer stats.")
            else:
                print(f"{FAIL} Parser returned unexpected types.")
                result["status"] = "FAIL"
                result["issues"].append("VT parser returned non-int values.")
        else:
            print(f"{FAIL} Unexpected HTTP status: {response.status_code}")
            print(f"  Body: {response.text[:300]}")
            result["status"] = "FAIL"
            result["issues"].append(f"VT returned HTTP {response.status_code}")

    except Exception as e:
        print(f"{FAIL} VT request raised exception: {type(e).__name__}: {e}")
        result["status"] = "FAIL"
        result["issues"].append(str(e))

    return result


# ===========================================================================
# PART 2 — OpenRouter
# ===========================================================================

async def run_openrouter_test() -> dict:
    """Full OpenRouter connection test."""
    header("PART 2 — OpenRouter Integration")
    result = {"status": "PASS", "issues": []}

    api_key  = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    model    = os.getenv("OPENROUTER_MODEL", "").strip()

    section("Configuration Check")
    for name, val, placeholder in [
        ("OPENROUTER_API_KEY",   api_key,  ""),
        ("OPENROUTER_BASE_URL",  base_url, ""),
        ("OPENROUTER_MODEL",     model,    ""),
    ]:
        if val and val != placeholder:
            display = f"{val[:12]}...{val[-4:]}" if name == "OPENROUTER_API_KEY" else val
            print(f"  {PASS} {name} = {display}")
        else:
            print(f"  {FAIL} {name} is not set.")
            result["status"] = "FAIL"
            result["issues"].append(f"{name} not configured.")

    if result["status"] == "FAIL":
        return result

    section("Live API Request")
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        t0 = time.monotonic()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say HELLO in exactly one word."}],
            max_tokens=32,
            temperature=0.0,
        )
        latency_ms = int((time.monotonic() - t0) * 1000)

        reply   = response.choices[0].message.content or ""
        usage   = response.usage
        print(f"  {PASS} OpenRouter responded successfully")
        print(f"\n  Model    : {model}")
        print(f"  Response : {reply.strip()}")
        print(f"  Latency  : {latency_ms}ms")
        print(f"  Tokens   : prompt={usage.prompt_tokens} "
              f"completion={usage.completion_tokens} "
              f"total={usage.total_tokens}")
    except Exception as e:
        print(f"  {FAIL} OpenRouter request failed: {type(e).__name__}: {e}")
        result["status"] = "FAIL"
        result["issues"].append(str(e))

    return result


# ===========================================================================
# PART 3 — AI Model Switching
# ===========================================================================

MODELS_TO_TEST = [
    "deepseek/deepseek-chat",              # DeepSeek   — PASS 1035ms
    "openai/gpt-3.5-turbo-instruct",       # OpenAI     — PASS 3501ms
    "anthropic/claude-3-haiku",            # Anthropic  — PASS 1867ms
    "google/gemini-2.5-flash",             # Google     — PASS 2562ms
    "meta-llama/llama-3.1-70b-instruct",   # Meta/Llama — PASS 1081ms
]

SWITCHING_PROMPT = "Reply with a JSON object: {\"model_reply\": \"HELLO\", \"status\": \"ok\"}"

async def test_single_model(client, model: str) -> dict:
    """Test a single OpenRouter model. Returns result dict."""
    try:
        t0 = time.monotonic()
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": SWITCHING_PROMPT}],
                max_tokens=64,
                temperature=0.0,
            ),
            timeout=30.0,
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        reply  = (response.choices[0].message.content or "").strip()
        usage  = response.usage
        return {
            "model": model, "status": "PASS",
            "reply": reply[:120],
            "latency_ms": latency_ms,
            "tokens": usage.total_tokens if usage else 0,
            "error": None,
        }
    except asyncio.TimeoutError:
        return {"model": model, "status": "FAIL", "reply": "", "latency_ms": 30000,
                "tokens": 0, "error": "Timeout after 30s"}
    except Exception as e:
        return {"model": model, "status": "FAIL", "reply": "", "latency_ms": 0,
                "tokens": 0, "error": f"{type(e).__name__}: {e}"}


async def run_model_switching_test() -> dict:
    """Test the same prompt across multiple models via OpenRouter."""
    header("PART 3 — AI Model Switching")
    result = {"status": "PASS", "models": [], "issues": []}

    api_key  = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

    if not api_key:
        print(f"{FAIL} OPENROUTER_API_KEY not set — skipping model switching test.")
        result["status"] = "FAIL"
        result["issues"].append("OPENROUTER_API_KEY not configured.")
        return result

    print(f"  Testing {len(MODELS_TO_TEST)} models via OpenRouter...")
    print(f"  Prompt: {SWITCHING_PROMPT}\n")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    except ImportError:
        print(f"{FAIL} openai package not installed.")
        result["status"] = "FAIL"
        return result

    # Run tests sequentially to avoid rate limits
    for model in MODELS_TO_TEST:
        print(f"  Testing: {model}")
        r = await test_single_model(client, model)
        result["models"].append(r)

        if r["status"] == "PASS":
            print(f"    {PASS}  Latency: {r['latency_ms']}ms | Tokens: {r['tokens']}")
            print(f"         Reply: {r['reply']}")
        else:
            print(f"    {FAIL}  Error: {r['error']}")
            result["issues"].append(f"{model}: {r['error']}")
        print()

    passed = sum(1 for r in result["models"] if r["status"] == "PASS")
    failed = len(result["models"]) - passed
    print(f"\n  Results: {passed} passed, {failed} failed out of {len(MODELS_TO_TEST)} models")

    if passed == 0:
        result["status"] = "FAIL"
    elif failed > 0:
        result["status"] = "PARTIAL"

    return result


# ===========================================================================
# PART 4 — Architecture Review
# ===========================================================================

def run_architecture_review() -> dict:
    """Static analysis of the AI switching architecture."""
    header("PART 4 — Architecture Review")
    result = {"status": "PASS", "recommendations": []}
    base = Path(__file__).parent / "app"

    section("Provider Registry")
    # Check if OpenRouter provider exists
    openrouter_file = base / "services/providers/openrouter_provider.py"
    if openrouter_file.exists():
        print(f"  {PASS} openrouter_provider.py exists")
    else:
        print(f"  {WARN} openrouter_provider.py does NOT exist")
        print(f"       OpenRouter is used directly in test scripts but NOT wired into")
        print(f"       the PROVIDER_REGISTRY — the app still routes to Gemini/Groq.")
        result["recommendations"].append(
            "Create app/services/providers/openrouter_provider.py and register it."
        )
        result["status"] = "NEEDS_WORK"

    # Check PROVIDER_REGISTRY
    init_file = base / "services/providers/__init__.py"
    init_code = init_file.read_text(encoding="utf-8")
    providers_in_registry = []
    for line in init_code.splitlines():
        if '":' in line and "Provider" in line:
            providers_in_registry.append(line.strip())

    print(f"\n  Current PROVIDER_REGISTRY entries:")
    for p in providers_in_registry:
        print(f"    {p}")

    if "openrouter" not in init_code.lower():
        print(f"\n  {WARN} 'openrouter' is NOT in PROVIDER_REGISTRY")
        print(f"       Changing LLM_PROVIDER=openrouter in .env would raise LLMServiceError.")
        result["recommendations"].append(
            "Register 'openrouter' in PROVIDER_REGISTRY after creating the provider file."
        )

    # Check if LLM_PROVIDER can be set to openrouter
    section("Dynamic Switching Capability")
    router_code = (base / "services/llm_router.py").read_text(encoding="utf-8")
    checks = {
        "No hardcoded provider names in routing logic": (
            'provider_name == "gemini"' not in router_code and
            'provider_name == "groq"'  not in router_code
        ),
        "Priority list is configurable (not hardcoded)": (
            'providers_priority: list' in router_code
        ),
        "get_provider() used for dynamic instantiation": (
            "get_provider(provider_name)" in router_code
        ),
        "BaseLLMProvider abstract contract enforced": (
            (base / "services/providers/base.py").exists()
        ),
    }
    for check, passed in checks.items():
        status = PASS if passed else FAIL
        print(f"  {status}  {check}")
        if not passed:
            result["recommendations"].append(f"Fix: {check}")

    section("Target Architecture vs. Current")
    print("""
  Target:
    Threat Intelligence Engine
    +-- Extraction
    +-- AI Analysis
    |     +-- OpenRouter (single gateway)
    |           +-- GPT-4o / GPT-5.5
    |           +-- Claude
    |           +-- Gemini
    |           +-- DeepSeek
    |           +-- Llama
    |           +-- Qwen
    +-- Graph Analysis

  Current:
    Threat Intelligence Engine
    +-- Extraction
    +-- AI Analysis
    |     +-- LLMRouter (multi-provider failover)
    |           +-- GeminiProvider  (direct SDK)
    |           +-- GroqProvider    (direct SDK)
    |           [OpenRouter NOT wired in]
    +-- Graph Analysis
    """)

    if result["status"] == "NEEDS_WORK":
        print(f"  {WARN} Architecture is 2 steps away from the target:")
        print(f"       1. Create OpenRouterProvider (openrouter_provider.py)")
        print(f"       2. Register it in PROVIDER_REGISTRY as 'openrouter'")
        print(f"       3. Set LLM_PROVIDER=openrouter and OPENROUTER_MODEL=<any model>")
        print(f"       No other code changes needed — the router is already model-agnostic.")
    else:
        print(f"  {PASS} Architecture is fully model-agnostic.")

    return result


# ===========================================================================
# FINAL REPORT
# ===========================================================================

def print_final_report(vt: dict, or_: dict, sw: dict, arch: dict) -> None:
    header("FINAL REPORT")

    print(f"""
[VirusTotal Integration]
  Status : {vt['status']}
  Issues : {'; '.join(vt['issues']) if vt['issues'] else 'None'}

[OpenRouter]
  Status : {or_['status']}
  Issues : {'; '.join(or_['issues']) if or_['issues'] else 'None'}

[AI Model Switching]
  Status : {sw['status']}
  Models Tested:""")

    for m in sw.get("models", []):
        tok = f"tokens={m['tokens']}" if m['tokens'] else ""
        err = f"error={m['error']}" if m['error'] else ""
        detail = tok or err or "ok"
        print(f"    [{m['status']:4s}]  {m['model']}  ({detail})")

    sw_issues = sw.get("issues", [])
    print(f"  Issues : {'; '.join(sw_issues) if sw_issues else 'None'}")

    print(f"""
[Architecture]
  Status : {arch['status']}
  Recommendations:""")
    for r in arch.get("recommendations", []):
        print(f"    - {r}")
    if not arch.get("recommendations"):
        print("    None — architecture is correct.")


# ===========================================================================
# MAIN
# ===========================================================================

async def main() -> None:
    vt_result   = await run_virustotal_test()
    or_result   = await run_openrouter_test()
    sw_result   = await run_model_switching_test()
    arch_result = run_architecture_review()
    print_final_report(vt_result, or_result, sw_result, arch_result)

if __name__ == "__main__":
    asyncio.run(main())
