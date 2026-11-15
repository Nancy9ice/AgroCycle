import { cn } from "@/lib/cn";
import { outcomeCopy } from "@/features/compare/labels";
import type { DecisionOutcome } from "@/features/compare/types";
import type { TestSetResult } from "./get-test-set";

const title = (outcome: string) =>
  outcomeCopy[outcome as DecisionOutcome]?.title ?? outcome.replaceAll("_", " ");

const notice: Record<Exclude<TestSetResult["status"], "available">, string> = {
  no_service:
    "This copy of the site is not connected to the data service, so the live test-field results are not shown.",
  not_loaded: "The test-field results have not been loaded into the data service yet.",
  unreachable:
    "The data service could not be reached, so the test-field results are not shown.",
};

/** The decision engine run over every test field, read live from the data service (F5). */
export function TestSetAudit({ result }: { result: TestSetResult }) {
  return (
    <section aria-labelledby="audit-title" className="mt-12">
      <h2 id="audit-title" className="font-display text-2xl font-semibold">
        The engine on our test fields
      </h2>
      {result.status !== "available" ? (
        <p
          role="status"
          className="mt-3 max-w-3xl rounded-2xl bg-sunken px-4 py-3 text-ink-soft"
        >
          {notice[result.status]}
        </p>
      ) : (
        <Audit audit={result.audit} />
      )}
    </section>
  );
}

function Audit({
  audit,
}: {
  audit: Extract<TestSetResult, { status: "available" }>["audit"];
}) {
  const { metrics } = audit.cdl_agreement;
  return (
    <>
      <p className="mt-2 max-w-3xl text-ink-soft">
        We ran the decision engine over all {audit.fields.length} test fields with every
        farm question answered. The fields are team-drawn demonstration polygons, so these
        are counts, not a measure of accuracy. Fields that get “not enough evidence” are
        the engine working as intended, not failing.
      </p>

      <ul className="mt-5 grid gap-3 sm:grid-cols-3">
        {Object.entries(audit.outcome_counts).map(([outcome, count]) => (
          <li
            key={outcome}
            className="rounded-[var(--radius-card)] border border-line bg-surface p-4"
          >
            <p className="font-mono text-2xl font-semibold">{count}</p>
            <p className="text-sm text-ink-soft">{title(outcome)}</p>
          </li>
        ))}
      </ul>

      <p className="mt-5 max-w-3xl text-[0.9375rem]">
        The engine’s answer matched what we expected for {audit.match_count} of{" "}
        {audit.fields.length} fields. We set the expectation ourselves from how each field
        was chosen, so this checks consistency, not correctness.
      </p>

      <div className="mt-5 overflow-x-auto rounded-[var(--radius-card)] border border-line bg-surface">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <caption className="sr-only">
            Engine result against expectation for each test field
          </caption>
          <thead className="bg-sunken text-xs tracking-wide text-ink-faint uppercase">
            <tr>
              <th scope="col" className="px-3 py-2">
                Field
              </th>
              <th scope="col" className="px-3 py-2">
                County
              </th>
              <th scope="col" className="px-3 py-2">
                Crop history
              </th>
              <th scope="col" className="px-3 py-2">
                Expected
              </th>
              <th scope="col" className="px-3 py-2">
                Engine said
              </th>
              <th scope="col" className="px-3 py-2">
                Match
              </th>
            </tr>
          </thead>
          <tbody>
            {audit.fields.map((field) => (
              <tr key={field.field_id} className="border-t border-line">
                <th scope="row" className="px-3 py-2 font-mono font-medium">
                  {field.field_id}
                </th>
                <td className="px-3 py-2">{field.county}</td>
                <td className="px-3 py-2">{field.sequence_summary}</td>
                <td className="px-3 py-2">{title(field.expected_outcome)}</td>
                <td className="px-3 py-2">{title(field.engine_outcome)}</td>
                <td
                  className={cn(
                    "px-3 py-2 font-medium",
                    field.match ? "text-forest-700" : "text-clay-700",
                  )}
                >
                  {field.match ? "Yes" : "No"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        role="note"
        className="mt-6 max-w-3xl rounded-[var(--radius-card)] border border-line bg-surface p-5"
      >
        <h3 className="font-semibold">Crop-history agreement</h3>
        <p className="mt-2 text-[0.9375rem]">
          {metrics.fields_agreeing} of {metrics.fields_compared} fields get the same
          crop-history class from how we chose them and from our classification rules.{" "}
          {audit.cdl_agreement.note}
        </p>
      </div>

      <ul className="mt-5 max-w-3xl list-disc space-y-1 pl-5 text-sm text-ink-soft">
        {audit.caveats.map((caveat) => (
          <li key={caveat}>{caveat}</li>
        ))}
      </ul>
      <p className="mt-3 font-mono text-xs break-words text-ink-faint">
        Rules {audit.engine_version} · run {audit.run_id} · data {audit.data_version}
      </p>
    </>
  );
}
