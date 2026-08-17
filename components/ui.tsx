import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight, Person, Star } from "@/components/icons";

/*
 * The pieces every screen is built from.
 *
 * Almost all of the interface's colour lives in this file. The detail screens
 * contain none of their own, so restyling ADAA means restyling this.
 *
 * The palette is defined in `app/globals.css`: ink ground, glass panels,
 * molten accent, jade for anything confirmed.
 */

/* ------------------------------------------------------------------ */
/* Layout                                                              */
/* ------------------------------------------------------------------ */

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm text-dim">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`glass rounded-2xl ${className}`}>{children}</div>;
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-3 text-lg font-bold text-white">{children}</h2>;
}

/** The heading strip inside a card, used by the detail screens. */
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
    <div className="flex items-start justify-between gap-4 border-b border-white/[0.07] px-5 py-4">
      <div>
        <h2 className="font-bold text-white">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-dim">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stats                                                               */
/* ------------------------------------------------------------------ */

const ICON_TONES = {
  blue: "bg-indigo-500/90",
  green: "bg-jade/90 text-ink",
  orange: "btn-molten",
  purple: "bg-fuchsia-500/90",
  slate: "bg-white/10",
};

/** One of the four figures across the top of the dashboard. */
export function StatCard({
  value,
  label,
  icon,
  tone = "blue",
}: {
  value: ReactNode;
  label: string;
  icon: ReactNode;
  tone?: keyof typeof ICON_TONES;
}) {
  return (
    <Card className="px-5 py-5">
      <span
        className={`mb-4 flex h-10 w-10 items-center justify-center rounded-lg text-white ${ICON_TONES[tone]}`}
      >
        {icon}
      </span>
      <div className="text-2xl font-bold tabular-nums text-white">{value}</div>
      <div className="mt-0.5 text-sm text-dim">{label}</div>
    </Card>
  );
}

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
      <div className="text-xs uppercase tracking-wide text-dim">{label}</div>
      <div className="mt-1 text-2xl font-bold tabular-nums text-white">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-dim">{hint}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Badges                                                              */
/* ------------------------------------------------------------------ */

const TONES = {
  green: "bg-jade/15 text-jade",
  blue: "bg-indigo-400/15 text-indigo-300",
  purple: "bg-fuchsia-400/15 text-fuchsia-300",
  amber: "bg-molten/15 text-molten-soft",
  rose: "bg-rose-500/15 text-rose-300",
  slate: "bg-white/10 text-dim",
};

export function Badge({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: keyof typeof TONES;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${TONES[tone]}`}
    >
      {children}
    </span>
  );
}

/**
 * The older name for Badge, kept because the detail screens use it and the
 * two are the same thing. The tone names differ, so they are mapped here.
 */
export function Tag({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "good" | "warn" | "bad" | "info" | "neutral" | keyof typeof TONES;
}) {
  const mapped: Record<string, keyof typeof TONES> = {
    good: "green",
    warn: "amber",
    bad: "rose",
    info: "blue",
    neutral: "slate",
  };
  return <Badge tone={mapped[tone] ?? (tone as keyof typeof TONES)}>{children}</Badge>;
}

export function statusTone(status: string | null | undefined): keyof typeof TONES {
  switch (status) {
    case "available":
    case "verified":
    case "completed":
    case "confirmed":
    case "accepted":
      return "green";
    case "busy":
    case "booked":
    case "pending":
    case "offered":
    case "open":
      return "amber";
    case "unavailable":
    case "unverified":
    case "declined":
    case "no_show":
    case "cancelled":
    case "failed":
      return "rose";
    default:
      return "slate";
  }
}

/** Crew Leader, Crew Member, Independent or Subcontractor. */
export function RoleBadge({
  role,
  crewName,
}: {
  role: string | null | undefined;
  crewName?: string | null;
}) {
  if (!crewName) return <Badge tone="green">Independent</Badge>;
  if (role === "leader") return <Badge tone="blue">Crew Leader</Badge>;
  return <Badge tone="slate">Crew Member</Badge>;
}

/* ------------------------------------------------------------------ */
/* Controls                                                            */
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
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
  className?: string;
}) {
  const variants = {
    primary:
      "btn-molten text-white shadow-[0_4px_20px_rgba(255,122,26,0.3)] hover:brightness-110 disabled:opacity-50",
    secondary: "glass-bright text-bone hover:bg-white/[0.14] disabled:text-dim",
    ghost: "text-dim hover:bg-white/10 hover:text-bone",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function FilterPill({
  children,
  active,
  onClick,
}: {
  children: ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition ${
        active
          ? "btn-molten text-white"
          : "border border-white/10 bg-white/[0.04] text-dim hover:bg-white/[0.09] hover:text-bone"
      }`}
    >
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* States                                                              */
/* ------------------------------------------------------------------ */

export function Loading({ what = "Loading" }: { what?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-14 text-sm text-dim">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/15 border-t-molten" />
      {what}…
    </div>
  );
}

export function ErrorNote({ error }: { error: string }) {
  return (
    <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-100">
      <div className="font-semibold text-rose-200">Something went wrong</div>
      <div className="mt-1 whitespace-pre-wrap text-rose-100/90">{error}</div>
    </div>
  );
}

/** The dashed empty panel used when a list has nothing in it. */
export function EmptyPanel({
  icon,
  children,
}: {
  icon?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-white/15 px-6 py-16 text-center">
      {icon && <span className="text-white/20">{icon}</span>}
      <p className="text-sm text-dim">{children}</p>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="px-5 py-10 text-center text-sm text-dim">{children}</div>;
}

/* ------------------------------------------------------------------ */
/* Bits and pieces                                                     */
/* ------------------------------------------------------------------ */

export function Avatar({ name }: { name: string }) {
  return (
    <span
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/[0.08] text-dim"
      title={name}
    >
      <Person className="h-5 w-5" />
    </span>
  );
}

/** A rating shown as a number with a star, as on the cards. */
export function RatingValue({ value }: { value: number | string | null }) {
  if (value === null || value === undefined) return <span className="text-dim">—</span>;
  return (
    <span className="inline-flex items-center gap-1 font-bold tabular-nums text-white">
      <Star className="h-3.5 w-3.5 text-molten-soft" />
      {Number(value).toFixed(1)}
    </span>
  );
}

/** Rating out of five, for the detail screens where precision matters. */
export function Rating({ value, count }: { value: number | string | null; count?: number }) {
  if (value === null || value === undefined)
    return <span className="text-dim">no rating yet</span>;
  return (
    <span className="tabular-nums">
      <span className="font-semibold text-white">{Number(value).toFixed(2)}</span>
      <span className="text-dim"> / 5</span>
      {count !== undefined && (
        <span className="ml-1 text-xs text-dim">
          from {count} {count === 1 ? "rating" : "ratings"}
        </span>
      )}
    </span>
  );
}

/** A row of small figures under a card heading: value on top, label below. */
export function MiniStats({
  items,
}: {
  items: { value: ReactNode; label: string }[];
}) {
  return (
    <div className="grid grid-cols-3 gap-2 text-center">
      {items.map((item) => (
        <div key={item.label}>
          <div className="text-sm font-bold text-white">{item.value}</div>
          <div className="text-xs text-dim">{item.label}</div>
        </div>
      ))}
    </div>
  );
}

export function CardLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-2 text-sm font-semibold text-molten transition hover:text-molten-soft"
    >
      {children}
      <ArrowRight className="h-4 w-4" />
    </Link>
  );
}
