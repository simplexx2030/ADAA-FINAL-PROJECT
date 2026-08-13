"""
The ADAA agent's connection to Gemini.

At this build step the agent can do two things:

  chat()           hold a conversation about workforce needs
  parse_request()  turn a sentence into structured facts

It cannot yet look anything up. The tools that search the database arrive
at the next step, and until then the prompt tells Gemini to say so rather
than inventing a crew.

One decision is worth pointing out, because it is the whole architecture in
miniature. When a contractor says "tomorrow", Gemini does NOT work out the
calendar date. It copies the word "tomorrow" back to us, and Python turns
it into a real date. Dates, quantities and wages are facts the application
owns. The model reads language; it does not decide numbers.
"""

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.agent.prompts import PARSE_PROMPT, system_prompt
from app.config import settings

# Low temperature: the same question should give the same answer. The
# specification asks whether the agent is consistent on unchanged data
# (section 23), and a chatty, creative model makes that impossible.
TEMPERATURE = 0.2


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


def _explain_failure(error: Exception) -> str:
    """Turn a raw API error into something a person can act on."""
    text = str(error)

    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return (
            f"The model '{settings.gemini_model}' has no quota left on this "
            "API key. Some models (the Pro ones) get zero quota on the free "
            "tier and need billing enabled. Try setting GEMINI_MODEL to "
            "gemini-3.5-flash in your .env file."
        )
    if "NOT_FOUND" in text or "404" in text:
        return (
            f"The model '{settings.gemini_model}' does not exist or is not "
            "available to this API key. Check GEMINI_MODEL in your .env file."
        )
    if "PERMISSION_DENIED" in text or "API key not valid" in text:
        return "The Gemini API key was rejected. Check GEMINI_API_KEY in .env."
    return f"Could not reach Gemini: {type(error).__name__}"


def _generate(contents, system_instruction: str, json_schema: dict | None = None):
    """Send one request to Gemini and return the raw response."""
    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=TEMPERATURE,
    )
    if json_schema is not None:
        config.response_mime_type = "application/json"
        config.response_schema = json_schema

    try:
        return _client().models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=config,
        )
    except GeminiUnavailable:
        raise
    except Exception as error:
        raise GeminiUnavailable(_explain_failure(error)) from error


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

def chat(message: str, history: list[Turn] | None = None,
         tools_available: bool = False) -> dict:
    """
    Answer one message from the user.

    ``history`` is the conversation so far, oldest first, so the agent can
    follow a request across several messages.
    """
    from google.genai import types

    contents = []
    for turn in history or []:
        role = "model" if turn.role == "model" else "user"
        contents.append(types.Content(role=role,
                                      parts=[types.Part(text=turn.text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    response = _generate(contents, system_prompt(tools_available))

    return {
        "reply": (response.text or "").strip(),
        "model": settings.gemini_model,
        "tools_used": [],          # none yet; the tools arrive at STEP 5
        "grounded": False,         # nothing here came from the database
    }


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

    return {
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
