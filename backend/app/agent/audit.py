"""
The record of what the agent did.

Specification section 24 asks for every important agent action to be
logged: the session, the action, the tool, its input and output, the time,
and whether it worked.

Two reasons this matters more than ordinary logging:

1. **Evaluation.** The university evaluation asks whether the agent calls
   the right tool, whether it uses real data, and whether it is consistent
   (sections 23 and 27). None of those questions can be answered from the
   chat text alone. They are answered from this table.

2. **Rule 9.** The agent must never claim an action happened unless a tool
   confirms it. This table is where "did it actually happen?" is settled.

Never log secrets. No API keys, no passwords, no connection strings. The
only things written here are the arguments the agent chose and the records
it read back, both of which are already visible to the user.

Logging must never break a request. If the database is unreachable, the
log entry is dropped and the agent carries on -- a lost audit row is
better than a failed answer in front of an audience.
"""

import functools
import json
import time
import uuid
from typing import Callable

from app.config import settings
from app.database import fetch_all, fetch_one

# How much of a tool result to keep. Full search results can be long, and
# the point of the log is what happened, not a second copy of the database.
MAX_LOGGED_CHARS = 4000


def new_session_id() -> str:
    """A fresh conversation id."""
    return uuid.uuid4().hex[:16]


def _shrink(value) -> str:
    """Turn any value into JSON, trimmed if it is very long."""
    try:
        text = json.dumps(value, default=str)
    except (TypeError, ValueError):
        text = json.dumps(str(value))

    if len(text) > MAX_LOGGED_CHARS:
        text = json.dumps({
            "truncated": True,
            "length": len(text),
            "preview": text[:MAX_LOGGED_CHARS],
        })
    return text


def record(session_id: str, action_type: str, tool_name: str | None = None,
           user_id: str | None = None, input_data=None, output_data=None,
           success: bool = True, error: str | None = None,
           duration_ms: int | None = None) -> None:
    """Write one row. Failures here are swallowed on purpose."""
    try:
        fetch_one(
            """
            insert into agent_actions
                (session_id, user_id, action_type, tool_name, input, output,
                 success, error, duration_ms, model)
            values (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
            returning id
            """,
            (session_id, user_id, action_type, tool_name,
             _shrink(input_data) if input_data is not None else None,
             _shrink(output_data) if output_data is not None else None,
             success, error, duration_ms, settings.gemini_model),
        )
    except Exception:
        # A missing audit row must never cost the user their answer.
        pass


# ---------------------------------------------------------------------------
# Wrapping the tools
# ---------------------------------------------------------------------------
#
# Gemini calls the tool functions directly through the SDK, so the only way
# to see what it did is to wrap each function before handing it over.

_current_session = {"id": None}


def set_session(session_id: str | None) -> None:
    """Tell the tool wrappers which conversation they are part of."""
    _current_session["id"] = session_id


def logged(function: Callable) -> Callable:
    """
    Wrap one tool so every call is recorded.

    functools.wraps keeps the name, the docstring and the signature, which
    is what the Google SDK reads to describe the tool to Gemini. If those
    were lost, the tool would become invisible to the model.
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        session_id = _current_session["id"]
        started = time.perf_counter()

        try:
            result = function(*args, **kwargs)
        except Exception as error:
            if session_id:
                record(session_id, "tool_call", function.__name__,
                       input_data=kwargs or list(args),
                       success=False, error=f"{type(error).__name__}: {error}",
                       duration_ms=int((time.perf_counter() - started) * 1000))
            raise

        if session_id:
            record(session_id, "tool_call", function.__name__,
                   input_data=kwargs or list(args),
                   output_data=result,
                   duration_ms=int((time.perf_counter() - started) * 1000))
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Reading the log back
# ---------------------------------------------------------------------------

def session_actions(session_id: str) -> list[dict]:
    """Everything that happened in one conversation, oldest first."""
    return fetch_all(
        """
        select id, action_type, tool_name, input, output, success, error,
               duration_ms, model, created_at
          from agent_actions
         where session_id = %s
         order by created_at, id
        """,
        (session_id,),
    )


def recent_sessions(limit: int = 20) -> list[dict]:
    """The most recent conversations, with a summary of each."""
    return fetch_all(
        """
        select session_id,
               min(created_at) as started_at,
               max(created_at) as last_action_at,
               count(*) as actions,
               count(*) filter (where action_type = 'tool_call') as tool_calls,
               count(*) filter (where not success) as failures,
               array_agg(distinct tool_name) filter (where tool_name is not null)
                   as tools_used
          from agent_actions
         group by session_id
         order by max(created_at) desc
         limit %s
        """,
        (limit,),
    )


def tool_usage() -> list[dict]:
    """
    How often each tool has been used, and how reliable it is.

    This is the table that answers the evaluation question "does the agent
    call the correct tool?" (specification section 23).
    """
    return fetch_all(
        """
        select tool_name,
               count(*) as calls,
               count(*) filter (where not success) as failures,
               round(avg(duration_ms)) as average_ms
          from agent_actions
         where tool_name is not null
         group by tool_name
         order by count(*) desc
        """
    )
