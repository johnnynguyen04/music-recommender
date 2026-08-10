// CSS-only aurora background, tinted by the playing track's album art.
// Invisible at rest; `active` fades it in while audio plays. All the heavy
// lifting (gradients, keyframes, blur, mask) lives in globals.css under
// .aurora-layer so tailwind v4 doesn't need to parse nested
// repeating-linear-gradients inside arbitrary-value brackets.

interface AuroraBackgroundProps {
  active?: boolean;
  showRadialGradient?: boolean;
}

export default function AuroraBackground({
  active = false,
  showRadialGradient = true,
}: AuroraBackgroundProps) {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      style={{ background: "var(--color-bg)" }}
    >
      <div
        className={`aurora-layer${active ? " on" : ""}${showRadialGradient ? " with-mask" : ""}`}
      />
    </div>
  );
}
