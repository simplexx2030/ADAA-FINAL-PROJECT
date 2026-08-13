"""
Tests for reputation.

Two business rules are the whole subject:

**Rule 3 -- worker and crew reputation are separate.** Rating a crew must
not move any member's own rating, and rating a member must not move the
crew's. This is the product's central idea, so it is tested from both
directions.

**Rule 4 -- reputation belongs to the worker.** Leaving a crew must not
cost a worker a single completed job or rating.

Everything else here is about one claim: that no reputation figure is
typed in. Every number is counted from job_assignments and ratings, and
``check_all`` proves it across the whole workforce.

These tests write to the real database, so each cleans up after itself.
"""

from datetime import date, timedelta

import pytest

from app.agent import actions, reputation
from app.agent.actions import ActionError
from app.database import connect, fetch_all, fetch_one


@pytest.fixture(scope="module", autouse=True)
def require_database():
    try:
        fetch_one("select 1 as ok")
    except Exception:
        pytest.skip("database not reachable")


def tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


@pytest.fixture
def sandbox():
    """Undo everything a test creates, including reputation changes."""
    created = {"jobs": [], "actions": [], "workers": [], "crews": []}

    yield created

    with connect() as conn:
        with conn.cursor() as cur:
            for job_id in created["jobs"]:
                cur.execute(
                    """
                    update availability set status = 'available'
                     where date = (select date from jobs where id = %s)
                       and worker_id in (
                           select worker_id from job_assignments
                            where job_id = %s and worker_id is not null
                           union
                           select cm.worker_id from job_assignments ja
                             join crew_members cm on cm.crew_id = ja.crew_id
                            where ja.job_id = %s)
                    """,
                    (job_id, job_id, job_id),
                )
                cur.execute("delete from ratings where job_id = %s", (job_id,))
                cur.execute("delete from job_assignments where job_id = %s",
                            (job_id,))
                cur.execute("delete from jobs where id = %s", (job_id,))
            for action_id in created["actions"]:
                cur.execute("delete from pending_actions where id = %s",
                            (action_id,))
        conn.commit()

    # The rows are gone; now put the stored figures back in step with them.
    for worker_id in set(created["workers"]):
        reputation.recalculate_worker(worker_id)
    for crew_id in set(created["crews"]):
        reputation.recalculate_crew(crew_id)


def a_completed_job(sandbox, worker_ids=(), crew_ids=(), attended=None):
    """Create a job, put people on it, confirm it and finish it."""
    proposal = actions.propose("create_job", {
        "contractor_id": "CON001", "title": "Reputation test job",
        "skill_required": "Mason", "workers_required": 2,
        "date": tomorrow(), "location_name": "Guntur",
        "start_time": "08:00", "wage": 800,
    }, "test job")
    sandbox["actions"].append(proposal["action_id"])
    job_id = actions.confirm(proposal["action_id"])["result"]["job_id"]
    sandbox["jobs"].append(job_id)
    sandbox["workers"].extend(worker_ids)
    sandbox["crews"].extend(crew_ids)

    offers = actions.propose("send_offers", {
        "job_id": job_id, "worker_ids": list(worker_ids),
        "crew_ids": list(crew_ids)}, "offers")
    sandbox["actions"].append(offers["action_id"])
    actions.confirm(offers["action_id"])

    assignment_ids = [o["assignment_id"] for o in actions.job_offers(job_id)]
    for assignment_id in assignment_ids:
        actions.respond_to_offer(assignment_id, accept=True)

    confirmation = actions.propose("confirm_assignment", {
        "assignment_ids": assignment_ids, "job_id": job_id}, "confirm")
    sandbox["actions"].append(confirmation["action_id"])
    actions.confirm(confirmation["action_id"])

    completion = actions.propose("complete_job", {
        "job_id": job_id,
        "outcomes": [{"assignment_id": a, "scheduled_days": 4,
                      "attended_days": 4 if attended is None else attended}
                     for a in assignment_ids]}, "complete")
    sandbox["actions"].append(completion["action_id"])
    actions.confirm(completion["action_id"])

    return job_id, assignment_ids


# --- everything is derived --------------------------------------------------

def test_every_stored_figure_matches_the_records():
    """
    The claim this whole design rests on. If this fails, some number was
    typed in rather than counted, and a professor could catch it.
    """
    assert reputation.check_all() == []


def test_attendance_is_days_attended_over_days_booked():
    figures = reputation.worker_figures("W001")

    expected = round(figures["days_attended"] / figures["days_booked"] * 100, 2)
    assert figures["attendance_rate"] == expected


