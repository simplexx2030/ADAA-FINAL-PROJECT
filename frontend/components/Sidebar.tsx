"use client";

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
  { href: "/", label: "Dashboard", icon: Home },
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
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-60 flex-col border-r border-slate-200 bg-white lg:flex">
      <Link href="/" className="flex items-center gap-3 px-5 py-5">
        <span className="brand-gradient flex h-11 w-11 items-center justify-center rounded-xl text-white shadow-sm">
          <HardHat className="h-6 w-6" />
        </span>
        <span>
          <span className="block text-lg font-bold leading-tight text-slate-900">
            ADAA
          </span>
          <span className="block text-xs text-slate-500">Workforce Agent</span>
        </span>
      </Link>

      <div className="mx-5 border-t border-slate-200" />

      <nav className="flex-1 space-y-1 px-3 py-4">
        {LINKS.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                active
                  ? "bg-slate-900 font-semibold text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <Icon className="h-[18px] w-[18px]" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 px-5 py-4 text-xs">
        {reachable === false ? (
          <span className="text-rose-600">Backend not reachable</span>
        ) : (
          <span className="text-slate-400">
            Powered by {model ?? "Gemini"}
          </span>
        )}
      </div>
    </aside>
  );
}

/** The same navigation, as a scrolling strip, for narrow screens. */
export function MobileNav() {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-20 border-b border-slate-200 bg-white lg:hidden">
      <div className="flex items-center gap-2 px-4 py-3">
        <span className="brand-gradient flex h-9 w-9 items-center justify-center rounded-lg text-white">
          <HardHat className="h-5 w-5" />
        </span>
        <span className="text-base font-bold text-slate-900">ADAA</span>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3">
        {LINKS.map(({ href, label }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${
                active
                  ? "bg-slate-900 font-medium text-white"
                  : "text-slate-600 hover:bg-slate-100"
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
