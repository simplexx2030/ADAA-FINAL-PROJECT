"""
The ADAA agent's connection to Gemini.

The agent can:

  chat()           hold a conversation, using the tools in tools.py to
                   search the real database
  parse_request()  turn a sentence into structured facts

Every reply reports which tools actually ran. That is how a caller tells
the difference between an answer built from database rows and an answer the
model produced on its own -- ``grounded`` is true only when a tool ran.

Replies are cached, because the free tier is small. ``cached`` on every
reply says whether the answer came from Gemini just now or from an earlier
identical question. See cache.py for why that is safe.

One decision is worth pointing out, because it is the whole architecture in
miniature. When a contractor says "tomorrow", Gemini does NOT work out the
calendar date. It copies the word "tomorrow" back to us, and Python turns
it into a real date. Dates, quantities and wages are facts the application
owns. The model reads language; it does not decide numbers.
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta

from app.agent import audit, cache
from app.agent.prompts import PARSE_PROMPT, system_prompt
from app.config import settings

# Low temperature: the same question should give the same answer. The
# specification asks whether the agent is consistent on unchanged data
# (section 23), and a chatty, creative model makes that impossible.
TEMPERATURE = 0.2

# The free tier caps requests per minute. A demonstration asks several
# questions in a row, so a rate limit is waited out instead of failing.
MAX_RATE_LIMIT_RETRIES = 2


class GeminiUnavailable(RuntimeError):
    """Raised when Gemini cannot be reached, with a readable explanation."""


@dataclass
class Turn:
    """One message in a conversation."""

    role: str   # "user" or "model"
    text: str


# ---------------------------------------------------------------------------
# Talking to Gemini
# ---------------------------------------------------------------------------

# The client is created once and kept. It must not be a throwaway: the
# client owns the underlying HTTP connection, so if it is garbage collected
# while a request is in flight the request dies with "client has been
# closed".
_cached_client = None


def _client():
    """Create the Gemini client once, or explain clearly why we cannot."""
    global _cached_client

    if _cached_client is not None:
        return _cached_client

    if not settings.gemini_api_key:
        raise GeminiUnavailable(
            "No GEMINI_API_KEY in your .env file. Get a key from "
            "https://aistudio.google.com/apikey"
        )
    try:
        from google import genai
    except ImportError:
        raise GeminiUnavailable(
            "The google-genai package is not installed. Run: "
            "pip install -r backend/requirements.txt"
        )

    _cached_client = genai.Client(api_key=settings.gemini_api_key)
    return _cached_client


def _retry_after(error: Exception) -> float | None:
    """
    How long Google says to wait, if this failure is worth waiting out.

    A 429 means one of two very different things, and the difference
    matters. "limit: 0" means the model is not available on this billing
    tier at all, and waiting will never help. Any other limit is a rate
    cap -- usually a few requests per minute -- and waiting fixes it.
    """
    text = str(error)
    if "RESOURCE_EXHAUSTED" not in text and "429" not in text:
        return None
    if "limit: 0" in text:
        return None
    # A per-DAY allowance does not come back for hours. Google still sends
    # a short retryDelay with it, which is misleading -- waiting 55 seconds
    # achieves nothing. Only per-minute caps are worth waiting out.
    if "PerDay" in text:
        return None

    match = re.search(r"retry in ([\d.]+)s", text)
    if match:
        return min(float(match.group(1)) + 1, 65.0)

    match = re.search(r"'retryDelay': '(\d+)s'", text)
    if match:
        return min(float(match.group(1)) + 1, 65.0)

    return 30.0


def _explain_failure(error: Exception) -> str:
    """Turn a raw API error into something a person can act on."""
    text = str(error)

    if "limit: 0" in text:
        return (
            f"The model '{settings.gemini_model}' gets zero quota on this "
            "API key's free tier, so it cannot be used at all without "
            "billing enabled on the Google Cloud project. Set GEMINI_MODEL "
            "in .env to a model your tier allows, such as gemini-3.5-flash."
        )
    if "PerDay" in text:
        return (
            f"The daily free-tier allowance for '{settings.gemini_model}' is "
            "used up. It resets after midnight Pacific time. To keep working "
            "today, set GEMINI_MODEL in .env to another model such as "
            "gemini-3.1-flash-lite, which has its own separate allowance."
        )
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return (
            f"Too many requests to '{settings.gemini_model}' in a short "
            "time. The free tier allows only a few requests per minute. "
            "Wait about a minute and try again."
        )
    if "NOT_FOUND" in text or "404" in text:
        return (
            f"The model '{settings.gemini_model}' does not exist or is not "
            "available to this API key. Check GEMINI_MODEL in your .env file."
        )
    if "PERMISSION_DENIED" in text or "API key not valid" in text:
        return "The Gemini API key was rejected. Check GEMINI_API_KEY in .env."
    return f"Could not reach Gemini: {type(error).__name__}"


def _generate(contents, system_instruction: str, json_schema: dict | None = None,
              tools: list | None = None):
    """Send one request to Gemini and return the raw response."""
    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=TEMPERATURE,
    )
    if json_schema is not None:
        config.response_mime_type = "application/json"
        config.response_schema = json_schema
    if tools:
        # The SDK reads each Python function's name, arguments and
        # docstring to describe it to Gemini, then calls it for us when the
        # model asks. That keeps tools.py as ordinary readable Python
        # rather than a pile of JSON schemas.
        config.tools = tools

    # The free tier allows only a handful of requests per minute. A live
    # demonstration runs several questions back to back and will hit that,
    # so a rate limit is waited out rather than shown to the audience.
    # A missing-quota error is different and is not retried, because
    # waiting would never fix it.
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return _client().models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=config,
            )
        except GeminiUnavailable:
            raise
        except Exception as error:
            wait = _retry_after(error)
            if wait is None or attempt == MAX_RATE_LIMIT_RETRIES:
                raise GeminiUnavailable(_explain_failure(error)) from error
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

def _tools_that_ran(response) -> list[dict]:
    """
    Work out which tools Gemini actually called, and with what.

    This is not decoration. Business rule 9 says never claim something
    happened unless a tool confirms it, so a caller has to be able to see
    the difference between an answer built from database rows and an answer
    the model produced on its own.
    """
    used = []
    history = getattr(response, "automatic_function_calling_history", None) or []

    for entry in history:
        for part in getattr(entry, "parts", None) or []:
            call = getattr(part, "function_call", None)
            if call is not None and call.name:
                used.append({
                    "tool": call.name,
                    "arguments": dict(call.args or {}),
                })
    return used


def chat(message: str, history: list[Turn] | None = None,
         use_tools: bool = True, session_id: str | None = None,
         user_id: str | None = None) -> dict:
    """
    Answer one message from the user.

    ``history`` is the conversation so far, oldest first, so the agent can
    follow a request across several messages.

    With ``use_tools`` on, Gemini can search the ADAA database through the
    functions in tools.py. The reply reports which tools ran, so nothing
    has to be taken on trust.

    Everything is recorded against ``session_id`` in the agent_actions
    table, so the whole conversation can be replayed afterwards. One is
    generated if you do not pass one.
    """
    session_id = session_id or audit.new_session_id()
    from google.genai import types

    from app.agent.tools import ALL_TOOLS

    turns = [{"role": t.role, "text": t.text} for t in (history or [])]

    # The key includes a fingerprint of the database, so if the workforce
    # data changes this answer is never reused. A cached reply about who is
    # available must not outlive the availability it was based on.
    key = cache.make_key(
        "chat",
        {"message": message, "history": turns, "use_tools": use_tools},
        include_data=True,
    )
    remembered = cache.get(key)
    if remembered is not None:
        # A cached answer still gets logged, marked as such, so the record
        # of the conversation is complete and honest about where the reply
        # came from.
        audit.record(session_id, "chat_cached", user_id=user_id,
                     input_data={"message": message},
                     output_data={"reply": remembered.get("reply", "")[:500]})
        return {**remembered, "cached": True, "session_id": session_id}

    contents = []
    for turn in history or []:
        role = "model" if turn.role == "model" else "user"
        contents.append(types.Content(role=role,
                                      parts=[types.Part(text=turn.text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    # Tell the tool wrappers which conversation their calls belong to.
    audit.set_session(session_id)
    started = time.perf_counter()

    try:
        response = _generate(
            contents,
            system_prompt(tools_available=use_tools),
            tools=ALL_TOOLS if use_tools else None,
        )
    except GeminiUnavailable as error:
        audit.record(session_id, "chat", user_id=user_id,
                     input_data={"message": message},
                     success=False, error=str(error),
                     duration_ms=int((time.perf_counter() - started) * 1000))
        raise
    finally:
        audit.set_session(None)

    tools_used = _tools_that_ran(response) if use_tools else []

    result = {
        "reply": (response.text or "").strip(),
        "model": settings.gemini_model,
        "tools_used": tools_used,
        # "grounded" means: at least one claim in this reply can be traced
        # to a database row. If no tool ran, nothing here came from ADAA's
        # data, whatever the reply sounds like.
        "grounded": bool(tools_used),
    }

    audit.record(session_id, "chat", user_id=user_id,
                 input_data={"message": message},
                 output_data={"reply": result["reply"][:1000],
                              "tools_used": [t["tool"] for t in tools_used],
                              "grounded": result["grounded"]},
                 duration_ms=int((time.perf_counter() - started) * 1000))

    cache.put(key, result)
    return {**result, "cached": False, "session_id": session_id}


# ---------------------------------------------------------------------------
# Turning a sentence into facts
# ---------------------------------------------------------------------------

# What we ask Gemini to fill in. Everything is optional, because a
# contractor's first message is often incomplete, and guessing is worse
# than admitting the gap.
PARSE_SCHEMA = {
    "type": "object",
    "properties": {
        "skill":     {"type": "string", "nullable": True},
        "quantity":  {"type": "integer", "nullable": True},
        "date_text": {"type": "string", "nullable": True},
        "time":      {"type": "string", "nullable": True},
        "location":  {"type": "string", "nullable": True},
        "wage":      {"type": "number", "nullable": True},
        "missing":   {"type": "array", "items": {"type": "string"}},
        "clarification_question": {"type": "string", "nullable": True},
    },
    "required": ["missing"],
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday"]


def resolve_date(phrase: str | None, today: date | None = None) -> str | None:
    """
    Turn the words a contractor used into a real calendar date.

    This is deliberately done in Python, not by the model. A wrong date is
    the kind of mistake that sends eight people to a site on the wrong
    morning, so it is not left to a language model's arithmetic.

    Returns an ISO date string, or None if the phrase cannot be understood.
    """
    if not phrase:
        return None

    today = today or date.today()
    text = phrase.strip().lower()

    # Already a proper date?
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        pass

    simple = {
        "today": 0, "tonight": 0, "this morning": 0,
        "tomorrow": 1, "tomorrow morning": 1, "tmrw": 1,
        "day after tomorrow": 2, "the day after tomorrow": 2,
    }
    if text in simple:
        return (today + timedelta(days=simple[text])).isoformat()

    # "in 3 days"
    match = re.fullmatch(r"in (\d+) days?", text)
    if match:
        return (today + timedelta(days=int(match.group(1)))).isoformat()

    # "monday", "next monday"
    match = re.fullmatch(r"(?:next |this |on )?(\w+day)", text)
    if match and match.group(1) in WEEKDAYS:
        target = WEEKDAYS.index(match.group(1))
        ahead = (target - today.weekday()) % 7
        if ahead == 0 or text.startswith("next"):
            ahead = ahead or 7
        return (today + timedelta(days=ahead)).isoformat()

    return None


def resolve_time(phrase: str | None) -> str | None:
    """
    Turn "8 AM", "8:30 am", "0800" into "08:00".

    Same reasoning as the date: the start time decides when people leave
    home, so the application normalises it rather than trusting whatever
    format the model happened to produce.
    """
    if not phrase:
        return None

    text = phrase.strip().lower().replace(".", "")

    match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    return f"{hour:02d}:{minute:02d}"


def clean_location(phrase: str | None) -> str | None:
    """
    Strip the words around a place name: "near Guntur" -> "Guntur".

    The location is looked up in the database, so it has to be the place
    itself and not the phrase the contractor wrapped around it.
    """
    if not phrase:
        return None

    text = phrase.strip()
    text = re.sub(r"^(near|in|at|around|close to|by)\s+", "", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"\s+(area|district|region|site)$", "", text,
                  flags=re.IGNORECASE)

    return text.strip() or None


def parse_request(text: str, today: date | None = None) -> dict:
    """
    Read a workforce request and pull the facts out of it.

    Example:
        "I need 8 masons tomorrow at 8 AM near Guntur"
        -> skill Mason, quantity 8, date 2026-08-14, time 08:00,
           location Guntur

    Gemini does the reading. Python does the date.
    """
    # No database fingerprint here: parsing a sentence does not depend on
    # the workforce data, only on the words and on today's date, which is
    # already part of the key.
    key = cache.make_key("parse", {"text": text, "today": str(today or "")},
                         include_data=False)
    remembered = cache.get(key)
    if remembered is not None:
        return {**remembered, "cached": True}

    response = _generate(text, PARSE_PROMPT, json_schema=PARSE_SCHEMA)

    raw = (response.text or "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise GeminiUnavailable(
            "Gemini did not return usable JSON for this request."
        )

    date_text = parsed.get("date_text")
    resolved = resolve_date(date_text, today)

    missing = list(parsed.get("missing") or [])
    # If the model gave us words for a date but they made no sense to us,
    # that counts as missing. Better to ask than to book the wrong day.
    if date_text and not resolved and "date" not in missing:
        missing.append("date")

    result = {
        "skill": parsed.get("skill"),
        "quantity": parsed.get("quantity"),
        "date_text": date_text,
        "date": resolved,
        "time_text": parsed.get("time"),
        "time": resolve_time(parsed.get("time")),
        "location": clean_location(parsed.get("location")),
        "wage": parsed.get("wage"),
        "missing": missing,
        "complete": not missing,
        "clarification_question": parsed.get("clarification_question"),
        "model": settings.gemini_model,
    }

    cache.put(key, result)
    return {**result, "cached": False}
