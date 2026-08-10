// shared framer-motion variants. one source of truth so the motion feels
// consistent across tabs. keep these conservative.

import type { Variants, Transition } from "framer-motion";

export const spring: Transition = {
  type: "spring",
  stiffness: 220,
  damping: 26,
  mass: 0.6,
};

export const easeOut: Transition = {
  duration: 0.45,
  ease: [0.16, 1, 0.3, 1],
};

// page / tab fade. used by AnimatePresence in page.tsx.
export const tabPage: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { ...easeOut, when: "beforeChildren", staggerChildren: 0.05 } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.18 } },
};

// list item rise-and-fade. parent should set initial="initial" animate="animate"
// and define staggerChildren on its own variants.
export const item: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: spring },
  exit: { opacity: 0, y: -6, transition: { duration: 0.15 } },
};

// stagger container — no visual change itself, just propagates timing.
export const list: Variants = {
  initial: {},
  animate: { transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
  exit: {},
};

// for the alpha-weighting bar reveal.
export const grow: Variants = {
  initial: { scaleX: 0 },
  animate: { scaleX: 1, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] } },
};
