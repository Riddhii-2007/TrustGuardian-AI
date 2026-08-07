"""
check_openrouter_models.py
===========================
Step 1: Query OpenRouter /models to list all available models.
Step 2: Pick best stable candidate per vendor (OpenAI, Anthropic, Google, Meta, DeepSeek).
Step 3: Live-test each candidate with the same prompt.
Step 4: Report PASS/FAIL with diagnostics.

Run from backend/:
    python check_openrouter_models.py
"""

import sys, os, io, asyncio, time, json
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

API_KEY  = os.getenv("OPENROUTER_API_KEY", "").strip()
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

if not API_KEY:
    print("[ERROR] OPENROUTER_API_KEY not set in backend/.env")
    sys.exit(1)

from openai import AsyncOpenAI
import httpx

SEP = "-" * 64

# ---------------------------------------------------------------------------
# Vendor filters — match model IDs by prefix
# ---------------------------------------------------------------------------
VENDOR_FILTERS = {
    "OpenAI":    lambda s: s.startswith("openai/"),
    "Anthropic": lambda s: s.startswith("anthropic/"),
    "Google":    lambda s: s.startswith("google/"),
    "Meta":      lambda s: s.startswith("meta-llama/"),
    "DeepSeek":  lambda s: s.startswith("deepseek/"),
}

# Heuristic score: prefer non-free, non-experimental, non-preview slugs
def stability_score(model_id: str) -> int:
    score = 0
    slug  = model_id.lower()
    if ":free"       in slug: score -= 5   # free tiers are often rate-limited
    if "preview"     in slug: score -= 3
    if "exp"         in slug: score -= 3
    if "beta"        in slug: score -= 2
    if "latest"      in slug: score += 1   # "latest" aliases tend to be stable
    if "instruct"    in slug: score += 2
    if "chat"        in slug: score += 1
    return score


