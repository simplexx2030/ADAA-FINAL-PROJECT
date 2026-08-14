import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MobileNav, Sidebar } from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "ADAA — Workforce Agent",
  description:
    "Connecting construction workforce demand with suitable workers, crews and " +
    "subcontractors, while helping every worker build an independent reputation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-white text-slate-900">
        <Sidebar />
        <MobileNav />
        <main className="lg:pl-60">
          <div className="mx-auto max-w-6xl px-6 py-8 lg:px-10 lg:py-10">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
