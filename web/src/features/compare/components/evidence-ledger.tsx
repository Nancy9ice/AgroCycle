import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { cn } from "@/lib/cn";
import {
  ledgerStateCopy,
  type EvidenceLedger as Ledger,
  type LedgerItem,
  type LedgerLayer,
} from "../evidence-ledger";

/**
 * The evidence hierarchy, in the open: six layers from "looked up for your field" to "assumed or
 * unknown", each saying whose land it is about. Always visible, never behind a drawer, because a
 * reader must not have to dig to learn that a figure comes from one research farm.
 *
 * `compact` is for the printed adviser brief: no cards, so it prints on a page or two.
 */
export function EvidenceLedger({
  ledger,
  compact = false,
}: {
  ledger: Ledger;
  compact?: boolean;
}) {
  return (
    <div>
      <p
        className={cn(
          "max-w-3xl font-medium",
          compact ? "text-[0.9375rem]" : "text-lg text-ink",
        )}
      >
        {ledger.headline}
      </p>
      <ol className="mt-5 space-y-4">
        {ledger.layers.map((entry) => (
          <li key={entry.layer.id}>
            <Layer entry={entry} compact={compact} />
          </li>
        ))}
      </ol>
    </div>
  );
}

function Layer({ entry, compact }: { entry: LedgerLayer; compact: boolean }) {
  const { layer, number, items, emptyNote } = entry;
  const headingId = `ledger-${layer.id}${compact ? "-brief" : ""}`;
  return (
    <section
      aria-labelledby={headingId}
      className={cn(
        "break-inside-avoid",
        compact
          ? "border-l-4 border-line-strong pl-4"
          : "rounded-[var(--radius-card)] border border-line bg-surface p-5 sm:p-6",
      )}
    >
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 id={headingId} className="text-lg font-semibold">
          <span className="mr-2 font-mono text-sm text-ink-faint">{number}</span>
          {layer.title}
        </h3>
        <span className="rounded-full border border-line-strong bg-sunken px-2.5 py-0.5 text-xs font-medium text-ink-soft">
          {layer.scope}
        </span>
      </header>
      <p className="mt-1 max-w-3xl text-sm text-ink-soft">{layer.meaning}</p>

      {items.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <Item key={item.id} item={item} />
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-ink-faint">{emptyNote}</p>
      )}
    </section>
  );
}

function Item({ item }: { item: LedgerItem }) {
  const state = ledgerStateCopy[item.state];
  return (
    <li className="flex gap-3 text-[0.9375rem]">
      <span
        aria-hidden
        className={cn(
          "mt-0.5 w-4 shrink-0 text-center font-mono text-xs leading-5 font-semibold",
          state.tone === "good" && "text-forest-700",
          state.tone === "stop" && "text-clay-700",
          state.tone === "neutral" && "text-ink-faint",
        )}
      >
        {state.glyph}
      </span>
      <span className="min-w-0">
        <span className="font-medium">{item.label}</span>{" "}
        <span className="text-xs font-semibold tracking-wide text-ink-soft uppercase">
          {state.label}
        </span>
        {item.detail ? (
          <span className="block text-sm text-ink-soft">{item.detail}</span>
        ) : null}
        {item.evidenceType || item.source ? (
          <span className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-faint">
            {item.evidenceType ? <EvidenceBadge type={item.evidenceType} /> : null}
            {item.source ? <span>{item.source}</span> : null}
          </span>
        ) : null}
      </span>
    </li>
  );
}