async def fetch_available_models() -> list[dict]:
    """GET /models — returns list of model objects the account can see."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept":        "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{BASE_URL}/models", headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])


def pick_candidates(models: list[dict]) -> dict[str, str]:
    """Pick the highest-stability model per vendor from the available list."""
    buckets: dict[str, list[str]] = {v: [] for v in VENDOR_FILTERS}

    for m in models:
        mid = m.get("id", "")
        for vendor, fn in VENDOR_FILTERS.items():
            if fn(mid):
                buckets[vendor].append(mid)

    selected = {}
    for vendor, candidates in buckets.items():
        if not candidates:
            selected[vendor] = None
            continue
        # Sort by stability score descending, then alphabetically for tie-breaking
        candidates.sort(key=lambda x: (-stability_score(x), x))
        selected[vendor] = candidates[0]

    return selected


TEST_PROMPT = (
    'Reply with ONLY a valid JSON object — no markdown, no explanation.\n'
    'Format: {"vendor": "<your provider name>", "status": "ok"}'
)


async def test_model(client: AsyncOpenAI, model_id: str) -> dict:
    """Send the test prompt to one model and return a result dict."""
    t0 = time.monotonic()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": TEST_PROMPT}],
                max_tokens=80,
                temperature=0.0,
            ),
            timeout=30.0,
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        reply      = (response.choices[0].message.content or "").strip()
        usage      = response.usage
        return {
            "model":      model_id,
            "status":     "PASS",
            "reply":      reply,
            "latency_ms": latency_ms,
            "tokens":     usage.total_tokens if usage else 0,
            "error":      None,
        }
    except asyncio.TimeoutError:
        return {"model": model_id, "status": "FAIL", "reply": "",
                "latency_ms": 30000, "tokens": 0, "error": "Timeout (>30s)"}
    except Exception as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        err  = f"{type(e).__name__}: {e}"
        # Classify the failure
        if "404" in str(e) or "No endpoints" in str(e):
            cause = "INVALID_MODEL_ID — not available on this account/plan"
        elif "401" in str(e) or "403" in str(e):
            cause = "AUTH — invalid API key or no access"
        elif "429" in str(e):
            cause = "RATE_LIMIT — too many requests"
        elif "402" in str(e) or "credit" in str(e).lower():
            cause = "NO_CREDITS — account balance insufficient"
        elif "500" in str(e) or "502" in str(e) or "503" in str(e):
            cause = "OPENROUTER_ERROR — upstream issue"
        else:
            cause = "UNKNOWN"
        return {"model": model_id, "status": "FAIL", "reply": "",
                "latency_ms": int((time.monotonic() - t0) * 1000),
                "tokens": 0, "error": err, "cause": cause}


async def main():
    print(f"\n{'='*64}")
    print("  OpenRouter Model Availability & Switching Validation")
    print(f"{'='*64}")
    print(f"  Base URL : {BASE_URL}")
    print(f"  API Key  : {API_KEY[:12]}...{API_KEY[-4:]}")

    # ── Step 1: Fetch all available models ──────────────────────────────────
    print(f"\n{SEP}")
    print("  Step 1 — Querying /models endpoint")
    print(SEP)
    try:
        all_models = await fetch_available_models()
        print(f"  [OK]  {len(all_models)} models returned by OpenRouter\n")
    except Exception as e:
        print(f"  [FAIL] Could not fetch models: {e}")
        sys.exit(1)

    # ── Step 2: Pick candidates ──────────────────────────────────────────────
    print(f"{SEP}")
    print("  Step 2 — Selecting best stable model per vendor")
    print(SEP)
    candidates = pick_candidates(all_models)

    for vendor, model_id in candidates.items():
        if model_id:
            print(f"  {vendor:12s}  =>  {model_id}")
        else:
            print(f"  {vendor:12s}  =>  [NO MODELS FOUND FOR THIS VENDOR]")

    # ── Step 3 & 4: Live test each candidate ─────────────────────────────────
    print(f"\n{SEP}")
    print("  Step 3 — Live testing each model")
    print(f"  Prompt: {TEST_PROMPT[:70]}...")
    print(SEP)

    client  = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    results = []

    for vendor, model_id in candidates.items():
        if not model_id:
            print(f"\n  [{vendor}] SKIP — no model available")
            results.append({"vendor": vendor, "model": None,
                            "status": "SKIP", "error": "No model found"})
            continue

        print(f"\n  [{vendor}] Testing: {model_id}")
        r = await test_model(client, model_id)
        r["vendor"] = vendor
        results.append(r)

        if r["status"] == "PASS":
            print(f"    [PASS]  {r['latency_ms']}ms | {r['tokens']} tokens")
            print(f"    Reply : {r['reply'][:120]}")
        else:
            cause = r.get("cause", "UNKNOWN")
            print(f"    [FAIL]  Cause: {cause}")
            print(f"    Error : {r['error'][:200]}")

    # ── Step 5: Summary report ───────────────────────────────────────────────
    print(f"\n{'='*64}")
    print("  FINAL REPORT")
    print(f"{'='*64}\n")

    passed_models = []
    for r in results:
        status = r.get("status", "SKIP")
        model  = r.get("model", "N/A") or "N/A"
        vendor = r.get("vendor", "?")
        tok    = r.get("tokens", 0)
        lat    = r.get("latency_ms", 0)
        err    = r.get("error", "")
        cause  = r.get("cause", "")

        if status == "PASS":
            passed_models.append(model)
            print(f"  [{status}] {vendor:12s}  {model}")
            print(f"             Latency: {lat}ms | Tokens: {tok}")
            print(f"             Reply  : {r.get('reply','')[:80]}")
        elif status == "SKIP":
            print(f"  [SKIP] {vendor:12s}  No model available")
        else:
            print(f"  [FAIL] {vendor:12s}  {model}")
            print(f"             Cause: {cause}")
        print()

    # ── Recommend updating .env if needed ───────────────────────────────────
    current_model = os.getenv("OPENROUTER_MODEL", "").strip()
    print(SEP)
    print("  Configuration Recommendation")
    print(SEP)
    print(f"  Current OPENROUTER_MODEL = {current_model}")
    if current_model in passed_models:
        print(f"  [OK]  Currently configured model passed the live test.")
        print(f"        No changes needed.")
    else:
        if passed_models:
            best = passed_models[0]
            print(f"  [WARN] Current model not in passing list.")
            print(f"         Recommended: change OPENROUTER_MODEL to:")
            print(f"           {best}")
        else:
            print(f"  [FAIL] No models passed. Check account credits/access.")

    # Print all passing slugs for easy reference
    if passed_models:
        print(f"\n  All validated model slugs:")
        for m in passed_models:
            print(f"    {m}")

    print(f"\n{'='*64}\n")


if __name__ == "__main__":
    asyncio.run(main())
