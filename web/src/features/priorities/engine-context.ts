import { questions, type Answers, type EngineKey } from "./questions";

/**
 * The farmer facts DS2's applicability rules read (`engine/rules/strategy_rules.py`).
 * `true` and `false` are answers; `null` is unknown, which makes the engine abstain or qualify
 * rather than assume. A skipped question and "Not sure" are both unknown, never "yes".
 */
export type EngineContext = Record<EngineKey, boolean | null>;

export function toEngineContext(answers: Answers): EngineContext {
  const context: EngineContext = {
    manure_access: null,
    forage_use_or_buyer: null,
    oat_use_or_buyer: null,
    small_grain_equipment_or_contractor: null,
  };

  for (const question of questions) {
    if (!("engineKey" in question)) continue;
    const answer = answers[question.id];
    if (answer === undefined) continue;
    const yes: readonly string[] = question.yes;
    const no: readonly string[] = question.no;
    if (yes.includes(answer)) context[question.engineKey] = true;
    else if (no.includes(answer)) context[question.engineKey] = false;
  }
  return context;
}
