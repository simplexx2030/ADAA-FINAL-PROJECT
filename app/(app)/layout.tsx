import { MobileNav, Sidebar } from "@/components/Sidebar";

/**
 * The application shell: everything behind the front door.
 *
 * The landing page sits in `(site)/` and never sees this, which is the whole
 * reason for the two route groups.
 */
export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <Sidebar />
      <MobileNav />
      <main className="lg:pl-60">
        <div className="mx-auto max-w-6xl px-6 py-8 lg:px-10 lg:py-10">
          {children}
        </div>
      </main>
    </>
  );
}
