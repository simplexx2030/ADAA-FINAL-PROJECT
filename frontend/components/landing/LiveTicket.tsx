"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/lib/useReducedMotion";
import { Check, Pin, Users } from "@/components/icons";

const WORKERS = [
  { name: "Suresh K.", meta: "6 yrs · 1.9 km" },
  { name: "Ramesh P.", meta: "4 yrs · 3.2 km" },
  { name: "Kishore M.", meta: "2 yrs · 2.7 km" },
  { name: "Anil V.", meta: "8 yrs · 4.5 km" },
  { name: "Praveen R.", meta: "5 yrs · 5.8 km" },
];

const NEEDED = 5;
const TOTAL_STEPS = 9; // 0 reset · 1-5 accepts · 6 confirm · 7-8 hold

/**
 * The signature element: the core loop, played on repeat.
 * A job ticket fills up live — accepts stream in, contractor confirms, crew locked.
 *
 * This is an illustration, not data. Nothing here is fetched, and it must
 * never be mistaken for a real job: the workers are invented.
 */
export function LiveTicket() {
  const reducedMotion = useReducedMotion();
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (reducedMotion) return;
    const id = setInterval(() => setStep((s) => (s + 1) % TOTAL_STEPS), 1200);
    return () => clearInterval(id);
  }, [reducedMotion]);

  // Anyone who asked for less motion gets the end of the story rather than
  // an empty ticket: a confirmed crew, held still.
  const shown = reducedMotion ? 6 : step;
  const accepted = Math.min(shown, NEEDED);
  const confirmed = shown >= 6;
  const status = confirmed ? "CONFIRMED" : accepted > 0 ? "FILLING" : "OPEN";

  return (
    <div className="relative w-full max-w-md">
      {/* molten halo behind the ticket */}
      <div className="absolute -inset-8 rounded-[2.5rem] bg-molten/20 blur-3xl" aria-hidden />

      <div className="glass-bright relative rounded-3xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-te text-sm text-dim">మేస్త్రీలు కావాలి</p>
            <h3 className="mt-0.5 text-2xl font-bold leading-tight text-white">
              {NEEDED} Masons · 7:00 AM
            </h3>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-dim">
              <Pin className="h-3.5 w-3.5 text-molten" />
              Gollapudi, Vijayawada · Tomorrow
            </p>
          </div>
          <span
            key={status}
            className={cn(
              "enter-up rounded-full px-3 py-1 text-xs font-bold tracking-widest",
              confirmed
                ? "bg-jade/20 text-jade"
                : accepted > 0
                  ? "btn-molten text-white"
                  : "bg-white/10 text-bone",
            )}
          >
            {status}
          </span>
        </div>

        {/* fill bar */}
        <div className="mt-5">
          <div className="flex items-center justify-between text-xs font-semibold text-dim">
            <span className="flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5" /> Accepted
            </span>
            <span className="tabular-nums text-bone">
              {accepted} / {NEEDED}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
            <div
              className={cn(
                "h-full rounded-full transition-[width] duration-500 ease-out",
                confirmed ? "bg-jade" : "btn-molten",
              )}
              style={{ width: `${(accepted / NEEDED) * 100}%` }}
            />
          </div>
        </div>

        {/* accepting workers */}
        <ul className="mt-4 space-y-2" aria-live="polite">
          {WORKERS.slice(0, accepted).map((w) => (
            <li
              // Keyed by name, so a row that is already on screen is never
              // re-created — only the newest row runs its slide-in.
              key={w.name}
              className="slide-in flex items-center justify-between rounded-xl bg-white/[0.06] px-3 py-2.5"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-molten/20 text-xs font-bold text-molten-soft">
                  {w.name.split(" ").map((p) => p[0]).join("")}
                </span>
                <div className="leading-tight">
                  <p className="text-sm font-semibold text-white">{w.name}</p>
                  <p className="text-xs text-dim">{w.meta}</p>
                </div>
              </div>
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full transition-colors duration-300",
                  confirmed ? "bg-jade text-ink" : "border border-white/20 text-dim",
                )}
              >
                <Check className="h-3.5 w-3.5" />
              </span>
            </li>
          ))}
        </ul>

        <p className="mt-4 text-center text-xs text-dim">
          {confirmed
            ? "Crew locked. Everyone gets the site pin."
            : "Nearby masons are accepting in real time…"}
        </p>
      </div>
    </div>
  );
}
