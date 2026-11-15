import type { PriorityReading } from "../priority-links";

/**
 * Reads the person's high priorities against what the engine returned. Priorities do not change
 * the outcome; this says where we can speak to them and, as importantly, where we cannot.
 */
export function PrioritiesPanel({ readings }: { readings: readonly PriorityReading[] }) {
  if (readings.length === 0) return null;
  return (
    <section
      aria-labelledby="priorities-title"
      className="rounded-[var(--radius-card)] border border-line bg-surface p-6"
    >
      <h3 id="priorities-title" className="font-display text-lg font-medium sm:text-xl">
        What you said matters most
      </h3>
      <p className="mt-1 text-sm text-ink-soft">
        These do not change the result. They show where we can, and cannot, speak to them.
      </p>
      <ul className="mt-4 space-y-4">
        {readings.map((reading) => (
          <li key={reading.id}>
            <p className="font-semibold">{reading.label}</p>
            <p className="mt-0.5 text-[0.9375rem] text-ink-soft">{describe(reading)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function describe(reading: PriorityReading): string {
  if (reading.related.length === 0) {
    return "None of the outcomes below measures this. Ask someone who knows your land and weather.";
  }
  if (reading.speakable.length === 0) {
    return `We cannot speak to this yet: ${listLabels(reading.related)} ${reading.related.length === 1 ? "is" : "are"} not available for your field.`;
  }
  if (reading.speakable.length < reading.related.length) {
    return `We can speak to part of this: ${listLabels(reading.speakable)}. The rest is held back or not assessed.`;
  }
  return `We can speak to this through: ${listLabels(reading.speakable)}.`;
}

const listLabels = (outcomes: PriorityReading["related"]) =>
  outcomes.map((outcome) => outcome.label.toLowerCase()).join("; ");
