"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import Brand from "@/components/Brand";
import GithubMark from "@/components/icons/GithubMark";
import AuroraBackground from "@/components/AuroraBackground";
import NowPlayingBar from "@/components/NowPlayingBar";
import TabNav, { TABS, type TabKey } from "@/components/TabNav";
import { useAudio } from "@/lib/audioPlayer";
import { cn } from "@/lib/utils";
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
  const { current } = useAudio();

  // tabs are deep-linkable: /#compare opens the comparison directly.
  // replaceState keeps back-button behavior sane (no history spam).
  useEffect(() => {
    const apply = () => {
      const h = window.location.hash.slice(1);
      if (TABS.some((t) => t.key === h)) setTab(h as TabKey);
    };
    apply();
    window.addEventListener("hashchange", apply);
    return () => window.removeEventListener("hashchange", apply);
  }, []);
  const changeTab = useCallback((t: TabKey) => {
    setTab(t);
    const base = window.location.pathname + window.location.search;
    window.history.replaceState(null, "", t === "try" ? base : `${base}#${t}`);
  }, []);

  return (
    <MotionConfig reducedMotion="user">
      <AuroraBackground />
      <div
        className={cn(
          "relative z-10 flex min-h-[100dvh] flex-col",
          // clear the fixed now-playing bar so it never covers the footer
          current && "pb-24 md:pb-20",
        )}
      >
        <motion.div
          variants={fadeUp}
          initial="initial"
          animate="animate"
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.25 }}
        >
          <Header tab={tab} onChange={changeTab} />
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
    </MotionConfig>
  );
}

// floating glass island, detached from the top edge. The lens layer gives
// it the same refraction as the cards so the whole chrome reads as one
// material. Mobile gets a second row inside the same island for the tabs.
function Header({ tab, onChange }: { tab: TabKey; onChange: (t: TabKey) => void }) {
  return (
    <header className="sticky top-0 z-20 px-3 pt-3 md:px-6 md:pt-4">
      <div className="mx-auto w-full max-w-[1160px]">
        <div className="relative isolate overflow-hidden rounded-[1.4rem] border border-white/[0.08] shadow-[0_16px_48px_-16px_rgba(0,0,0,0.65)] md:rounded-full">
          <span
            aria-hidden="true"
            className="liquid-lens pointer-events-none absolute inset-0 rounded-[inherit]"
          />
          <div className="relative z-10 flex h-[3.25rem] items-center gap-4 pl-5 pr-2.5 md:h-14">
            <Brand />
            <div className="hidden min-w-0 flex-1 justify-center md:flex">
              <TabNav active={tab} onChange={onChange} layoutGroup="desktop" />
            </div>
            <a
              href="https://github.com/johnnynguyen04/music-recommender"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
              className="ml-auto flex h-9 w-9 items-center justify-center rounded-full text-(color:--color-fg-muted) transition-colors duration-200 hover:bg-white/[0.07] hover:text-(color:--color-fg)"
            >
              <GithubMark size={17} />
            </a>
          </div>
          <div className="relative z-10 border-t border-white/[0.05] px-2 py-1.5 md:hidden">
            <TabNav active={tab} onChange={onChange} layoutGroup="mobile" />
          </div>
        </div>
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
