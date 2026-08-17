"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Activity,
  Briefcase,
  Chat,
  HardHat,
  Home,
  Layers,
  Users,
} from "@/components/icons";

const LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/assistant", label: "AI Assistant", icon: Chat },
  { href: "/contractor", label: "Contractor", icon: Briefcase },
  { href: "/workers", label: "Workers", icon: Users },
  { href: "/crews", label: "Crews", icon: Layers },
  { href: "/jobs", label: "Jobs", icon: HardHat },
  { href: "/activity", label: "AI Activity", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const [model, setModel] = useState<string | null>(null);
  const [reachable, setReachable] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .status()
      .then((status) => {
        setModel(status.gemini_model);
        setReachable(true);
      })
      .catch(() => setReachable(false));
  }, []);

  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-60 flex-col border-r border-white/[0.07] bg-deep lg:flex">
      {/* The logo goes home to the landing page, not to the dashboard —
          the dashboard has its own entry in the list below. */}
      <Link href="/" className="flex items-center gap-3 px-5 py-5">
        <Image src="/adaa-logo.png" alt="" width={44} height={44} className="rounded-xl" />
        <span>
          <span className="block text-lg font-bold leading-tight text-white">ADAA</span>
          <span className="block text-xs text-dim">Workforce Agent</span>
        </span>
      </Link>

      <div className="mx-5 border-t border-white/[0.07]" />

      <nav className="flex-1 space-y-1 px-3 py-4">
        {LINKS.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                active
                  ? "btn-molten font-semibold text-white shadow-[0_4px_16px_rgba(255,122,26,0.25)]"
                  : "text-dim hover:bg-white/[0.06] hover:text-bone"
              }`}
            >
              <Icon className="h-[18px] w-[18px]" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/[0.07] px-5 py-4 text-xs">
        {reachable === false ? (
          <span className="text-rose-300">Backend not reachable</span>
        ) : (
          <span className="text-dim">Powered by {model ?? "Gemini"}</span>
        )}
      </div>
    </aside>
  );
}

/** The same navigation, as a scrolling strip, for narrow screens. */
export function MobileNav() {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-20 border-b border-white/[0.07] bg-deep lg:hidden">
      <div className="flex items-center gap-2 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/adaa-logo.png" alt="" width={36} height={36} className="rounded-lg" />
          <span className="text-base font-bold text-white">ADAA</span>
        </Link>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3">
        {LINKS.map(({ href, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${
                active
                  ? "btn-molten font-medium text-white"
                  : "text-dim hover:bg-white/[0.06] hover:text-bone"
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
