"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import GlassCard from "@/components/GlassCard";
import { api, type MetricsBlob } from "@/lib/api";

export default function HowItPicks() {
  const [metrics, setMetrics] = useState<MetricsBlob | null>(null);
  useEffect(() => { api.metrics().then(setMetrics).catch(() => {}); }, []);
  const alpha = (metrics?.hybrid?.alpha as number | undefined) ?? 0.9;
  const cfPct = Math.round(alpha * 100);
  const fitPct = 100 - cfPct;

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.5fr_1fr]">
      <div className="flex flex-col gap-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            How it picks.
          </h1>
          <p className="max-w-[60ch] text-(color:--color-fg-muted) leading-relaxed">
            Every suggestion gets two scores. The app blends them into one
            ranking. The blend ratio was tuned on a set of playlists the model
            never saw, so we know it generalizes.
          </p>
        </header>

        <div className="flex flex-col gap-5">
          <Block
            kicker="01"
            title="Listening pattern"
            body="The model has seen thousands of real playlists, so it knows which songs people tend to put together. If your starting songs show up alongside country music in lots of those playlists, you get country suggestions back. No genre tags, no editorial taste — just who-plays-what."
          />
          <Block
            kicker="02"
            title="Music fit"
            body="The Music-aware model also asks: do these songs actually sound right next to each other? Are the keys compatible, is the tempo close, does the energy line up? It's the same kind of check a DJ runs in their head when picking the next track to drop."
          />
        </div>
      </div>

      <GlassCard className="self-start p-6 md:p-7">
        <h2 className="text-[0.78rem] font-semibold uppercase tracking-[0.18em] text-(color:--color-fg-muted)">
          Final score split
        </h2>
        <div className="num mt-4 flex items-baseline justify-between">
          <div>
            <span className="text-3xl font-semibold text-(color:--color-accent)">{cfPct}%</span>
            <span className="ml-2 text-xs text-(color:--color-fg-muted)">Listening pattern</span>
          </div>
          <div className="text-right">
            <span className="text-2xl font-semibold text-(color:--color-fg-muted)">{fitPct}%</span>
            <span className="ml-2 text-xs text-(color:--color-fg-muted)">Music fit</span>
          </div>
        </div>
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-white/[0.05]">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: cfPct / 100 }}
            transition={{ duration: 0.95, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
            style={{ originX: 0 }}
            className="h-full w-full bg-(color:--color-accent)"
          />
        </div>
        <p className="mt-5 text-xs leading-relaxed text-(color:--color-fg-muted)">
          Listening patterns carry most of the weight; music fit nudges the
          rankings. The exact split came from trying every ratio on a held-out
          set of playlists and picking the one that scored highest.
        </p>
      </GlassCard>
    </div>
  );
}

function Block({ kicker, title, body }: { kicker: string; title: string; body: string }) {
  return (
    <div className="flex gap-5">
      <span className="num pt-1 text-xs text-(color:--color-fg-dim)">{kicker}</span>
      <div className="flex flex-col gap-1.5">
        <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
        <p className="max-w-[60ch] text-sm text-(color:--color-fg-muted) leading-relaxed">
          {body}
        </p>
      </div>
    </div>
  );
}
