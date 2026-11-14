import { cn } from "@/lib/cn";
import type { VegetationMonth, VegetationState } from "../types";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

const stateLabel: Record<VegetationState, string> = {
  growing: "Crops growing",
  bare: "Mostly bare",
  unknown: "Don't know",
};

const CHART_HEIGHT = "h-44";

/**
 * Monthly greenness bars. The state of each month arrives decided by the data layer; this only
 * draws it. Unknown months are drawn as a dashed "?" box, never as a bar, and every month shows
 * how many clear images it rests on. A table below is the text alternative.
 */
export function GreennessChart({ months }: { months: readonly VegetationMonth[] }) {
  return (
    <div>
      <div aria-hidden className="grid grid-cols-12 gap-1 sm:gap-2.5">
        {months.map((m) => (
          <div key={m.month} className="flex min-w-0 flex-col items-center gap-1.5">
            <div className={cn("flex w-full items-end", CHART_HEIGHT)}>
              {m.state === "unknown" || m.ndvi === null ? (
                <div className="flex h-1/3 w-full items-center justify-center rounded-lg border-2 border-dashed border-line-strong font-mono text-sm text-ink-faint">
                  ?
                </div>
              ) : (
                <div
                  className={cn(
                    "w-full rounded-lg",
                    m.state === "growing" ? "bg-forest-600" : "bg-crop-hay",
                  )}
                  style={{ height: `${Math.max(m.ndvi, 0.04) * 100}%` }}
                />
              )}
            </div>
            <span className="text-xs font-medium">
              <span className="sm:hidden">{MONTHS[m.month - 1][0]}</span>
              <span className="hidden sm:inline">{MONTHS[m.month - 1]}</span>
            </span>
            <span className="font-mono text-[0.6875rem] text-ink-faint">
              {m.clearImages}
            </span>
          </div>
        ))}
      </div>

      <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-soft">
        <li className="flex items-center gap-2">
          <span aria-hidden className="size-3 rounded bg-forest-600" /> Crops growing
        </li>
        <li className="flex items-center gap-2">
          <span aria-hidden className="size-3 rounded bg-crop-hay" /> Mostly bare
        </li>
        <li className="flex items-center gap-2">
          <span
            aria-hidden
            className="flex size-3 items-center justify-center rounded border border-dashed border-line-strong"
          />{" "}
          Don&rsquo;t know
        </li>
        <li className="font-mono text-xs text-ink-faint">
          Number under each month = clear images
        </li>
      </ul>

      {/* sr-only on a <table> is not clipped by browsers, so wrap it. */}
      <div className="sr-only">
        <table>
          <caption>
            Greenness by month, with the number of clear images behind each month
          </caption>
          <thead>
            <tr>
              <th scope="col">Month</th>
              <th scope="col">Greenness index</th>
              <th scope="col">Clear images</th>
              <th scope="col">What it shows</th>
            </tr>
          </thead>
          <tbody>
            {months.map((m) => (
              <tr key={m.month}>
                <th scope="row">{MONTHS[m.month - 1]}</th>
                <td>{m.ndvi === null ? "Not enough clear images" : m.ndvi.toFixed(2)}</td>
                <td>{m.clearImages}</td>
                <td>{stateLabel[m.state]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
