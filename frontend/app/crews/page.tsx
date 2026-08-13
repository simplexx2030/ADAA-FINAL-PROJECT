"use client";

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
  Tag,
  statusTone,
} from "@/components/ui";

export default function Crews() {
  const { data, loading, error } = useLoad(() => api.crews(), []);
  const crews = data?.crews ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Crews</h1>
        <p className="mt-1 text-sm text-stone-600">
          A crew has a reputation of its own, separate from the reputations of the
          workers in it.
        </p>
      </div>

      {error && <ErrorNote error={error} />}

      <Card>
        <CardHeader title={`${crews.length} crews`} subtitle="Best rated first" />
        {loading ? (
          <Loading what="Loading crews" />
        ) : crews.length === 0 ? (
          <Empty>No crews on record.</Empty>
        ) : (
          <ul className="divide-y divide-stone-100">
            {crews.map((crew) => (
              <li key={crew.id}>
                <Link
                  href={`/crews/${crew.id}`}
                  className="flex flex-wrap items-center justify-between gap-4 px-5 py-4 transition hover:bg-stone-50"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-stone-900">{crew.name}</span>
                      <Tag tone={statusTone(crew.verification_status)}>
                        {crew.verification_status}
                      </Tag>
                    </div>
                    <div className="mt-0.5 text-sm text-stone-500">
                      {crew.primary_trade} · led by {crew.leader_name ?? "—"} ·{" "}
                      {crew.location_name}
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-right">
                      <div className="text-xs text-stone-500">Crew rating</div>
                      <Rating value={crew.rating} />
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-stone-500">Jobs</div>
                      <div className="font-semibold tabular-nums">
                        {crew.completed_jobs}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-stone-500">Members</div>
                      <div className="font-semibold tabular-nums">
                        {crew.active_members ?? 0}
                      </div>
                    </div>
                    <Tag tone={statusTone(crew.availability_status)}>
                      {crew.availability_status}
                    </Tag>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
