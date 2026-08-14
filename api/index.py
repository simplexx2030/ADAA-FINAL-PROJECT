"""
The ADAA backend, packaged as a Vercel function.

Vercel serves every file under `/api` as a function. This one is a thin
wrapper: it puts `backend/` on the import path and hands Vercel the same
FastAPI application that `uvicorn app.main:app` runs locally. There is no
second copy of the API and no Vercel-only behaviour — if it works here it
works there, and vice versa.

`vercel.json` rewrites every `/api/*` request to this file, so FastAPI still
sees the original path (`/api/workers`, `/api/agent/chat`, and so on) and
routes it exactly as it does on a laptop.

Because the frontend is served from the same domain, the browser calls
`/api/...` as a relative path. No cross-origin request is made, so no CORS
configuration is involved at all.
"""

import sys
from pathlib import Path

# backend/ sits next to api/ in the repository root.
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402  (the path must be set up first)

# Vercel looks for a module-level `app`. Re-exported explicitly so a tidying
# tool cannot decide the import above is unused and delete it.
__all__ = ["app"]
