// Spotify-style color wash at the top of the page, like their album
// headers. Green at rest; --art-color follows the playing track's album
// art and the @property transition eases the change. `.deep` kicks in
// while audio plays so the shift registers.

interface BackdropProps {
  active?: boolean;
}

export default function Backdrop({ active = false }: BackdropProps) {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      style={{ background: "var(--color-bg)" }}
    >
      <div className={`top-wash${active ? " deep" : ""}`} />
    </div>
  );
}
