// CSS-only aurora background. green palette, slow drift (60s loop).
// All the heavy lifting (gradients, keyframes, blur, mask) lives in
// globals.css under .aurora-layer so tailwind v4 doesn't need to parse
// nested repeating-linear-gradients inside arbitrary-value brackets.

interface AuroraBackgroundProps {
  showRadialGradient?: boolean;
}

export default function AuroraBackground({
  showRadialGradient = true,
}: AuroraBackgroundProps) {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      style={{ background: "var(--color-bg)" }}
    >
      <div className={`aurora-layer${showRadialGradient ? " with-mask" : ""}`} />
    </div>
  );
}
