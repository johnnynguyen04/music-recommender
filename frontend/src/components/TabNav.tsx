"use client";

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
}

export default function TabNav({ active, onChange }: TabNavProps) {
  return (
    <nav
      role="tablist"
      aria-label="Sections"
      className="no-scrollbar flex items-center gap-0.5 overflow-x-auto"
    >
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <button
            key={tab.key}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.key)}
            className={cn(
              "relative shrink-0 rounded-md px-3.5 py-2 text-[0.92rem] font-medium",
              "outline-none transition-colors duration-150",
              "focus-visible:ring-2 focus-visible:ring-(color:--color-accent)/40",
              isActive
                ? "text-(color:--color-fg)"
                : "text-(color:--color-fg-muted) hover:bg-white/[0.04] hover:text-(color:--color-fg)",
            )}
          >
            <span className="relative z-10">{tab.label}</span>
            {isActive && (
              <motion.span
                layoutId="tab-underline"
                aria-hidden="true"
                transition={{ type: "spring", stiffness: 380, damping: 32, mass: 0.6 }}
                className="absolute inset-x-3 -bottom-px h-[2px] rounded-full bg-(color:--color-accent)"
              />
            )}
          </button>
        );
      })}
    </nav>
  );
}
