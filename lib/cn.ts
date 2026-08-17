/**
 * Join class names, dropping anything falsy.
 *
 *   cn("rounded", isOpen && "shadow-glow")
 *
 * Deliberately not clsx + tailwind-merge: nothing in this interface relies on
 * a later class overriding an earlier conflicting one, so the merge step would
 * be two dependencies bought for nothing.
 */
export function cn(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}
