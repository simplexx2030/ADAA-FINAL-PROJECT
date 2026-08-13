"""
The ADAA backend API.

STEP 0 deliberately contains only a health check. No database, no AI agent,
no matching logic yet -- those arrive in later steps of the build spec.

Run it with:
    backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend
"""

from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title="ADAA Workforce Coordination Agent",
    description=(
        "Backend API for ADAA, a construction workforce coordination "
        "platform. The AI agent is powered by Gemini and is added in a "
        "later build step."
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    """
    Confirm the server is running.

    This is the success criterion for STEP 0 of the build spec.
    """
    return {"status": "ok"}


@app.get("/")
def root():
    """
    A friendly landing response, so opening the base URL is not confusing.

    Note that we report *whether* a Gemini key is configured, never the key
    itself. Secrets must never be exposed through the API or the logs.
    """
    return {
        "name": "ADAA Workforce Coordination Agent",
        "step": "STEP 0 - environment setup",
        "environment": settings.app_env,
        "gemini_model": settings.gemini_model,
        "gemini_key_configured": bool(settings.gemini_api_key),
        "docs": "/docs",
    }
