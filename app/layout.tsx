import type { Metadata, Viewport } from "next";
import { Anek_Latin, Noto_Sans_Telugu } from "next/font/google";
import "./globals.css";

/*
 * The root layout carries nothing but the page shell, the fonts and the
 * stylesheet. The navigation lives in `(app)/layout.tsx`, because the landing
 * page in `(site)/` must not have it.
 */

const anek = Anek_Latin({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-anek",
});

// Telugu is a first-class language here, not a translation afterthought, so
// its font is loaded alongside the Latin one rather than falling back.
//
// Noto Sans Telugu, not Anek Telugu (which the source design used): under
// Next 16 / Turbopack, Anek Telugu's generated @font-face rules fail to
// resolve — "Can't resolve '@vercel/turbopack-next/internal/font/google/font'"
// — and take the whole build down with them. Noto is the same skeleton at a
// slightly lower contrast and loads cleanly.
const telugu = Noto_Sans_Telugu({
  subsets: ["telugu"],
  weight: ["400", "600", "700"],
  variable: "--font-anek-te",
});

export const metadata: Metadata = {
  title: "ADAA — Crew up by sunrise",
  description:
    "ADAA matches contractors with skilled construction workers, crews and " +
    "subcontractors nearby, while helping every worker build an independent " +
    "professional reputation.",
  icons: { icon: "/adaa-logo.png" },
};

export const viewport: Viewport = {
  themeColor: "#070D1A",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${anek.variable} ${telugu.variable}`}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
