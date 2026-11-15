import { PageHeader } from "@/components/layout/page-header";
import { readNotice, type ApiRead } from "@/lib/api-read";
import { routes } from "@/lib/routes";
import { Evidence, Row } from "./methods-screen";
import type { Lineage } from "./methods-types";

/** `/methods/[indicatorId]`: the full method behind one indicator, from the API's lineage record. */
export function IndicatorScreen({ result }: { result: ApiRead<Lineage> }) {
  if (result.status !== "ok") {
    return (
      <>
        <PageHeader
          title="Indicator method"
          back={{ href: routes.methods, label: "data and methods" }}
        />
        <p role="status" className="mt-8 rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
          {readNotice[result.status]}
        </p>
      </>
    );
  }
  const lineage = result.data;
  return (
    <>
      <PageHeader
        eyebrow="How this is worked out"
        title={lineage.label.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase())}
        back={{ href: routes.methods, label: "data and methods" }}
        aside={<Evidence type={lineage.evidence_type} />}
      >
        <p className="font-mono text-xs">{lineage.indicator_id}</p>
      </PageHeader>

      <dl className="mt-8 grid gap-x-8 gap-y-4 rounded-[var(--radius-card)] border border-line bg-surface p-6 text-[0.9375rem] sm:grid-cols-[11rem_1fr]">
        <Row term="Formula">{lineage.formula}</Row>
        <Row term="Time window">{lineage.aggregation_window}</Row>
        <Row term="Scale">{lineage.scale}</Row>
        <Row term="Spatial support">{lineage.spatial_support}</Row>
        <Row term="Data used">
          {lineage.source_ids.join(", ")}
          {lineage.variables.length > 0 ? ` (${lineage.variables.join(", ")})` : ""}
        </Row>
        <Row term="When data is missing">{lineage.missing_data_rule}</Row>
        <Row term="How to read it">{lineage.interpretation}</Row>
        <Row term="What it cannot tell you">{lineage.limitation}</Row>
        <Row term="Method version">
          <span className="font-mono text-xs">{lineage.code_version}</span>
        </Row>
      </dl>
    </>
  );
}
