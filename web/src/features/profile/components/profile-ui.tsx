"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import type { Provenance } from "../types";

export type ProfileView = "simple" | "detailed";

interface ProfileUi {
  view: ProfileView;
  setView: (view: ProfileView) => void;
  openProvenance: (provenance: Provenance, isSample: boolean) => void;
}

const ProfileUiContext = createContext<ProfileUi | null>(null);

export function useProfileUi(): ProfileUi {
  const value = useContext(ProfileUiContext);
  if (!value) throw new Error("useProfileUi must be used inside <ProfileUiProvider>");
  return value;
}

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h3 className="text-sm font-semibold text-ink-faint">{title}</h3>
      <div className="text-[0.9375rem] text-ink">{children}</div>
    </section>
  );
}

function Technical({ provenance }: { provenance: Provenance }) {
  const t = provenance.technical;
  const rows: [string, string | undefined][] = [
    ["scale", t.scale],
    ["product", t.product],
    ["variable", t.variable],
    ["version", t.version],
    ["retrieved", t.retrieved],
    ["indicator_id", t.indicatorId],
  ];
  return (
    <dl className="grid grid-cols-[7rem_1fr] gap-x-4 gap-y-2 rounded-2xl bg-sunken p-4 font-mono text-xs">
      <dt className="text-ink-faint">evidence_type</dt>
      <dd>
        <EvidenceBadge type={t.evidenceType} />
      </dd>
      {rows
        .filter(([, value]) => value)
        .map(([name, value]) => (
          <div key={name} className="contents">
            <dt className="text-ink-faint">{name}</dt>
            <dd className="break-words text-ink">{value}</dd>
          </div>
        ))}
    </dl>
  );
}

/**
 * Holds the Simple/Detailed view and the one shared "where this comes from" drawer.
 * The drawer is a native modal <dialog>: Esc closes it, focus is trapped while open and
 * returns to the control that opened it.
 */
export function ProfileUiProvider({ children }: { children: ReactNode }) {
  const [view, setView] = useState<ProfileView>("simple");
  const [active, setActive] = useState<{
    provenance: Provenance;
    isSample: boolean;
  } | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const openProvenance = useCallback((provenance: Provenance, isSample: boolean) => {
    setActive({ provenance, isSample });
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (active && dialog && !dialog.open) dialog.showModal();
  }, [active]);

  const value = useMemo(
    () => ({ view, setView, openProvenance }),
    [view, openProvenance],
  );

  return (
    <ProfileUiContext.Provider value={value}>
      {children}
      <dialog
        ref={dialogRef}
        aria-labelledby="provenance-title"
        onClose={() => setActive(null)}
        onClick={(event) => {
          // A click on the dialog element itself is a click on the backdrop.
          if (event.target === event.currentTarget) event.currentTarget.close();
        }}
        className="m-0 ml-auto h-dvh max-h-dvh w-full max-w-lg overflow-y-auto bg-surface p-0 text-ink shadow-2xl backdrop:bg-forest-950/50"
      >
        {active ? (
          <div className="space-y-6 p-6 sm:p-8">
            <header className="flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-xs font-medium tracking-[0.14em] text-forest-600 uppercase">
                  Where this comes from
                </p>
                <h2
                  id="provenance-title"
                  className="mt-2 font-display text-2xl font-semibold"
                >
                  {active.provenance.title}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => dialogRef.current?.close()}
                className="flex size-11 shrink-0 items-center justify-center rounded-full border border-line-strong hover:bg-forest-50"
                aria-label="Close"
              >
                <svg
                  viewBox="0 0 24 24"
                  className="size-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden
                >
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </header>

            {active.isSample ? (
              <p
                role="note"
                className="rounded-2xl bg-harvest-100 px-4 py-3 text-[0.9375rem] text-harvest-700"
              >
                <strong className="font-semibold">Sample values.</strong> This number is a
                placeholder until the data pipeline is connected. The description below is
                how the real number will be made.
              </p>
            ) : null}

            <Block title="What it is">{active.provenance.whatItIs}</Block>
            <Block title="Where it comes from">
              {active.provenance.sourceUrl ? (
                <a
                  href={active.provenance.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-forest-700 underline underline-offset-2"
                >
                  {active.provenance.source}
                  <span className="sr-only"> (opens in a new tab)</span>
                </a>
              ) : (
                active.provenance.source
              )}
            </Block>
            <Block title="How precise it is">{active.provenance.precision}</Block>
            <Block title="What is missing">{active.provenance.gaps}</Block>
            <Block title="Technical record">
              <Technical provenance={active.provenance} />
            </Block>
          </div>
        ) : null}
      </dialog>
    </ProfileUiContext.Provider>
  );
}
