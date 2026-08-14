import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight, Person, Star } from "@/components/icons";

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
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm text-slate-500">{subtitle}</p>}
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
  return (
    <div className={`rounded-xl border border-slate-200 bg-white ${className}`}>
      {children}
    </div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 text-lg font-bold text-slate-900">{children}</h2>
  );
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
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
      <div>
        <h2 className="font-bold text-slate-900">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stats                                                               */
/* ------------------------------------------------------------------ */

const ICON_TONES = {
  blue: "bg-blue-600",
  green: "bg-emerald-600",
  orange: "bg-orange-500",
  purple: "bg-fuchsia-600",
  slate: "bg-slate-700",
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
      <div className="text-2xl font-bold tabular-nums text-slate-900">{value}</div>
      <div className="mt-0.5 text-sm text-slate-500">{label}</div>
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
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold tabular-nums text-slate-900">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Badges                                                              */
/* ------------------------------------------------------------------ */

const TONES = {
  green: "bg-emerald-50 text-emerald-700",
  blue: "bg-blue-50 text-blue-700",
  purple: "bg-purple-50 text-purple-700",
  amber: "bg-amber-50 text-amber-700",
  rose: "bg-rose-50 text-rose-700",
  slate: "bg-slate-100 text-slate-600",
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
      "brand-gradient text-white shadow-sm hover:opacity-95 disabled:opacity-50",
    secondary:
      "bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 disabled:text-slate-400",
    ghost: "text-slate-600 hover:bg-slate-100",
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
          ? "bg-slate-900 text-white"
          : "border border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
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
    <div className="flex items-center justify-center gap-2 py-14 text-sm text-slate-500">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-200 border-t-slate-500" />
      {what}…
    </div>
  );
}

export function ErrorNote({ error }: { error: string }) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-900">
      <div className="font-semibold">Something went wrong</div>
      <div className="mt-1 whitespace-pre-wrap text-rose-800">{error}</div>
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
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-300 px-6 py-16 text-center">
      {icon && <span className="text-slate-300">{icon}</span>}
      <p className="text-sm text-slate-500">{children}</p>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="px-5 py-10 text-center text-sm text-slate-500">{children}</div>;
}

/* ------------------------------------------------------------------ */
/* Bits and pieces                                                     */
/* ------------------------------------------------------------------ */

export function Avatar({ name }: { name: string }) {
  return (
    <span
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-400"
      title={name}
    >
      <Person className="h-5 w-5" />
    </span>
  );
}

/** A rating shown as a number with a star, as on the cards. */
export function RatingValue({ value }: { value: number | string | null }) {
  if (value === null || value === undefined)
    return <span className="text-slate-400">—</span>;
  return (
    <span className="inline-flex items-center gap-1 font-bold tabular-nums text-slate-900">
      <Star className="h-3.5 w-3.5 text-amber-400" />
      {Number(value).toFixed(1)}
    </span>
  );
}

/** Rating out of five, for the detail screens where precision matters. */
export function Rating({ value, count }: { value: number | string | null; count?: number }) {
  if (value === null || value === undefined)
    return <span className="text-slate-400">no rating yet</span>;
  return (
    <span className="tabular-nums">
      <span className="font-semibold">{Number(value).toFixed(2)}</span>
      <span className="text-slate-400"> / 5</span>
      {count !== undefined && (
        <span className="ml-1 text-xs text-slate-500">
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
          <div className="text-sm font-bold text-slate-900">{item.value}</div>
          <div className="text-xs text-slate-500">{item.label}</div>
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
      className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 hover:text-orange-700"
    >
      {children}
      <ArrowRight className="h-4 w-4" />
    </Link>
  );
}