def test_a_worker_with_no_history_has_no_invented_reputation():
    """A new worker should have nothing, not a flattering default."""
    empty = reputation.worker_figures("W999-does-not-exist")

    assert empty["completed_jobs"] == 0
    assert empty["average_rating"] is None
    assert empty["attendance_rate"] is None
    assert empty["reliability_score"] is None


# --- completing a job changes the right records -----------------------------

def test_completing_a_job_increases_that_workers_completed_jobs(sandbox):
    before = reputation.worker_figures("W012")["completed_jobs"]

    a_completed_job(sandbox, worker_ids=["W012"])

    assert reputation.worker_figures("W012")["completed_jobs"] == before + 1


def test_completing_a_job_does_not_touch_an_uninvolved_worker(sandbox):
    """The most basic correctness check: the right record, and only it."""
    before = reputation.worker_figures("W013")

    a_completed_job(sandbox, worker_ids=["W012"])

    assert reputation.worker_figures("W013") == before


def test_turning_up_to_none_of_the_days_is_a_no_show_not_a_completed_job(sandbox):
    before = reputation.worker_figures("W012")

    _job_id, assignment_ids = a_completed_job(sandbox, worker_ids=["W012"],
                                              attended=0)

    after = reputation.worker_figures("W012")
    assert after["completed_jobs"] == before["completed_jobs"]
    assert after["no_shows"] == before["no_shows"] + 1


def test_missing_days_lowers_attendance(sandbox):
    before = reputation.worker_figures("W012")["attendance_rate"]

    a_completed_job(sandbox, worker_ids=["W012"], attended=1)   # 1 of 4 days

    assert reputation.worker_figures("W012")["attendance_rate"] < before


def test_a_job_cannot_be_completed_twice(sandbox):
    job_id, assignment_ids = a_completed_job(sandbox, worker_ids=["W012"])

    proposal = actions.propose("complete_job", {
        "job_id": job_id,
        "outcomes": [{"assignment_id": assignment_ids[0]}]}, "again")
    sandbox["actions"].append(proposal["action_id"])

    with pytest.raises(ActionError, match="already marked completed"):
        actions.confirm(proposal["action_id"])


def test_attending_more_days_than_booked_is_refused(sandbox):
    proposal = actions.propose("create_job", {
        "contractor_id": "CON001", "title": "x", "skill_required": "Mason",
        "workers_required": 1, "date": tomorrow(), "location_name": "Guntur",
    }, "job")
    sandbox["actions"].append(proposal["action_id"])
    job_id = actions.confirm(proposal["action_id"])["result"]["job_id"]
    sandbox["jobs"].append(job_id)

    offers = actions.propose("send_offers",
                             {"job_id": job_id, "worker_ids": ["W012"]}, "o")
    sandbox["actions"].append(offers["action_id"])
    actions.confirm(offers["action_id"])
    assignment_id = actions.job_offers(job_id)[0]["assignment_id"]
    actions.respond_to_offer(assignment_id, accept=True)
    confirm = actions.propose("confirm_assignment",
                              {"assignment_ids": [assignment_id],
                               "job_id": job_id}, "c")
    sandbox["actions"].append(confirm["action_id"])
    actions.confirm(confirm["action_id"])

    bad = actions.propose("complete_job", {
        "job_id": job_id,
        "outcomes": [{"assignment_id": assignment_id, "scheduled_days": 3,
                      "attended_days": 5}]}, "bad")
    sandbox["actions"].append(bad["action_id"])

    with pytest.raises(ActionError, match="between 0 and"):
        actions.confirm(bad["action_id"])


# --- rule 3: the two reputations are separate -------------------------------

def test_rating_a_crew_does_not_change_any_members_own_rating(sandbox):
    """
    Business rule 3, from the crew's side. This is the product's central
    idea: a crew rated 4.8 does not make its members 4.8 workers.
    """
    members = [row["worker_id"] for row in fetch_all(
        "select worker_id from crew_members where crew_id='RAVI01' "
        "and status='active'")]
    before = {m: reputation.worker_figures(m)["average_rating"] for m in members}
    sandbox["workers"].extend(members)

    job_id, _ = a_completed_job(sandbox, crew_ids=["RAVI01"])
    actions.record_rating(job_id, "CON001", 5.0, crew_id="RAVI01")

    after = {m: reputation.worker_figures(m)["average_rating"] for m in members}
    assert after == before


