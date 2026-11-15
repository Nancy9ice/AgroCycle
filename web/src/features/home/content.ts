import type { EvidenceTypeId } from "@/domain/evidence";
import type { StackCardData } from "@/components/scroll-stack/types";
import { demoFieldsRoute, routes } from "@/lib/routes";

export const decisionPoints = [
  {
    title: "What each option could offer",
    body: "Potential benefits for soil cover, weather risk and input use, each labelled as measured, published or only possible.",
  },
  {
    title: "What it would cost you to try",
    body: "Trade-offs and practical needs: equipment, manure, storage, labour and somewhere to sell oats or hay.",
  },
  {
    title: "What we don't know",
    body: "Evidence gaps, shown plainly. Missing information is never treated as good news.",
  },
] as const;

export const flowSteps = [
  {
    title: "Add your field",
    body: "Find your field with your phone or mark its corners on a map, inside Story or Boone County. Or look around with a demo field first.",
  },
  {
    title: "Read its profile",
    body: "What was grown, the soil, the weather, and when the ground sits bare, each with where the number came from.",
  },
  {
    title: "Say what matters",
    body: "Soil, dry years, input costs, and what is possible on your farm: manure, machinery, buyers.",
  },
  {
    title: "Compare the options",
    body: "Side by side, with benefits, trade-offs and an honest answer, including “not enough evidence”.",
  },
  {
    title: "Plan the switch",
    body: "A year-by-year outline to talk through with an adviser. A starting point, not a final plan.",
  },
] as const;

/** The five steps as stacked cards. Mirrors `flowSteps`, with what each step shows. */
export const howItWorksCards: readonly StackCardData[] = [
  {
    kicker: "Step 01",
    title: flowSteps[0].title,
    desc: flowSteps[0].body,
    list: [
      "Find your field with your phone",
      "Or mark its corners on a map",
      "Inside Story or Boone County, Iowa",
    ],
    pills: [
      { label: "Explore your field", href: routes.field },
      { label: "Try a demo first", href: demoFieldsRoute },
    ],
  },
  {
    kicker: "Step 02",
    title: flowSteps[1].title,
    desc: flowSteps[1].body,
    list: [
      "What was grown, year by year",
      "The soil and how well it drains",
      "Rain, temperature and dry spells",
      "When the ground sits bare",
    ],
    pills: [{ label: "Where the data comes from", href: "#evidence" }],
  },
  {
    kicker: "Step 03",
    title: flowSteps[2].title,
    desc: flowSteps[2].body,
    pills: [
      { label: "Soil" },
      { label: "Dry years" },
      { label: "Input costs" },
      { label: "Manure" },
      { label: "Machinery" },
      { label: "Buyers" },
    ],
  },
  {
    kicker: "Step 04",
    title: flowSteps[3].title,
    desc: flowSteps[3].body,
    list: [
      "Keep it as it is: corn and soybeans",
      "A three-year rotation",
      "A four-year rotation",
    ],
    pills: [{ label: "See the three options", href: "#strategies" }],
  },
  {
    kicker: "Step 05",
    title: flowSteps[4].title,
    desc: flowSteps[4].body,
    list: [
      "A year-by-year outline",
      "Questions to ask an adviser",
      "A printable page to bring along",
    ],
    pills: [{ label: "Start with your field", href: routes.field }],
  },
];

export const outcomes = [
  {
    title: "Worth a closer look",
    body: "The evidence and your answers make an option a reasonable candidate to explore with an adviser. It is not a prescription.",
    tone: "bg-forest-100 text-forest-800",
  },
  {
    title: "No clear winner",
    body: "The options trade off against each other, or the evidence cannot separate them. We show the trade-offs rather than force a ranking.",
    tone: "bg-harvest-100 text-harvest-700",
  },
  {
    title: "Not enough evidence",
    body: "Data is missing or conflicting, or your field sits outside what the research covers. We say so instead of guessing.",
    tone: "bg-clay-100 text-clay-700",
  },
] as const;

export const wontClaim = [
  "Predict your yield or profit",
  "Boil the options down to one score",
  "Treat satellite images as a soil test",
  "Promise soil-carbon, erosion or nitrate results",
  "Assume trial results apply to every field",
] as const;

/** The three honest outcomes, then the limits, as stacked cards. */
export const honestyCards: readonly StackCardData[] = [
  ...outcomes.map((outcome, index): StackCardData => ({
    kicker: `Outcome 0${index + 1}`,
    title: outcome.title,
    desc: outcome.body,
  })),
  {
    kicker: "Limits",
    title: "Some things we won’t promise.",
    desc: "These stay off the page, however tempting a single number would be:",
    list: wontClaim,
    pills: [{ label: "See the evidence", href: "#evidence" }],
  },
];

export interface EvidenceSource {
  name: string;
  provider: string;
  role: string;
  evidence: EvidenceTypeId;
  scale: string;
}

export const evidenceSources: readonly EvidenceSource[] = [
  {
    name: "Harmonized Landsat Sentinel-2",
    provider: "NASA",
    role: "How green the field is through the year, and when the soil is bare.",
    evidence: "derived",
    scale: "30 m, cloud-screened",
  },
  {
    name: "POWER",
    provider: "NASA",
    role: "Temperature, rain and dry spells for your area.",
    evidence: "model_reanalysis",
    scale: "Grid of about 50 km, not your field",
  },
  {
    name: "Cropland Data Layer",
    provider: "USDA",
    role: "What was grown on the field each year.",
    evidence: "classified",
    scale: "30 m, 10 m from 2024",
  },
  {
    name: "SSURGO soil survey",
    provider: "USDA",
    role: "Soil type and drainage from soil survey maps.",
    evidence: "survey",
    scale: "Mapped units, not a test of this field",
  },
  {
    name: "Marsden Farm trial",
    provider: "Iowa State University",
    role: "Nine years of fertiliser and weed-killer records from an Iowa research farm (2003–2011).",
    evidence: "experimental",
    scale: "One research site, not a promise for your field",
  },
] as const;
