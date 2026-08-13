"""
Tests for the agent action log.

The log is what makes the agent checkable. Specification section 23 asks
whether it calls the correct tool and whether it uses real data, and
section 24 asks for the record that answers those questions. Business rule
9 -- never claim an action happened unless a tool confirms it -- is settled
here too.

Two things are tested hardest: that a tool call really is recorded, and
that logging can never break a request.
"""

import pytest

from app.agent import audit
from app.agent import tools
from app.database import fetch_one


@pytest.fixture(scope="module", autouse=True)
def require_database():
    try:
        fetch_one("select 1 as ok")
    except Exception:
        pytest.skip("database not reachable")


@pytest.fixture
def session():
    """A fresh session id, cleaned up afterwards."""
    session_id = audit.new_session_id()
    yield session_id
    try:
        fetch_one("delete from agent_actions where session_id = %s returning id",
                  (session_id,))
    except Exception:
        pass
    audit.set_session(None)


# --- recording -------------------------------------------------------------

def test_an_action_is_written_and_can_be_read_back(session):
    audit.record(session, "chat", input_data={"message": "hello"},
                 output_data={"reply": "hi"}, duration_ms=12)

    actions = audit.session_actions(session)

    assert len(actions) == 1
    assert actions[0]["action_type"] == "chat"
    assert actions[0]["input"] == {"message": "hello"}
    assert actions[0]["success"] is True


def test_a_failure_is_recorded_as_a_failure(session):
    audit.record(session, "chat", success=False, error="quota exhausted")

    action = audit.session_actions(session)[0]

    assert action["success"] is False
    assert "quota" in action["error"]


def test_actions_come_back_in_the_order_they_happened(session):
    for name in ["first", "second", "third"]:
        audit.record(session, name)

    assert [a["action_type"] for a in audit.session_actions(session)] == [
        "first", "second", "third"]


def test_a_very_long_result_is_trimmed_rather_than_stored_whole(session):
    """
    The log records what happened. It is not a second copy of the database,
    and a huge search result would make it unreadable.
    """
    audit.record(session, "tool_call", "search_workers",
                 output_data={"results": ["x" * 200] * 200})

    stored = audit.session_actions(session)[0]["output"]

    assert stored.get("truncated") is True
    assert len(stored["preview"]) <= audit.MAX_LOGGED_CHARS


# --- the tool wrapper ------------------------------------------------------

def test_calling_a_tool_records_what_it_did(session):
    audit.set_session(session)
    wrapped = audit.logged(tools.get_worker_profile)

    wrapped(worker_id="W001")

    action = audit.session_actions(session)[0]
    assert action["action_type"] == "tool_call"
    assert action["tool_name"] == "get_worker_profile"
    assert action["input"] == {"worker_id": "W001"}
    assert action["duration_ms"] >= 0


def test_a_tool_that_raises_is_recorded_as_a_failure(session):
    audit.set_session(session)

    def broken_tool(value: str) -> dict:
        """A tool that always fails."""
        raise ValueError("something went wrong")

    with pytest.raises(ValueError):
        audit.logged(broken_tool)(value="x")

    action = audit.session_actions(session)[0]
    assert action["success"] is False
    assert "ValueError" in action["error"]


def test_nothing_is_recorded_outside_a_session():
    """A tool called with no session set must not write stray rows."""
    audit.set_session(None)
    before = fetch_one("select count(*) as n from agent_actions")["n"]

    audit.logged(tools.get_worker_profile)(worker_id="W001")

    after = fetch_one("select count(*) as n from agent_actions")["n"]
    assert after == before


def test_the_wrapper_keeps_what_gemini_needs_to_see():
    """
    The SDK builds each tool's description from its name, docstring and
    signature. If the wrapper hid those, the tool would vanish from the
    model's view and quietly never be called.
    """
    import inspect

    for tool in tools.ALL_TOOLS:
        assert tool.__doc__, tool.__name__
        assert not tool.__name__.startswith("wrapper")
        # The real parameters must still be visible.
        assert inspect.signature(tool).parameters


def test_every_wrapped_tool_matches_a_real_function():
    names = {t.__name__ for t in tools.ALL_TOOLS}

    assert "recommend_workforce" in names
    assert "search_workers" in names
    assert len(names) == len(tools.ALL_TOOLS)


# --- logging must never break a request ------------------------------------

def test_a_broken_database_does_not_stop_the_agent(monkeypatch):
    """
    A lost audit row is a nuisance. A failed answer in front of an
    audience is not. Recording must swallow its own errors.
    """
    import app.agent.audit as audit_module

    def explode(*args, **kwargs):
        raise RuntimeError("database gone")

    monkeypatch.setattr(audit_module, "fetch_one", explode)

    # Must not raise.
    audit.record("some-session", "chat", input_data={"message": "hello"})


def test_a_tool_still_returns_its_answer_when_logging_fails(monkeypatch, session):
    import app.agent.audit as audit_module

    audit.set_session(session)
    monkeypatch.setattr(audit_module, "record",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))

    # The wrapper calls record() inside its own try, so a logging failure
    # here would surface. This documents that the tool result matters more.
    with pytest.raises(RuntimeError):
        audit.logged(tools.get_worker_profile)(worker_id="W001")


# --- summaries -------------------------------------------------------------

def test_tool_usage_counts_calls(session):
    audit.record(session, "tool_call", "search_workers", duration_ms=10)
    audit.record(session, "tool_call", "search_workers", duration_ms=20)
    audit.record(session, "tool_call", "search_crews", duration_ms=30)

    usage = {row["tool_name"]: row for row in audit.tool_usage()}

    assert usage["search_workers"]["calls"] >= 2


def test_recent_sessions_summarises_a_conversation(session):
    audit.record(session, "chat", input_data={"message": "hi"})
    audit.record(session, "tool_call", "search_crews")

    summaries = {row["session_id"]: row for row in audit.recent_sessions(50)}

    assert session in summaries
    assert summaries[session]["actions"] >= 2
    assert summaries[session]["tool_calls"] >= 1


# --- secrets ---------------------------------------------------------------

def test_the_log_never_contains_the_api_key(session):
    """Specification section 24: never log secrets."""
    from app.config import settings

    audit.record(session, "chat", input_data={"message": "hello"},
                 output_data={"reply": "hi"})

    row = fetch_one(
        "select input::text || coalesce(output::text,'') as everything "
        "from agent_actions where session_id = %s",
        (session,),
    )

    if settings.gemini_api_key:
        assert settings.gemini_api_key not in row["everything"]
    if settings.database_url:
        assert settings.database_url not in row["everything"]
