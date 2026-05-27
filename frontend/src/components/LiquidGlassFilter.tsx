// Mounts the shared SVG filter that every LiquidGlass surface references.
// Single global instance keeps the GPU pipeline cheap; the actual filter ID
// is exported so other components can target it via backdrop-filter.

import { LQG_DISPLACEMENT_MAP } from "./lqgMap";

export const LIQUID_FILTER_ID = "lqg-filter";

export default function LiquidGlassFilter() {
  return (
    <svg
      aria-hidden="true"
      className="pointer-events-none absolute h-0 w-0"
      style={{ position: "absolute", overflow: "hidden" }}
    >
      <filter id={LIQUID_FILTER_ID} primitiveUnits="objectBoundingBox">
        <feImage
          result="map"
          width="100%"
          height="100%"
          x="0"
          y="0"
          href={LQG_DISPLACEMENT_MAP}
          preserveAspectRatio="none"
        />
        <feGaussianBlur in="SourceGraphic" stdDeviation="0.01" result="blur" />
        <feDisplacementMap
          in="blur"
          in2="map"
          scale="0.5"
          xChannelSelector="R"
          yChannelSelector="G"
        />
      </filter>
    </svg>
  );
}
