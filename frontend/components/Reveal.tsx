"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/lib/useReducedMotion";

/**
 * Fade-and-rise a section into view the first time it is scrolled to.
 *
 * The whole animation is CSS (`.reveal` / `.revealed` in globals.css); this
 * component only decides *when*. That keeps it to one IntersectionObserver
 * per section and no animation library.
 *
 * `delay` staggers the members of a grid — pass `i * 0.12` and the cards
 * arrive one after another.
 */
export function Reveal({
  children,
  delay = 0,
  className,
  as: Tag = "div",
}: {
  children: React.ReactNode;
  /** Seconds to wait after the element enters the viewport. */
  delay?: number;
  className?: string;
  as?: "div" | "section" | "li";
}) {
  const ref = useRef<HTMLElement>(null);
  const [seen, setSeen] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion) return;
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        // Fires once on observe with the element's current state, so anything
        // already on screen at load is revealed straight away.
        if (!entry.isIntersecting) return;
        setSeen(true);
        observer.disconnect(); // once only — this is an entrance, not a toggle
      },
      // Trigger a little before the element is fully in view, so the movement
      // is finishing rather than starting as the reader reaches it.
      { threshold: 0.15, rootMargin: "0px 0px -80px 0px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [reducedMotion]);

  return (
    <Tag
      ref={ref as React.Ref<HTMLDivElement & HTMLLIElement>}
      className={cn("reveal", (seen || reducedMotion) && "revealed", className)}
      style={delay ? ({ "--reveal-delay": `${delay}s` } as React.CSSProperties) : undefined}
    >
      {children}
    </Tag>
  );
}
