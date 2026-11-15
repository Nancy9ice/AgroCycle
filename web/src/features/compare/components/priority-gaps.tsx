import { priorityGaps, type Emphasis } from "../emphasis";

/**
 * What you said matters most, and what we cannot tell you about it. The reordering of the outcomes below is half of
 * what priorities do; this is the other half, and it is what keeps it honest rather than flattering: someone who
 * picks soil is told we do not measure soil carbon.
 */
export function PriorityGaps({ emphasis }: { emphasis: Emphasis }) {
  const gaps = priorityGaps(emphasis);
  if (gaps.length === 0) return null;
  return (
    <section
      aria-labelledby="priority-gaps-title"
      className="rounded-[var(--radius-card)] border border-line bg-surface p-6"
    >
      <h3
        id="priority-gaps-title"
        className="font-display text-lg font-medium sm:text-xl"
      >
        What you said matters most
      </h3>
      <p className="mt-1 text-sm text-ink-soft">{emphasis.note}</p>
      <ul className="mt-4 space-y-4">
        {gaps.map((item) => (
          <li key={item.id}>
            <p className="font-semibold">{item.label}</p>
            <p className="mt-0.5 text-[0.9375rem] text-ink-soft">
              <span className="font-semibold text-ink">What we cannot tell you: </span>
              {item.gap}
            </p>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-sm text-ink-soft">
        The outcomes below are listed with the ones that speak to your priorities first.
        Every outcome is still shown, including the ones we cannot claim.
      </p>
    </section>
  );
}
