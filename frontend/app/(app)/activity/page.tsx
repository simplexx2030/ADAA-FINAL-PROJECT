"use client";

/**
 * AI activity — what the assistant has been doing.
 *
 * Reads the agent_actions table: recent conversations, and how often each
 * tool is used. Every row links to the full trail for that conversation.
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
  Stat,
  Tag,
} from "@/components/ui";

function when(timestamp: string | null | undefined) {
  if (!timestamp) return "—";
  const date = new Date(timestamp);
  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Activity() {
  const sessions = useLoad(() => api.sessions(), []);
  const usage = useLoad(() => api.toolUsage(), []);

  const list = sessions.data?.sessions ?? [];
  const tools = usage.data?.tools ?? [];

  const totalCalls = tools.reduce((sum, tool) => sum + Number(tool.calls), 0);
  const totalFailures = tools.reduce((sum, tool) => sum + Number(tool.failures), 0);
  const busiest = tools[0]?.tool_name;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          AI activity
        </h1>
        <p className="mt-1 text-sm text-dim">
          What the assistant looked up, and when.
        </p>
      </div>

      {(sessions.error || usage.error) && (
        <ErrorNote error={sessions.error || usage.error || ""} />
      )}

      <Card>
        <div className="grid grid-cols-2 gap-6 px-5 py-5 sm:grid-cols-4">
          <Stat
            label="Conversations"
            value={sessions.loading ? "…" : list.length}
          />
          <Stat label="Tool calls" value={usage.loading ? "…" : totalCalls} />
          <Stat
            label="Failures"
            value={usage.loading ? "…" : totalFailures}
            hint={totalFailures === 0 ? "none" : undefined}
          />
          <Stat
            label="Most used"
            value={
              usage.loading ? (
                "…"
              ) : busiest ? (
                <span className="font-mono text-base">{busiest}</span>
              ) : (
                "—"
              )
            }
          />
        </div>
      </Card>

      {/* --- Conversations ------------------------------------------ */}
      <Card>
        <CardHeader title="Recent conversations" />
        {sessions.loading ? (
          <Loading what="Loading activity" />
        ) : list.length === 0 ? (
          <Empty>
            No conversations yet.{" "}
            <Link href="/assistant" className="underline">
              Ask the assistant something
            </Link>
            .
          </Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/[0.04] text-left text-xs uppercase tracking-wide text-dim">
                <tr>
                  <th className="px-5 py-2 font-medium">Session</th>
                  <th className="px-5 py-2 font-medium">Started</th>
                  <th className="px-5 py-2 font-medium">Actions</th>
                  <th className="px-5 py-2 font-medium">Tool calls</th>
                  <th className="px-5 py-2 font-medium">Tools used</th>
                  <th className="px-5 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.07]">
                {list.map((session) => (
                  <tr key={session.session_id} className="hover:bg-white/[0.04]">
                    <td className="px-5 py-2.5 font-mono text-xs text-dim">
                      {session.session_id.slice(0, 12)}
                    </td>
                    <td className="px-5 py-2.5 whitespace-nowrap text-dim">
                      {when(session.started_at)}
                    </td>
                    <td className="px-5 py-2.5 tabular-nums text-bone">
                      {session.actions}
                    </td>
                    <td className="px-5 py-2.5 tabular-nums text-bone">
                      {session.tool_calls}
                    </td>
                    <td className="px-5 py-2.5">
                      <div className="flex flex-wrap gap-1">
                        {(session.tools_used ?? []).slice(0, 3).map((tool) => (
                          <span
                            key={tool}
                            className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[11px] text-bone"
                          >
                            {tool}
                          </span>
                        ))}
                        {(session.tools_used ?? []).length > 3 && (
                          <span className="text-xs text-dim">
                            +{(session.tools_used ?? []).length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-2.5">
                      <div className="flex items-center justify-end gap-3">
                        {session.failures > 0 && <Tag tone="bad">failed</Tag>}
                        <Link
                          href={`/sessions/${session.session_id}`}
                          className="text-sm text-dim underline"
                        >
                          View
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* --- Tool usage --------------------------------------------- */}
      <Card>
        <CardHeader title="Tools" />
        {usage.loading ? (
          <Loading what="Loading tool usage" />
        ) : tools.length === 0 ? (
          <Empty>No tool calls recorded yet.</Empty>
        ) : (
          <ul className="divide-y divide-white/[0.07]">
            {tools.map((tool) => {
              const share = totalCalls
                ? Math.round((Number(tool.calls) / totalCalls) * 100)
                : 0;
              return (
                <li key={tool.tool_name} className="px-5 py-3">
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <span className="font-mono text-bone">
                      {tool.tool_name}
                    </span>
                    <span className="shrink-0 text-dim">
                      {tool.calls} {Number(tool.calls) === 1 ? "call" : "calls"}
                      {tool.average_ms !== null && ` · ${tool.average_ms} ms avg`}
                      {Number(tool.failures) > 0 && (
                        <span className="ml-2 text-rose-700">
                          {tool.failures} failed
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="mt-1.5 h-1.5 overflow-hidden rounded bg-white/10">
                    <div
                      className="h-full rounded bg-molten"
                      style={{ width: `${share}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
