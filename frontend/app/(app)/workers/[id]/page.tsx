"use client";

/**
 * Screen 4 — Worker Profile.
 *
 * This is the screen the whole product is for. It shows a worker's record
 * as something that belongs to them: their jobs, their ratings, their
 * attendance, their verified skills — and their crew history, including
 * crews they have left, with everything they earned there still intact.
 *
 * Two deliberate choices:
 *
 * 1. The reputation panel is loaded from /reputation, which recounts from
 *    the job records rather than reading the summary columns. Showing the
 *    recount means the figures on screen are demonstrably derived.
 * 2. The independence assessment is behind a button and is labelled a
 *    recommendation everywhere it appears. It is advice, not a status, and
 *    the interface must not imply otherwise (business rule 5).
 */

import { use, useState } from "react";
import Link from "next/link";
import { api, type Independence } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
  Button,
  Card,
  CardHeader,
  Empty,
  ErrorNote,
  Loading,
  Rating,
  Stat,
  Tag,
  statusTone,
} from "@/components/ui";

export default function WorkerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const worker = useLoad(() => api.worker(id), [id]);
  const reputation = useLoad(() => api.workerReputation(id), [id]);

  if (worker.loading) return <Loading what="Loading worker" />;
  if (worker.error) return <ErrorNote error={worker.error} />;
  if (!worker.data) return <Empty>Worker not found.</Empty>;

  const person = worker.data;
  const counted = reputation.data;
  const currentCrew = person.crew_history.find((c) => c.status === "active");
  const pastCrews = person.crew_history.filter((c) => c.status !== "active");

  return (
    <div className="space-y-6">
      <div>
        <Link href="/workers" className="text-sm text-dim hover:underline">
          ← All workers
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            {person.name}
          </h1>
          <Tag tone={statusTone(person.verification_status)}>
            {person.verification_status}
          </Tag>
          <Tag tone={statusTone(person.availability_status)}>
            {person.availability_status}
          </Tag>
        </div>
        <p className="mt-1 text-sm text-dim">
          {person.id} · {person.location_name} · {person.experience_years} years in the
          trade · speaks {person.preferred_language} · travels up to{" "}
          {person.travel_radius_km} km
        </p>
      </div>

      {/* --- Reputation, recounted from the records ----------------- */}
      <Card>
        <CardHeader title="Reputation" />
        <div className="grid grid-cols-2 gap-6 px-5 py-5 sm:grid-cols-4">
          <Stat
            label="Completed jobs"
            value={counted?.completed_jobs ?? person.completed_jobs}
            hint={
              counted
                ? `${counted.no_shows} no-show${counted.no_shows === 1 ? "" : "s"}`
                : undefined
            }
          />
          <Stat
            label="Average rating"
            value={
              counted?.average_rating === null || counted?.average_rating === undefined
                ? "—"
                : counted.average_rating.toFixed(2)
            }
            hint={counted ? `from ${counted.ratings_count} ratings` : undefined}
          />
          <Stat
            label="Attendance"
            value={
              counted?.attendance_rate === null || counted?.attendance_rate === undefined
                ? "—"
                : `${counted.attendance_rate.toFixed(1)}%`
            }
            hint={
              counted
                ? `${counted.days_attended} of ${counted.days_booked} days`
                : undefined
            }
          />
          <Stat
            label="Reliability"
            value={
              counted?.reliability_score === null ||
              counted?.reliability_score === undefined
                ? "—"
                : counted.reliability_score.toFixed(2)
            }
            hint="out of 5"
          />
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* --- Skills ---------------------------------------------- */}
        <Card>
          <CardHeader title="Skills" />
          {person.skills.length === 0 ? (
            <Empty>No skills recorded.</Empty>
          ) : (
            <ul className="divide-y divide-white/[0.07]">
              {person.skills.map((skill) => (
                <li
                  key={skill.name}
                  className="flex items-center justify-between px-5 py-3"
                >
                  <div>
                    <div className="font-medium text-white">{skill.name}</div>
                    <div className="text-xs text-dim">
                      {skill.category} · {skill.years_experience} years
                    </div>
                  </div>
                  <Tag tone={statusTone(skill.verification_status)}>
                    {skill.verification_status}
                  </Tag>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* --- Crew history ---------------------------------------- */}
        <Card>
          <CardHeader title="Crew history" />
          {person.crew_history.length === 0 ? (
            <Empty>Works independently.</Empty>
          ) : (
            <ul className="divide-y divide-white/[0.07]">
              {currentCrew && (
                <li className="flex items-center justify-between px-5 py-3">
                  <div>
                    <Link
                      href={`/crews/${currentCrew.crew_id}`}
                      className="font-medium text-white hover:underline"
                    >
                      {currentCrew.crew_name}
                    </Link>
                    <div className="text-xs text-dim">
                      {currentCrew.role} since {currentCrew.joined_at}
                    </div>
                  </div>
                  <Tag tone="good">current</Tag>
                </li>
              )}
              {pastCrews.map((crew) => (
                <li
                  key={crew.crew_id}
                  className="flex items-center justify-between px-5 py-3"
                >
                  <div>
                    <Link
                      href={`/crews/${crew.crew_id}`}
                      className="font-medium text-white hover:underline"
                    >
                      {crew.crew_name}
                    </Link>
                    <div className="text-xs text-dim">
                      {crew.joined_at} → {crew.left_at}
                    </div>
                  </div>
                  <Tag tone="neutral">left</Tag>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {/* --- Independence ------------------------------------------- */}
      <IndependencePanel workerId={person.id} name={person.name} />

      {/* --- Ratings ------------------------------------------------ */}
      <Card>
        <CardHeader
          title="Ratings received"
          subtitle={`${person.ratings_received.length} on record`}
        />
        {person.ratings_received.length === 0 ? (
          <Empty>No ratings yet.</Empty>
        ) : (
          <ul className="divide-y divide-white/[0.07]">
            {person.ratings_received.slice(0, 10).map((rating, index) => (
              <li key={index} className="flex items-start gap-4 px-5 py-3">
                <div className="w-16 shrink-0 text-sm font-semibold tabular-nums text-white">
                  {Number(rating.rating).toFixed(2)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-bone">
                    {rating.comment || <span className="text-dim">no comment</span>}
                  </div>
                  <div className="text-xs text-dim">job {rating.job_id}</div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */

/**
 * Independence readiness.
 *
 * Behind a button on purpose: it is advice a person asks for, not a label
 * the system hangs on somebody. And the disclaimer is shown in full, from
 * the API response rather than written into the page, so the interface
 * cannot drift away from what the backend actually said.
 */
function IndependencePanel({ workerId, name }: { workerId: string; name: string }) {
  const [assessment, setAssessment] = useState<Independence | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function assess() {
    setBusy(true);
    setError(null);
    try {
      setAssessment(await api.workerIndependence(workerId));
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : String(problem));
    } finally {
      setBusy(false);
    }
  }

  const readable: Record<string, string> = {
    ready_for_consideration: "Ready for consideration",
    developing: "Building a record",
    not_yet: "Not yet",
    not_enough_history: "Not enough history to judge",
  };

  return (
    <Card>
      <CardHeader
        title="Independent work"
        subtitle="A recommendation only — the worker decides"
        right={
          !assessment ? (
            <Button onClick={assess} disabled={busy} variant="secondary">
              {busy ? "Assessing…" : "Assess readiness"}
            </Button>
          ) : undefined
        }
      />

      {error && (
        <div className="px-5 py-4">
          <ErrorNote error={error} />
        </div>
      )}

      {!assessment && !error && (
        <Empty>Assess {name}&rsquo;s readiness from their verified history.</Empty>
      )}

      {assessment && (
        <div className="space-y-5 px-5 py-5">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-dim">Score</div>
              <div className="text-3xl font-semibold tabular-nums text-white">
                {assessment.score}
                <span className="text-lg text-dim"> / 100</span>
              </div>
            </div>
            <Tag
              tone={
                assessment.readiness === "ready_for_consideration"
                  ? "good"
                  : assessment.readiness === "not_enough_history"
                    ? "neutral"
                    : "warn"
              }
            >
              {readable[assessment.readiness] ?? assessment.readiness}
            </Tag>
          </div>

          <p className="text-sm text-bone">{assessment.recommendation}</p>

          {assessment.blockers.length > 0 && (
            <ul className="list-inside list-disc space-y-1 text-sm text-dim">
              {assessment.blockers.map((blocker, index) => (
                <li key={index}>{blocker}</li>
              ))}
            </ul>
          )}

          {/* the five factors from the assessment */}
          <div>
            <div className="mb-2 text-xs uppercase tracking-wide text-dim">
              Factors
            </div>
            <div className="space-y-1.5">
              {Object.entries(assessment.factors).map(([factor, value]) => (
                <div key={factor} className="flex items-center gap-3 text-sm">
                  <div className="w-52 shrink-0 text-dim">
                    {factor.replace(/_/g, " ")}
                  </div>
                  <div className="h-2 flex-1 overflow-hidden rounded bg-white/10">
                    <div
                      className="h-full rounded bg-molten"
                      style={{ width: `${Math.round(value * 100)}%` }}
                    />
                  </div>
                  <div className="w-12 shrink-0 text-right tabular-nums text-dim">
                    {Math.round(value * 100)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 border-t border-white/[0.07] pt-4 text-sm sm:grid-cols-2">
            <div>
              <div className="text-xs uppercase tracking-wide text-dim">
                Evidence
              </div>
              <ul className="mt-1 space-y-0.5 text-bone">
                <li>{assessment.evidence.completed_jobs} completed jobs</li>
                <li>
                  rating <Rating value={assessment.evidence.average_rating} />
                </li>
                <li>
                  attendance{" "}
                  {assessment.evidence.attendance_rate === null
                    ? "—"
                    : `${assessment.evidence.attendance_rate}%`}
                </li>
                <li>
                  verified skills:{" "}
                  {assessment.evidence.verified_skills.join(", ") || "none"}
                </li>
              </ul>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-dim">
                Contractors worked for ({assessment.evidence.distinct_contractors})
              </div>
              <ul className="mt-1 space-y-0.5 text-bone">
                {assessment.evidence.contractors.slice(0, 4).map((contractor) => (
                  <li key={contractor.company}>
                    {contractor.company}{" "}
                    <span className="text-dim">— {contractor.jobs} jobs</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Straight from the API, not rewritten here. */}
          <div className="rounded-md border border-molten/25 bg-molten/10 px-4 py-3 text-sm text-molten-soft">
            {assessment.important}
          </div>
        </div>
      )}
    </Card>
  );
}
