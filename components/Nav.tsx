"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/assistant", label: "AI Assistant" },
  { href: "/activity", label: "AI Activity" },
  { href: "/crews", label: "Crews" },
  { href: "/workers", label: "Workers" },
];

/**
 * The top bar, and the health indicator.
 *
 * The indicator is not decoration. During a demonstration the most likely
 * failure is that the backend is not running or the database is asleep,
 * and it is far better to see that in the corner of the screen than to
 * discover it when a page comes back empty.
 */
export function Nav() {
  const pathname = usePathname();
  const [health, setHealth] = useState<"checking" | "ok" | "down">("checking");
  const [workers, setWorkers] = useState<number | null>(null);

  useEffect(() => {
    api
      .databaseHealth()
      .then((result) => {
        setHealth("ok");
        setWorkers(result.workers);
      })
      .catch(() => setHealth("down"));
  }, []);

  return (
    <header className="border-b border-white/[0.07] bg-deep">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-lg font-bold tracking-tight text-white">ADAA</span>
          <span className="hidden text-xs text-dim sm:inline">
            Workforce Coordination
          </span>
        </Link>

        <nav className="flex flex-1 flex-wrap gap-1">
          {LINKS.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 text-sm transition ${
                  active
                    ? "btn-molten text-white"
                    : "text-dim hover:bg-white/10 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              health === "ok"
                ? "bg-jade"
                : health === "down"
                  ? "bg-rose-500"
                  : "bg-white/25"
            }`}
          />
          <span className="text-dim">
            {health === "ok" && `connected · ${workers} workers`}
            {health === "down" && "backend not reachable"}
            {health === "checking" && "checking…"}
          </span>
        </div>
      </div>
    </header>
  );
}
