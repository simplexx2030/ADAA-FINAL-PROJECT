/**
 * The public side of ADAA. A passthrough: the landing page brings its own
 * header and footer, and deliberately has no application navigation.
 */
export default function SiteLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <>{children}</>;
}
