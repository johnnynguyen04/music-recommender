"use client";

import { ArrowUpRight } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import GithubMark from "@/components/icons/GithubMark";

export default function About() {
  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.4fr_1fr] items-start">
      <div className="flex flex-col gap-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">About.</h1>
          <p className="max-w-[60ch] text-(color:--color-fg-muted) leading-relaxed">
            Built by Johnny Nguyen. Source code, training scripts, and a longer
            write-up live on GitHub.
          </p>
        </header>

        <div className="flex flex-wrap gap-3">
          <a
            href="https://github.com/johnnynguyen04/music-recommender"
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-sm text-(color:--color-fg-muted) transition-colors hover:border-white/[0.16] hover:text-(color:--color-fg)"
          >
            <GithubMark size={15} />
            github.com/johnnynguyen04/music-recommender
            <ArrowUpRight size={14} className="opacity-60 group-hover:opacity-100" />
          </a>
        </div>
      </div>

      <GlassCard className="p-6">
        <div className="text-[0.7rem] uppercase tracking-[0.16em] text-(color:--color-fg-muted)">Stack</div>
        <ul className="mt-3 flex flex-col gap-1.5 text-sm text-(color:--color-fg-muted)">
          <li><span className="num text-(color:--color-accent)">·</span> Next.js 16, Tailwind v4, TypeScript</li>
          <li><span className="num text-(color:--color-accent)">·</span> FastAPI inference server</li>
          <li><span className="num text-(color:--color-accent)">·</span> PyTorch two-tower model, ALS baseline</li>
          <li><span className="num text-(color:--color-accent)">·</span> Spotify Million Playlist Dataset</li>
          <li><span className="num text-(color:--color-accent)">·</span> Model checkpoint hosted on AWS S3</li>
        </ul>
      </GlassCard>
    </div>
  );
}
