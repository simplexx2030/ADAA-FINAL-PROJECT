"""
Tests for the parts of the matching engine that are pure arithmetic.

These need no database and no internet, so they run instantly and always.
"""

from datetime import date

import pytest

from app.agent.matching import (
    WEIGHTS,
    WorkforceRequest,
    _proximity_score,
    calculate_distance,
    score_candidate,
)

GUNTUR = (16.3067, 80.4365)
VIJAYAWADA = (16.5062, 80.6480)
TENALI = (16.2430, 80.6400)


def a_request(max_distance_km=25.0):
    return WorkforceRequest(
        skill="Mason", quantity=8, on_date=date(2026, 8, 14),
        location_lat=GUNTUR[0], location_lng=GUNTUR[1],
        location_name="Guntur", max_distance_km=max_distance_km,
    )


# --- distance --------------------------------------------------------------

def test_distance_to_itself_is_zero():
    assert calculate_distance(*GUNTUR, *GUNTUR) == 0.0


def test_guntur_to_vijayawada_is_about_30_km():
    """The real road distance is around 30-40 km; straight line is shorter."""
    km = calculate_distance(*GUNTUR, *VIJAYAWADA)

    assert 25 < km < 40, f"got {km} km"


def test_distance_is_symmetric():
    there = calculate_distance(*GUNTUR, *TENALI)
    back = calculate_distance(*TENALI, *GUNTUR)

    assert there == back


def test_distance_grows_with_separation():
    near = calculate_distance(*GUNTUR, *TENALI)
    far = calculate_distance(*GUNTUR, *VIJAYAWADA)

    assert near < far


# --- proximity score -------------------------------------------------------

def test_proximity_is_one_at_the_site():
    assert _proximity_score(0.0, 25.0) == 1.0


def test_proximity_is_zero_at_the_edge():
    assert _proximity_score(25.0, 25.0) == 0.0


def test_proximity_never_goes_negative_beyond_the_edge():
    assert _proximity_score(100.0, 25.0) == 0.0


def test_proximity_halfway_is_half():
    assert _proximity_score(12.5, 25.0) == pytest.approx(0.5)


# --- scoring ---------------------------------------------------------------

def test_weights_sum_to_one():
    """Otherwise the score would not be a percentage of anything."""
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_a_perfect_candidate_scores_100():
    perfect = {
        "skill_years": 50, "free_days": 50,
        "reliability_score": 5.0, "rating": 5.0, "experience_years": 50,
    }
    score, parts = score_candidate(perfect, 0.0, a_request())

    assert score == 100.0
    assert all(value == 1.0 for value in parts.values())


def test_an_empty_candidate_scores_zero():
    empty = {
        "skill_years": 0, "free_days": 0,
        "reliability_score": 0, "rating": 0, "experience_years": 0,
    }
    score, _ = score_candidate(empty, 25.0, a_request())

    assert score == 0.0


def test_missing_values_do_not_crash_and_score_zero():
    """A worker with no rating yet must not break the ranking."""
    score, parts = score_candidate({}, 0.0, a_request())

    assert parts["rating"] == 0.0
    assert 0 <= score <= 100


def test_score_is_always_between_0_and_100():
    odd = {
        "skill_years": 999, "free_days": -5,
        "reliability_score": 99, "rating": -1, "experience_years": 999,
    }
    score, parts = score_candidate(odd, 5.0, a_request())

    assert 0 <= score <= 100
    assert all(0.0 <= value <= 1.0 for value in parts.values())


def test_better_rating_produces_a_better_score():
    base = {"skill_years": 5, "free_days": 5, "reliability_score": 4.0,
            "experience_years": 5}
    worse, _ = score_candidate({**base, "rating": 3.0}, 5.0, a_request())
    better, _ = score_candidate({**base, "rating": 4.8}, 5.0, a_request())

    assert better > worse


def test_being_closer_produces_a_better_score():
    candidate = {"skill_years": 5, "free_days": 5, "reliability_score": 4.0,
                 "rating": 4.0, "experience_years": 5}
    near, _ = score_candidate(candidate, 2.0, a_request())
    far, _ = score_candidate(candidate, 20.0, a_request())

    assert near > far
