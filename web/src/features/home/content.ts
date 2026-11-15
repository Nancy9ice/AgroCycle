import type { EvidenceTypeId } from "@/domain/evidence";

export const decisionPoints = [
  {
    title: "What each option could offer",
    body: "Potential benefits for soil cover, weather risk and input use, each labelled as measured, published or only possible.",
    image: {
      src: "/images/fields/sunset-field.jpg",
      alt: "A harvested field at sunset, with long rows running to the horizon.",
    },
  },
  {
    title: "What it would cost you to try",
    body: "Trade-offs and practical needs: equipment, manure, storage, labour and somewhere to sell oats or hay.",
    image: {
      src: "/images/fields/tractor.jpg",
      alt: "A tractor with a long auger working through a field of ripe wheat.",
    },
  },
  {
    title: "What we don't know",
    body: "Evidence gaps, shown plainly. Missing information is never treated as good news.",
    image: {
      src: "/images/fields/misty-valley.jpg",
      alt: "Green hills with low cloud and a road fading into the distance.",
    },
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

export interface EvidenceSource {
  name: string;
  provider: string;
  role: string;
  evidence: EvidenceTypeId;
  scale: string;
  /** An illustrative photo for the scroll section, not a picture of real data. */
  image: { src: string; alt: string };
}

export const evidenceSources: readonly EvidenceSource[] = [
  {
    name: "Harmonized Landsat Sentinel-2",
    provider: "NASA",
    role: "How green the field is through the year, and when the soil is bare.",
    evidence: "derived",
    scale: "30 m, cloud-screened",
    image: {
      src: "/images/hero-left-unsplash.webp",
      alt: "A patchwork of green fields, orchards and a farmhouse seen from above.",
    },
  },
  {
    name: "POWER",
    provider: "NASA",
    role: "Temperature, rain and dry spells for your area.",
    evidence: "model_reanalysis",
    scale: "Grid of about 50 km, not your field",
    image: {
      src: "/images/evidence/weather-sky.jpg",
      alt: "Wide open sky over a green field at sunrise.",
    },
  },
  {
    name: "Cropland Data Layer",
    provider: "USDA",
    role: "What was grown on the field each year.",
    evidence: "classified",
    scale: "30 m, 10 m from 2024",
    image: {
      src: "/images/evidence/crop-rows.jpg",
      alt: "Young corn plants growing in a straight row.",
    },
  },
  {
    name: "SSURGO soil survey",
    provider: "USDA",
    role: "Soil type and drainage from soil survey maps.",
    evidence: "survey",
    scale: "Mapped units, not a test of this field",
    image: {
      src: "/images/evidence/soil.jpg",
      alt: "Dark soil and a garden scoop on a table.",
    },
  },
  {
    name: "Marsden Farm trial",
    provider: "Iowa State University",
    role: "Nine years of fertiliser and weed-killer records from an Iowa research farm (2003–2011).",
    evidence: "experimental",
    scale: "One research site, not a promise for your field",
    image: {
      src: "/images/evidence/research-field.jpg",
      alt: "Two people shaking hands in a field of ripe wheat.",
    },
  },
] as const;
