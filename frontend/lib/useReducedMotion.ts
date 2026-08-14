"use client";

import { useSyncExternalStore } from "react";

/**
 * Has the reader asked their system for less motion?
 *
 * A media query is an external store, so it is read with
 * `useSyncExternalStore` rather than an effect. That matters for two reasons:
 * the value is available during the first client render (so nothing has to
 * flash and then correct itself), and the server is given an explicit
 * snapshot instead of guessing.
 *
 * The server snapshot is `false` — the honest answer, because the server
 * cannot know. React re-renders with the real value the moment it hydrates.
 */
const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(onChange: () => void) {
  const list = window.matchMedia(QUERY);
  list.addEventListener("change", onChange);
  return () => list.removeEventListener("change", onChange);
}

export function useReducedMotion() {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(QUERY).matches,
    () => false,
  );
}