def test_rating_a_worker_does_not_change_their_crews_rating(sandbox):
    """Business rule 3, from the worker's side."""
    before = reputation.crew_figures("RAVI01")["rating"]
    sandbox["crews"].append("RAVI01")
    sandbox["workers"].append("W001")

    job_id, _ = a_completed_job(sandbox, worker_ids=["W001"])
    actions.record_rating(job_id, "CON001", 5.0, worker_id="W001")

    assert reputation.crew_figures("RAVI01")["rating"] == before


def test_a_rating_must_target_a_worker_or_a_crew_but_not_both(sandbox):
    job_id, _ = a_completed_job(sandbox, worker_ids=["W012"])

    with pytest.raises(ActionError, match="exactly one"):
        actions.record_rating(job_id, "CON001", 4.0,
                              worker_id="W012", crew_id="RAVI01")
    with pytest.raises(ActionError, match="exactly one"):
        actions.record_rating(job_id, "CON001", 4.0)


def test_a_rating_changes_the_workers_average(sandbox):
    sandbox["workers"].append("W012")
    before = reputation.worker_figures("W012")

    job_id, _ = a_completed_job(sandbox, worker_ids=["W012"])
    actions.record_rating(job_id, "CON001", 5.0, worker_id="W012",
                          comment="Excellent")

    after = reputation.worker_figures("W012")
    assert after["ratings_count"] == before["ratings_count"] + 1
    assert after["average_rating"] > before["average_rating"]


# --- what cannot be rated ---------------------------------------------------

def test_work_that_is_not_finished_cannot_be_rated(sandbox):
    proposal = actions.propose("create_job", {
        "contractor_id": "CON001", "title": "unfinished",
        "skill_required": "Mason", "workers_required": 1,
        "date": tomorrow(), "location_name": "Guntur"}, "job")
    sandbox["actions"].append(proposal["action_id"])
    job_id = actions.confirm(proposal["action_id"])["result"]["job_id"]
    sandbox["jobs"].append(job_id)

    with pytest.raises(ActionError, match="Only completed work"):
        actions.record_rating(job_id, "CON001", 5.0, worker_id="W012")


def test_someone_who_did_not_work_on_the_job_cannot_be_rated_for_it(sandbox):
    """Otherwise reputation could be awarded for work nobody did."""
    job_id, _ = a_completed_job(sandbox, worker_ids=["W012"])

    with pytest.raises(ActionError, match="did not complete this job"):
        actions.record_rating(job_id, "CON001", 5.0, worker_id="W013")


def test_the_same_person_cannot_be_rated_twice_for_one_job(sandbox):
    sandbox["workers"].append("W012")
    job_id, _ = a_completed_job(sandbox, worker_ids=["W012"])
    actions.record_rating(job_id, "CON001", 4.0, worker_id="W012")

    with pytest.raises(ActionError, match="already been rated"):
        actions.record_rating(job_id, "CON001", 5.0, worker_id="W012")


def test_a_rating_outside_zero_to_five_is_refused(sandbox):
    job_id, _ = a_completed_job(sandbox, worker_ids=["W012"])

    with pytest.raises(ActionError, match="between 0 and 5"):
        actions.record_rating(job_id, "CON001", 7.0, worker_id="W012")


# --- rule 4: leaving a crew costs a worker nothing --------------------------

def test_leaving_a_crew_preserves_everything_the_worker_earned():
    """
    Business rule 4, checked against real records rather than described.

    Bhaskar left Ravi Crew. His completed jobs, ratings, attendance and
    verified skill are all still his, because they are attached to him and
    not to the crew.
    """
    figures = reputation.worker_figures("W014")

    assert figures["completed_jobs"] > 0
    assert figures["average_rating"] is not None
    assert figures["attendance_rate"] is not None

    membership = fetch_one(
        "select status, left_at from crew_members "
        "where worker_id='W014' and crew_id='RAVI01'")
    assert membership["status"] == "left"
    assert membership["left_at"] is not None

    skills = fetch_all(
        "select s.name from worker_skills ws join skills s on s.id=ws.skill_id "
        "where ws.worker_id='W014' and ws.verification_status='verified'")
    assert any(row["name"] == "Mason" for row in skills)


def test_reputation_never_filters_by_crew_membership():
    """
    The mechanism behind rule 4. If the queries joined crew_members, a
    worker's history would vanish the day they left, so they must not.
    """
    import inspect

    # The docstring mentions crew_members while explaining the rule, which
    # is fine. What matters is that the queries never join it.
    for query_function in ["worker_figures", "crew_figures",
                           "recalculate_worker", "recalculate_crew"]:
        body = inspect.getsource(getattr(reputation, query_function))
        assert "crew_members" not in body, query_function
