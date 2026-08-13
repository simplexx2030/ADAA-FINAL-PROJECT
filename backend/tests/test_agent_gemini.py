"""
Tests for the agent's Gemini layer.

Gemini itself is replaced with a stand-in, so these tests are free, fast
and give the same answer every time. What is being checked is our code
around the model:

  - that the application, not the model, decides the calendar date
  - that a missing detail is reported rather than filled in
  - that API failures become a readable message instead of a stack trace
  - that the prompt keeps the model honest about what it looked up

There is one optional test at the end that really does call Gemini. It is
skipped unless you ask for it, so a normal test run never uses your quota.
"""

import json
import os
from datetime import date

import pytest

from app.agent import agent as agent_module
from app.agent.agent import GeminiUnavailable, chat, parse_request
from app.agent.prompts import system_prompt

TODAY = date(2026, 8, 13)


def flat(text: str) -> str:
    """
    Collapse line breaks so a test can look for a sentence.

    The prompt is hard-wrapped for readability, so a phrase we care about
    is often split across two lines. What matters is that the instruction
    is there, not where the line happens to break.
    """
    return " ".join(text.split())


class FakeResponse:
    def __init__(self, text):
        self.text = text


@pytest.fixture
def fake_gemini(monkeypatch):
    """
    Replace the call to Gemini with something we control.

    Returns a function you call with the JSON (or text) the model should
    pretend to have produced.
    """
    def use(reply):
        captured = {}

        def fake_generate(contents, system_instruction, json_schema=None,
                          tools=None):
            captured["contents"] = contents
            captured["system_instruction"] = system_instruction
            captured["json_schema"] = json_schema
            captured["tools"] = tools
            body = reply if isinstance(reply, str) else json.dumps(reply)
            return FakeResponse(body)

        monkeypatch.setattr(agent_module, "_generate", fake_generate)
        return captured

    return use


# --- parsing ---------------------------------------------------------------

def test_the_application_resolves_the_date_not_the_model(fake_gemini):
    """
    The model returns the WORD "tomorrow". The calendar date must be
    calculated by us. If this ever fails, the model has been allowed to do
    arithmetic it should not be doing.
    """
    fake_gemini({
        "skill": "Mason", "quantity": 8, "date_text": "tomorrow",
        "time": "8 AM", "location": "near Guntur", "wage": None,
        "missing": [], "clarification_question": None,
    })

    result = parse_request("I need 8 masons tomorrow at 8 AM near Guntur",
                           today=TODAY)

    assert result["date_text"] == "tomorrow"
    assert result["date"] == "2026-08-14"


def test_a_full_request_is_extracted_and_normalised(fake_gemini):
    fake_gemini({
        "skill": "Mason", "quantity": 8, "date_text": "tomorrow",
        "time": "8 AM", "location": "near Guntur", "wage": 900,
        "missing": [], "clarification_question": None,
    })

    result = parse_request("...", today=TODAY)

    assert result["skill"] == "Mason"
    assert result["quantity"] == 8
    assert result["time"] == "08:00"        # normalised from "8 AM"
    assert result["location"] == "Guntur"   # "near" removed
    assert result["wage"] == 900
    assert result["complete"] is True


def test_missing_details_are_reported_not_invented(fake_gemini):
    fake_gemini({
        "skill": None, "quantity": None, "date_text": None, "time": None,
        "location": None, "wage": None,
        "missing": ["skill", "quantity", "location", "date"],
        "clarification_question": "What trade, how many, and where?",
    })

    result = parse_request("I need some workers", today=TODAY)

    assert result["complete"] is False
    assert set(result["missing"]) == {"skill", "quantity", "location", "date"}
    assert result["clarification_question"]
    assert result["skill"] is None


def test_an_unusable_date_phrase_becomes_a_missing_detail(fake_gemini):
    """
    The model said something about a date, but we could not turn it into a
    real day. That must count as missing, so the contractor gets asked,
    rather than silently dropping the date.
    """
    fake_gemini({
        "skill": "Mason", "quantity": 8, "date_text": "whenever suits",
        "time": None, "location": "Guntur", "wage": None,
        "missing": [], "clarification_question": None,
    })

    result = parse_request("...", today=TODAY)

    assert result["date"] is None
    assert "date" in result["missing"]
    assert result["complete"] is False


def test_bad_json_from_the_model_is_reported_clearly(fake_gemini):
    fake_gemini("this is not json at all")

    with pytest.raises(GeminiUnavailable, match="usable JSON"):
        parse_request("...", today=TODAY)


# --- the prompt ------------------------------------------------------------

