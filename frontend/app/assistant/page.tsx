"use client";

/**
 * Screen 2 — AI Workforce Assistant.
 *
 * The design decision that matters here is what is shown alongside the
 * answer. A chat bubble on its own is not evidence of anything: a language
 * model can write a confident paragraph about eight masons who do not
 * exist.
 *
 * So every reply carries its provenance -- which tools actually ran, and
 * whether the answer is grounded in the database at all. An ungrounded
 * reply is marked as such, in the interface, where a reader will see it.
 * That is business rule 9 made visible rather than promised.
 */

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, ApiError, type ChatReply } from "@/lib/api";
import { Button, Card, CardHeader, ErrorNote, Tag } from "@/components/ui";

type Turn = {
  role: "user" | "model";
  text: string;
  meta?: ChatReply;
};

const SUGGESTIONS = [
  "I need 8 masons tomorrow at 8 AM near Guntur.",
  "Can Ravi's crew handle it?",
  "Is Suresh ready to work independently?",
  "I need 40 electricians in Guntur tomorrow.",
];

export default function Assistant() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, busy]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;

    setError(null);
    setMessage("");
    setTurns((previous) => [...previous, { role: "user", text: question }]);
    setBusy(true);

    try {
      const reply = await api.chat({
        message: question,
        // The whole conversation so far, so "can Ravi's crew handle it?"
        // knows what "it" refers to.
        history: turns.map((turn) => ({ role: turn.role, text: turn.text })),
        session_id: sessionId,
      });

      if (reply.session_id) setSessionId(reply.session_id);
      setTurns((previous) => [
        ...previous,
        { role: "model", text: reply.reply, meta: reply },
      ]);
    } catch (problem) {
      const message =
        problem instanceof ApiError ? problem.message : String(problem);
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-stone-900">
            AI workforce assistant
          </h1>
          <p className="mt-1 text-sm text-stone-600">
            Ask for workforce in plain language.
          </p>
        </div>
        {sessionId && (
          <Link
            href={`/sessions/${sessionId}`}
            className="text-sm text-stone-600 underline decoration-stone-300 underline-offset-2 hover:decoration-stone-600"
          >
            See what the agent did →
          </Link>
        )}
      </div>

      <Card>
        <CardHeader
          title="Conversation"
          right={
            turns.length > 0 ? (
              <Button
                variant="secondary"
                onClick={() => {
                  setTurns([]);
                  setSessionId(null);
                  setError(null);
                }}
              >
                Start again
              </Button>
            ) : undefined
          }
        />

        <div className="max-h-[26rem] min-h-[16rem] space-y-4 overflow-y-auto px-5 py-5">
          {turns.length === 0 && (
            <div className="space-y-3 py-6 text-center">
              <p className="text-sm text-stone-500">
                Try one of these, or type your own:
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => send(suggestion)}
                    className="rounded-full border border-stone-300 bg-white px-3 py-1.5 text-sm text-stone-700 transition hover:border-stone-500 hover:bg-stone-50"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {turns.map((turn, index) =>
            turn.role === "user" ? (
              <div key={index} className="flex justify-end">
                <div className="max-w-[80%] rounded-lg rounded-br-sm bg-stone-900 px-4 py-2.5 text-sm text-white">
                  {turn.text}
                </div>
              </div>
            ) : (
              <div key={index} className="space-y-2">
                <div className="max-w-[90%] rounded-lg rounded-bl-sm border border-stone-200 bg-stone-50 px-4 py-3 text-sm leading-relaxed text-stone-800">
                  <div className="whitespace-pre-wrap">{turn.text}</div>
                </div>
                {turn.meta && <Provenance reply={turn.meta} />}
              </div>
            ),
          )}

          {busy && (
            <div className="flex items-center gap-2 text-sm text-stone-500">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
              Searching the workforce database…
            </div>
          )}

          <div ref={bottom} />
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            send(message);
          }}
          className="flex gap-2 border-t border-stone-200 px-5 py-4"
        >
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="What workforce do you need?"
            disabled={busy}
            className="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-stone-500 disabled:bg-stone-100"
          />
          <Button type="submit" disabled={busy || !message.trim()}>
            {busy ? "Asking…" : "Ask"}
          </Button>
        </form>
      </Card>

      {error && <ErrorNote error={error} />}

      <p className="text-xs text-stone-500">
        The assistant proposes; a person confirms.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */

/**
 * Where this answer came from.
 *
 * "Grounded" means at least one tool ran and returned database records. If
 * nothing ran, the reply is the model talking on its own, and saying so is
 * more useful than hiding it.
 */
function Provenance({ reply }: { reply: ChatReply }) {
  return (
    <div className="flex flex-wrap items-center gap-2 pl-1 text-xs">
      {reply.grounded ? (
        <Tag tone="good">from the database</Tag>
      ) : (
        <Tag tone="warn">no data looked up</Tag>
      )}

      {reply.tools_used.map((tool, index) => (
        <span
          key={index}
          className="rounded bg-stone-100 px-2 py-0.5 font-mono text-[11px] text-stone-700 ring-1 ring-inset ring-stone-200"
          title={JSON.stringify(tool.arguments)}
        >
          {tool.tool}()
        </span>
      ))}

      {reply.cached && <Tag tone="info">cached</Tag>}
      <span className="text-stone-400">{reply.model}</span>
    </div>
  );
}
