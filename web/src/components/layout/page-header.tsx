import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeftIcon } from "@/components/icons/arrow-left-icon";
import { cn } from "@/lib/cn";

interface PageHeaderProps {
  title: ReactNode;
  /** Where the back arrow goes, and what to call that place for screen readers. */
  back?: { href: string; label: string };
  /** A small label above the title. */
  eyebrow?: string;
  /** A control for the top right, such as a view switch. */
  aside?: ReactNode;
  /** The sentence or two under the title. */
  children?: ReactNode;
  className?: string;
}

/**
 * The top of every page after the landing page: a back arrow, the title, an optional control on the
 * right, and a short introduction. One header everywhere keeps the pages feeling like one product.
 */
export function PageHeader({
  title,
  back,
  eyebrow,
  aside,
  children,
  className,
}: PageHeaderProps) {
  return (
    <header className={cn("space-y-2", className)}>
      {eyebrow ? (
        <p className="font-mono text-xs font-medium tracking-[0.14em] text-forest-600 uppercase">
          {eyebrow}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
        <div className="flex items-center gap-1">
          {back ? (
            <Link
              href={back.href}
              aria-label={`Back to ${back.label}`}
              title={`Back to ${back.label}`}
              className="-ml-2 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ink-soft transition-colors hover:bg-forest-100 hover:text-forest-800 print:hidden"
            >
              <ArrowLeftIcon className="size-5" />
            </Link>
          ) : null}
          <h1 className="font-display text-2xl font-medium tracking-tight text-balance sm:text-3xl">
            {title}
          </h1>
        </div>
        {aside ? <div className="ml-auto print:hidden">{aside}</div> : null}
      </div>
      {children ? (
        <div className="max-w-3xl space-y-2 text-sm text-ink-soft sm:text-base">
          {children}
        </div>
      ) : null}
    </header>
  );
}
