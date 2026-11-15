import type { ReactNode } from "react";
import { strategies } from "@/domain/strategies";
import { ACCENT, cropFill, Frame, INK, LABEL } from "./illustration-kit";

/** Decorative illustrations for the "Honest by nature" scroll stack: one per outcome, then the limits. */

function Ribbon({ y, id, dim }: { y: number; id: 0 | 1 | 2; dim?: boolean }) {
  const strategy = strategies[id];
  const width = 330 / strategy.phases.length;
  return (
    <g opacity={dim ? 0.4 : 1}>
      {strategy.phases.map((phase, index) => (
        <rect
          key={index}
          x={140 + index * width}
          y={y}
          width={width - 6}
          height={64}
          rx={14}
          fill={cropFill[phase]}
        />
      ))}
    </g>
  );
}

function Letter({ y, text }: { y: number; text: string }) {
  return (
    <g>
      <circle cx="90" cy={y + 32} r="22" fill={ACCENT} />
      <text
        x="90"
        y={y + 38}
        textAnchor="middle"
        fill={INK}
        fontSize="18"
        fontWeight="700"
      >
        {text}
      </text>
    </g>
  );
}

/** Outcome 1: one option stands out from the rest. */
function WorthALookIllustration() {
  return (
    <Frame>
      <Letter y={100} text="A" />
      <Ribbon y={100} id={0} dim />
      <rect
        x="26"
        y="196"
        width="468"
        height="112"
        rx="30"
        fill="none"
        stroke={ACCENT}
        strokeWidth={3}
        strokeDasharray="10 8"
      />
      <Letter y={220} text="B" />
      <Ribbon y={220} id={1} />
      <circle
        cx="462"
        cy="252"
        r="16"
        fill="var(--color-forest-600)"
        stroke="#fff"
        strokeWidth={3}
      />
      <path
        d="M455 252l5 5 9-10"
        fill="none"
        stroke="#fff"
        strokeWidth={3}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <Letter y={340} text="C" />
      <Ribbon y={340} id={2} dim />
      <text x="40" y="450" fill={ACCENT} style={LABEL}>
        A candidate to explore
      </text>
    </Frame>
  );
}

/** Outcome 2: the options balance, so we show trade-offs instead of a ranking. */
function NoWinnerIllustration() {
  return (
    <Frame>
      <path
        d="M260 150V400M170 400H350"
        stroke="#fff"
        strokeOpacity={0.5}
        strokeWidth={6}
        strokeLinecap="round"
      />
      <path d="M90 190H430" stroke={ACCENT} strokeWidth={6} strokeLinecap="round" />
      <path
        d="M90 190L60 290H120ZM430 190L400 290H460Z"
        fill="none"
        stroke="#fff"
        strokeOpacity={0.5}
        strokeWidth={3}
        strokeLinejoin="round"
      />
      <path
        d="M44 290H136A46 24 0 0 1 44 290ZM384 290H476A46 24 0 0 1 384 290Z"
        fill={ACCENT}
      />
      <circle cx="260" cy="190" r="14" fill={ACCENT} stroke={INK} strokeWidth={5} />
      <rect
        x="60"
        y="232"
        width="60"
        height="40"
        rx="10"
        fill="var(--color-crop-maize)"
      />
      <rect x="400" y="232" width="60" height="40" rx="10" fill="var(--color-crop-oat)" />
      <circle cx="90" cy="344" r="9" fill="var(--color-harvest-500)" />
      <circle cx="430" cy="344" r="9" fill="var(--color-harvest-500)" />
      <text x="260" y="460" textAnchor="middle" fill={ACCENT} style={LABEL}>
        Trade-offs, not a ranking
      </text>
    </Frame>
  );
}

/** Outcome 3: the evidence is missing, and we say so. */
function NotEnoughIllustration() {
  return (
    <Frame>
      <rect
        x="70"
        y="120"
        width="380"
        height="190"
        rx="30"
        fill="none"
        stroke="#fff"
        strokeOpacity={0.7}
        strokeWidth={3}
        strokeDasharray="12 10"
      />
      {[0, 1, 2, 3].map((index) => (
        <rect
          key={index}
          x={104 + index * 84}
          y={176}
          width={70}
          height={78}
          rx={14}
          fill="#fff"
          opacity={0.1}
        />
      ))}
      <circle
        cx="260"
        cy="215"
        r="44"
        fill={INK}
        stroke="var(--color-clay-100)"
        strokeWidth={3}
        strokeDasharray="6 6"
      />
      <text
        x="260"
        y="233"
        textAnchor="middle"
        fill="var(--color-clay-100)"
        fontSize="52"
        fontWeight="600"
        fontFamily="var(--font-display)"
      >
        ?
      </text>
      <text x="260" y="372" textAnchor="middle" fill={ACCENT} style={LABEL}>
        Missing is never good news
      </text>
    </Frame>
  );
}

/** Limits: the claims we will not make, each crossed out. */
function LimitsIllustration() {
  const claims = ["Yield", "Profit", "One score", "Soil carbon", "Nitrate"];
  return (
    <Frame>
      {claims.map((label, index) => {
        const y = 60 + index * 82;
        return (
          <g key={label} transform={`translate(70 ${y})`}>
            <rect
              width="380"
              height="58"
              rx="29"
              fill="#fff"
              opacity={0.08}
              stroke="#fff"
              strokeOpacity={0.25}
            />
            <circle cx="30" cy="29" r="14" fill="var(--color-clay-700)" />
            <path
              d="M24 23l12 12M36 23l-12 12"
              stroke="#fff"
              strokeWidth={3}
              strokeLinecap="round"
            />
            <text
              x="62"
              y="35"
              fill="#fff"
              fillOpacity={0.85}
              fontSize="18"
              fontWeight="500"
            >
              {label}
            </text>
            <path d="M58 29H300" stroke="#fff" strokeOpacity={0.35} strokeWidth={2} />
          </g>
        );
      })}
    </Frame>
  );
}

export const honestyIllustrations: readonly ReactNode[] = [
  <WorthALookIllustration key="worth" />,
  <NoWinnerIllustration key="balance" />,
  <NotEnoughIllustration key="missing" />,
  <LimitsIllustration key="limits" />,
];