def test_without_tools_the_model_is_told_it_cannot_look_anything_up():
    """
    A model with nothing to search will still produce a convincing crew of
    masons if asked, so when tools are off we say so plainly.
    """
    prompt = flat(system_prompt(tools_available=False))

    assert "do NOT have access to the ADAA database" in prompt
    assert "Never invent names" in prompt


def test_with_tools_the_model_is_told_how_to_use_them_honestly():
    prompt = flat(system_prompt(tools_available=True))

    assert "do NOT have access to the ADAA database" not in prompt
    assert "You are the ADAA Workforce Coordination Agent." in prompt
    # The instructions that keep it truthful about what it found.
    assert "Report exactly what the tool returned" in prompt
    assert "never add a name to make the total look better" in prompt
    assert "An empty result is a real answer." in prompt


def test_with_tools_the_model_is_told_it_proposes_but_cannot_confirm():
    """
    Business rule 7. The agent may propose a job or an offer, but a person
    confirms it. The prompt has to say so, because the model will otherwise
    announce that it has done what it only suggested.
    """
    prompt = flat(system_prompt(tools_available=True))

    assert "You propose; a person confirms." in prompt
    assert "You have no way to confirm a proposal yourself" in prompt
    assert "do NOT do anything" in prompt


def test_with_tools_the_model_is_told_what_it_may_never_do():
    """Rules 6 and 7: some things need a person, full stop."""
    prompt = flat(system_prompt(tools_available=True))

    assert "cannot remove a worker from a crew" in prompt
    assert "change anyone's verified skills or ratings" in prompt


def test_the_business_rules_are_in_the_prompt():
    prompt = flat(system_prompt())

    assert "Never invent worker availability" in prompt
    assert "Keep worker reputation separate from crew reputation" in prompt
    assert "Treat the database as the source of truth" in prompt


def test_chat_sends_the_system_prompt_and_offers_the_tools(fake_gemini):
    captured = fake_gemini("Here is what I found.")

    result = chat("I need 8 masons tomorrow")

    assert result["reply"] == "Here is what I found."
    assert "ADAA Workforce Coordination Agent" in captured["system_instruction"]
    # The tools really were offered to the model.
    assert captured["tools"]
    assert any(tool.__name__ == "recommend_workforce"
               for tool in captured["tools"])


def test_a_reply_with_no_tool_call_is_reported_as_not_grounded(fake_gemini):
    """
    The safeguard behind business rule 9. If no tool ran, nothing in the
    reply came from ADAA's data, however confident it sounds.
    """
    fake_gemini("Ravi Crew has six masons free tomorrow.")

    result = chat("Who is available?")

    assert result["tools_used"] == []
    assert result["grounded"] is False


# --- failures --------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("429 RESOURCE_EXHAUSTED limit: 0",             "zero quota"),
    ("429 RESOURCE_EXHAUSTED PerDay quotaValue 20", "daily free-tier allowance"),
    ("429 RESOURCE_EXHAUSTED PerMinute",            "few requests per minute"),
    ("404 NOT_FOUND model missing",                 "does not exist"),
    ("PERMISSION_DENIED",                           "key was rejected"),
    ("something else entirely",                     "Could not reach Gemini"),
])
def test_api_errors_become_readable_advice(raw, expected):
    message = agent_module._explain_failure(RuntimeError(raw))

    assert expected in message


@pytest.mark.parametrize("raw,should_wait", [
    ("429 RESOURCE_EXHAUSTED PerMinute. Please retry in 45.2s", True),
    ("429 RESOURCE_EXHAUSTED PerDay quotaValue 20. retry in 55s", False),
    ("429 RESOURCE_EXHAUSTED limit: 0", False),
    ("404 NOT_FOUND", False),
])
def test_only_a_per_minute_limit_is_worth_waiting_out(raw, should_wait):
    """
    A per-minute cap clears in a minute. A daily allowance does not, and
    Google sends a short retryDelay with it anyway -- waiting on that just
    stalls for a minute and then fails regardless.
    """
    wait = agent_module._retry_after(RuntimeError(raw))

    assert (wait is not None) == should_wait


def test_a_missing_api_key_is_explained(monkeypatch):
    monkeypatch.setattr(agent_module, "_cached_client", None)
    monkeypatch.setattr(agent_module.settings, "gemini_api_key", "")

    with pytest.raises(GeminiUnavailable, match="GEMINI_API_KEY"):
        agent_module._client()


# --- optional live check ---------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("ADAA_LIVE_GEMINI") != "1",
    reason="set ADAA_LIVE_GEMINI=1 to really call Gemini",
)
def test_live_gemini_extracts_the_demonstration_request():
    result = parse_request("I need 8 masons tomorrow at 8 AM near Guntur")

    assert result["skill"] == "Mason"
    assert result["quantity"] == 8
    assert result["location"] == "Guntur"
    assert result["time"] == "08:00"
