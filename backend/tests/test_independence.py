"""
Tests for the independence assessment.

Business rule 5 is the subject: **AI cannot force independence.** It
recommends; the worker decides. So the tests that matter most are the ones
proving that assessing somebody changes nothing about them -- not their
status, not their crew membership, not their availability.

The rest is about the score being honest: built only from verified
history, refusing to judge someone whose record is too thin, and never
presented as validated.
"""

import pytest

from app.agent import independence, reputation, tools
from app.database import connect, fetch_all, fetch_one


@pytest.fixture(scope="module", autouse=True)
def require_database():
    try:
        fetch_one("select 1 as ok")
    except Exception:
        pytest.skip("database not reachable")


@pytest.fixture
def clean_assessments():
    """Remove any assessment rows a test saves."""
    before = fetch_one("select coalesce(max(id), 0) as highest "
                       "from independence_assessments")["highest"]
    yield
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("delete from independence_assessments where id > %s",
                        (before,))
        conn.commit()


# --- rule 5: assessing changes nothing --------------------------------------

def test_assessing_a_worker_does_not_change_their_record():
    """
    The heart of business rule 5. An assessment is advice, and advice must
    not quietly alter the person it is about.
    """
    before = fetch_one(
        "select availability_status, verification_status, completed_jobs, "
        "average_rating, attendance_rate, reliability_score "
        "from workers where id='W001'")

    independence.assess("W001")

    after = fetch_one(
        "select availability_status, verification_status, completed_jobs, "
        "average_rating, attendance_rate, reliability_score "
        "from workers where id='W001'")

    assert after == before


def test_assessing_a_worker_does_not_touch_their_crew_membership():
    """
    Rule 6 as well: the AI cannot remove anyone from a crew. Being told
    you are ready to work alone must not eject you from the crew you are
    happily in.
    """
    before = fetch_all(
        "select crew_id, role, status, left_at from crew_members "
        "where worker_id='W001' order by crew_id")

    independence.assess("W001", save=True)

    after = fetch_all(
        "select crew_id, role, status, left_at from crew_members "
        "where worker_id='W001' order by crew_id")

    assert after == before
    # Clean up the saved row.
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("delete from independence_assessments where worker_id='W001' "
                        "and id = (select max(id) from independence_assessments "
                        "where worker_id='W001')")
        conn.commit()


def test_saving_writes_only_to_the_assessments_table(clean_assessments):
    workers_before = fetch_all("select * from workers order by id")

    result = independence.assess("W001", save=True)

    assert "assessment_id" in result
    assert fetch_all("select * from workers order by id") == workers_before


def test_nothing_in_the_module_writes_to_the_workers_table():
    """The mechanism behind rule 5, checked in the source."""
    import inspect

    source = inspect.getsource(independence).lower()

    assert "update workers" not in source
    assert "delete from workers" not in source
    assert "update crew_members" not in source


# --- the recommendation is worded as a recommendation -----------------------

def test_every_result_carries_the_disclaimer():
    """
    This sentence is what stops the score being read as a promotion. It is
    in the payload rather than only in the prompt, because the prompt is
    the part a model can drift away from.
    """
    result = independence.assess("W001")

    important = result["important"]
    assert "RECOMMENDATION, not a change of status" in important
    assert "The worker decides" in important
    assert "not been scientifically" in important


def test_the_agents_tool_passes_the_disclaimer_through():
    result = tools.check_independence_readiness("W001")

    assert "RECOMMENDATION, not a change of status" in result["important"]


def test_the_recommendation_is_phrased_as_consideration_not_a_decision():
    result = independence.assess("W001")

    wording = result["recommendation"].lower()
    assert "consideration" in wording
    for forbidden in ["is now independent", "has been made independent",
                      "promoted", "removed from"]:
        assert forbidden not in wording


# --- the score is built from verified history -------------------------------

def test_the_evidence_matches_what_the_records_say():
    """The assessment must not disagree with the reputation figures."""
    result = independence.assess("W001")
    figures = reputation.worker_figures("W001")

    assert result["evidence"]["completed_jobs"] == figures["completed_jobs"]
    assert result["evidence"]["average_rating"] == figures["average_rating"]
    assert result["evidence"]["attendance_rate"] == figures["attendance_rate"]


