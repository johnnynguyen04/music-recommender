"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Info } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import { api, type MetricsBlob } from "@/lib/api";
import { list, item } from "@/lib/motion";

const MODELS = [
  { key: "classical", label: "Classical", note: "Matrix factorization (ALS)" },
  { key: "neural", label: "Neural", note: "Two-tower deep learning" },
  { key: "hybrid", label: "Music-aware", note: "Neural + music theory re-rank" },
] as const;

interface ColSpec {
  key: string;
  label: string;
  help: string;
  pct?: boolean;
}
const COLS: ColSpec[] = [
  {
    key: "ndcg@10",
    label: "Ranking quality",
    help: "How well-ranked the correct songs are in the top 10. Industry name: NDCG@10.",
  },
  {
    key: "hit@10",
    label: "Hit in top 10",
    help: "What share of test playlists had at least one correct song in the top 10 (Hit Rate@10).",
    pct: true,
  },
  {
    key: "hit@50",
    label: "Hit in top 50",
    help: "Same idea but checking the top 50 (Hit Rate@50).",
    pct: true,
  },
  {
    key: "precision@10",
    label: "Accuracy in top 10",
    help: "Of the 10 songs the model picked, what fraction were actually correct (Precision@10).",
  },
  {
    key: "recall@50",
    label: "Coverage in top 50",
    help: "Of all the correct songs we hid, what fraction the top 50 actually found (Recall@50).",
  },
];

export default function CompareModels() {
  const [m, setM] = useState<MetricsBlob | null>(null);
  useEffect(() => { api.metrics().then(setM).catch(() => {}); }, []);
  const comp = m?.comparison;

  return (
    <div className="flex flex-col gap-7">
      <header className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
          Compare models.
        </h1>
        <p className="max-w-[65ch] text-(color:--color-fg-muted) leading-relaxed">
          All three models tested the same way: take 2,000 real Spotify playlists,
          hide the last few songs, ask each model to predict them. Higher is
          better on every column. Nothing was removed when its number came in
          lower than expected.
        </p>
      </header>

      {!comp ? (
        <GlassCard className="p-8 text-sm text-(color:--color-fg-muted)">
          Metrics not loaded yet.
        </GlassCard>
      ) : (
        <GlassCard className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[0.7rem] uppercase tracking-[0.14em] text-(color:--color-fg-dim)">
                  <th className="sticky left-0 z-1 bg-transparent px-6 py-4 text-left font-semibold">Architecture</th>
                  {COLS.map((c) => (
                    <th
                      key={c.key}
                      className="px-4 py-4 text-right font-semibold align-bottom"
                    >
                      <ColumnLabel label={c.label} help={c.help} />
                    </th>
                  ))}
                </tr>
              </thead>
              <motion.tbody variants={list} initial="initial" animate="animate">
                {MODELS.map((mod) => {
                  const row = comp[mod.key] as Record<string, number>;
                  const isHybrid = mod.key === "hybrid";
                  return (
                    <motion.tr
                      key={mod.key}
                      variants={item}
                      className={
                        "border-t border-white/[0.04] " +
                        (isHybrid ? "bg-(color:--color-accent)/[0.04]" : "")
                      }
                    >
                      <td className="px-6 py-4 align-top">
                        <div className="flex items-center gap-2">
                          <span className={"h-1.5 w-1.5 rounded-full " + (isHybrid ? "bg-(color:--color-accent)" : "bg-white/30")} />
                          <div className="flex flex-col">
                            <span className="font-medium">{mod.label}</span>
                            <span className="text-[0.7rem] text-(color:--color-fg-dim)">{mod.note}</span>
                          </div>
                        </div>
                      </td>
                      {COLS.map((c) => (
                        <td key={c.key} className={"num px-4 py-4 text-right " + (isHybrid ? "text-(color:--color-accent)" : "")}>
                          {fmt(row?.[c.key], c.pct)}
                        </td>
                      ))}
                    </motion.tr>
                  );
                })}
              </motion.tbody>
            </table>
          </div>
          <div className="border-t border-white/[0.04] bg-black/30 px-6 py-3 text-[0.7rem] text-(color:--color-fg-dim)">
            <span className="num">{comp.eval_playlists?.toLocaleString()}</span> held-out playlists ·
            audio features matched for <span className="num">{Math.round(comp.audio_feature_match_rate * 1000) / 10}%</span> of catalog
          </div>
        </GlassCard>
      )}

      <p className="max-w-[65ch] text-sm leading-relaxed text-(color:--color-fg-muted)">
        The classical model wins. Counterintuitive but a known result: matrix
        factorization with implicit confidence scaling is a very strong baseline.
        Beating it would take more training time than this project ran for, plus
        better music feature coverage than the public Kaggle dataset offers.
        Both limits are written up in the README.
      </p>
    </div>
  );
}

function fmt(v: number | undefined, pct?: boolean) {
  if (v === undefined || v === null || Number.isNaN(v)) return "-";
  if (pct) return `${(v * 100).toFixed(1)}%`;
  return v.toFixed(4);
}

function ColumnLabel({ label, help }: { label: string; help: string }) {
  return (
    <span className="group relative inline-flex cursor-help items-center gap-1.5">
      {label}
      <Info size={11} className="text-(color:--color-fg-dim) opacity-70" aria-hidden="true" />
      <span
        role="tooltip"
        className="invisible pointer-events-none absolute right-0 top-full z-10 mt-2 w-64 rounded-xl border border-white/[0.08] bg-black/90 px-3 py-2 text-left text-[0.7rem] font-normal normal-case leading-relaxed tracking-normal text-(color:--color-fg-muted) opacity-0 shadow-[0_12px_32px_-12px_rgba(0,0,0,0.6)] backdrop-blur-md transition-opacity duration-150 group-hover:visible group-hover:opacity-100"
      >
        {help}
      </span>
    </span>
  );
}
