import { useId, type SVGProps } from "react";
import type { CropPhaseId } from "@/domain/strategies";

interface Parcel {
  points: string;
  crop: CropPhaseId;
  angle: number;
  highlight?: boolean;
}

/** Illustrative patchwork of parcels. Decorative: no data, no real geography. */
const parcels: readonly Parcel[] = [
  { points: "10,10 170,0 180,140 20,150", crop: "maize", angle: 12 },
  { points: "186,0 340,12 332,128 192,146", crop: "soybean", angle: -20 },
  { points: "356,14 510,6 504,150 348,134", crop: "oat-red-clover", angle: 70 },
  { points: "20,166 190,162 176,300 14,310", crop: "alfalfa", angle: 35 },
  { points: "206,162 350,150 360,300 192,318", crop: "maize", angle: 8, highlight: true },
  { points: "368,150 512,166 506,310 374,300", crop: "soybean", angle: -50 },
  { points: "10,326 168,318 180,470 4,470", crop: "soybean", angle: 28 },
  { points: "196,334 352,318 346,470 188,470", crop: "oat-alfalfa", angle: -12 },
  { points: "370,316 514,326 516,470 366,470", crop: "maize", angle: 60 },
];

const fillClass: Record<CropPhaseId, string> = {
  maize: "fill-crop-maize",
  soybean: "fill-crop-soybean",
  "oat-red-clover": "fill-crop-oat",
  "oat-alfalfa": "fill-crop-oat",
  alfalfa: "fill-crop-alfalfa",
};

export function FieldPatchwork({ className, ...props }: SVGProps<SVGSVGElement>) {
  const id = useId();

  return (
    <svg
      viewBox="0 0 520 480"
      role="img"
      aria-label="Illustration: a patchwork of farm fields in different crops, with one field outlined as your field."
      className={className}
      {...props}
    >
      <defs>
        {parcels.map((parcel, index) => (
          <pattern
            key={index}
            id={`${id}-rows-${index}`}
            width="9"
            height="9"
            patternUnits="userSpaceOnUse"
            patternTransform={`rotate(${parcel.angle})`}
          >
            <rect width="9" height="9" className={fillClass[parcel.crop]} />
            <rect width="2" height="9" fill="#16201a" opacity="0.14" />
          </pattern>
        ))}
      </defs>

      {parcels.map((parcel, index) => (
        <polygon
          key={index}
          points={parcel.points}
          fill={`url(#${id}-rows-${index})`}
          stroke="#f0f6ef"
          strokeWidth="6"
          strokeLinejoin="round"
        />
      ))}

      {/* Highlighted parcel: "your field" */}
      {parcels
        .filter((parcel) => parcel.highlight)
        .map((parcel) => (
          <polygon
            key="highlight"
            points={parcel.points}
            fill="none"
            stroke="#0e2616"
            strokeWidth="3.5"
            strokeDasharray="9 7"
            strokeLinejoin="round"
          />
        ))}

      <g transform="translate(212 200)">
        <rect width="136" height="36" rx="18" fill="#0e2616" />
        <circle cx="20" cy="18" r="5" fill="#e3b33f" />
        <text
          x="34"
          y="23"
          fontSize="15"
          fontWeight="600"
          fill="#fff"
          fontFamily="var(--font-sans)"
        >
          Your field
        </text>
      </g>
    </svg>
  );
}
