"""
Tests for actions that change something.

Business rule 7 is the subject here: consequential actions require
confirmation. The tests are mostly about things NOT happening -- proposing
must not create anything, a cancelled proposal must change nothing, and the
agent must have no way to approve its own proposal.

These tests write to the real database, so each one cleans up after itself.
If they did not, confirming a crew would leave its members booked and the
demonstration would stop working.
"""

from datetime import date, timedelta

import pytest

from app.agent import actions, tools
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
    """
    Track what a test creates, and undo it afterwards.

    Availability is restored explicitly: confirming an assignment marks
    people booked, and leaving them that way would quietly break the
    demonstration dataset for everyone afterwards.
    """
    created = {"jobs": [], "actions": [], "workers": []}

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
                cur.execute("delete from job_assignments where job_id = %s",
                            (job_id,))
                cur.execute("delete from jobs where id = %s", (job_id,))
            # Any worker a test booked directly, rather than through an
            # assignment. Without this, one test leaves somebody booked and
            # the next test quietly gets a different database.
            for worker_id in created["workers"]:
                cur.execute(
                    "update availability set status = 'available' "
                    "where worker_id = %s and date = %s",
                    (worker_id, tomorrow()),
                )
            for action_id in created["actions"]:
                cur.execute("delete from pending_actions where id = %s",
                            (action_id,))
        conn.commit()


def propose_a_job(sandbox, **overrides) -> dict:
    payload = {
        "contractor_id": "CON001", "title": "Test brickwork",
        "skill_required": "Mason", "workers_required": 4,
        "date": tomorrow(), "location_name": "Guntur",
        "start_time": "08:00", "wage": 800,
        **overrides,
    }
    proposal = actions.propose("create_job", payload, "Test job proposal")
    sandbox["actions"].append(proposal["action_id"])
    return proposal


# --- proposing changes nothing ---------------------------------------------

def test_proposing_a_job_does_not_create_it(sandbox):
    """The heart of business rule 7."""
    before = fetch_one("select count(*) as n from jobs")["n"]

    proposal = propose_a_job(sandbox)

    assert proposal["status"] == "pending"
    assert proposal["confirmed"] is False
    assert fetch_one("select count(*) as n from jobs")["n"] == before


def test_a_proposal_says_plainly_that_nothing_has_happened(sandbox):
    """
    The wording matters. This note goes back to the model, and it is what
    stops it announcing that the job is created.
    """
    proposal = propose_a_job(sandbox)

    assert "NOTHING HAS HAPPENED YET" in proposal["note"]
    assert "confirm" in proposal["note"].lower()


def test_the_agents_propose_tool_also_creates_nothing(sandbox):
    before = fetch_one("select count(*) as n from jobs")["n"]

    result = tools.propose_job("CON001", "Test wall", "Mason", 3,
                               tomorrow(), "Guntur", wage=800)
    sandbox["actions"].append(result["action_id"])

    assert result["proposed"] is True
    assert result["status"] == "pending"
    assert fetch_one("select count(*) as n from jobs")["n"] == before


# --- confirming ------------------------------------------------------------

def test_confirming_creates_the_job(sandbox):
    proposal = propose_a_job(sandbox)

    result = actions.confirm(proposal["action_id"])
    sandbox["jobs"].append(result["result"]["job_id"])

    assert result["status"] == "confirmed"
    job = fetch_one("select id, status, workers_required from jobs where id = %s",
                    (result["result"]["job_id"],))
    assert job is not None
    assert job["status"] == "open"
    assert job["workers_required"] == 4


def test_the_same_proposal_cannot_be_confirmed_twice(sandbox):
    """Otherwise a refresh of the confirmation page would create two jobs."""
    proposal = propose_a_job(sandbox)
    first = actions.confirm(proposal["action_id"])
    sandbox["jobs"].append(first["result"]["job_id"])

    with pytest.raises(ActionError, match="already been carried out"):
        actions.confirm(proposal["action_id"])


