"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
  Badge,
  Card,
  CardLink,
  ErrorNote,
  Loading,
  RatingValue,
  SectionTitle,
  StatCard,
} from "@/components/ui";
import {
  Briefcase,
  Chat,
  Layers,
  Shield,
  TrendUp,
  Users,
} from "@/components/icons";

export default function Dashboard() {
  const workers = useLoad(() => api.workers(), []);
  const crews = useLoad(() => api.crews(), []);
  const jobs = useLoad(() => api.jobs(), []);

  const error = workers.error || crews.error || jobs.error;
  const allWorkers = workers.data?.workers ?? [];
  const allCrews = crews.data?.crews ?? [];
  const allJobs = jobs.data?.jobs ?? [];

  const verified = allWorkers.filter((w) => w.verification_status === "verified");
  const openJobs = allJobs.filter(
    (job) => job.status === "open" || job.status === "confirmed",
  );

  return (
    <div>
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700">
        <TrendUp className="h-3.5 w-3.5" />
        University Research Prototype
      </span>

      <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900">
        ADAA Workforce Coordination Agent
      </h1>
      <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-600">
        Connecting construction workforce demand with suitable workers, crews, and
        subcontractors — while helping every worker build an independent professional
        reputation.
      </p>

      {error && (
        <div className="mt-6">
          <ErrorNote error={error} />
        </div>
      )}

      {/* --- The four figures --------------------------------------- */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          tone="blue"
          icon={<Users className="h-5 w-5" />}
          value={workers.loading ? "…" : allWorkers.length}
          label="Workers"
        />
        <StatCard
          tone="green"
          icon={<Shield className="h-5 w-5" />}
          value={workers.loading ? "…" : verified.length}
          label="Verified Workers"
        />
        <StatCard
          tone="orange"
          icon={<Layers className="h-5 w-5" />}
          value={crews.loading ? "…" : allCrews.length}
          label="Crews"
        />
        <StatCard
          tone="purple"
          icon={<Briefcase className="h-5 w-5" />}
          value={jobs.loading ? "…" : openJobs.length}
          label="Active Jobs"
        />
      </div>

      {/* --- The two ways in ---------------------------------------- */}
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Link
          href="/assistant"
          className="brand-gradient group rounded-xl px-7 py-7 text-white transition hover:opacity-95"
        >
          <Chat className="h-7 w-7" />
          <h2 className="mt-5 text-xl font-bold">AI Workforce Assistant</h2>
          <p className="mt-2 text-sm leading-relaxed text-white/90">
            Tell the agent what workforce you need in plain language. It searches the
            database, applies eligibility rules, and recommends the right workers and
            crews.
          </p>
          <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold">
            Start chatting
            <span className="transition group-hover:translate-x-0.5">→</span>
          </span>
        </Link>

        <Card className="px-7 py-7">
          <Briefcase className="h-7 w-7 text-orange-500" />
          <h2 className="mt-5 text-xl font-bold text-slate-900">
            Contractor Dashboard
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Post workforce requirements, view active jobs, and see recommended workforce
            for each assignment.
          </p>
          <div className="mt-5">
            <CardLink href="/contractor">Open dashboard</CardLink>
          </div>
        </Card>
      </div>

      {/* --- Top rated ---------------------------------------------- */}
      <div className="mt-10">
        <div className="mb-3 flex items-end justify-between">
          <SectionTitle>Top rated workers</SectionTitle>
          <Link href="/workers" className="text-sm font-medium text-slate-500 hover:text-slate-900">
            View all
          </Link>
        </div>

        {workers.loading ? (
          <Card>
            <Loading what="Loading workers" />
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {allWorkers.slice(0, 3).map((worker) => (
              <Link key={worker.id} href={`/workers/${worker.id}`}>
                <Card className="px-5 py-4 transition hover:border-slate-300 hover:shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate font-semibold text-slate-900">
                        {worker.name}
                      </div>
                      <div className="truncate text-xs text-slate-500">
                        {worker.verified_skills || "no verified skill"}
                      </div>
                    </div>
                    <RatingValue value={worker.average_rating} />
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <Badge tone={worker.crew_name ? "blue" : "green"}>
                      {worker.crew_name ?? "Independent"}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      {worker.completed_jobs} jobs
                    </span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
