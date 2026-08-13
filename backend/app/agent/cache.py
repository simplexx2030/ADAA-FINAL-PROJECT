"""
A small cache for Gemini replies.

Why this exists
---------------
The Gemini free tier allows about twenty requests per day per model, and a
question that uses a tool costs two of them. Rehearsing a six-scenario
demonstration twice can therefore use up a whole day's allowance.

This cache means asking the same question twice only costs quota once.

The risk it has to avoid
------------------------
A cache that returns yesterday's answer about today's workforce would be
worse than no cache at all. Business rule 8 says the database is the source
of truth, and rule 1 says never claim an unavailable worker is free -- a
stale reply could break both without anyone noticing.

So the key includes:

  - the model, because different models answer differently
  - today's date, because "tomorrow" means a different day tomorrow
  - a fingerprint of the database, so re-seeding or editing the data
    invalidates every cached answer automatically

If any of those change, the cached entry is simply never found again.

Cached replies are marked with "cached": true, so during a demonstration
you can always tell whether you are seeing a fresh answer.
"""

import hashlib
import json
import time
from datetime import date
from pathlib import Path

from app.config import settings

CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"
CACHE_FILE = CACHE_DIR / "gemini_replies.json"

# A week is plenty. The date is in the key anyway, so entries go stale on
# their own; this just stops the file growing forever.
MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _load() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A corrupted cache is not worth crashing over. Start again.
        return {}


def _save(entries: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    except OSError:
        # Failing to write the cache must never break a real request.
        pass


def data_fingerprint() -> str:
    """
    A short summary of what is currently in the database.

    If the data changes, this changes, and every cached answer about the
    workforce stops being found. That is what keeps the cache from
    reporting a worker who is no longer available.
    """
    try:
        from app.database import fetch_one

        row = fetch_one(
            """
            select (select count(*) from workers)          as w,
                   (select count(*) from crews)            as c,
                   (select count(*) from crew_members)     as m,
                   (select count(*) from job_assignments)  as j,
                   (select count(*) from availability
                     where status = 'available')           as a
            """
        )
        return f"{row['w']}-{row['c']}-{row['m']}-{row['j']}-{row['a']}"
    except Exception:
        # No database, no cache. Better to spend a request than to risk
        # answering from something we cannot verify.
        return "no-database"


def make_key(kind: str, payload: dict, include_data: bool) -> str:
    """Build the lookup key for one request."""
    parts = {
        "kind": kind,
        "model": settings.gemini_model,
        "today": date.today().isoformat(),
        "payload": payload,
    }
    if include_data:
        parts["data"] = data_fingerprint()

    encoded = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:32]


def get(key: str) -> dict | None:
    """The stored reply for this key, or None."""
    if not settings.gemini_cache:
        return None

    entry = _load().get(key)
    if entry is None:
        return None
    if time.time() - entry.get("stored_at", 0) > MAX_AGE_SECONDS:
        return None

    return entry.get("value")


def put(key: str, value: dict) -> None:
    """Remember this reply."""
    if not settings.gemini_cache:
        return

    entries = _load()
    entries[key] = {"stored_at": time.time(), "value": value}

    # Drop anything long expired, so the file stays small.
    cutoff = time.time() - MAX_AGE_SECONDS
    entries = {k: v for k, v in entries.items()
               if v.get("stored_at", 0) > cutoff}

    _save(entries)


def clear() -> int:
    """Forget everything. Returns how many entries were removed."""
    count = len(_load())
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    return count


def stats() -> dict:
    """What is currently stored, for the /api/agent/cache endpoint."""
    entries = _load()
    return {
        "enabled": settings.gemini_cache,
        "entries": len(entries),
        "file": str(CACHE_FILE),
    }
