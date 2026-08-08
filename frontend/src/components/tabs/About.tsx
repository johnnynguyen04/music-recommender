"use client";

import { ArrowUpRight } from "@phosphor-icons/react";
import GlassCard from "@/components/GlassCard";
import GithubMark from "@/components/icons/GithubMark";

export default function About() {
  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.4fr_1fr] items-start">
      <div className="flex flex-col gap-6">
        <header className="flex flex-col gap-3">
          <span className="text-[0.66rem] font-medium uppercase tracking-[0.2em] text-(color:--color-fg-dim)">
            Credits
          </span>
          <h1 className="text-balance text-5xl font-bold leading-[0.98] tracking-[-0.035em] md:text-6xl">About.</h1>
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
            className="group inline-flex items-center gap-2.5 rounded-full border border-white/[0.08] bg-white/[0.02] py-1.5 pl-4 pr-1.5 text-sm text-(color:--color-fg-muted) transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-px hover:border-white/[0.16] hover:text-(color:--color-fg) active:scale-[0.98]"
          >
            <GithubMark size={15} />
            github.com/johnnynguyen04/music-recommender
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/[0.06] transition-transform duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:bg-(color:--color-accent) group-hover:text-black">
              <ArrowUpRight size={13} weight="bold" />
            </span>
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
