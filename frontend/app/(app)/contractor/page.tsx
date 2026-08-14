"use client";

/**
 * Contractor Dashboard.
 *
 * Post a job, then see the workforce the matching engine recommends for it.
 * The recommendation is deterministic — no AI involved — so it appears
 * without anyone asking, and a shortfall is shown as a shortfall.
 */

import { useState } from "react";
import Link from "next/link";
import { api, type Job, type Match } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
  Badge,
  Button,
  Card,
  EmptyPanel,
  ErrorNote,
  Loading,
  PageHeader,
  SectionTitle,
  statusTone,
} from "@/components/ui";
import {
  Briefcase,
  Calendar,
  Chat,
  Close,
  Pin,
  Plus,
  Rupee,
  Star,
  Tool,
  Users,
} from "@/components/icons";

export default function Contractor() {
  const [posting, setPosting] = useState(false);
  const jobs = useLoad(() => api.jobs(), []);

  const active = (jobs.data?.jobs ?? []).filter(
    (job) => job.status === "open" || job.status === "confirmed",
  );

  return (
    <div>
      <PageHeader
        title="Contractor Dashboard"
        subtitle="Post workforce requirements and track active jobs."
        action={
          <Button onClick={() => setPosting(true)}>
            <Plus className="h-4 w-4" />
            Post Job
          </Button>
        }
      />

      {jobs.error && <ErrorNote error={jobs.error} />}

      <SectionTitle>Active Jobs</SectionTitle>

      {jobs.loading ? (
        <Card>
          <Loading what="Loading jobs" />
        </Card>
      ) : active.length === 0 ? (
        <EmptyPanel icon={<Briefcase className="h-10 w-10" />}>
          No jobs posted yet. Click &ldquo;Post Job&rdquo; to create one.
        </EmptyPanel>
      ) : (
        <div className="space-y-5">
          {active.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}

      {/* --- Assistant call-to-action -------------------------------- */}
      <Link
        href="/assistant"
        className="btn-molten mt-6 flex items-center justify-between gap-4 rounded-xl px-6 py-5 text-white transition hover:opacity-95"
      >
        <span className="flex items-center gap-4">
          <Chat className="h-6 w-6" />
          <span>
            <span className="block font-bold">Need help finding workers?</span>
            <span className="block text-sm text-white/90">
              Ask the AI Workforce Assistant
            </span>
          </span>
        </span>
        <Chat className="h-5 w-5" />
      </Link>

      {posting && (
        <PostJob
          onClose={() => setPosting(false)}
          onPosted={() => {
            setPosting(false);
            jobs.reload();
          }}
        />
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */

/**
 * How well this candidate fits, out of 100.
 *
 * Shown because "why this person?" is the first thing a contractor asks,
 * and a bare list of names does not answer it.
 */
function MatchScore({ score }: { score: number }) {
  const tone =
    score >= 80
      ? "bg-jade/15 text-jade"
      : score >= 60
        ? "bg-molten/15 text-molten-soft"
        : "bg-white/10 text-dim";
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-semibold tabular-nums ${tone}`}
      title="Match score out of 100 — skill, availability, reliability, rating, proximity, experience"
    >
      {Math.round(score)}
    </span>
  );
}

function JobCard({ job }: { job: Job }) {
  const recommendation = useLoad<Match & { job_id: string }>(
    () => api.jobRecommendation(job.id),
    [job.id],
  );

  const result = recommendation.data;

  return (
    <Card className="px-6 py-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white">{job.title}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-dim">
            <span className="inline-flex items-center gap-1">
              <Tool className="h-3.5 w-3.5" />
              {job.skill_required}
            </span>
            <span className="inline-flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              {job.workers_required} needed
            </span>
            <span className="inline-flex items-center gap-1">
              <Pin className="h-3.5 w-3.5" />
              {job.location_name}
            </span>
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {job.date}
            </span>
            {job.wage && (
              <span className="inline-flex items-center gap-1">
                <Rupee className="h-3.5 w-3.5" />
                {Number(job.wage).toFixed(0)}/day
              </span>
            )}
          </div>
        </div>
        <Badge tone={statusTone(job.status)}>{job.status}</Badge>
      </div>

      <div className="mt-5 border-t border-white/[0.07] pt-4">
        {recommendation.loading ? (
          <div className="py-2 text-xs text-dim">Matching workforce…</div>
        ) : recommendation.error ? (
          <div className="text-xs text-rose-600">{recommendation.error}</div>
        ) : result ? (
          <>
            <div className="mb-2.5 text-xs font-semibold uppercase tracking-wide text-dim">
              Recommended workforce ({result.filled}/{job.workers_required} filled)
            </div>

            {result.selection.length === 0 ? (
              <p className="text-sm text-dim">
                Nobody eligible was found for this trade, place and date.
              </p>
            ) : (
              <>
              <ul className="space-y-1.5">
                {result.selection.map((entry) => (
                  <li
                    key={`${entry.kind}-${entry.id}`}
                    className="rounded-lg bg-white/[0.04] px-3 py-2.5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="flex min-w-0 items-center gap-3">
                        <Badge tone={entry.kind === "crew" ? "blue" : "green"}>
                          {entry.kind}
                        </Badge>
                        <Link
                          href={
                            entry.kind === "crew"
                              ? `/crews/${entry.id}`
                              : `/workers/${entry.id}`
                          }
                          className="truncate text-sm font-semibold text-white hover:underline"
                        >
                          {entry.name}
                        </Link>
                      </span>
                      <span className="flex shrink-0 items-center gap-3">
                        <MatchScore score={entry.match_score} />
                        <span className="w-4 text-right text-sm font-bold tabular-nums text-white">
                          {entry.supply}
                        </span>
                      </span>
                    </div>

                    {/* Why this candidate: the figures behind the score. */}
                    <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 pl-[4.25rem] text-xs text-dim">
                      <span className="inline-flex items-center gap-1">
                        <Pin className="h-3 w-3" />
                        {entry.distance_km} km away
                      </span>

                      {entry.kind === "crew" ? (
                        <>
                          <span className="inline-flex items-center gap-1">
                            <Star className="h-3 w-3 text-molten-soft" />
                            {entry.evidence.crew_rating ?? "—"} crew rating
                          </span>
                          <span>
                            {entry.evidence.contributing} of{" "}
                            {entry.evidence.of_available} available
                          </span>
                        </>
                      ) : (
                        <>
                          <span className="inline-flex items-center gap-1">
                            <Star className="h-3 w-3 text-molten-soft" />
                            {entry.evidence.average_rating ?? "—"}
                          </span>
                          <span>{entry.evidence.completed_jobs} jobs</span>
                          {entry.evidence.attendance_rate != null && (
                            <span>
                              {Number(entry.evidence.attendance_rate).toFixed(0)}%
                              attendance
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </li>
                ))}
              </ul>

              <p className="mt-3 text-xs text-dim">
                Ranked on skill depth, availability, reliability, rating, proximity and
                experience. Prototype weights.
              </p>
              </>
            )}

            {result.shortfall > 0 && (
              <p className="mt-3 text-xs text-molten">
                Shortfall of {result.shortfall} worker(s). Consider expanding search
                radius or adjusting the date.
              </p>
            )}
          </>
        ) : null}
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */

function PostJob({
  onClose,
  onPosted,
}: {
  onClose: () => void;
  onPosted: () => void;
}) {
  const skills = useLoad(() => api.skills(), []);
  const locations = useLoad(() => api.locations(), []);

  const tomorrow = new Date(Date.now() + 86_400_000).toISOString().slice(0, 10);

  const [form, setForm] = useState({
    title: "",
    skill_required: "Mason",
    workers_required: 8,
    location: "Guntur",
    date: tomorrow,
    start_time: "08:00",
    wage: 900,
    site_address: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((previous) => ({ ...previous, [key]: value }));
  }

  async function submit() {
    if (!form.title.trim()) {
      setError("Give the job a title.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.createJob({ ...form, title: form.title.trim() });
      onPosted();
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : String(problem));
    } finally {
      setBusy(false);
    }
  }

  const field =
    "w-full rounded-lg border border-white/15 px-3 py-2 text-sm outline-none focus:border-molten";

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/80 p-4 py-10">
      <div className="glass w-full max-w-lg rounded-2xl">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-6 py-4">
          <h2 className="text-lg font-bold text-white">Post a job</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-dim hover:bg-white/10 hover:text-bone"
          >
            <Close className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 px-6 py-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-bone">
              Job title
            </label>
            <input
              className={field}
              value={form.title}
              onChange={(event) => set("title", event.target.value)}
              placeholder="Brickwork for first floor slab"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-bone">
                Trade
              </label>
              <select
                className={field}
                value={form.skill_required}
                onChange={(event) => set("skill_required", event.target.value)}
              >
                {(skills.data?.skills ?? []).map((skill) => (
                  <option key={skill.id} value={skill.name}>
                    {skill.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-bone">
                Workers needed
              </label>
              <input
                type="number"
                min={1}
                className={field}
                value={form.workers_required}
                onChange={(event) =>
                  set("workers_required", Number(event.target.value))
                }
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-bone">
                Location
              </label>
              <select
                className={field}
                value={form.location}
                onChange={(event) => set("location", event.target.value)}
              >
                {(locations.data?.locations ?? []).map((place) => (
                  <option key={place.name} value={place.name}>
                    {place.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-bone">
                Date
              </label>
              <input
                type="date"
                className={field}
                value={form.date}
                onChange={(event) => set("date", event.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-bone">
                Start time
              </label>
              <input
                type="time"
                className={field}
                value={form.start_time}
                onChange={(event) => set("start_time", event.target.value)}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-bone">
                Wage per day (₹)
              </label>
              <input
                type="number"
                min={0}
                className={field}
                value={form.wage}
                onChange={(event) => set("wage", Number(event.target.value))}
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-bone">
              Site address <span className="text-dim">(optional)</span>
            </label>
            <input
              className={field}
              value={form.site_address}
              onChange={(event) => set("site_address", event.target.value)}
              placeholder="Plot 22, Ring Road"
            />
          </div>

          {error && <ErrorNote error={error} />}
        </div>

        <div className="flex justify-end gap-3 border-t border-white/[0.07] px-6 py-4">
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={busy}>
            {busy ? "Posting…" : "Post Job"}
          </Button>
        </div>
      </div>
    </div>
  );
}
