"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import {
  Badge,
  Card,
  EmptyPanel,
  ErrorNote,
  Loading,
  PageHeader,
  RatingValue,
} from "@/components/ui";
import { Layers, Pin, Shield, Users } from "@/components/icons";

export default function Crews() {
  const { data, loading, error } = useLoad(() => api.crews(), []);
  const crews = data?.crews ?? [];

  return (
    <div>
      <PageHeader title="Crews" subtitle="Browse all registered construction crews." />

      {error && <ErrorNote error={error} />}

      {loading ? (
        <Card>
          <Loading what="Loading crews" />
        </Card>
      ) : crews.length === 0 ? (
        <EmptyPanel icon={<Layers className="h-10 w-10" />}>
          No crews on record.
        </EmptyPanel>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2">
          {crews.map((crew) => (
            <Link key={crew.id} href={`/crews/${crew.id}`}>
              <Card className="h-full px-5 py-4 transition hover:border-white/15 hover:shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
                      <Layers className="h-5 w-5" />
                    </span>
                    <div className="min-w-0">
                      <div className="truncate font-bold text-white">
                        {crew.name}
                      </div>
                      <div className="truncate text-xs text-dim">
                        Led by {crew.leader_name ?? "—"}
                      </div>
                    </div>
                  </div>
                  {crew.verification_status === "verified" && (
                    <Shield className="h-[18px] w-[18px] shrink-0 text-jade" />
                  )}
                </div>

                <div className="mt-3.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-dim">
                  <span className="inline-flex items-center gap-1">
                    <Pin className="h-3.5 w-3.5" />
                    {crew.location_name}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Users className="h-3.5 w-3.5" />
                    {crew.available_members ?? 0} available
                  </span>
                </div>

                <div className="mt-3.5 flex items-center justify-between gap-3 border-t border-white/[0.07] pt-3.5">
                  <span className="flex items-center gap-3 text-sm">
                    <RatingValue value={crew.rating} />
                    <span className="text-dim">
                      <span className="font-bold text-white">
                        {crew.completed_jobs}
                      </span>{" "}
                      jobs
                    </span>
                  </span>
                  <Badge tone="blue">{crew.primary_trade}</Badge>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
