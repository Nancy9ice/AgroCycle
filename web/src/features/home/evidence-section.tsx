import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { Section } from "@/components/ui/section";
import { evidenceSources } from "@/features/home/content";
import { cn } from "@/lib/cn";

export function EvidenceSection() {
  return (
    <Section
      id="evidence"
      eyebrow="Data behind every result"
      title="Real data, labelled for what it is"
      intro="Satellite images, weather models, crop maps, soil surveys and field trials are different kinds of evidence. Every number in AgroCycle says which kind it is, how coarse it is, and where it came from."
    >
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {evidenceSources.map((source, index) => (
          <li
            key={source.name}
            className={cn(
              "flex flex-col rounded-[var(--radius-card)] border border-line bg-surface p-6",
              index === evidenceSources.length - 1 && "lg:col-span-2",
            )}
          >
            <p className="font-mono text-xs font-medium tracking-[0.12em] text-forest-600 uppercase">
              {source.provider}
            </p>
            <h3 className="mt-2 text-lg font-semibold">{source.name}</h3>
            <p className="mt-2 flex-1 text-[0.9375rem] text-ink-soft">{source.role}</p>
            <div className="mt-5 space-y-2 border-t border-line pt-4">
              <EvidenceBadge type={source.evidence} />
              <p className="text-sm text-ink-faint">{source.scale}</p>
            </div>
          </li>
        ))}
      </ul>
    </Section>
  );
}
