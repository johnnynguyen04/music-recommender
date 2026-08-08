"use client";

import { motion } from "framer-motion";
import GlassCard from "@/components/GlassCard";

// Camelot wheel: 12 positions, two rings. B (outer) = major, A (inner) = minor.
// Convention: 12 sits at 12 o'clock and numbers go clockwise. Putting 1 at
// the top reads as "rotated 30° off" to anyone who's used the wheel before.
const POSITIONS = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
const EXAMPLE_SEED = "8B";
const EXAMPLE_CANDIDATES = ["8B", "9B", "10B", "5A", "12A"];

export default function MusicTheory() {
  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_1fr] items-start">
      <div className="flex flex-col gap-6">
        <header className="flex flex-col gap-3">
          <span className="text-[0.66rem] font-medium uppercase tracking-[0.2em] text-(color:--color-fg-dim)">
            Theory
          </span>
          <h1 className="text-balance text-5xl font-bold leading-[0.98] tracking-[-0.035em] md:text-6xl">
            The Camelot wheel.
          </h1>
          <p className="max-w-[60ch] text-(color:--color-fg-muted) leading-relaxed">
            DJs use this wheel to figure out which songs will blend smoothly.
            Every musical key gets a number (1-12) and a letter (A for minor,
            B for major). Adjacent keys share most of their notes, so a cut
            between them sounds clean. Opposite sides clash.
          </p>
        </header>

        <div className="flex flex-col gap-3 text-sm text-(color:--color-fg-muted) leading-relaxed">
          <p>
            The Music-aware model uses this directly. When ranking candidate
            songs, it checks whether the candidate&apos;s key is close to your
            seeds&apos; keys on the wheel and rewards smaller distances.
          </p>
          <p>
            On the diagram, the seed song&apos;s key
            (<span className="num text-(color:--color-accent)">{EXAMPLE_SEED}</span>,
            which is C major) is highlighted green. The small green dots
            around the rim mark candidate songs the model is considering.
            Anything within one step of the seed will sound smooth; anything
            across the wheel will sound jarring without preparation.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 pt-2">
          <Stat label="Same code" value="0" />
          <Stat label="Adjacent" value="1" />
          <Stat label="Opposite face" value="6+" />
        </div>
      </div>

      <GlassCard className="p-6 md:p-8 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.94, rotate: -6 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          className="w-full"
        >
          <CamelotSVG seed={EXAMPLE_SEED} candidates={EXAMPLE_CANDIDATES} />
        </motion.div>
      </GlassCard>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] px-4 py-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="num text-[1.7rem] font-semibold leading-none tracking-tight text-(color:--color-accent)">{value}</div>
      <div className="mt-1.5 text-[0.66rem] uppercase tracking-[0.14em] text-(color:--color-fg-dim)">{label}</div>
    </div>
  );
}

function CamelotSVG({ seed, candidates }: { seed: string; candidates: string[] }) {
  const size = 360;
  const cx = size / 2;
  const cy = size / 2;
  const rOuter = 145;
  const rInner = 95;
  const segAngle = (2 * Math.PI) / 12;

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width="100%" className="mx-auto block max-w-[380px]">
      {POSITIONS.map((n, i) => {
        const ang = i * segAngle - Math.PI / 2;
        const a = ang - segAngle / 2;
        const b = ang + segAngle / 2;
        const outerPath = arcPath(cx, cy, rInner + 6, rOuter, a, b);
        const innerPath = arcPath(cx, cy, rInner - 38, rInner, a, b);
        const seedCode = parseCode(seed);
        const isOuterSeed = seedCode?.n === n && seedCode?.ring === "B";
        const isInnerSeed = seedCode?.n === n && seedCode?.ring === "A";

        const hasOuterCand = candidates.some((c) => {
          const p = parseCode(c); return p?.n === n && p.ring === "B";
        });
        const hasInnerCand = candidates.some((c) => {
          const p = parseCode(c); return p?.n === n && p.ring === "A";
        });

        return (
          <g key={n}>
            <path
              d={outerPath}
              fill={isOuterSeed ? "rgba(30,215,96,0.18)" : "rgba(255,255,255,0.025)"}
              stroke={isOuterSeed ? "rgba(30,215,96,0.6)" : "rgba(255,255,255,0.06)"}
              strokeWidth="0.5"
            />
            <path
              d={innerPath}
              fill={isInnerSeed ? "rgba(30,215,96,0.18)" : "rgba(255,255,255,0.015)"}
              stroke={isInnerSeed ? "rgba(30,215,96,0.6)" : "rgba(255,255,255,0.04)"}
              strokeWidth="0.5"
            />
            <text
              x={cx + (rOuter - 22) * Math.cos(ang)}
              y={cy + (rOuter - 22) * Math.sin(ang)}
              fill={isOuterSeed ? "#1ed760" : "#e5e5e5"}
              fontSize="11"
              fontFamily="var(--font-geist-mono)"
              fontWeight="500"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {n}B
            </text>
            <text
              x={cx + (rInner - 22) * Math.cos(ang)}
              y={cy + (rInner - 22) * Math.sin(ang)}
              fill={isInnerSeed ? "#1ed760" : "#a3a3a3"}
              fontSize="9.5"
              fontFamily="var(--font-geist-mono)"
              fontWeight="500"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {n}A
            </text>
            {/* candidate dots sit OUTWARD along the radial line from center,
                so they stay symmetric no matter where on the wheel they are */}
            {hasOuterCand && !isOuterSeed && (
              <circle
                cx={cx + (rOuter + 8) * Math.cos(ang)}
                cy={cy + (rOuter + 8) * Math.sin(ang)}
                r="3"
                fill="#1ed760"
                className="camelot-dot"
                style={{ animationDelay: `${i * 0.35}s` }}
              />
            )}
            {hasInnerCand && !isInnerSeed && (
              <circle
                cx={cx + (rInner - 56) * Math.cos(ang)}
                cy={cy + (rInner - 56) * Math.sin(ang)}
                r="2.5"
                fill="#1ed760"
                opacity="0.85"
                className="camelot-dot"
                style={{ animationDelay: `${i * 0.35 + 0.6}s` }}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
}

function parseCode(code: string): { n: number; ring: "A" | "B" } | null {
  const m = code.match(/^(\d{1,2})([AB])$/);
  if (!m) return null;
  return { n: parseInt(m[1], 10), ring: m[2] as "A" | "B" };
}

function arcPath(cx: number, cy: number, r1: number, r2: number, a1: number, a2: number) {
  const p1 = [cx + r1 * Math.cos(a1), cy + r1 * Math.sin(a1)];
  const p2 = [cx + r2 * Math.cos(a1), cy + r2 * Math.sin(a1)];
  const p3 = [cx + r2 * Math.cos(a2), cy + r2 * Math.sin(a2)];
  const p4 = [cx + r1 * Math.cos(a2), cy + r1 * Math.sin(a2)];
  const large = a2 - a1 > Math.PI ? 1 : 0;
  return `M ${p1[0]} ${p1[1]} L ${p2[0]} ${p2[1]} A ${r2} ${r2} 0 ${large} 1 ${p3[0]} ${p3[1]} L ${p4[0]} ${p4[1]} A ${r1} ${r1} 0 ${large} 0 ${p1[0]} ${p1[1]} Z`;
}
