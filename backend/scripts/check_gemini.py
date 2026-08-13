"""
Check that we can actually talk to Gemini.

Run this after you have put a real key into the ".env" file:

    backend/.venv/Scripts/python backend/scripts/check_gemini.py

Why this script exists
----------------------
The build spec names the model "gemini-3.1-pro-preview". Model names change
over time, and the only reliable way to know whether that name still works
with your API key is to ask Google. This script does exactly that and gives
you a plain-language answer.

If the model name is wrong, you do NOT need to change any code -- just edit
the GEMINI_MODEL line in your ".env" file.

This script is a developer tool. The application itself never imports it.
"""

import sys
from pathlib import Path

# Allow "from app.config import settings" when running this file directly.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402  (import must follow the path setup)


def main() -> int:
    """Send one tiny prompt to Gemini and report what happened."""
    print("ADAA - Gemini connection check")
    print("-" * 40)

    if not settings.gemini_api_key:
        print("No API key found.")
        print()
        print("Fix it like this:")
        print("  1. Copy .env.example to .env")
        print("  2. Get a key from https://aistudio.google.com/apikey")
        print("  3. Put it after GEMINI_API_KEY= in your .env file")
        return 1

    print(f"Model being tested: {settings.gemini_model}")
    print("Sending a test message...")
    print()

    try:
        from google import genai
    except ImportError:
        print("The 'google-genai' package is not installed.")
        print("Fix it with: backend/.venv/Scripts/pip install -r backend/requirements.txt")
        return 1

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents="Reply with exactly one word: ready",
        )
    except Exception as error:
        # We show the raw error too, because it usually names the real cause.
        print("The request failed.")
        print(f"Error: {error}")
        print()
        print("Common causes:")
        print("  - The model name in GEMINI_MODEL does not exist or is not")
        print("    available to your account. Try 'gemini-2.5-pro' in .env")
        print("    to confirm the key itself works.")
        print("  - The API key is invalid or has no quota.")
        print("  - No internet connection.")
        return 1

    print("SUCCESS - Gemini replied:")
    print(f"  {(response.text or '').strip()}")
    print()
    print(f"The model '{settings.gemini_model}' works with your key.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
