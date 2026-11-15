/**
 * Single source of truth for app routes. Link to these instead of hard-coding paths,
 * so renaming a route is a one-line change.
 */
export const routes = {
  home: "/",
  field: "/field",
  validation: "/validation",
} as const;

export type AppRoute = (typeof routes)[keyof typeof routes];

/** Step 1 on the demo fields tab, for people who want to see the product before drawing their own field. */
export const demoFieldsRoute = `${routes.field}?mode=demo`;

/** Field selection with a field preselected, e.g. when returning from the profile. */
export const fieldRoute = (fieldId: string) =>
  `${routes.field}?field=${encodeURIComponent(fieldId)}`;

/** Step 2. Mirrors `GET /fields/{field_id}/profile` in the API. */
export const profileRoute = (fieldId: string) =>
  `/fields/${encodeURIComponent(fieldId)}/profile`;

/** Step 3. Priorities and constraints for the selected field; answers come back as query parameters. */
export const prioritiesRoute = (fieldId: string, answers?: URLSearchParams) => {
  const query = answers?.toString();
  return `/fields/${encodeURIComponent(fieldId)}/priorities${query ? `?${query}` : ""}`;
};

/** Step 4. Carries the answers from step 3 as query parameters. */
export const compareRoute = (fieldId: string, answers?: URLSearchParams) => {
  const query = answers?.toString();
  return `/fields/${encodeURIComponent(fieldId)}/compare${query ? `?${query}` : ""}`;
};

/** Step 5. A printable brief for an adviser; carries the answers and the preview flag. */
export const planRoute = (fieldId: string, answers?: URLSearchParams) => {
  const query = answers?.toString();
  return `/fields/${encodeURIComponent(fieldId)}/plan${query ? `?${query}` : ""}`;
};
