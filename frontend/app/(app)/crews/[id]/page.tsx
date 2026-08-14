"use client";

/**
 * Screen 3 — Crew Dashboard.
 *
 * The whole point of this screen is the members table, and specifically the
 * column headed "their own rating". A crew rated 4.8 does not make its
 * members 4.8 workers, and putting the two side by side is the clearest way
 * to show that ADAA keeps them apart (business rule 3).
 */

import { use } from "react";
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

export default function CrewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: crew, loading, error } = useLoad(() => api.crew(id), [id]);

  if (loading) return <Loading what="Loading crew" />;
  if (error) return <ErrorNote error={error} />;
  if (!crew) return <Empty>Crew not found.</Empty>;

  const active = crew.members.filter((m) => m.status === "active");
  const former = crew.members.filter((m) => m.status !== "active");

  return (
    <div className="space-y-6">
      <div>
        <Link href="/crews" className="text-sm text-dim hover:underline">
          ← All crews
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            {crew.name}
          </h1>
          <Tag tone={statusTone(crew.verification_status)}>
            {crew.verification_status}
          </Tag>
          <Tag tone={statusTone(crew.availability_status)}>
            {crew.availability_status}
          </Tag>
        </div>
        <p className="mt-1 text-sm text-dim">
          {crew.primary_trade} · {crew.location_name} · led by{" "}
          {crew.leader_name ?? "—"}
        </p>
      </div>

      <Card>
        <div className="grid grid-cols-2 gap-6 px-5 py-5 sm:grid-cols-4">
          <Stat
            label="Crew rating"
            value={crew.rating === null ? "—" : Number(crew.rating).toFixed(2)}
          />
          <Stat label="Jobs completed" value={crew.completed_jobs} hint="as a crew" />
          <Stat label="Active members" value={active.length} />
          <Stat
            label="Reliability"
            value={
              crew.reliability_score === null
                ? "—"
                : Number(crew.reliability_score).toFixed(2)
            }
            hint="out of 5"
          />
        </div>
      </Card>

      {/* --- The members, and their own records --------------------- */}
      <Card>
        <CardHeader
          title="Members"
          subtitle={`${active.length} active`}
        />
        {active.length === 0 ? (
          <Empty>No active members.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/[0.04] text-left text-xs uppercase tracking-wide text-dim">
                <tr>
                  <th className="px-5 py-2 font-medium">Worker</th>
                  <th className="px-5 py-2 font-medium">Role</th>
                  <th className="px-5 py-2 font-medium">Worker rating</th>
                  <th className="px-5 py-2 font-medium">Worker jobs</th>
                  <th className="px-5 py-2 font-medium">Since</th>
                  <th className="px-5 py-2 font-medium">Availability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.07]">
                {active.map((member) => (
                  <tr key={member.id} className="hover:bg-white/[0.04]">
                    <td className="px-5 py-2.5">
                      <Link
                        href={`/workers/${member.id}`}
                        className="font-medium text-white hover:underline"
                      >
                        {member.name}
                      </Link>
                    </td>
                    <td className="px-5 py-2.5">
                      {member.role === "leader" ? (
                        <Tag tone="info">leader</Tag>
                      ) : (
                        <span className="text-dim">member</span>
                      )}
                    </td>
                    <td className="px-5 py-2.5">
                      <Rating value={member.worker_own_rating} />
                    </td>
                    <td className="px-5 py-2.5 tabular-nums text-bone">
                      {member.worker_own_completed_jobs}
                    </td>
                    <td className="px-5 py-2.5 tabular-nums text-dim">
                      {member.joined_at}
                    </td>
                    <td className="px-5 py-2.5">
                      <Tag tone={statusTone(member.availability_status)}>
                        {member.availability_status}
                      </Tag>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* --- Former members ----------------------------------------- */}
      {former.length > 0 && (
        <Card>
          <CardHeader
            title="Former members" subtitle={`${former.length} on record`} />
          <ul className="divide-y divide-white/[0.07]">
            {former.map((member) => (
              <li
                key={member.id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
              >
                <div>
                  <Link
                    href={`/workers/${member.id}`}
                    className="font-medium text-white hover:underline"
                  >
                    {member.name}
                  </Link>
                  <div className="text-xs text-dim">
                    {member.joined_at} → {member.left_at}
                  </div>
                </div>
                <div className="text-right text-sm">
                  <Rating value={member.worker_own_rating} />
                  <div className="text-xs text-dim">
                    {member.worker_own_completed_jobs} jobs
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
