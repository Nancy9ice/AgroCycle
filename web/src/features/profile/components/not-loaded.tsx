import { cn } from "@/lib/cn";

/** A dimension we have no data for yet. Unknown is shown as unknown, never as a value. */
export function NotLoaded({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-dashed border-clay-700/50 bg-clay-100/60 px-3 py-1 text-sm font-medium text-clay-700",
        className,
      )}
    >
      <span aria-hidden className="font-mono">
        ?
      </span>
      {children}
    </span>
  );
}
