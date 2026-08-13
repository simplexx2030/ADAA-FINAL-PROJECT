"use client";

/**
 * Screen 1 — Contractor Dashboard.
 *
 * What a contractor wants to know on opening the app: what workforce is
 * available right now, what jobs are running, and a way to ask for people.
 */

import Link from "next/link";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
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

export default function Dashboard() {
  const workers = useLoad(() => api.workers(), []);
  const crews = useLoad(() => api.crews(), []);
  const jobs = useLoad(() => api.jobs(), []);

  const error = workers.error || crews.error || jobs.error;

  const allWorkers = workers.data?.workers ?? [];
  const allCrews = crews.data?.crews ?? [];
  const allJobs = jobs.data?.jobs ?? [];

  const availableWorkers = allWorkers.filter(
    (w) => w.availability_status === "available" && w.verification_status === "verified",
  );
  const availableCrews = allCrews.filter((c) => c.availability_status === "available");
  const openJobs = allJobs.filter((j) => j.status === "open" || j.status === "confirmed");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">
          Contractor dashboard
        </h1>
        <p className="mt-1 text-sm text-stone-600">Guntur district</p>
      </div>

      {error && <ErrorNote error={error} />}

      {/* --- Ask for workforce ------------------------------------- */}
      <Card className="bg-stone-900 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4 px-5 py-5">
          <div>
            <h2 className="text-base font-semibold">Need workers?</h2>
            <p className="mt-1 text-sm text-stone-300">
              Ask in plain language — &ldquo;I need 8 masons tomorrow at 8 AM near
              Guntur&rdquo;
            </p>
          </div>
          <Link
            href="/assistant"
            className="rounded-md bg-white px-4 py-2 text-sm font-medium text-stone-900 transition hover:bg-stone-100"
          >
            Open the AI assistant
          </Link>
        </div>
      </Card>

      {/* --- Summary ------------------------------------------------ */}
      <Card>
        <div className="grid grid-cols-2 gap-6 px-5 py-5 sm:grid-cols-4">
          <Stat
            label="Verified & free"
            value={workers.loading ? "…" : availableWorkers.length}
            hint={`of ${allWorkers.length} workers`}
          />
          <Stat
            label="Crews available"
            value={crews.loading ? "…" : availableCrews.length}
            hint={`of ${allCrews.length} crews`}
          />
          <Stat
            label="Active jobs"
            value={jobs.loading ? "…" : openJobs.length}
            hint="open or confirmed"
          />
          <Stat
            label="Jobs on record"
            value={jobs.loading ? "…" : (jobs.data?.total ?? allJobs.length)}
            hint="including completed"
          />
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* --- Available now ---------------------------------------- */}
        <Card>
          <CardHeader
            title="Available now"
            subtitle="Verified workers, best rated first"
            right={
              <Link href="/workers" className="text-sm text-stone-600 underline">
                All workers
              </Link>
            }
          />
          {workers.loading ? (
            <Loading what="Loading workers" />
          ) : availableWorkers.length === 0 ? (
            <Empty>Nobody is marked available.</Empty>
          ) : (
            <ul className="divide-y divide-stone-100">
              {availableWorkers.slice(0, 6).map((worker) => (
                <li key={worker.id} className="flex items-center justify-between gap-3 px-5 py-3">
                  <div className="min-w-0">
                    <Link
                      href={`/workers/${worker.id}`}
                      className="font-medium text-stone-900 hover:underline"
                    >
                      {worker.name}
                    </Link>
                    <div className="truncate text-xs text-stone-500">
                      {worker.verified_skills || "no verified skill"} · {worker.location_name}
                    </div>
                  </div>
                  <div className="shrink-0 text-right text-sm">
                    <Rating value={worker.average_rating} />
                    <div className="text-xs text-stone-500">
                      {worker.completed_jobs} jobs
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* --- Crews ------------------------------------------------- */}
        <Card>
          <CardHeader
            title="Crews"
            subtitle="By rating"
            right={
              <Link href="/crews" className="text-sm text-stone-600 underline">
                All crews
              </Link>
            }
          />
          {crews.loading ? (
            <Loading what="Loading crews" />
          ) : allCrews.length === 0 ? (
            <Empty>No crews on record.</Empty>
          ) : (
            <ul className="divide-y divide-stone-100">
              {allCrews.slice(0, 6).map((crew) => (
                <li key={crew.id} className="flex items-center justify-between gap-3 px-5 py-3">
                  <div className="min-w-0">
                    <Link
                      href={`/crews/${crew.id}`}
                      className="font-medium text-stone-900 hover:underline"
                    >
                      {crew.name}
                    </Link>
                    <div className="truncate text-xs text-stone-500">
                      {crew.primary_trade} · led by {crew.leader_name ?? "—"} ·{" "}
                      {crew.active_members ?? 0} members
                    </div>
                  </div>
                  <div className="shrink-0 text-right text-sm">
                    <Rating value={crew.rating} />
                    <div className="mt-0.5">
                      <Tag tone={statusTone(crew.availability_status)}>
                        {crew.availability_status}
                      </Tag>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {/* --- Recent jobs -------------------------------------------- */}
      <Card>
        <CardHeader title="Recent jobs" subtitle="Newest first" />
        {jobs.loading ? (
          <Loading what="Loading jobs" />
        ) : allJobs.length === 0 ? (
          <Empty>No jobs yet.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-left text-xs uppercase tracking-wide text-stone-500">
                <tr>
                  <th className="px-5 py-2 font-medium">Job</th>
                  <th className="px-5 py-2 font-medium">Trade</th>
                  <th className="px-5 py-2 font-medium">Where</th>
                  <th className="px-5 py-2 font-medium">Date</th>
                  <th className="px-5 py-2 font-medium">Need</th>
                  <th className="px-5 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {allJobs.slice(0, 10).map((job) => (
                  <tr key={job.id} className="hover:bg-stone-50">
                    <td className="px-5 py-2.5">
                      <div className="font-medium text-stone-900">{job.title}</div>
                      <div className="text-xs text-stone-500">{job.id}</div>
                    </td>
                    <td className="px-5 py-2.5 text-stone-700">{job.skill_required}</td>
                    <td className="px-5 py-2.5 text-stone-700">{job.location_name}</td>
                    <td className="px-5 py-2.5 tabular-nums text-stone-700">{job.date}</td>
                    <td className="px-5 py-2.5 tabular-nums text-stone-700">
                      {job.workers_required}
                    </td>
                    <td className="px-5 py-2.5">
                      <Tag tone={statusTone(job.status)}>{job.status}</Tag>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
