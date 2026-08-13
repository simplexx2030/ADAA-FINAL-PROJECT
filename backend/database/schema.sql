-- ADAA database schema.
-- Eleven tables, following section 9 of the build specification.
--
-- Running this file drops and recreates everything, so it is safe to run
-- again while we are still prototyping.

drop table if exists independence_assessments cascade;
drop table if exists availability            cascade;
drop table if exists ratings                 cascade;
drop table if exists job_assignments         cascade;
drop table if exists jobs                    cascade;
drop table if exists crew_members            cascade;
drop table if exists crews                   cascade;
drop table if exists contractors             cascade;
drop table if exists worker_skills           cascade;
drop table if exists workers                 cascade;
drop table if exists skills                  cascade;


-- 9.2 skills ---------------------------------------------------------------
create table skills (
    id       integer primary key,
    name     text not null unique,
    category text not null
);


-- 9.1 workers --------------------------------------------------------------
-- A worker is a person. This record belongs to them, not to any crew.
create table workers (
    id                  text primary key,
    name                text not null,
    phone               text,
    photo_url           text,
    preferred_language  text    not null default 'Telugu',
    location_name       text,
    location_lat        double precision,
    location_lng        double precision,
    travel_radius_km    integer not null default 15,
    experience_years    integer not null default 0,
    verification_status text    not null default 'unverified',
    availability_status text    not null default 'available',
    reliability_score   numeric(4, 2),
    average_rating      numeric(3, 2),
    completed_jobs      integer not null default 0,
    attendance_rate     numeric(5, 2),
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now(),

    constraint workers_verification_ck check (
        verification_status in ('verified', 'pending', 'unverified')),
    constraint workers_availability_ck check (
        availability_status in ('available', 'busy', 'unavailable')),
    constraint workers_rating_ck check (
        average_rating is null or average_rating between 0 and 5)
);


-- 9.3 worker_skills --------------------------------------------------------
-- Only a VERIFIED skill may be used when recommending a worker (Rule 2).
create table worker_skills (
    worker_id           text    not null references workers(id) on delete cascade,
    skill_id            integer not null references skills(id)  on delete cascade,
    verification_status text    not null default 'unverified',
    years_experience    integer not null default 0,

    primary key (worker_id, skill_id),
    constraint worker_skills_verification_ck check (
        verification_status in ('verified', 'pending', 'unverified'))
);


-- 9.4 contractors ----------------------------------------------------------
create table contractors (
    id                  text primary key,
    name                text not null,
    phone               text,
    company_name        text,
    location            text,
    verification_status text not null default 'unverified',
    rating              numeric(3, 2),
    completed_jobs      integer not null default 0,
    created_at          timestamptz not null default now()
);


-- 9.5 crews ----------------------------------------------------------------
-- A crew has its own reputation, separate from its members' (Rule 3).
create table crews (
    id                  text primary key,
    name                text not null,
    leader_worker_id    text references workers(id),
    primary_trade       text not null,
    location_name       text,
    location_lat        double precision,
    location_lng        double precision,
    travel_radius_km    integer not null default 25,
    availability_status text    not null default 'available',
    rating              numeric(3, 2),
    completed_jobs      integer not null default 0,
    reliability_score   numeric(4, 2),
    verification_status text    not null default 'unverified',
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);


-- 9.6 crew_members ---------------------------------------------------------
-- IMPORTANT: this is a RELATIONSHIP, not an identity.
-- When a worker leaves a crew we set status='left' and fill left_at.
-- The worker's own record, ratings and history are never touched (Rule 4).
create table crew_members (
    id        serial primary key,
    crew_id   text not null references crews(id)   on delete cascade,
    worker_id text not null references workers(id) on delete cascade,
    role      text not null default 'member',
    status    text not null default 'active',
    joined_at date not null,
    left_at   date,

    constraint crew_members_status_ck check (status in ('active', 'left'))
);


-- 9.7 jobs -----------------------------------------------------------------
create table jobs (
    id               text primary key,
    contractor_id    text not null references contractors(id),
    title            text not null,
    description      text,
    skill_required   text not null,
    workers_required integer not null,
    location_name    text,
    location_lat     double precision,
    location_lng     double precision,
    site_address     text,
    date             date not null,
    start_time       time not null,
    wage             numeric(10, 2),
    status           text not null default 'open',
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),

    constraint jobs_status_ck check (
        status in ('open', 'confirmed', 'in_progress', 'completed', 'cancelled'))
);


