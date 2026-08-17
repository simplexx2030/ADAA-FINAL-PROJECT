"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/lib/useReducedMotion";

// H.264 mp4 only, deliberately. Cloudinary CAN transcode to webm on the fly
// (same URL with .webm), and it is ~30-50% smaller — but the on-the-fly
// transcode streams without duration metadata on cold requests (observed:
// video.duration === NaN until fully buffered), which makes `ended` timing
// flaky. For a 5s clip the mp4 is small enough; if bandwidth matters later,
// pre-generate the webm with an eager transformation in Cloudinary and add
// <source src=".webm" type="video/webm"> ABOVE the mp4 source.
const VIDEO_MP4 =
  "https://res.cloudinary.com/dkaccpujn/video/upload/v1783799172/Hero-video_d5inhl.mp4";
const POSTER =
  "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_1600/v1783798007/footer_fg0t0e.jpg";

// The clip is only 5s and plays exactly once — slow it to a cinematic pace so
// the sketch → dawn → sketch transformation has room to breathe. 0.5 ≈ 10s.
// The handoff gradient below (`duration-[9000ms]`) is tuned to this runtime;
// change both together if you retune the rate.
const PLAYBACK_RATE = 0.5;

type Phase = "idle" | "playing" | "ended";

/**
 * Pinned-scroll hero with a play-once background video.
 *
 * Desktop: the section is a 130vh scroll container whose visible 100vh face is
 * position:sticky — the hero pins for ~30vh of scroll while the 5s video plays
 * (sketch → photoreal dawn → sketch), then the next section arrives. Sticky
 * never blocks scroll, so a fast scroller just blows through the buffer and
 * the pin releases naturally. If the video ends while the viewer hasn't
 * scrolled yet, the buffer is dropped (the change happens below the fold, so
 * it's invisible) and their first scroll goes straight to the next section.
 *
 * Playback is triggered once by an IntersectionObserver — never scrubbed by
 * scroll position, which is janky in-browser.
 *
 * Mobile (< lg): no pin, no buffer — the hero is a normal full-height section
 * and the video simply autoplays inline once.
 *
 * prefers-reduced-motion: no video at all; the static sketch poster fades in.
 */
export function VideoHero({ children }: { children: React.ReactNode }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playedRef = useRef(false);
  const [videoPhase, setVideoPhase] = useState<Phase>("idle");
  const [pinBuffer, setPinBuffer] = useState(true);
  const reducedMotion = useReducedMotion();

  // With no video to perform, there is nothing to wait for: settle the
  // overlays, show the content at full opacity, and drop the pin buffer.
  const phase = reducedMotion ? "ended" : videoPhase;
  const buffer = pinBuffer && !reducedMotion;

  useEffect(() => {
    if (reducedMotion) return;
    const video = videoRef.current;
    if (!video) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || playedRef.current) return;
        playedRef.current = true;
        io.disconnect();
        // defaultPlaybackRate survives (re)loads; playbackRate set before
        // metadata is ready gets discarded in some browsers, so we also
        // reassert it on loadedmetadata below.
        video.defaultPlaybackRate = PLAYBACK_RATE;
        video.playbackRate = PLAYBACK_RATE;
        video
          .play()
          .then(() => setVideoPhase("playing"))
          // Autoplay blocked → poster keeps showing; settle into end state.
          .catch(() => setVideoPhase("ended"));
      },
      { threshold: 0.3 },
    );
    io.observe(video);

    // Reassert the slow rate once metadata is in — a rate set before this
    // fires is silently dropped by some browsers, which plays the clip at
    // full speed. If metadata is already loaded, apply immediately.
    const applyRate = () => {
      video.defaultPlaybackRate = PLAYBACK_RATE;
      video.playbackRate = PLAYBACK_RATE;
    };
    if (video.readyState >= 1) applyRate();
    video.addEventListener("loadedmetadata", applyRate);

    return () => {
      io.disconnect();
      video.removeEventListener("loadedmetadata", applyRate);
    };
  }, [reducedMotion]);

  // Browsers pause ambient video in plenty of situations (tab backgrounded,
  // low-power mode, data saver). If the performance was interrupted mid-play,
  // resume quietly; if it can't resume, settle into the end state so the
  // overlays and content aren't left half-dimmed.
  useEffect(() => {
    if (reducedMotion) return;
    const video = videoRef.current;
    if (!video) return;
    const resume = () => {
      if (
        playedRef.current &&
        video.paused &&
        !video.ended &&
        document.visibilityState === "visible"
      ) {
        video.playbackRate = PLAYBACK_RATE; // some resumes reset it to 1
        video.play().catch(() => setVideoPhase("ended"));
      }
    };
    const onPause = () => {
      // Natural end also fires `pause` — by the time this runs, `ended` is
      // set and the guard inside resume() lets it through untouched.
      setTimeout(resume, 250);
    };
    video.addEventListener("pause", onPause);
    document.addEventListener("visibilitychange", resume);
    // Watchdog: if the video stalls and never ends, settle the overlays
    // anyway rather than leaving the hero half-dimmed forever.
    const watchdog = setTimeout(() => {
      if (!video.ended) setVideoPhase((p) => (p === "playing" ? "ended" : p));
    }, 15_000);
    return () => {
      video.removeEventListener("pause", onPause);
      document.removeEventListener("visibilitychange", resume);
      clearTimeout(watchdog);
    };
  }, [reducedMotion]);

  function handleEnded() {
    setVideoPhase("ended");
    // Viewer watched to the end without entering the buffer zone: drop the
    // buffer so the pin is already released when they do scroll. scrollY is
    // still near 0, so the removed 30vh sits entirely below the fold —
    // no visible jump.
    if (window.scrollY < window.innerHeight * 0.15) setPinBuffer(false);
  }

  return (
    <section className={cn("relative", buffer && "lg:h-[130vh]")}>
      <div className="relative flex min-h-[100svh] flex-col justify-center overflow-hidden lg:sticky lg:top-0 lg:h-screen">
        {/* media layer */}
        {reducedMotion ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={POSTER}
            alt=""
            className="absolute inset-0 h-full w-full animate-[fadeIn_0.8s_ease-out] object-cover"
          />
        ) : (
          <video
            ref={videoRef}
            muted
            playsInline
            preload="auto"
            poster={POSTER}
            onEnded={handleEnded}
            disablePictureInPicture
            aria-hidden
            className="absolute inset-0 h-full w-full object-cover"
          >
            <source src={VIDEO_MP4} type="video/mp4" />
          </video>
        )}

        {/* legibility scrim — constant */}
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-b from-ink/70 via-ink/45 to-ink/60"
        />

        {/* handoff gradient — deepens over ~the video's runtime while playing */}
        <div
          aria-hidden
          className={cn(
            "absolute inset-x-0 bottom-0 h-[45%] bg-gradient-to-t from-ink to-transparent transition-opacity duration-[9000ms] ease-linear",
            phase === "idle" ? "opacity-40" : "opacity-100",
          )}
        />

        {/* content — dims slightly while the video performs, returns on end */}
        <div
          className={cn(
            "relative z-10 w-full transition-opacity duration-1000",
            phase === "playing" ? "opacity-[0.85]" : "opacity-100",
          )}
        >
          {children}
        </div>
      </div>
    </section>
  );
}
