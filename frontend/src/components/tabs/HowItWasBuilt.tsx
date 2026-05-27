"use client";

import { useEffect, useState } from "react";
import { api, type MetricsBlob } from "@/lib/api";
import GlassCard from "@/components/GlassCard";

export default function HowItWasBuilt() {
  const [m, setM] = useState<MetricsBlob | null>(null);
  useEffect(() => { api.metrics().then(setM).catch(() => {}); }, []);
  const mr = m?.match_rate;

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.6fr_1fr] items-start">
      <div className="flex flex-col gap-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            How it was built.
          </h1>
        </header>

        <div className="flex flex-col gap-5 text-sm leading-relaxed text-(color:--color-fg-muted) max-w-[68ch]">
          <p>
            The training data is 20,000 real Spotify playlists pulled from
            their Million Playlist Dataset, which Spotify released for
            research. Playlists range from 5 songs to a few hundred. For
            testing, the last 20% of each playlist is hidden and the model
            has to guess what was there.
          </p>
          <p>
            For the music-theory side, Spotify used to expose per-song
            features like tempo, key, and energy through a free API. They
            shut that off for new developer apps in late 2024, which is
            annoying but the reality. This project pulls those features from
            a public Kaggle dataset instead. It only covers about 2% of the
            tracks in the playlists, which is why the Music-aware model
            doesn&apos;t pull ahead by more than it does.
          </p>
          <p>
            All three models were scored on the same 2,000 held-out playlists
            with the same five metrics. None got hidden from the comparison
            table when its numbers came in lower than expected. That includes
            the neural model, which trails the classical baseline by a clear
            margin in this run.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <GlassCard className="p-5">
          <div className="text-[0.7rem] uppercase tracking-[0.16em] text-(color:--color-fg-dim)">
            Training playlists
          </div>
          <div className="num mt-1 text-3xl font-semibold text-(color:--color-fg)">20,000</div>
          <div className="mt-1 text-xs text-(color:--color-fg-muted)">First 20 slices of the MPD</div>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="text-[0.7rem] uppercase tracking-[0.16em] text-(color:--color-fg-dim)">
            Held-out for testing
          </div>
          <div className="num mt-1 text-3xl font-semibold text-(color:--color-fg)">2,000</div>
          <div className="mt-1 text-xs text-(color:--color-fg-muted)">Per-playlist tail holdout, 20%</div>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="text-[0.7rem] uppercase tracking-[0.16em] text-(color:--color-fg-dim)">
            Music feature coverage
          </div>
          <div className="num mt-1 text-3xl font-semibold text-(color:--color-accent)">
            {mr ? `${(mr.match_rate * 100).toFixed(1)}%` : "-"}
          </div>
          <div className="mt-1 text-xs text-(color:--color-fg-muted)">
            {mr ? `${mr.matched.toLocaleString()} of ${mr.total_mpd_tracks.toLocaleString()} tracks` : "loading"}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
