"""
Tests for the reply cache.

The cache saves Gemini quota, which matters on a free tier that allows
about twenty requests a day. But a cache that hands back a stale answer
about who is available would break business rules 1 and 8 quietly, which
would be far worse than spending a request.

So most of these tests are about the cache NOT being used: when the data
changes, when the day changes, when the model changes, when it is switched
off.
"""

import pytest

from app.agent import cache as cache_module
from app.agent import agent as agent_module

# Grabbed before the fixture below replaces it, so one test can exercise
# the real thing.
REAL_FINGERPRINT = cache_module.data_fingerprint


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Give every test its own empty cache file."""
    monkeypatch.setattr(cache_module, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache_module, "CACHE_FILE", tmp_path / "replies.json")
    monkeypatch.setattr(cache_module.settings, "gemini_cache", True)
    # Keep the database out of it; fingerprint changes are tested directly.
    monkeypatch.setattr(cache_module, "data_fingerprint", lambda: "fixed")


# --- storing and finding ---------------------------------------------------

def test_a_stored_reply_is_found_again():
    key = cache_module.make_key("chat", {"message": "hello"}, include_data=False)
    cache_module.put(key, {"reply": "hi"})

    assert cache_module.get(key) == {"reply": "hi"}


def test_an_unknown_key_returns_nothing():
    assert cache_module.get("never-stored") is None


def test_different_questions_do_not_share_an_answer():
    first = cache_module.make_key("chat", {"message": "8 masons"}, False)
    second = cache_module.make_key("chat", {"message": "8 painters"}, False)

    assert first != second


def test_clearing_removes_everything():
    key = cache_module.make_key("chat", {"message": "hello"}, False)
    cache_module.put(key, {"reply": "hi"})

    assert cache_module.clear() == 1
    assert cache_module.get(key) is None


# --- when the cache must NOT be used ---------------------------------------

def test_changing_the_data_changes_the_key(monkeypatch):
    """
    The important one. If the workforce data changes, an answer about who
    is available must not be reused.
    """
    monkeypatch.setattr(cache_module, "data_fingerprint", lambda: "32-5-21")
    before = cache_module.make_key("chat", {"message": "who is free?"}, True)

    monkeypatch.setattr(cache_module, "data_fingerprint", lambda: "31-5-21")
    after = cache_module.make_key("chat", {"message": "who is free?"}, True)

    assert before != after


def test_changing_the_model_changes_the_key(monkeypatch):
    monkeypatch.setattr(cache_module.settings, "gemini_model", "gemini-3.5-flash")
    first = cache_module.make_key("chat", {"message": "hello"}, False)

    monkeypatch.setattr(cache_module.settings, "gemini_model", "gemini-3.6-flash")
    second = cache_module.make_key("chat", {"message": "hello"}, False)

    assert first != second


def test_the_key_changes_with_the_date(monkeypatch):
    """
    "Tomorrow" means a different day tomorrow, so yesterday's answer about
    tomorrow must not be reused today.
    """
    import datetime

    class Day1(datetime.date):
        @classmethod
        def today(cls):
            return datetime.date(2026, 8, 13)

    class Day2(datetime.date):
        @classmethod
        def today(cls):
            return datetime.date(2026, 8, 14)

    monkeypatch.setattr(cache_module, "date", Day1)
    first = cache_module.make_key("chat", {"message": "who is free?"}, False)

    monkeypatch.setattr(cache_module, "date", Day2)
    second = cache_module.make_key("chat", {"message": "who is free?"}, False)

    assert first != second


def test_nothing_is_stored_or_returned_when_caching_is_off(monkeypatch):
    key = cache_module.make_key("chat", {"message": "hello"}, False)
    cache_module.put(key, {"reply": "hi"})

    monkeypatch.setattr(cache_module.settings, "gemini_cache", False)

    assert cache_module.get(key) is None


def test_an_expired_entry_is_ignored(monkeypatch):
    key = cache_module.make_key("chat", {"message": "hello"}, False)
    cache_module.put(key, {"reply": "hi"})

    # Pretend a very long time has passed.
    monkeypatch.setattr(cache_module.time, "time", lambda: 10 ** 12)

    assert cache_module.get(key) is None


def test_a_corrupted_cache_file_does_not_crash_anything():
    cache_module.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_module.CACHE_FILE.write_text("{ this is not json", encoding="utf-8")

    assert cache_module.get("anything") is None
    # And it recovers: a new entry can still be stored.
    key = cache_module.make_key("chat", {"message": "hello"}, False)
    cache_module.put(key, {"reply": "hi"})
    assert cache_module.get(key) == {"reply": "hi"}


def test_no_database_means_no_caching_of_workforce_answers(monkeypatch):
    """
    If we cannot fingerprint the data, we cannot know whether a cached
    answer is still true. The fingerprint says so plainly.
    """
    import app.database

    def explode(*args, **kwargs):
        raise RuntimeError("no database")

    monkeypatch.setattr(app.database, "fetch_one", explode)

    assert REAL_FINGERPRINT() == "no-database"


# --- how the agent uses it -------------------------------------------------

def test_the_second_identical_question_does_not_call_gemini(monkeypatch):
    """The whole point: the same question twice costs one request."""
    calls = {"count": 0}

    class FakeResponse:
        text = "Ravi Crew can supply six masons."

    def fake_generate(contents, system_instruction, json_schema=None, tools=None):
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr(agent_module, "_generate", fake_generate)

    first = agent_module.chat("I need 8 masons tomorrow")
    second = agent_module.chat("I need 8 masons tomorrow")

    assert calls["count"] == 1
    assert first["cached"] is False
    assert second["cached"] is True
    assert first["reply"] == second["reply"]


def test_a_different_question_does_call_gemini(monkeypatch):
    calls = {"count": 0}

    class FakeResponse:
        text = "ok"

    def fake_generate(contents, system_instruction, json_schema=None, tools=None):
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr(agent_module, "_generate", fake_generate)

    agent_module.chat("I need 8 masons tomorrow")
    agent_module.chat("I need 4 painters tomorrow")

    assert calls["count"] == 2


def test_a_cached_reply_keeps_its_tool_record(monkeypatch):
    """
    tools_used and grounded must survive caching. They are how a caller
    knows the answer came from the database (business rule 9).
    """
    class FakeResponse:
        text = "Six masons are available."
        automatic_function_calling_history = []

    monkeypatch.setattr(
        agent_module, "_generate",
        lambda contents, system_instruction, json_schema=None, tools=None: FakeResponse())
    monkeypatch.setattr(agent_module, "_tools_that_ran",
                        lambda response: [{"tool": "search_crews", "arguments": {}}])

    first = agent_module.chat("who is free?")
    second = agent_module.chat("who is free?")

    assert second["cached"] is True
    assert second["tools_used"] == first["tools_used"]
    assert second["grounded"] is True
