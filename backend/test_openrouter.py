"""
test_openrouter.py — Smoke test for the OpenRouter integration.

Usage:
    python test_openrouter.py

Reads OPENROUTER_API_KEY, OPENROUTER_BASE_URL, and OPENROUTER_MODEL from the
.env file in the same directory (backend/.env).
"""

import sys
import os
import io
from pathlib import Path

# Ensure UTF-8 output on Windows terminals that default to cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Load .env from the same directory as this script ─────────────────────────
try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: 'python-dotenv' is not installed. Run: pip install python-dotenv")
    sys.exit(1)

env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print(f"ERROR: .env file not found at {env_path}")
    sys.exit(1)

load_dotenv(env_path)

# ── Read configuration ────────────────────────────────────────────────────────
api_key   = os.getenv("OPENROUTER_API_KEY", "").strip()
base_url  = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
model     = os.getenv("OPENROUTER_MODEL", "").strip()

if not api_key or api_key == "your-openrouter-api-key":
    print("ERROR: OPENROUTER_API_KEY is not set or is still the placeholder value.")
    print("  Add your real key to backend/.env: OPENROUTER_API_KEY=sk-or-v1-...")
    sys.exit(1)

if not model:
    print("ERROR: OPENROUTER_MODEL is not set.")
    print("  Example: OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324")
    sys.exit(1)

# ── Import OpenAI SDK (OpenRouter is OpenAI-compatible) ───────────────────────
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: 'openai' package is not installed. Run: pip install openai")
    sys.exit(1)

# ── Run the test ──────────────────────────────────────────────────────────────
print(f"  Base URL : {base_url}")
print(f"  Model    : {model}")
print(f"  API Key  : {api_key[:12]}...{api_key[-4:]}")
print("-" * 50)

try:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Hello! Reply with a single sentence confirming you are reachable.",
            }
        ],
        max_tokens=64,
        temperature=0.1,
    )

    reply = response.choices[0].message.content
    usage = response.usage

    print("[OK] OpenRouter responded successfully!")
    print(f"\nModel reply:\n  {reply}")
    print(f"\nToken usage:")
    print(f"  Prompt     : {usage.prompt_tokens}")
    print(f"  Completion : {usage.completion_tokens}")
    print(f"  Total      : {usage.total_tokens}")

except Exception as exc:
    print(f"[FAIL] OpenRouter request failed: {type(exc).__name__}: {exc}")
    sys.exit(1)
