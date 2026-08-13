import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "ADAA — Workforce Coordination",
  description:
    "Connecting construction workforce demand with suitable workers, crews and " +
    "subcontractors, while helping every worker build an independent reputation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <Nav />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 pb-10 pt-4 text-xs text-stone-500">
          ADAA — university research prototype. The workforce data is generated for
          demonstration. Match scores and independence scores are prototype figures and
          have not been validated.
        </footer>
      </body>
    </html>
  );
}
