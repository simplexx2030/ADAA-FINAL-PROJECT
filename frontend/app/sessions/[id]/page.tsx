"use client";

/**
 * What the agent actually did.
 *
 * This screen exists because "the agent uses real data" is a claim, and a
 * claim is worth less than a record. Every tool call is listed with the
 * arguments the agent chose and how long it took, straight from the
 * agent_actions table.
 */

import { use } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import { Card, CardHeader, Empty, ErrorNote, Loading, Tag } from "@/components/ui";

export default function SessionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, loading, error } = useLoad(() => api.sessionTrail(id), [id]);

  return (
    <div className="space-y-6">
      <div>
        <Link href="/assistant" className="text-sm text-stone-500 hover:underline">
          ← Back to the assistant
        </Link>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-stone-900">
          What the agent did
        </h1>
        <p className="mt-1 font-mono text-xs text-stone-500">session {id}</p>
      </div>

      {error && <ErrorNote error={error} />}

      <Card>
        <CardHeader
          title="Action trail"
          subtitle="Every tool call, in order, with the arguments the agent chose"
        />
        {loading ? (
          <Loading what="Loading the trail" />
        ) : !data || data.actions.length === 0 ? (
          <Empty>Nothing recorded for this session yet.</Empty>
        ) : (
          <ul className="divide-y divide-stone-100">
            {data.actions.map((action) => (
              <li key={action.id} className="flex flex-wrap items-start gap-3 px-5 py-3">
                <div className="w-28 shrink-0">
                  {action.tool_name ? (
                    <Tag tone="info">tool</Tag>
                  ) : (
                    <Tag tone="neutral">{action.action_type}</Tag>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  {action.tool_name && (
                    <div className="font-mono text-sm text-stone-900">
                      {action.tool_name}()
                    </div>
                  )}
                  <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-words text-xs text-stone-600">
                    {JSON.stringify(action.input, null, 0)}
                  </pre>
                </div>

                <div className="shrink-0 text-right text-xs text-stone-500">
                  <div>{action.duration_ms ?? "—"} ms</div>
                  <div>{action.success ? "ok" : "failed"}</div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <p className="text-xs text-stone-500">
        Recorded in the <code className="font-mono">agent_actions</code> table. This is
        the evidence behind every name the assistant mentioned.
      </p>
    </div>
  );
}
