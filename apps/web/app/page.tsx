import { SearchForm } from "@/components/search-form";

export default function HomePage() {
  return (
    <main className="mx-auto grid min-h-screen max-w-7xl gap-10 px-6 py-12 lg:grid-cols-[1.15fr_0.85fr]">
      <section className="grid content-start gap-8">
        <div className="inline-flex w-fit rounded-full bg-white/70 px-4 py-2 text-sm font-semibold uppercase tracking-[0.18em] text-teal shadow-panel">
          Agentic Material Search V2
        </div>
        <div className="grid gap-5">
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-ink">
            Search, verify, rank, and package academic materials with an orchestrated retrieval pipeline.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-600">
            This baseline ships a single-tenant product flow: submit a search task, poll job progress, inspect stage events, and download the ranked artifact bundle.
          </p>
        </div>
        <div className="rounded-[32px] bg-white/75 p-8 shadow-panel">
          <SearchForm />
        </div>
      </section>

      <aside className="grid content-start gap-6">
        <div className="rounded-[32px] bg-ink p-8 text-white shadow-panel">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-sand">Pipeline</p>
          <ul className="mt-6 grid gap-3 text-sm text-slate-200">
            <li>Intent parsing with OpenAI structured output and deterministic fallback</li>
            <li>Brave, GitHub, and crawler-based discovery</li>
            <li>Transport, format, semantic, and institution verification</li>
            <li>Goal-aware ranking and bundle packaging</li>
          </ul>
        </div>
        <div className="rounded-[32px] bg-white/75 p-8 shadow-panel">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-coral">Outputs</p>
          <div className="mt-5 grid gap-3 text-sm text-slate-700">
            <div className="rounded-2xl bg-sand p-4">`manifest.json`, `results.csv`, `summary.md`, `why_selected.json`, `bundle.zip`</div>
            <div className="rounded-2xl bg-mist p-4">Status polling with event timeline and ranked file table</div>
          </div>
        </div>
      </aside>
    </main>
  );
}

