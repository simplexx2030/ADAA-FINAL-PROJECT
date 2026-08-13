/**
 * The small pieces every screen is built from.
 *
 * Kept deliberately plain. There is no component library, no design system
 * and no state management -- a card is a div with a border. That is enough
 * for a prototype, and it means the whole interface can be read without
 * learning anything first.
 */

import Link from "next/link";
import type { ReactNode } from "react";

/* ------------------------------------------------------------------ */

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-lg border border-stone-200 bg-white shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  right,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-stone-200 px-5 py-4">
      <div>
        <h2 className="text-base font-semibold text-stone-900">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-stone-500">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

/* ------------------------------------------------------------------ */

/**
 * A short coloured label. Used for availability, verification and job
 * status, which are the three things a reader scans for first.
 */
export function Tag({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "good" | "warn" | "bad" | "info" | "neutral";
}) {
  const tones = {
    good: "bg-emerald-50 text-emerald-800 ring-emerald-200",
    warn: "bg-amber-50 text-amber-800 ring-amber-200",
    bad: "bg-rose-50 text-rose-800 ring-rose-200",
    info: "bg-sky-50 text-sky-800 ring-sky-200",
    neutral: "bg-stone-100 text-stone-700 ring-stone-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

/** Pick a colour for a status word without repeating the mapping everywhere. */
export function statusTone(status: string | null | undefined) {
  switch (status) {
    case "available":
    case "verified":
    case "completed":
    case "confirmed":
    case "accepted":
      return "good" as const;
    case "busy":
    case "booked":
    case "pending":
    case "offered":
    case "open":
      return "warn" as const;
    case "unavailable":
    case "unverified":
    case "declined":
    case "no_show":
    case "cancelled":
    case "failed":
      return "bad" as const;
    default:
      return "neutral" as const;
  }
}

/* ------------------------------------------------------------------ */

/** One number with a label. The building block of every summary row. */
export function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-stone-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-stone-900">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-stone-500">{hint}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */

export function Button({
  children,
  onClick,
  type = "button",
  variant = "primary",
  disabled,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  className?: string;
}) {
  const variants = {
    primary: "bg-stone-900 text-white hover:bg-stone-700 disabled:bg-stone-400",
    secondary:
      "bg-white text-stone-800 ring-1 ring-inset ring-stone-300 hover:bg-stone-50 disabled:text-stone-400",
    danger: "bg-rose-600 text-white hover:bg-rose-700 disabled:bg-rose-300",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ */

export function Loading({ what = "Loading" }: { what?: string }) {
  return (
    <div className="flex items-center gap-2 px-5 py-8 text-sm text-stone-500">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
      {what}…
    </div>
  );
}

/**
 * Something went wrong, said plainly.
 *
 * Nearly always this is "the backend is not running", so the message from
 * the API client already explains what to do about it.
 */
export function ErrorNote({ error }: { error: string }) {
  return (
    <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
      <div className="font-medium">Something went wrong</div>
      <div className="mt-1 whitespace-pre-wrap text-rose-800">{error}</div>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="px-5 py-8 text-center text-sm text-stone-500">{children}</div>;
}

/* ------------------------------------------------------------------ */

/**
 * A rating shown as a number rather than as stars.
 *
 * Stars flatter. A contractor deciding whether to send someone to a site
 * is better served by "4.7 from 31 jobs" than by five little shapes, and
 * the count matters as much as the average.
 */
export function Rating({
  value,
  count,
}: {
  value: number | string | null;
  count?: number;
}) {
  if (value === null || value === undefined)
    return <span className="text-stone-400">no rating yet</span>;
  return (
    <span className="tabular-nums">
      <span className="font-semibold">{Number(value).toFixed(2)}</span>
      <span className="text-stone-400"> / 5</span>
      {count !== undefined && (
        <span className="ml-1 text-xs text-stone-500">
          from {count} {count === 1 ? "rating" : "ratings"}
        </span>
      )}
    </span>
  );
}

export function WorkerLink({ id, name }: { id: string; name: string }) {
  return (
    <Link href={`/workers/${id}`} className="font-medium text-stone-900 underline decoration-stone-300 underline-offset-2 hover:decoration-stone-600">
      {name}
    </Link>
  );
}

export function CrewLink({ id, name }: { id: string; name: string }) {
  return (
    <Link href={`/crews/${id}`} className="font-medium text-stone-900 underline decoration-stone-300 underline-offset-2 hover:decoration-stone-600">
      {name}
    </Link>
  );
}
