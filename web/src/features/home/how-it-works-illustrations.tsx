import type { ReactNode } from "react";
import { cropPhases, strategies, type CropPhaseId } from "@/domain/strategies";
import { ACCENT, cropFill, Frame, INK, LABEL } from "./illustration-kit";

/**
 * Decorative illustrations for the "How it works" scroll stack, one per step.
 * They show the idea of each step with no real data or geography.
 */

/** Step 1: a patchwork of fields with one outlined by its four corners. */
function FieldIllustration() {
  const parcels: [string, string][] = [
    ["30,60 170,40 190,150 40,170", "maize"],
    ["186,38 330,56 316,150 200,150", "soybean"],
    ["346,58 490,44 480,160 332,150", "alfalfa"],
    ["30,186 150,180 140,330 34,340", "soybean"],
    ["360,176 490,184 484,340 350,330", "maize"],
    ["30,356 180,348 190,480 40,486", "alfalfa"],
    ["206,360 350,350 360,480 200,484", "soybean"],
    ["368,350 490,358 486,482 372,480", "maize"],
  ];
  return (
    <Frame>
      {parcels.map(([points, crop], index) => (
        <polygon
          key={index}
          points={points}
          fill={cropFill[crop as CropPhaseId]}
          opacity={0.5}
          stroke="#1d3a2a"
          strokeWidth={6}
          strokeLinejoin="round"
        />
      ))}
      <polygon
        points="170,176 340,164 352,328 162,340"
        fill="var(--color-crop-maize)"
        stroke={ACCENT}
        strokeWidth={3.5}
        strokeDasharray="10 8"
        strokeLinejoin="round"
      />
      {[
        [170, 176],
        [340, 164],
        [352, 328],
        [162, 340],
      ].map(([x, y]) => (
        <g key={`${x}-${y}`}>
          <circle cx={x} cy={y} r={13} fill={INK} />
          <circle cx={x} cy={y} r={7} fill={ACCENT} />
        </g>
      ))}
      <g transform="translate(206 232)">
        <rect width="104" height="34" rx="17" fill={INK} />
        <circle cx="19" cy="17" r="5" fill={ACCENT} />
        <text x="32" y="22" fill="#fff" fontSize="14" fontWeight="600">
          Your field
        </text>
      </g>
    </Frame>
  );
}

/** Step 2: the green-up curve through a year, the bare-ground stretches, and the crop history. */
function ProfileIllustration() {
  const history: CropPhaseId[] = [
    "maize",
    "soybean",
    "maize",
    "soybean",
    "maize",
    "soybean",
    "maize",
    "soybean",
  ];
  return (
    <Frame>
      <rect x="30" y="50" width="460" height="290" rx="22" fill={INK} opacity={0.55} />
      <rect
        x="30"
        y="50"
        width="76"
        height="290"
        rx="22"
        fill="var(--color-clay-700)"
        opacity={0.35}
      />
      <rect
        x="414"
        y="50"
        width="76"
        height="290"
        rx="22"
        fill="var(--color-clay-700)"
        opacity={0.35}
      />
      <path d="M50 120H470M50 190H470M50 260H470" stroke="#fff" strokeOpacity={0.1} />
      <path
        d="M50 296C110 296 130 288 170 230S240 96 300 100 380 176 410 262 450 300 470 300"
        fill="none"
        stroke={ACCENT}
        strokeWidth={5}
        strokeLinecap="round"
      />
      <path
        d="M50 296C110 296 130 288 170 230S240 96 300 100 380 176 410 262 450 300 470 300V320H50Z"
        fill={ACCENT}
        opacity={0.12}
      />
      <text x="56" y="76" fill={ACCENT} style={LABEL}>
        Green through the year
      </text>
      <text
        x="56"
        y="326"
        fill="#fff"
        fillOpacity={0.6}
        style={{ ...LABEL, fontSize: 11 }}
      >
        Bare
      </text>
      <text
        x="420"
        y="326"
        fill="#fff"
        fillOpacity={0.6}
        style={{ ...LABEL, fontSize: 11 }}
      >
        Bare
      </text>
      <text x="30" y="388" fill="#fff" fillOpacity={0.7} style={LABEL}>
        What was grown
      </text>
      {history.map((crop, index) => (
        <rect
          key={index}
          x={30 + index * 58}
          y={404}
          width={50}
          height={50}
          rx={12}
          fill={cropFill[crop]}
        />
      ))}
    </Frame>
  );
}

