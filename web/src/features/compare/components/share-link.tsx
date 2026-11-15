"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

/**
 * Copies the link to this saved comparison. The full address is built on the click, from where the site is
 * actually served, and shown afterwards, so it can still be copied by hand if the browser blocks the clipboard.
 */
export function ShareLink({ path, className }: { path: string; className?: string }) {
  const [link, setLink] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean | null>(null);

  async function copy() {
    const url = new URL(path, window.location.origin).toString();
    setLink(url);
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      <button
        type="button"
        onClick={copy}
        className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-line-strong bg-surface px-6 text-base font-semibold text-ink transition-colors hover:border-forest-600 hover:bg-forest-50"
      >
        Copy a link to this result
      </button>
      {link ? (
        <div role="status" className="text-sm text-ink-soft">
          <p>
            {copied
              ? "Link copied. Anyone with it sees this same saved result."
              : "Your browser did not allow copying. Select the link below instead."}
          </p>
          <input
            readOnly
            value={link}
            aria-label="Link to this result"
            onFocus={(event) => event.currentTarget.select()}
            className="mt-1 w-full max-w-xl rounded-xl border border-line bg-surface px-3 py-2 font-mono text-xs"
          />
        </div>
      ) : null}
    </div>
  );
}
