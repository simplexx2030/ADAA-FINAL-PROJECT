"use client";

import { useState } from "react";
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

export default function Workers() {
  const [skill, setSkill] = useState("");
  const skills = useLoad(() => api.skills(), []);
  const workers = useLoad(() => api.workers(skill ? { skill } : undefined), [skill]);

  const list = workers.data?.workers ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Workers</h1>
        <p className="mt-1 text-sm text-stone-600">
          Filtering by skill shows only workers whose skill is <strong>verified</strong>.
        </p>
      </div>

      {(workers.error || skills.error) && (
        <ErrorNote error={workers.error || skills.error || ""} />
      )}

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSkill("")}
          className={`rounded-full px-3 py-1.5 text-sm transition ${
            skill === ""
              ? "bg-stone-900 text-white"
              : "border border-stone-300 bg-white text-stone-700 hover:bg-stone-50"
          }`}
        >
          All trades
        </button>
        {(skills.data?.skills ?? []).map((entry) => (
          <button
            key={entry.id}
            onClick={() => setSkill(entry.name)}
            className={`rounded-full px-3 py-1.5 text-sm transition ${
              skill === entry.name
                ? "bg-stone-900 text-white"
                : "border border-stone-300 bg-white text-stone-700 hover:bg-stone-50"
            }`}
          >
            {entry.name}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader
          title={`${list.length} workers`}
          subtitle={skill ? `with a verified ${skill} skill` : "all trades"}
        />
        {workers.loading ? (
          <Loading what="Loading workers" />
        ) : list.length === 0 ? (
          <Empty>Nobody has a verified {skill} skill.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-left text-xs uppercase tracking-wide text-stone-500">
                <tr>
                  <th className="px-5 py-2 font-medium">Worker</th>
                  <th className="px-5 py-2 font-medium">Verified skills</th>
                  <th className="px-5 py-2 font-medium">Rating</th>
                  <th className="px-5 py-2 font-medium">Jobs</th>
                  <th className="px-5 py-2 font-medium">Attendance</th>
                  <th className="px-5 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {list.map((worker) => (
                  <tr key={worker.id} className="hover:bg-stone-50">
                    <td className="px-5 py-2.5">
                      <Link
                        href={`/workers/${worker.id}`}
                        className="font-medium text-stone-900 hover:underline"
                      >
                        {worker.name}
                      </Link>
                      <div className="text-xs text-stone-500">
                        {worker.location_name}
                      </div>
                    </td>
                    <td className="px-5 py-2.5 text-stone-700">
                      {worker.verified_skills || (
                        <span className="text-stone-400">none verified</span>
                      )}
                    </td>
                    <td className="px-5 py-2.5">
                      <Rating value={worker.average_rating} />
                    </td>
                    <td className="px-5 py-2.5 tabular-nums text-stone-700">
                      {worker.completed_jobs}
                    </td>
                    <td className="px-5 py-2.5 tabular-nums text-stone-700">
                      {worker.attendance_rate === null
                        ? "—"
                        : `${Number(worker.attendance_rate).toFixed(1)}%`}
                    </td>
                    <td className="px-5 py-2.5">
                      <div className="flex flex-wrap gap-1">
                        <Tag tone={statusTone(worker.availability_status)}>
                          {worker.availability_status}
                        </Tag>
                        <Tag tone={statusTone(worker.verification_status)}>
                          {worker.verification_status}
                        </Tag>
                      </div>
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
