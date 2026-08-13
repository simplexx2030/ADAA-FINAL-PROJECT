"""
Test setup.

Two jobs:

1. Let the tests import the application (``from app.main import app``) no
   matter which folder pytest is run from.
2. Keep the reply cache out of the way.

The second one matters more than it looks. The agent caches Gemini replies
to save quota, and the cache is keyed on the message text. Several tests
send the same placeholder text with different fake responses, so without
this they would quietly read each other's answers and pass or fail for the
wrong reason. Tests that are actually about the cache switch it back on
themselves.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def cache_disabled_by_default(tmp_path, monkeypatch):
    """Turn the reply cache off, and point it at a throwaway file."""
    from app.agent import cache

    monkeypatch.setattr(cache.settings, "gemini_cache", False)
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(cache, "CACHE_FILE", tmp_path / "cache" / "replies.json")