def test_a_cancelled_proposal_changes_nothing(sandbox):
    before = fetch_one("select count(*) as n from jobs")["n"]
    proposal = propose_a_job(sandbox)

    actions.cancel(proposal["action_id"])

    assert fetch_one("select count(*) as n from jobs")["n"] == before
    with pytest.raises(ActionError):
        actions.confirm(proposal["action_id"])


def test_an_expired_proposal_cannot_be_confirmed(sandbox):
    """
    A proposal was checked against the data at the time it was written.
    Hours later that check means nothing, so it has to be made again.
    """
    proposal = propose_a_job(sandbox)
    fetch_one(
        "update pending_actions set expires_at = now() - interval '1 hour' "
        "where id = %s returning id",
        (proposal["action_id"],),
    )

    with pytest.raises(ActionError, match="expired"):
        actions.confirm(proposal["action_id"])


def test_confirming_an_unknown_action_is_refused():
    with pytest.raises(ActionError, match="no action"):
        actions.confirm("act_doesnotexist")


def test_a_job_for_an_unknown_contractor_fails_at_confirmation(sandbox):
    proposal = propose_a_job(sandbox, contractor_id="CON999")

    with pytest.raises(ActionError, match="No contractor"):
        actions.confirm(proposal["action_id"])

    # And the failure is recorded rather than left looking pending.
    assert actions.look_up(proposal["action_id"])["status"] == "failed"


# --- offers ----------------------------------------------------------------

@pytest.fixture
def open_job(sandbox):
    """A confirmed job, ready to send offers for."""
    proposal = propose_a_job(sandbox)
    result = actions.confirm(proposal["action_id"])
    job_id = result["result"]["job_id"]
    sandbox["jobs"].append(job_id)
    return job_id


def test_offers_are_recorded_but_nothing_is_actually_sent(sandbox, open_job):
    proposal = actions.propose(
        "send_offers", {"job_id": open_job, "worker_ids": ["W003"]},
        "Offer to Raju")
    sandbox["actions"].append(proposal["action_id"])

    result = actions.confirm(proposal["action_id"])["result"]

    assert result["offers_sent"] == 1
    assert "simulated" in result["delivery"]
    offers = actions.job_offers(open_job)
    assert offers[0]["status"] == "offered"


def test_an_offer_is_not_sent_to_someone_no_longer_free(sandbox, open_job):
    """
    Business rule 1. Between proposing and confirming, a worker may have
    been booked. The check is made again at the moment of sending.
    """
    proposal = actions.propose(
        "send_offers", {"job_id": open_job, "worker_ids": ["W003", "W012"]},
        "Offer to two masons")
    sandbox["actions"].append(proposal["action_id"])

    # Raju gets booked elsewhere in the meantime.
    sandbox["workers"].append("W003")
    fetch_one(
        "update availability set status='booked' "
        "where worker_id='W003' and date=%s returning id",
        (tomorrow(),),
    )

    result = actions.confirm(proposal["action_id"])["result"]

    assert result["offers_sent"] == 1
    assert any(s["worker_id"] == "W003" for s in result["skipped"])


def test_a_worker_can_accept_and_a_worker_can_decline(sandbox, open_job):
    proposal = actions.propose(
        "send_offers", {"job_id": open_job, "worker_ids": ["W003", "W012"]},
        "Offers")
    sandbox["actions"].append(proposal["action_id"])
    actions.confirm(proposal["action_id"])

    offers = actions.job_offers(open_job)
    accepted = actions.respond_to_offer(offers[0]["assignment_id"], accept=True)
    declined = actions.respond_to_offer(offers[1]["assignment_id"], accept=False)

    assert accepted["status"] == "accepted"
    assert declined["status"] == "declined"


