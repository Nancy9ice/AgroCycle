"use client";

import { cn } from "@/lib/cn";

/** Opens the browser's print dialog, from which the page can be saved as a PDF. */
export function PrintButton({ className }: { className?: string }) {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className={cn(
        "inline-flex min-h-12 items-center justify-center rounded-full bg-forest-700 px-6 text-base font-semibold text-white transition-colors hover:bg-forest-800 active:bg-forest-950 print:hidden",
        className,
      )}
    >
      Print this page
    </button>
  );
}
