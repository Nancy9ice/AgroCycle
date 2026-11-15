import { FieldPatchwork } from "@/components/illustrations/field-patchwork";
import { cropPhases } from "@/domain/strategies";

export function HeroFieldVisual() {
  return (
    <figure className="relative">
      <div className="overflow-hidden rounded-[1.75rem] border border-line bg-surface p-3 shadow-card">
        <FieldPatchwork className="h-auto w-full rounded-2xl bg-forest-50" />
      </div>

      <figcaption className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 px-1 text-sm text-ink-soft">
        <span className="font-mono text-xs text-ink-faint">Illustration</span>
        {(["maize", "soybean", "oat-red-clover", "alfalfa"] as const).map((id) => (
          <span key={id} className="inline-flex items-center gap-2">
            <span
              aria-hidden
              className={`size-3 rounded-full ${cropPhases[id].swatch}`}
            />
            {id === "oat-red-clover" ? "Oat" : cropPhases[id].label}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
