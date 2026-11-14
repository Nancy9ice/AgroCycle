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
