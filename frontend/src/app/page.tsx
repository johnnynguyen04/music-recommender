"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Brand from "@/components/Brand";
import GithubMark from "@/components/icons/GithubMark";
import AuroraBackground from "@/components/AuroraBackground";
import NowPlayingBar from "@/components/NowPlayingBar";
import TabNav, { type TabKey } from "@/components/TabNav";
import TryIt from "@/components/tabs/TryIt";
import HowItPicks from "@/components/tabs/HowItPicks";
import CompareModels from "@/components/tabs/CompareModels";
import MusicTheory from "@/components/tabs/MusicTheory";
import HowItWasBuilt from "@/components/tabs/HowItWasBuilt";
import About from "@/components/tabs/About";
import { tabPage } from "@/lib/motion";

// first-load entrance: aurora fades in via CSS, header slides up after,
// main content lands last. Total choreography ~1s. Subsequent tab
// switches use only the inner tabPage variant, so the header doesn't
// re-animate every time.
const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

export default function Home() {
  const [tab, setTab] = useState<TabKey>("try");

  return (
    <>
      <AuroraBackground />
      <div className="relative z-10 flex min-h-[100dvh] flex-col">
        <motion.div
          variants={fadeUp}
          initial="initial"
          animate="animate"
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.25 }}
        >
          <Header tab={tab} onChange={setTab} />
        </motion.div>

        <main className="mx-auto w-full max-w-[1200px] flex-1 px-5 py-10 md:px-8 md:py-16">
          <motion.div
            variants={fadeUp}
            initial="initial"
            animate="animate"
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.45 }}
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={tab}
                variants={tabPage}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                {tab === "try" && <TryIt />}
                {tab === "how-it-picks" && <HowItPicks />}
                {tab === "compare" && <CompareModels />}
                {tab === "theory" && <MusicTheory />}
                {tab === "build" && <HowItWasBuilt />}
                {tab === "about" && <About />}
              </motion.div>
            </AnimatePresence>
          </motion.div>
        </main>

        <motion.div
          variants={fadeUp}
          initial="initial"
          animate="animate"
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.65 }}
        >
          <Footer />
        </motion.div>
      </div>
      <NowPlayingBar />
    </>
  );
}

function Header({ tab, onChange }: { tab: TabKey; onChange: (t: TabKey) => void }) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/[0.06] bg-black/60 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-[1200px] items-center gap-6 px-5 md:px-8">
        <Brand />
        <div className="hidden flex-1 md:block">
          <TabNav active={tab} onChange={onChange} />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <a
            href="https://github.com/johnnynguyen04/music-recommender"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            className="rounded-full p-2 text-(color:--color-fg-muted) transition-colors hover:bg-white/[0.05] hover:text-(color:--color-fg)"
          >
            <GithubMark size={18} />
          </a>
        </div>
      </div>
      <div className="border-t border-white/[0.04] px-3 py-2 md:hidden">
        <TabNav active={tab} onChange={onChange} />
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mx-auto w-full max-w-[1200px] px-5 pb-10 pt-6 text-xs text-(color:--color-fg-dim) md:px-8">
      <div className="flex flex-col gap-2 border-t border-white/[0.04] pt-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span>Built by Johnny Nguyen</span>
          <span className="text-(color:--color-border-strong)">·</span>
          <span>Spotify Million Playlist Dataset</span>
          <span className="text-(color:--color-border-strong)">·</span>
          <span>iTunes Preview API</span>
        </div>
        <div className="flex gap-4">
          <a className="hover:text-(color:--color-fg)" href="https://github.com/johnnynguyen04/music-recommender" target="_blank" rel="noopener noreferrer">Source</a>
          <a className="hover:text-(color:--color-fg)" href={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/docs"} target="_blank" rel="noopener noreferrer">API</a>
        </div>
      </div>
    </footer>
  );
}
