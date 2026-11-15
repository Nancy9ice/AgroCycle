"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Logo } from "@/components/brand/logo";
import { CloseIcon } from "@/components/icons/close-icon";
import { MenuIcon } from "@/components/icons/menu-icon";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { cn } from "@/lib/cn";
import {
  compareRoute,
  fieldRoute,
  planRoute,
  prioritiesRoute,
  profileRoute,
  routes,
} from "@/lib/routes";

/** The five steps of the core journey (PRD §5.2). Order matters: it is the user's path. */
const steps = [
  { label: "Field", segment: "" },
  { label: "Profile", segment: "profile" },
  { label: "Priorities", segment: "priorities" },
  { label: "Compare", segment: "compare" },
  { label: "Plan", segment: "plan" },
] as const;

const FIELD_PATH = /^\/fields\/([^/]+)\/(profile|priorities|compare|plan)\/?$/;

/** Where the visitor is in the journey, read from the URL. */
function useJourney() {
  const pathname = usePathname();
  const search = useSearchParams();

  const match = FIELD_PATH.exec(pathname);
  const fieldId = match ? decodeURIComponent(match[1]) : null;
  const current = match
    ? steps.findIndex((step) => step.segment === match[2])
    : pathname.startsWith(routes.field)
      ? 0
      : -1;

  /** Steps 2 to 5 need a field. Steps 3 to 5 also carry the priorities answers forward. */
  const hrefs = steps.map((_, index): string | null => {
    if (index === 0) return fieldId ? fieldRoute(fieldId) : routes.field;
    if (!fieldId) return null;
    const answers = current >= 2 ? new URLSearchParams(search.toString()) : undefined;
    if (index === 1) return profileRoute(fieldId);
    if (index === 2) return prioritiesRoute(fieldId, answers);
    if (index === 3) return compareRoute(fieldId, answers);
    return planRoute(fieldId, answers);
  });

  return { pathname, current, hrefs };
}

const linkClass =
  "rounded-full px-3.5 py-2 text-[0.9375rem] font-medium text-ink-soft underline-offset-8 transition-colors hover:text-forest-800 hover:underline";

/**
 * Navigation for every page except the landing page. Fixed to the top, so the journey (and a way home)
 * is always one click away. A spacer keeps page content from sliding under it.
 */
export function AppNav() {
  const { pathname, current, hrefs } = useJourney();
  const inJourney = current >= 0;
  const onValidation = pathname.startsWith(routes.validation);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-40 border-b border-line/80 bg-paper/95 backdrop-blur print:hidden">
        <Container className="flex h-16 items-center justify-between gap-4">
          <Logo />

          {inJourney ? (
            <nav aria-label="Progress" className="hidden lg:block">
              <ol className="flex items-center gap-1.5">
                {steps.map((step, index) => {
                  const state =
                    index < current ? "done" : index === current ? "current" : "todo";
                  const href = hrefs[index];
                  const pill = cn(
                    "inline-flex min-h-10 items-center gap-2 rounded-full px-3.5 text-sm font-medium transition-colors",
                    state === "current" && "bg-forest-700 text-white",
                    state === "done" && "bg-forest-100 text-forest-800",
                    state === "todo" && "text-ink-faint",
                    state !== "current" &&
                      href &&
                      "hover:bg-forest-100 hover:text-forest-800",
                  );
                  const content = (
                    <>
                      <span
                        aria-hidden
                        className={cn(
                          "flex size-5 items-center justify-center rounded-full font-mono text-xs",
                          state === "current" && "bg-white/20",
                          state === "done" && "bg-forest-700 text-white",
                          state === "todo" && "border border-line-strong",
                        )}
                      >
                        {index + 1}
                      </span>
                      {step.label}
                      {state === "done" ? (
                        <span className="sr-only"> (completed)</span>
                      ) : null}
                    </>
                  );
                  return (
                    <li key={step.label} className="flex items-center gap-1.5">
                      {href && state !== "current" ? (
                        <Link href={href} className={pill}>
                          {content}
                        </Link>
                      ) : (
                        <span
                          className={pill}
                          aria-current={state === "current" ? "step" : undefined}
                        >
                          {content}
                        </span>
                      )}
                      {index < steps.length - 1 ? (
                        <span aria-hidden className="h-px w-3 bg-line-strong" />
                      ) : null}
                    </li>
                  );
                })}
              </ol>
            </nav>
          ) : null}

          <div className="flex items-center gap-1">
            <Link
              href={routes.validation}
              aria-current={onValidation ? "page" : undefined}
              className={cn(
                linkClass,
                "hidden sm:inline-flex",
                onValidation && "text-forest-800 underline",
              )}
            >
              How we checked this
            </Link>
            {!inJourney ? (
              <ButtonLink
                href={routes.field}
                className="hidden min-h-11 px-5 text-[0.9375rem] sm:inline-flex"
              >
                Add your field
              </ButtonLink>
            ) : null}

            {/* Small screens: the step you are on, with the whole journey in a native menu. */}
            <details className="group relative lg:hidden">
              <summary
                className="flex min-h-10 cursor-pointer list-none items-center gap-2 rounded-full bg-surface px-3 text-sm font-medium [&::-webkit-details-marker]:hidden"
                aria-label="Menu"
              >
                {inJourney ? (
                  <span className="font-mono text-xs tracking-[0.1em] text-forest-700 uppercase">
                    {current + 1}/{steps.length} · {steps[current].label}
                  </span>
                ) : null}
                <MenuIcon className="size-5 group-open:hidden" />
                <CloseIcon className="hidden size-5 group-open:block" />
              </summary>
              <nav
                aria-label="Menu"
                className="absolute right-0 mt-3 flex w-72 flex-col gap-1 rounded-2xl border border-line bg-surface p-3 shadow-card"
              >
                {inJourney
                  ? steps.map((step, index) => {
                      const href = hrefs[index];
                      const isCurrent = index === current;
                      const row = cn(
                        linkClass,
                        "flex items-center gap-3 py-3",
                        isCurrent && "bg-forest-100 text-forest-800",
                        !href && !isCurrent && "text-ink-faint hover:text-ink-faint",
                      );
                      const inner = (
                        <>
                          <span className="font-mono text-xs">{index + 1}</span>
                          {step.label}
                        </>
                      );
                      return href && !isCurrent ? (
                        <Link key={step.label} href={href} className={row}>
                          {inner}
                        </Link>
                      ) : (
                        <span
                          key={step.label}
                          className={row}
                          aria-current={isCurrent ? "step" : undefined}
                        >
                          {inner}
                        </span>
                      );
                    })
                  : null}
                <Link href={routes.validation} className={cn(linkClass, "py-3")}>
                  How we checked this
                </Link>
                <Link href={routes.home} className={cn(linkClass, "py-3")}>
                  Home
                </Link>
                {!inJourney ? (
                  <ButtonLink href={routes.field} className="mt-2">
                    Add your field
                  </ButtonLink>
                ) : null}
              </nav>
            </details>
          </div>
        </Container>
      </header>
      <div aria-hidden className="h-16 print:hidden" />
    </>
  );
}
