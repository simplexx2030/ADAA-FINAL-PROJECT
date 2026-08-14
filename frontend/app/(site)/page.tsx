import Image from "next/image";
import Link from "next/link";
import { Reveal } from "@/components/Reveal";
import { LiveTicket } from "@/components/landing/LiveTicket";
import { VideoHero } from "@/components/landing/VideoHero";
import {
  ArrowRight,
  CheckCircle,
  ClipboardList,
  MessagesSquare,
  PhoneMissed,
  Radar,
  UserX,
} from "@/components/icons";

/*
 * The front door.
 *
 * This page fetches nothing. It is the only page in the interface that does
 * not talk to the backend, which is why it still renders perfectly when the
 * backend is down — and why it is a server component.
 *
 * Motion is CSS: `Reveal` for scroll entrances, `.enter-up` for the hero,
 * and the two client components (`VideoHero`, `LiveTicket`) for the pieces
 * that genuinely need state.
 */

export default function Landing() {
  return (
    // overflow-clip (not hidden): an overflow-hidden ancestor becomes the
    // scroll container for position:sticky and silently kills the hero pin
    <main className="relative overflow-clip bg-ink text-bone">
      {/* ambient mesh */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 top-[-10%] h-[34rem] w-[34rem] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute right-[-15%] top-[35%] h-[30rem] w-[30rem] rounded-full bg-molten/[0.13] blur-[120px]" />
        <div className="absolute bottom-[-20%] left-[20%] h-[28rem] w-[28rem] rounded-full bg-orange-500/10 blur-[130px]" />
        <div className="blueprint absolute inset-0" />
      </div>

      {/* nav */}
      <header className="fixed inset-x-0 top-0 z-50 px-4 pt-4">
        <div className="glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-4 py-3 sm:px-6">
          <Image src="/adaa-logo.png" alt="ADAA" width={48} height={48} className="rounded-xl" />
          <Link
            href="/dashboard"
            className="btn-molten rounded-xl px-4 py-2.5 text-sm font-bold text-white shadow-[0_4px_20px_rgba(255,122,26,0.35)] transition hover:brightness-110"
          >
            Open ADAA
          </Link>
        </div>
      </header>

      {/* hero — pinned scroll, play-once background video */}
      <VideoHero>
        <div className="relative mx-auto flex max-w-6xl flex-col items-center gap-14 px-4 pb-16 pt-32 sm:px-6 lg:flex-row lg:items-center lg:gap-10 lg:pb-10 lg:pt-28">
          <div className="max-w-xl text-center lg:text-left">
            <p className="enter-up font-te text-sm font-semibold tracking-wide text-molten-soft">
              నిర్మాణ కార్మికుల నెట్‌వర్క్ · ఆంధ్రప్రదేశ్
            </p>
            <h1
              className="enter-up mt-4 text-balance text-5xl font-extrabold leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl"
              style={{ "--enter-delay": "0.08s" } as React.CSSProperties}
            >
              Eight masons on site <span className="molten-text">by 7 AM.</span>
            </h1>
            <p
              className="enter-up mt-6 text-lg leading-relaxed text-dim sm:text-xl"
              style={{ "--enter-delay": "0.18s" } as React.CSSProperties}
            >
              Post a job tonight. Skilled workers nearby see it instantly, accept in
              minutes, and your crew is confirmed before dinner. No call chains, no
              middlemen, no no-shows.
            </p>
            <div
              className="enter-up mt-9 flex flex-col items-center gap-3 sm:flex-row lg:justify-start"
              style={{ "--enter-delay": "0.28s" } as React.CSSProperties}
            >
              <Link
                href="/contractor"
                className="btn-molten group flex h-14 w-full items-center justify-center gap-2 rounded-2xl px-8 text-lg font-bold text-white shadow-[0_6px_30px_rgba(255,122,26,0.4)] transition hover:brightness-110 sm:w-auto"
              >
                Post a job
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="/workers"
                className="glass-bright flex h-14 w-full items-center justify-center rounded-2xl px-8 text-lg font-bold text-bone transition hover:bg-white/[0.14] sm:w-auto"
              >
                Find work <span className="font-te ml-2 text-base text-dim">పని వెతకండి</span>
              </Link>
            </div>
          </div>

          <div
            className="enter-up flex w-full justify-center lg:w-auto"
            style={{ "--enter-delay": "0.35s" } as React.CSSProperties}
          >
            <LiveTicket />
          </div>
        </div>
      </VideoHero>

      {/* problem — rises to meet the hero as the pin releases */}
      <section className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Reveal>
          <p className="text-xs font-bold tracking-[0.3em] text-molten">THE OLD WAY</p>
          <h2 className="mt-3 max-w-2xl text-balance text-4xl font-extrabold leading-tight sm:text-5xl">
            Hiring still runs on missed calls.
          </h2>
        </Reveal>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {[
            {
              icon: PhoneMissed,
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798104/call-chain_jmiugq.png",
              title: "The 5 AM call chain",
              body: "Fourteen calls before sunrise. Three answered. One showed up. The slab pour waits for no one.",
            },
            {
              icon: MessagesSquare,
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798106/whatsapp-routte_ertv0b.png",
              title: "WhatsApp roulette",
              body: "“Need 5 masons URGENT” forwarded to eleven groups. Strangers reply. No history, no guarantee.",
            },
            {
              icon: UserX,
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798105/middleman-cut_ph0v23.png",
              title: "The middleman cut",
              body: "A labour leader promises a crew, takes his share from every wage, and owns your schedule.",
            },
          ].map((c, i) => (
            <Reveal
              key={c.title}
              delay={i * 0.12}
              className="glass group overflow-hidden rounded-3xl transition-all duration-300 hover:-translate-y-1 hover:bg-white/[0.08]"
            >
              {/* photo banner — the molten icon rides it as a floating badge.
                  Base image is nudged in (scale-110) so hover can zoom OUT to
                  full frame without ever exposing edge gaps. */}
              <div className="relative h-64 overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={c.img}
                  alt=""
                  loading="lazy"
                  className="h-full w-full scale-110 object-cover transition-transform duration-500 ease-out group-hover:scale-100"
                />
                <div
                  aria-hidden
                  className="absolute inset-0 bg-gradient-to-t from-ink via-ink/10 to-transparent"
                />
                <span className="absolute bottom-3 left-4 flex h-11 w-11 items-center justify-center rounded-xl bg-ink/70 ring-1 ring-white/15 backdrop-blur-sm">
                  <c.icon className="h-6 w-6 text-molten" />
                </span>
              </div>
              <div className="p-7 pt-5">
                <h3 className="text-xl font-bold text-white">{c.title}</h3>
                <p className="mt-2.5 leading-relaxed text-dim">{c.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* solution */}
      <section className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Reveal className="text-center">
          <p className="text-xs font-bold tracking-[0.3em] text-molten">THE ADAA WAY</p>
          <h2 className="mx-auto mt-3 max-w-2xl text-balance text-4xl font-extrabold leading-tight sm:text-5xl">
            Post. Match. Confirm.
          </h2>
        </Reveal>

        <div className="relative mt-14 grid gap-5 md:grid-cols-3">
          {[
            {
              n: "01",
              icon: ClipboardList,
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798084/contractor_yy5k7d.png",
              title: "Post",
              body: "Trade, headcount, place, date. Sixty seconds on any phone.",
            },
            {
              n: "02",
              icon: Radar,
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798085/worker-register_i7sugy.png",
              title: "Match",
              body: "Every online worker in that trade within 10 km sees your job instantly.",
            },
            {
              n: "03",
              icon: CheckCircle,
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798084/confirmhand-shake_lcqrhi.png",
              title: "Confirm",
              body: "First to accept line up in your list. Tap confirm — crew locked.",
            },
          ].map((s, i) => (
            <Reveal
              key={s.n}
              delay={i * 0.14}
              className="glass group relative overflow-hidden rounded-3xl text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-glow"
            >
              {/* photo banner — square frame, object-contain shows the WHOLE
                  image (never cropped); hover eases it out for breathing room */}
              <div className="relative aspect-[4/5] overflow-hidden bg-deep">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={s.img}
                  alt=""
                  loading="lazy"
                  className="h-full w-full object-contain transition-transform duration-500 ease-out group-hover:scale-95"
                />
                <div
                  aria-hidden
                  className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-ink to-transparent"
                />
              </div>
              {/* molten badge sits astride the image edge */}
              <div className="btn-molten relative z-10 mx-auto -mt-9 flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-2xl shadow-[0_6px_24px_rgba(255,122,26,0.35)] ring-4 ring-ink">
                <s.icon className="h-8 w-8 text-white" />
              </div>
              <div className="px-7 pb-7 pt-4">
                <p className="text-xs font-bold tabular-nums tracking-[0.3em] text-dim">
                  STEP {s.n}
                </p>
                <h3 className="mt-1 text-2xl font-extrabold text-white">{s.title}</h3>
                <p className="mt-2.5 leading-relaxed text-dim">{s.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* professions */}
      <section className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Reveal className="text-center">
          <p className="text-xs font-bold tracking-[0.3em] text-molten">EVERY TRADE</p>
          <h2 className="mx-auto mt-3 max-w-2xl text-balance text-4xl font-extrabold leading-tight sm:text-5xl">
            Whoever the site needs, nearby.
          </h2>
          <p className="font-te mt-3 text-dim">ప్రతి పనికి నిపుణులు — ఒకే చోట</p>
        </Reveal>

        <div className="mt-12 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {[
            {
              slug: "mason",
              en: "Mason",
              te: "మేస్త్రీ",
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798033/mason_dd1ago.png",
            },
            {
              slug: "carpenter",
              en: "Carpenter",
              te: "వడ్రంగి",
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798031/carpenter_sgz4mh.jpg",
            },
            {
              slug: "electrician",
              en: "Electrician",
              te: "ఎలక్ట్రీషియన్",
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798031/electrician_drt7s9.jpg",
            },
            {
              slug: "painter",
              en: "Painter",
              te: "పెయింటర్",
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798033/painter_mizmkh.jpg",
            },
            {
              slug: "lifter",
              en: "Lifter",
              te: "లిఫ్టర్",
              img: "https://res.cloudinary.com/dkaccpujn/image/upload/f_auto,q_auto,w_900/v1783798033/lifter_g7wnxz.png",
            },
          ].map((p, i) => (
            <Reveal
              key={p.slug}
              delay={i * 0.08}
              className="group relative aspect-[3/4] overflow-hidden rounded-3xl border border-white/10"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={p.img}
                alt={p.en}
                loading="lazy"
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-110"
              />
              <div
                aria-hidden
                className="absolute inset-0 bg-gradient-to-t from-ink via-ink/40 to-transparent"
              />
              <div className="absolute inset-x-0 bottom-0 p-4">
                <h3 className="text-lg font-extrabold leading-tight text-white">{p.en}</h3>
                <p className="font-te text-sm text-molten-soft">{p.te}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* trust */}
      <section className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <Reveal className="glass rounded-3xl px-6 py-10 sm:px-10">
          <div className="grid grid-cols-2 gap-8 text-center lg:grid-cols-4">
            {[
              ["6", "skilled trades"],
              ["10 km", "matching radius"],
              ["< 5 min", "to first accept"],
              ["₹0", "middleman cut"],
            ].map(([big, small]) => (
              <div key={small}>
                <p className="text-4xl font-extrabold tabular-nums text-white sm:text-5xl">
                  {big}
                </p>
                <p className="mt-1 text-sm font-semibold uppercase tracking-wider text-dim">
                  {small}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-10 border-t border-white/10 pt-6 text-center text-dim">
            <span className="font-te text-bone">తెలుగులో పనిచేస్తుంది</span> · Telugu-first ·
            Works on a ₹6,000 phone · Free for workers, always
          </p>
        </Reveal>
      </section>

      {/* CTA */}
      <section className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Reveal className="glass-bright relative overflow-hidden rounded-[2.5rem] px-6 py-16 text-center sm:px-12">
          <div
            aria-hidden
            className="absolute -top-24 left-1/2 h-64 w-[36rem] -translate-x-1/2 rounded-full bg-molten/20 blur-[100px]"
          />
          <h2 className="relative text-balance text-4xl font-extrabold leading-tight sm:text-6xl">
            Tonight&rsquo;s job. <span className="molten-text">Tomorrow&rsquo;s crew.</span>
          </h2>
          <p className="font-te relative mt-4 text-lg text-dim">
            ఈ రాత్రి పోస్ట్ చేయండి. తెల్లారి పని మొదలు.
          </p>
          <div className="relative mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/contractor"
              className="btn-molten flex h-14 w-full items-center justify-center rounded-2xl px-9 text-lg font-bold text-white shadow-[0_6px_30px_rgba(255,122,26,0.4)] transition hover:brightness-110 sm:w-auto"
            >
              Post a job
            </Link>
            <Link
              href="/assistant"
              className="flex h-14 w-full items-center justify-center rounded-2xl border border-white/20 px-9 text-lg font-bold text-bone transition hover:bg-white/[0.08] sm:w-auto"
            >
              Ask the assistant
            </Link>
          </div>
          <p className="relative mt-6 text-sm text-dim">
            Free during the Vijayawada pilot · No app install needed
          </p>
        </Reveal>
      </section>

      {/* footer */}
      <footer className="relative border-t border-white/[0.07] px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <Image src="/adaa-logo.png" alt="ADAA" width={40} height={40} className="rounded-lg" />
          <p className="text-sm text-dim">
            Built for Andhra Pradesh&rsquo;s construction workforce · Vijayawada pilot · 2026
          </p>
        </div>
      </footer>
    </main>
  );
}