-- 9.8 job_assignments ------------------------------------------------------
-- Either worker_id or crew_id is filled, depending on assignment_type.
create table job_assignments (
    id              serial primary key,
    job_id          text not null references jobs(id) on delete cascade,
    worker_id       text references workers(id),
    crew_id         text references crews(id),
    assignment_type text not null,
    status          text not null default 'offered',
    confirmed_at    timestamptz,
    completed_at    timestamptz,

    constraint job_assignments_type_ck check (
        assignment_type in ('individual', 'crew', 'subcontractor')),
    constraint job_assignments_status_ck check (
        status in ('offered', 'accepted', 'declined', 'confirmed', 'completed', 'no_show')),
    constraint job_assignments_target_ck check (
        (worker_id is not null) or (crew_id is not null))
);


-- 9.9 ratings --------------------------------------------------------------
-- A rating targets a worker OR a crew, never both. This is how worker and
-- crew reputation stay separate (Rule 3).
create table ratings (
    id         serial primary key,
    job_id     text not null references jobs(id) on delete cascade,
    rater_id   text not null references contractors(id),
    worker_id  text references workers(id),
    crew_id    text references crews(id),
    rating     numeric(3, 2) not null,
    comment    text,
    created_at timestamptz not null default now(),

    constraint ratings_range_ck check (rating between 0 and 5),
    constraint ratings_target_ck check (
        (worker_id is not null and crew_id is null)
     or (worker_id is null and crew_id is not null))
);


-- 9.10 availability --------------------------------------------------------
-- The ONLY source of truth for whether someone can work (Rule 1).
create table availability (
    id         serial primary key,
    worker_id  text not null references workers(id) on delete cascade,
    date       date not null,
    start_time time not null default '08:00',
    end_time   time not null default '18:00',
    status     text not null default 'available',

    unique (worker_id, date),
    constraint availability_status_ck check (
        status in ('available', 'booked', 'unavailable'))
);


-- 9.11 independence_assessments -------------------------------------------
-- An AI RECOMMENDATION record. It never changes a worker's status by
-- itself -- the worker decides (Rule 5).
create table independence_assessments (
    id                              serial primary key,
    worker_id                       text not null references workers(id) on delete cascade,
    score                           numeric(5, 2) not null,
    completed_jobs_factor           numeric(5, 2),
    rating_factor                   numeric(5, 2),
    attendance_factor               numeric(5, 2),
    reliability_factor              numeric(5, 2),
    contractor_relationship_factor  numeric(5, 2),
    recommendation                  text,
    created_at                      timestamptz not null default now()
);


-- Agent action log (specification section 24) ------------------------------
-- Every meaningful thing the agent does is recorded here: which tool it
-- called, with what, what came back, and whether it worked.
--
-- This table is deliberately NOT dropped and recreated with the rest.
-- Re-seeding the workforce data should not erase the record of what the
-- agent did, because that record is the evidence for the evaluation.
--
-- Never log secrets: no API keys, no passwords, no connection strings.
create table if not exists agent_actions (
    id           serial primary key,
    session_id   text not null,
    user_id      text,
    action_type  text not null,
    tool_name    text,
    input        jsonb,
    output       jsonb,
    success      boolean not null default true,
    error        text,
    duration_ms  integer,
    model        text,
    created_at   timestamptz not null default now()
);

create index if not exists agent_actions_session_idx
    on agent_actions (session_id, created_at);
create index if not exists agent_actions_tool_idx
    on agent_actions (tool_name, created_at);


-- Pending actions (business rule 7) -----------------------------------------
-- Anything consequential -- creating a job, sending offers, confirming a
-- worker -- is written here FIRST, as a proposal, and only carried out
-- when a person confirms it.
--
-- The agent can propose. It cannot confirm. That separation is the whole
-- point of the table: it is what stops "the AI booked eight people" from
-- being something the AI could do on its own.
--
-- Like agent_actions, this is not dropped when the workforce data is
-- re-seeded. Note that re-seeding does delete the jobs a proposal refers
-- to, so old proposals become stale -- they expire anyway.
create table if not exists pending_actions (
    id           text primary key,
    session_id   text,
    action_type  text not null,
    summary      text not null,
    payload      jsonb not null,
    status       text not null default 'pending',
    result       jsonb,
    error        text,
    created_at   timestamptz not null default now(),
    expires_at   timestamptz not null,
    decided_at   timestamptz,

    constraint pending_actions_status_ck check (
        status in ('pending', 'confirmed', 'cancelled', 'expired', 'failed'))
);

create index if not exists pending_actions_status_idx
    on pending_actions (status, expires_at);
create index if not exists pending_actions_session_idx
    on pending_actions (session_id, created_at);


-- Indexes for the searches the matching engine will run most often.
create index workers_availability_idx   on workers (availability_status, verification_status);
create index worker_skills_skill_idx    on worker_skills (skill_id, verification_status);
create index crew_members_crew_idx      on crew_members (crew_id, status);
create index crew_members_worker_idx    on crew_members (worker_id, status);
create index availability_lookup_idx    on availability (date, status);
create index jobs_status_idx            on jobs (status, date);
