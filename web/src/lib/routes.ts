/**
 * Single source of truth for app routes. Link to these instead of hard-coding paths,
 * so renaming a route is a one-line change.
 */
export const routes = {
  home: "/",
  field: "/field",
  priorities: "/priorities",
  compare: "/compare",
  plan: "/plan",
  validation: "/validation",
} as const;

export type AppRoute = (typeof routes)[keyof typeof routes];

/** Field selection with a field preselected, e.g. when returning from the profile. */
export const fieldRoute = (fieldId: string) =>
  `${routes.field}?field=${encodeURIComponent(fieldId)}`;

/** Step 2. Mirrors `GET /fields/{field_id}/profile` in the API. */
export const profileRoute = (fieldId: string) =>
  `/fields/${encodeURIComponent(fieldId)}/profile`;