def test_only_verified_skills_are_counted():
    """Business rule 2, applied to independence."""
    result = independence.assess("W001")

    verified = {row["name"] for row in fetch_all(
        "select s.name from worker_skills ws join skills s on s.id=ws.skill_id "
        "where ws.worker_id='W001' and ws.verification_status='verified'")}

    assert set(result["evidence"]["verified_skills"]) == verified


def test_the_weights_sum_to_one():
    assert round(sum(independence.WEIGHTS.values()), 6) == 1.0


def test_the_five_factors_from_the_specification_are_all_present():
    """Section 9.11 names these, and the table has a column for each."""
    result = independence.assess("W001")

    assert set(result["factors"]) == {
        "completed_jobs", "rating", "attendance", "reliability",
        "contractor_relationships"}


def test_scores_and_factors_stay_in_range():
    for worker in fetch_all("select id from workers"):
        result = independence.assess(worker["id"])
        assert 0 <= result["score"] <= 100
        assert all(0.0 <= value <= 1.0 for value in result["factors"].values())


def test_the_same_worker_assessed_twice_gets_the_same_score():
    """Specification section 23: consistent decisions on unchanged data."""
    first = independence.assess("W001")
    second = independence.assess("W001")

    assert first["score"] == second["score"]
    assert first["factors"] == second["factors"]


# --- refusing to judge a thin record ----------------------------------------

def test_a_worker_with_too_little_history_gets_no_recommendation():
    """
    Better to say "not enough to judge" than to guess. A handful of jobs
    is not evidence of readiness either way.
    """
    thin = fetch_one(
        "select id from workers where completed_jobs < %s "
        "order by completed_jobs limit 1", (independence.MINIMUM_JOBS,))
    if thin is None:
        pytest.skip("no worker with a thin record in this dataset")

    result = independence.assess(thin["id"])

    assert result["readiness"] == "not_enough_history"
    assert result["blockers"]
    assert "does not yet have enough verified history" in result["recommendation"]


def test_the_gates_override_a_high_score():
    """
    A worker can average well on few jobs. The gates are separate from the
    score precisely so that a good average cannot substitute for a record.
    """
    blocked = [
        w for w in fetch_all("select id from workers")
        if (result := independence.assess(w["id"]))["blockers"]
        and result["score"] >= independence.READY_SCORE
    ]
    if not blocked:
        pytest.skip("no worker in this dataset scores high on a thin record")

    for worker in blocked:
        result = independence.assess(worker["id"])
        assert result["readiness"] == "not_enough_history"


def test_an_unverified_worker_is_never_recommended():
    unverified = fetch_all(
        "select id from workers where verification_status <> 'verified'")

    for worker in unverified:
        result = independence.assess(worker["id"])
        assert result["readiness"] == "not_enough_history"
        assert any("not verified" in blocker for blocker in result["blockers"])


def test_an_unknown_worker_is_reported_not_scored():
    result = independence.assess("W999-nobody")

    assert result["found"] is False
    assert "score" not in result


# --- the record of advice given ---------------------------------------------

def test_a_saved_assessment_can_be_read_back(clean_assessments):
    saved = independence.assess("W001", save=True)

    entries = independence.history("W001")

    assert entries
    assert float(entries[0]["score"]) == saved["score"]
    assert entries[0]["recommendation"] == saved["recommendation"]


def test_the_saved_row_keeps_all_five_factors(clean_assessments):
    independence.assess("W001", save=True)

    row = independence.history("W001")[0]

    for column in ["completed_jobs_factor", "rating_factor",
                   "attendance_factor", "reliability_factor",
                   "contractor_relationship_factor"]:
        assert row[column] is not None, column


# --- demonstration scenario 4 -----------------------------------------------

def test_suresh_is_a_credible_candidate():
    """
    Specification section 16. Suresh's record should support a
    recommendation -- and the evidence behind it must be real.
    """
    result = independence.assess("W001")

    assert result["name"] == "Suresh"
    assert result["readiness"] == "ready_for_consideration"
    assert result["blockers"] == []
    assert result["evidence"]["completed_jobs"] == 31
    assert result["evidence"]["average_rating"] == 4.7
    assert "Mason" in result["evidence"]["verified_skills"]


def test_a_worker_who_left_a_crew_is_still_assessable():
    """
    Business rules 4 and 5 together. Bhaskar left Ravi Crew, and his
    history still supports an assessment -- leaving cost him nothing.
    """
    result = independence.assess("W014")

    assert result["evidence"]["completed_jobs"] > 0
    assert result["readiness"] in ("ready_for_consideration", "developing")
