export const roles = [
  { value: "farmer", label: "A farmer" },
  { value: "adviser", label: "An adviser" },
  { value: "researcher", label: "A researcher" },
  { value: "other", label: "Someone else" },
] as const;

export const wouldUseChoices = [
  { value: "yes", label: "Yes" },
  { value: "maybe", label: "Maybe" },
  { value: "no", label: "No" },
] as const;

export type Role = (typeof roles)[number]["value"];
export type WouldUse = (typeof wouldUseChoices)[number]["value"];

export const MAX_MISSING = 1000;

export interface FeedbackDraft {
  role: Role | "";
  farmingContext: string;
  usefulness: number | null;
  clarity: number | null;
  whatWasMissing: string;
  wouldUse: WouldUse | "";
  contact: string;
  consent: boolean;
  fieldId?: string;
  analysisId?: string;
}

export const emptyDraft = (fieldId?: string, analysisId?: string): FeedbackDraft => ({
  role: "",
  farmingContext: "",
  usefulness: null,
  clarity: null,
  whatWasMissing: "",
  wouldUse: "",
  contact: "",
  consent: false,
  fieldId,
  analysisId,
});

/** The first thing wrong with the form, in plain words, or null when it can be sent. The API checks again. */
export function problem(draft: FeedbackDraft): string | null {
  if (draft.role === "")
    return "Say who you are, so we can read your answers in context.";
  if (draft.usefulness === null) return "Rate how useful it was, from 1 to 5.";
  if (draft.clarity === null) return "Rate how clear it was, from 1 to 5.";
  if (draft.whatWasMissing.length > MAX_MISSING)
    return `Keep what was missing under ${MAX_MISSING} characters.`;
  if (draft.contact.trim() !== "" && !draft.consent)
    return "Tick the box if you want us to keep your contact details, or clear them.";
  return null;
}

/** The API request. A skipped answer is null, which means "not provided", never "no". */
export function toRequest(draft: FeedbackDraft): Record<string, unknown> {
  const text = (value: string) => (value.trim() === "" ? null : value.trim());
  const contact = text(draft.contact);
  return {
    role: draft.role,
    farming_context: text(draft.farmingContext),
    usefulness: draft.usefulness,
    clarity: draft.clarity,
    what_was_missing: text(draft.whatWasMissing),
    would_use: draft.wouldUse === "" ? null : draft.wouldUse,
    contact,
    // Consent only means something when there is a contact to keep.
    contact_consent: contact !== null && draft.consent,
    field_id: draft.fieldId ?? null,
    analysis_id: draft.analysisId ?? null,
  };
}
