import Link from "next/link";

export default function Brand() {
  return (
    <Link
      href="/"
      className="num inline-flex items-baseline gap-1 text-(color:--color-accent) hover:opacity-80"
    >
      <span className="text-[1.05rem] font-semibold tracking-tight">music</span>
      <span className="text-[0.7rem] font-medium tracking-[0.18em] text-(color:--color-fg-muted)">
        / RECOMMENDER
      </span>
    </Link>
  );
}