def test_an_offer_cannot_be_answered_twice(sandbox, open_job):
    proposal = actions.propose(
        "send_offers", {"job_id": open_job, "worker_ids": ["W003"]}, "Offer")
    sandbox["actions"].append(proposal["action_id"])
    actions.confirm(proposal["action_id"])

    assignment_id = actions.job_offers(open_job)[0]["assignment_id"]
    actions.respond_to_offer(assignment_id, accept=True)

    with pytest.raises(ActionError, match="already been answered"):
        actions.respond_to_offer(assignment_id, accept=False)


# --- confirming workers onto a job -----------------------------------------

def test_confirming_a_worker_marks_them_booked(sandbox, open_job):
    """
    Without this, business rule 1 would hold only until the next request:
    a confirmed worker would still look available to the matching engine.
    """
    offer_proposal = actions.propose(
        "send_offers", {"job_id": open_job, "worker_ids": ["W012"]}, "Offer")
    sandbox["actions"].append(offer_proposal["action_id"])
    actions.confirm(offer_proposal["action_id"])

    assignment_id = actions.job_offers(open_job)[0]["assignment_id"]
    actions.respond_to_offer(assignment_id, accept=True)

    confirm_proposal = actions.propose(
        "confirm_assignment",
        {"assignment_ids": [assignment_id], "job_id": open_job}, "Confirm")
    sandbox["actions"].append(confirm_proposal["action_id"])
    actions.confirm(confirm_proposal["action_id"])

    availability = fetch_one(
        "select status from availability where worker_id='W012' and date=%s",
        (tomorrow(),),
    )
    assert availability["status"] == "booked"


def test_a_confirmed_worker_stops_appearing_as_available(sandbox, open_job):
    """The same rule, seen from the matching engine's side."""
    before = {w["worker_id"] for w in
              tools.search_workers("Mason", "Guntur", tomorrow())["results"]}
    assert "W012" in before

    offer = actions.propose("send_offers",
                            {"job_id": open_job, "worker_ids": ["W012"]}, "Offer")
    sandbox["actions"].append(offer["action_id"])
    actions.confirm(offer["action_id"])
    assignment_id = actions.job_offers(open_job)[0]["assignment_id"]
    actions.respond_to_offer(assignment_id, accept=True)

    confirmation = actions.propose(
        "confirm_assignment",
        {"assignment_ids": [assignment_id], "job_id": open_job}, "Confirm")
    sandbox["actions"].append(confirmation["action_id"])
    actions.confirm(confirmation["action_id"])

    after = {w["worker_id"] for w in
             tools.search_workers("Mason", "Guntur", tomorrow())["results"]}
    assert "W012" not in after


# --- the guarantee that makes rule 7 real ----------------------------------

def test_the_agent_has_no_tool_that_confirms_anything():
    """
    The most important test in this file.

    If the model could approve its own proposal, business rule 7 would be a
    suggestion. Confirmation must arrive from a person, through the API.
    """
    tool_names = {tool.__name__ for tool in tools.ALL_TOOLS}

    for forbidden in ["confirm", "cancel", "execute", "approve"]:
        offenders = [name for name in tool_names
                     if forbidden in name and name != "check_action_status"]
        assert not offenders, f"agent must not be able to {forbidden}: {offenders}"


def test_no_tool_calls_the_confirm_function():
    """Even indirectly: no tool may reach actions.confirm."""
    import inspect

    for tool in tools.ALL_TOOLS:
        source = inspect.getsource(tool)
        assert "actions.confirm" not in source, tool.__name__
        assert "actions.cancel" not in source, tool.__name__


def test_check_action_status_reports_pending_honestly(sandbox):
    proposal = propose_a_job(sandbox)

    status = tools.check_action_status(proposal["action_id"])

    assert status["status"] == "pending"
    assert "Not done" in status["note"]


def test_check_action_status_on_an_unknown_id_says_so():
    assert tools.check_action_status("act_nope")["found"] is False
