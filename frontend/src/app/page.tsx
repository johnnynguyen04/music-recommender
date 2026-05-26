// placeholder home. real layout lands once stitch mocks are in.
import Link from "next/link";
import { api } from "@/lib/api";

export default async function Home() {
  let healthOk = false;
  let loaded = false;
  let metricsAvailable = false;

  try {
    const h = await api.health();
    healthOk = h.status === "ok";
    loaded = h.loaded;
    const m = await api.metrics();
    metricsAvailable = !!m.comparison;
  } catch {
    // server not up; render the diagnostic block
  }

  return (
    <main className="mx-auto flex w-full max-w-[1100px] flex-col gap-12 px-6 py-20">
      <header className="flex flex-col gap-3">
        <span className="num text-xs uppercase tracking-[0.18em] text-(color:--color-fg-dim)">
          v0.1 · placeholder
        </span>
        <h1 className="text-5xl font-bold leading-none tracking-tighter md:text-6xl">
          Music Recommender
        </h1>
        <p className="max-w-[60ch] text-(color:--color-fg-muted) leading-relaxed">
          The real layout is coming. This page only exists to prove the Next.js app
          is wired up to the FastAPI server. Once the design mocks land, the six
          tabs will live here.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Diag label="FastAPI reachable" ok={healthOk} />
        <Diag label="Model loaded" ok={loaded} />
        <Diag label="Metrics available" ok={metricsAvailable} />
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Quick check</h2>
        <p className="text-(color:--color-fg-muted) text-sm leading-relaxed">
          The API server runs at{" "}
          <code className="num text-(color:--color-accent)">http://localhost:8000</code>.
          Open <Link href="http://localhost:8000/docs" className="text-(color:--color-accent) underline">
            the OpenAPI docs
          </Link>{" "}
          to poke at endpoints directly.
        </p>
      </section>
    </main>
  );
}

function Diag({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="rounded-(--radius-card) border border-(color:--color-border) bg-(color:--color-surface) p-5 card-hover">
      <div className="flex items-center gap-3">
        <span
          className={
            "h-2.5 w-2.5 rounded-full " +
            (ok ? "bg-(color:--color-accent)" : "bg-(color:--color-danger)")
          }
        />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="num mt-2 text-xs text-(color:--color-fg-dim)">
        {ok ? "ok" : "not reachable"}
      </div>
    </div>
  );
}