/** Step 3: what matters to you, as sliders and a switch. */
function PrioritiesIllustration() {
  const rows = [
    { label: "Soil health", value: 0.78 },
    { label: "Dry years", value: 0.45 },
    { label: "Input costs", value: 0.62 },
  ];
  return (
    <Frame>
      {rows.map((row, index) => {
        const y = 110 + index * 100;
        const knobX = 40 + row.value * 440;
        return (
          <g key={row.label}>
            <text x="40" y={y - 24} fill="#fff" fillOpacity={0.8} style={LABEL}>
              {row.label}
            </text>
            <rect
              x="40"
              y={y}
              width="440"
              height="12"
              rx="6"
              fill="#fff"
              opacity={0.14}
            />
            <rect x="40" y={y} width={row.value * 440} height="12" rx="6" fill={ACCENT} />
            <circle
              cx={knobX}
              cy={y + 6}
              r={19}
              fill={ACCENT}
              stroke={INK}
              strokeWidth={5}
            />
          </g>
        );
      })}
      <text x="40" y="386" fill="#fff" fillOpacity={0.8} style={LABEL}>
        What is possible on your farm
      </text>
      {["Manure", "Machinery", "Buyers"].map((label, index) => (
        <g key={label} transform={`translate(${40 + index * 150} 410)`}>
          <rect
            width="136"
            height="44"
            rx="22"
            fill={index === 1 ? "none" : ACCENT}
            stroke={ACCENT}
            strokeWidth={1.5}
          />
          <text
            x="68"
            y="27"
            textAnchor="middle"
            fill={index === 1 ? ACCENT : INK}
            fontSize="14"
            fontWeight="600"
          >
            {label}
          </text>
        </g>
      ))}
    </Frame>
  );
}

/** Step 4: the three rotations side by side, with an honest "not enough evidence" mark. */
function CompareIllustration() {
  const marks = ["var(--color-forest-600)", "var(--color-harvest-500)", "none"];
  return (
    <Frame>
      {strategies.map((strategy, row) => {
        const y = 70 + row * 130;
        const width = 330 / strategy.phases.length;
        return (
          <g key={strategy.id}>
            <circle cx="62" cy={y + 35} r="22" fill={ACCENT} />
            <text
              x="62"
              y={y + 41}
              textAnchor="middle"
              fill={INK}
              fontSize="18"
              fontWeight="700"
            >
              {strategy.id}
            </text>
            {strategy.phases.map((phase, index) => (
              <rect
                key={index}
                x={104 + index * width}
                y={y}
                width={width - 6}
                height={70}
                rx={14}
                fill={cropFill[phase]}
              />
            ))}
            <circle
              cx="470"
              cy={y + 35}
              r="14"
              fill={marks[row]}
              stroke={row === 2 ? "var(--color-clay-100)" : "none"}
              strokeWidth={2.5}
              strokeDasharray={row === 2 ? "4 4" : undefined}
            />
          </g>
        );
      })}
      <text
        x="40"
        y="478"
        fill="#fff"
        fillOpacity={0.7}
        style={{ ...LABEL, fontSize: 11 }}
      >
        Benefits · Trade-offs · Unknowns
      </text>
    </Frame>
  );
}

/** Step 5: a year-by-year outline on a sheet, ready to talk through with an adviser. */
function PlanIllustration() {
  const phases = strategies[2].phases;
  return (
    <Frame>
      <rect x="60" y="40" width="400" height="440" rx="24" fill="var(--color-paper)" />
      <text x="96" y="92" fill="var(--color-forest-700)" style={LABEL}>
        Your outline
      </text>
      {phases.map((phase, index) => (
        <g key={index} transform={`translate(96 ${122 + index * 62})`}>
          <text x="0" y="30" fill="var(--color-ink-faint)" fontSize="14" fontWeight="600">
            Y{index + 1}
          </text>
          <rect
            x="44"
            y="0"
            width={150 + index * 40}
            height="42"
            rx="12"
            fill={cropFill[phase]}
          />
          <text x="60" y="26" fill={INK} fontSize="14" fontWeight="600">
            {cropPhases[phase].label}
          </text>
        </g>
      ))}
      <path d="M96 386H424" stroke="var(--color-line)" strokeWidth={2} />
      <text
        x="96"
        y="418"
        fill="var(--color-forest-700)"
        style={{ ...LABEL, fontSize: 11 }}
      >
        Questions for your adviser
      </text>
      {[0, 1].map((i) => (
        <g key={i} transform={`translate(96 ${436 + i * 22})`}>
          <rect
            width="14"
            height="14"
            rx="4"
            fill="none"
            stroke="var(--color-forest-700)"
            strokeWidth={1.8}
          />
          <rect
            x="26"
            y="4"
            width={i === 0 ? 240 : 180}
            height="6"
            rx="3"
            fill="var(--color-line-strong)"
          />
        </g>
      ))}
    </Frame>
  );
}

export const howItWorksIllustrations: readonly ReactNode[] = [
  <FieldIllustration key="field" />,
  <ProfileIllustration key="profile" />,
  <PrioritiesIllustration key="priorities" />,
  <CompareIllustration key="compare" />,
  <PlanIllustration key="plan" />,
];
