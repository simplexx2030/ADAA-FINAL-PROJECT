"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
  Avatar,
  Badge,
  Card,
  EmptyPanel,
  ErrorNote,
  FilterPill,
  Loading,
  MiniStats,
  PageHeader,
  RatingValue,
  RoleBadge,
} from "@/components/ui";
import { Layers, Pin, Shield, Users } from "@/components/icons";

export default function Workers() {
  const [skill, setSkill] = useState("");
  const [search, setSearch] = useState("");

  const skills = useLoad(() => api.skills(), []);
  const workers = useLoad(() => api.workers(skill ? { skill } : undefined), [skill]);

  const list = useMemo(() => {
    const all = workers.data?.workers ?? [];
    const term = search.trim().toLowerCase();
    if (!term) return all;
    return all.filter((worker) => worker.name.toLowerCase().includes(term));
  }, [workers.data, search]);

  return (
    <div>
      <PageHeader
        title="Workers"
        subtitle="Browse all registered construction workers."
      />

      {(workers.error || skills.error) && (
        <ErrorNote error={workers.error || skills.error || ""} />
      )}

      {/* --- Search and trade filters -------------------------------- */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by name…"
          className="w-full rounded-lg border border-white/15 px-4 py-2.5 text-sm outline-none focus:border-molten sm:w-72"
        />
        <FilterPill active={skill === ""} onClick={() => setSkill("")}>
          All Skills
        </FilterPill>
        {(skills.data?.skills ?? []).map((entry) => (
          <FilterPill
            key={entry.id}
            active={skill === entry.name}
            onClick={() => setSkill(entry.name)}
          >
            {entry.name}
          </FilterPill>
        ))}
      </div>

      {workers.loading ? (
        <Card>
          <Loading what="Loading workers" />
        </Card>
      ) : list.length === 0 ? (
        <EmptyPanel icon={<Users className="h-10 w-10" />}>
          {search
            ? `Nobody matching “${search}”.`
            : `Nobody has a verified ${skill} skill.`}
        </EmptyPanel>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((worker) => (
            <Link key={worker.id} href={`/workers/${worker.id}`}>
              <Card className="h-full px-5 py-4 transition hover:border-white/15 hover:shadow-sm">
                {/* name and verification */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <Avatar name={worker.name} />
                    <div className="min-w-0">
                      <div className="truncate font-bold text-white">
                        {worker.name}
                      </div>
                      <div className="flex items-center gap-1 text-xs text-dim">
                        <Pin className="h-3 w-3" />
                        {worker.location_name}
                      </div>
                    </div>
                  </div>
                  {worker.verification_status === "verified" && (
                    <Shield className="h-[18px] w-[18px] shrink-0 text-jade" />
                  )}
                </div>

                {/* verified trades */}
                <div className="mt-3.5 flex flex-wrap gap-1.5">
                  {(worker.verified_skills ?? "")
                    .split(",")
                    .map((name) => name.trim())
                    .filter(Boolean)
                    .map((name) => (
                      <Badge key={name} tone="green">
                        {name}
                      </Badge>
                    ))}
                  {!worker.verified_skills && (
                    <Badge tone="slate">no verified skill</Badge>
                  )}
                </div>

                {/* the three figures */}
                <div className="mt-4 border-t border-white/[0.07] pt-3.5">
                  <MiniStats
                    items={[
                      {
                        value: <RatingValue value={worker.average_rating} />,
                        label: "Rating",
                      },
                      { value: worker.completed_jobs, label: "Jobs" },
                      { value: `${worker.experience_years}y`, label: "Exp" },
                    ]}
                  />
                </div>

                {/* role, and crew if any */}
                <div className="mt-3.5 flex items-center justify-between gap-2 border-t border-white/[0.07] pt-3.5">
                  <RoleBadge role={worker.crew_role} crewName={worker.crew_name} />
                  {worker.crew_name && (
                    <span className="inline-flex items-center gap-1 text-xs text-dim">
                      <Layers className="h-3.5 w-3.5" />
                      {worker.crew_name}
                    </span>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
