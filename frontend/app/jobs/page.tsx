"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
  Badge,
  Card,
  EmptyPanel,
  ErrorNote,
  FilterPill,
  Loading,
  PageHeader,
  statusTone,
} from "@/components/ui";
import { Calendar, HardHat, Pin, Rupee, Tool, Users } from "@/components/icons";

const FILTERS = ["all", "open", "confirmed", "completed"] as const;

export default function Jobs() {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const { data, loading, error } = useLoad(() => api.jobs(), []);

  const all = data?.jobs ?? [];
  const jobs = filter === "all" ? all : all.filter((job) => job.status === filter);

  return (
    <div>
      <PageHeader
        title="Jobs"
        subtitle={`${data?.total ?? 0} jobs on record. Showing the most recent.`}
      />

      {error && <ErrorNote error={error} />}

      <div className="mb-6 flex flex-wrap gap-2">
        {FILTERS.map((option) => (
          <FilterPill
            key={option}
            active={filter === option}
            onClick={() => setFilter(option)}
          >
            {option === "all" ? "All jobs" : option}
          </FilterPill>
        ))}
      </div>

      {loading ? (
        <Card>
          <Loading what="Loading jobs" />
        </Card>
      ) : jobs.length === 0 ? (
        <EmptyPanel icon={<HardHat className="h-10 w-10" />}>
          No {filter === "all" ? "" : filter} jobs.
        </EmptyPanel>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Card key={job.id} className="px-5 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-bold text-slate-900">{job.title}</h3>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
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
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-slate-400">{job.id}</span>
                  <Badge tone={statusTone(job.status)}>{job.status}</Badge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
