"""
test_schema_validation.py
Live validation of the strict JSON LLM prompt for the two-level AI schema.

Sends 3 emails (Safe, Suspicious, Phishing) to all 5 configured OpenRouter models.
Validates that every model returns strict, parsable JSON matching the schema.

Run from backend/:
    python test_schema_validation.py
"""

import sys, os, io, asyncio, time, json
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).parent / ".env")

API_KEY  = os.getenv("OPENROUTER_API_KEY", "").strip()
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

if not API_KEY:
    print("[ERROR] OPENROUTER_API_KEY not set in backend/.env")
    sys.exit(1)

from openai import AsyncOpenAI
import httpx

from app.services.analyzer_service import analyzer_service
from app.models.scan import ScanType

PROMPT = analyzer_service._get_system_prompt(ScanType.TEXT)

EMAILS = {
    "Safe": "Hi team, attached is the Q3 project update presentation. Let me know if you have any questions before the meeting on Thursday. - Alice",
    "Suspicious": "Hello, kindly review the attached document immediately. We need your feedback today to process your account upgrade.",
    "Phishing": "URGENT: I am in a meeting. Wire $50,000 to the attached vendor account right now or we lose the contract. Do not call me, just reply when done. - CEO"
}

MODELS = [
    "deepseek/deepseek-chat",
    "openai/gpt-3.5-turbo-instruct",
    "anthropic/claude-3-haiku",
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.1-70b-instruct"
]

async def test_model_with_email(client, model, email_type, content):
    print(f"\n[{model}] Testing {email_type} Email...")
    try:
        user_prompt = f"Analyze this business request:\n\n{content}"
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            # Ask for JSON output — most models on OpenRouter honour this
            response_format={"type": "json_object"},
        )
        reply = response.choices[0].message.content or ""
        
        # Parse JSON
        try:
            data = json.loads(reply)
            
            # Check basic structure
            required_keys = ["psychology", "flags", "summary", "positive_signals", "negative_signals", "threats_detected", "recommendation", "reasoning"]
            missing = [k for k in required_keys if k not in data]
            
            if missing:
                print(f"  [FAIL] JSON missing keys: {missing}")
                return False, data
            
            print(f"  [PASS] Returned valid strict JSON matching schema.")
            return True, data
            
        except json.JSONDecodeError:
            print(f"  [FAIL] Invalid JSON returned. Raw response:\n{reply}")
            return False, None
            
    except Exception as e:
        print(f"  [FAIL] API Error: {e}")
        return False, None

async def main():
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    overall_pass = True
    samples = {}
    
    for model in MODELS:
        print(f"\n{'='*60}\nTesting Model: {model}\n{'='*60}")
        for email_type, content in EMAILS.items():
            success, data = await test_model_with_email(client, model, email_type, content)
            if not success:
                overall_pass = False
            
            # Save the deepseek results as our samples for the report
            if model == "deepseek/deepseek-chat" and success:
                samples[email_type] = data

    print(f"\n\n{'='*60}")
    if overall_pass:
        print("ALL MODELS PASSED - SCHEMA VALIDATION SUCCESSFUL")
    else:
        print("SOME MODELS FAILED SCHEMA VALIDATION")
    print(f"{'='*60}\n")
    
    print("\nSAMPLE API RESPONSE (DEEPSEEK):")
    for k, v in samples.items():
        print(f"\n--- {k} Email ---")
        print(json.dumps(v, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
