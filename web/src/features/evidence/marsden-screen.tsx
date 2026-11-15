import { PageHeader } from "@/components/layout/page-header";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import type { EvidenceTypeId } from "@/domain/evidence";
import { evidenceTypes } from "@/domain/evidence";
import { readNotice, type ApiRead } from "@/lib/api-read";
import { routes } from "@/lib/routes";
import {
  buildMarsdenLines,
  formatFigure,
  rotations,
  type Marsden,
} from "./marsden-table";

const isEvidenceType = (value: string): value is EvidenceTypeId => value in evidenceTypes;

/** `/evidence/marsden`: the experiment behind the comparison, and what it does not show. */
export function MarsdenScreen({ result }: { result: ApiRead<Marsden> }) {
  return (
    <>
      <PageHeader
        eyebrow="Experimental evidence"
        title="What the Marsden Farm experiment measured"
        back={{ href: routes.home, label: "home" }}
      >
        <p>
          The comparison rests on one long-running experiment, not on your field. Here are
          the figures it uses and where they stop.
        </p>
      </PageHeader>

      {result.status !== "ok" ? (
        <p role="status" className="mt-8 rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
          {readNotice[result.status]}
        </p>
      ) : (
        <Figures marsden={result.data} />
      )}
    </>
  );
}

function Figures({ marsden }: { marsden: Marsden }) {
  const lines = buildMarsdenLines(marsden.rows);
  return (
    <>
      <p className="mt-8 max-w-3xl text-[0.9375rem]">{marsden.description}</p>

      <div className="mt-6 overflow-x-auto rounded-[var(--radius-card)] border border-line bg-surface">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <caption className="sr-only">
            Marsden Farm nine-year averages for the two-, three- and four-year rotations
          </caption>
          <thead className="bg-sunken text-xs tracking-wide text-ink-faint uppercase">
            <tr>
              <th scope="col" className="px-3 py-2">
                Measure
              </th>
              {rotations.map((rotation) => (
                <th key={rotation.id} scope="col" className="px-3 py-2">
                  {rotation.label}{" "}
                  <span className="font-mono normal-case">
                    (option {rotation.strategy})
                  </span>
                </th>
              ))}
              <th scope="col" className="px-3 py-2">
                Kind of evidence
              </th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line) => (
              <tr key={line.metric} className="border-t border-line align-top">
                <th scope="row" className="px-3 py-3 font-medium">
                  {line.label}
                  <span className="mt-0.5 block font-mono text-xs font-normal text-ink-faint">
                    {line.unit}
                  </span>
                </th>
                {rotations.map((rotation) => (
                  <td key={rotation.id} className="px-3 py-3 font-mono">
                    {rotation.id in line.values
                      ? formatFigure(line.metric, line.values[rotation.id])
                      : "–"}
                  </td>
                ))}
                <td className="px-3 py-3">
                  {isEvidenceType(line.evidenceType) ? (
                    <EvidenceBadge type={line.evidenceType} />
                  ) : (
                    line.evidenceType
                  )}
                  <span className="mt-1 block font-mono text-xs text-ink-faint">
                    {line.sourceId}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-sm text-ink-soft">
        Rotations:{" "}
        {rotations.map((r) => `${r.label.toLowerCase()} (${r.detail})`).join("; ")}.
      </p>

      <section aria-labelledby="not-show-title" className="mt-10">
        <h2 id="not-show-title" className="font-display text-2xl font-semibold">
          What this does not show
        </h2>
        <ul className="mt-3 max-w-3xl list-disc space-y-2 pl-5 text-ink-soft">
          {marsden.caveats.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      </section>

      <p className="mt-8 max-w-3xl text-sm text-ink-soft">
        <span className="font-semibold text-ink">Source: </span>
        {marsden.reference}
      </p>
      <p className="mt-2 font-mono text-xs break-words text-ink-faint">
        Data {marsden.data_version}
      </p>
    </>
  );
}
