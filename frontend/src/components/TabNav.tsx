"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export type TabKey =
  | "try"
  | "how-it-picks"
  | "compare"
  | "theory"
  | "build"
  | "about";

export const TABS: { key: TabKey; label: string }[] = [
  { key: "try", label: "Try it" },
  { key: "how-it-picks", label: "How it picks" },
  { key: "compare", label: "Compare models" },
  { key: "theory", label: "Music theory" },
  { key: "build", label: "How it was built" },
  { key: "about", label: "About" },
];

interface TabNavProps {
  active: TabKey;
  onChange: (k: TabKey) => void;
  /** distinct layoutId namespace — the nav renders twice (desktop + mobile)
      and duplicate layoutIds would make framer animate between the copies. */
  layoutGroup?: string;
}

export default function TabNav({ active, onChange, layoutGroup = "main" }: TabNavProps) {
  // keep the active pill visible when the strip scrolls (mobile deep links)
  const activeRef = useRef<HTMLButtonElement | null>(null);
  useEffect(() => {
    activeRef.current?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
  }, [active]);

  return (
    <nav
      role="tablist"
      aria-label="Sections"
      className="no-scrollbar flex items-center gap-1 overflow-x-auto"
    >
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <button
            key={tab.key}
            ref={isActive ? activeRef : null}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.key)}
            className={cn(
              "relative shrink-0 rounded-full px-3.5 py-1.5 text-[0.86rem] font-medium",
              "outline-none transition-colors duration-200",
              "focus-visible:ring-2 focus-visible:ring-(color:--color-accent)/40",
              isActive
                ? "text-(color:--color-fg)"
                : "text-(color:--color-fg-dim) hover:text-(color:--color-fg)",
            )}
          >
            {isActive && (
              <motion.span
                layoutId={`tab-pill-${layoutGroup}`}
                aria-hidden="true"
                transition={{ type: "spring", stiffness: 420, damping: 34, mass: 0.7 }}
                className="absolute inset-0 rounded-full bg-white/[0.09] shadow-[inset_0_1px_0_rgba(255,255,255,0.10),inset_0_-1px_1px_rgba(0,0,0,0.2)]"
              />
            )}
            <span className="relative z-10">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
