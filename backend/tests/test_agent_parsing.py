"""
Tests for the parts of the agent that are pure Python.

The date, the time and the place name are worked out by the application,
not by Gemini. That is the point of these tests: they prove those values
are decided by code we can check, so a wrong answer is a bug we can fix
rather than a model having an off day.

Nothing here calls the Gemini API, so these tests cost nothing and run
offline.
"""

from datetime import date

import pytest

from app.agent.agent import clean_location, resolve_date, resolve_time

# A Thursday, so weekday arithmetic is easy to reason about.
TODAY = date(2026, 8, 13)


# --- dates -----------------------------------------------------------------

@pytest.mark.parametrize("phrase,expected", [
    ("today",               "2026-08-13"),
    ("tonight",             "2026-08-13"),
    ("tomorrow",            "2026-08-14"),
    ("Tomorrow",            "2026-08-14"),
    ("  tomorrow  ",        "2026-08-14"),
    ("day after tomorrow",  "2026-08-15"),
    ("in 3 days",           "2026-08-16"),
    ("in 1 day",            "2026-08-14"),
    ("2026-09-01",          "2026-09-01"),
])
def test_common_date_phrases_resolve(phrase, expected):
    assert resolve_date(phrase, TODAY) == expected


def test_a_weekday_means_the_next_one():
    """13 Aug 2026 is a Thursday, so 'monday' is the 17th."""
    assert resolve_date("monday", TODAY) == "2026-08-17"


def test_next_weekday_skips_a_week_when_it_is_today():
    """Asking for 'next thursday' on a Thursday means a week away."""
    assert resolve_date("next thursday", TODAY) == "2026-08-20"


@pytest.mark.parametrize("phrase", [
    None, "", "sometime", "when the rain stops", "next week", "soon",
])
def test_vague_dates_return_nothing_rather_than_guessing(phrase):
    """
    Booking eight people onto the wrong morning is worse than asking a
    question, so anything unclear returns None and gets reported as
    missing.
    """
    assert resolve_date(phrase, TODAY) is None


# --- times -----------------------------------------------------------------

@pytest.mark.parametrize("phrase,expected", [
    ("8 AM",    "08:00"),
    ("8am",     "08:00"),
    ("8:30 am", "08:30"),
    ("08:00",   "08:00"),
    ("5 pm",    "17:00"),
    ("12 pm",   "12:00"),
    ("12 am",   "00:00"),
    ("14:45",   "14:45"),
])
def test_times_normalise_to_24_hour(phrase, expected):
    assert resolve_time(phrase) == expected


@pytest.mark.parametrize("phrase", [None, "", "early", "after lunch", "25:00"])
def test_unclear_times_return_nothing(phrase):
    assert resolve_time(phrase) is None


# --- places ----------------------------------------------------------------

@pytest.mark.parametrize("phrase,expected", [
    ("Guntur",           "Guntur"),
    ("near Guntur",      "Guntur"),
    ("Near Guntur",      "Guntur"),
    ("in Vijayawada",    "Vijayawada"),
    ("at Tenali",        "Tenali"),
    ("around Mangalagiri", "Mangalagiri"),
    ("close to Ponnur",  "Ponnur"),
    ("Guntur district",  "Guntur"),
    ("Guntur area",      "Guntur"),
    ("  Bapatla  ",      "Bapatla"),
])
def test_location_phrases_reduce_to_the_place_itself(phrase, expected):
    """
    The place name is looked up in the database, so "near Guntur" has to
    become "Guntur" or the lookup fails.
    """
    assert clean_location(phrase) == expected


@pytest.mark.parametrize("phrase", [None, "", "   "])
def test_empty_locations_return_nothing(phrase):
    assert clean_location(phrase) is None
