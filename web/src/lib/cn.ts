import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Join conditional class names and resolve Tailwind conflicts, so a caller's
 * `className` reliably overrides a component's defaults (e.g. `hidden` over `inline-flex`).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
