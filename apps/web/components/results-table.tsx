import { ArtifactItem, RankedFile, buildArtifactUrl } from "@/lib/api";

export function ResultsTable({
  results,
  artifacts
}: {
  results: RankedFile[];
  artifacts: ArtifactItem[];
}) {
  return (
    <div className="grid gap-6">
      <section className="rounded-[28px] bg-white/70 p-6 shadow-panel">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Ranked Results</h2>
          <span className="text-sm text-slate-600">{results.length} verified files</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="pb-3 pr-4">Title</th>
                <th className="pb-3 pr-4">Score</th>
                <th className="pb-3 pr-4">Type</th>
                <th className="pb-3 pr-4">Source</th>
                <th className="pb-3">Link</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result) => (
                <tr key={result.id} className="border-t border-slate-100">
                  <td className="py-4 pr-4">
                    <p className="font-semibold text-ink">{result.title}</p>
                    {result.summary ? <p className="mt-1 text-slate-600">{result.summary}</p> : null}
                  </td>
                  <td className="py-4 pr-4 font-semibold text-teal">{result.final_score.toFixed(2)}</td>
                  <td className="py-4 pr-4">{result.file_type ?? "unknown"}</td>
                  <td className="py-4 pr-4">{result.source_domain ?? "unknown"}</td>
                  <td className="py-4">
                    <a
                      href={result.download_url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-full border border-slate-200 px-3 py-2 font-medium text-ink hover:bg-slate-50"
                    >
                      Open source
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-[28px] bg-white/70 p-6 shadow-panel">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Artifacts</h2>
          <span className="text-sm text-slate-600">{artifacts.length} files</span>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {artifacts.map((artifact) => (
            <a
              key={artifact.id}
              href={buildArtifactUrl(artifact.download_url)}
              className="rounded-2xl border border-slate-100 bg-white/80 p-4 transition hover:-translate-y-0.5 hover:shadow-panel"
            >
              <p className="font-semibold text-ink">{artifact.name}</p>
              <p className="mt-1 text-sm text-slate-600">{artifact.kind}</p>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

