"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchJobResults, fetchJobStatus, JobResults, JobStatus } from "@/lib/api";
import { JobTimeline } from "@/components/job-timeline";
import { ResultsTable } from "@/components/results-table";

export function JobStatusView({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [results, setResults] = useState<JobResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let timer: NodeJS.Timeout | undefined;

    async function load() {
      try {
        const nextStatus = await fetchJobStatus(jobId);
        if (!active) {
          return;
        }
        setStatus(nextStatus);
        if (nextStatus.stage === "DONE" || nextStatus.stage === "FAILED") {
          const nextResults = await fetchJobResults(jobId);
          if (!active) {
            return;
          }
          setResults(nextResults);
        } else {
          timer = setTimeout(load, 2000);
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unknown error");
      }
    }

    void load();
    return () => {
      active = false;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [jobId]);

  return (
    <div className="mx-auto grid max-w-7xl gap-8 px-6 py-10 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="grid gap-8">
        <div className="rounded-[32px] bg-white/70 p-8 shadow-panel">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal">Job Progress</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink">{jobId}</h1>
            </div>
            <Link href="/" className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-ink">
              New Search
            </Link>
          </div>
          {status ? (
            <div className="grid gap-5">
              <div className="grid gap-2">
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>{status.stage}</span>
                  <span>{status.progress}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-gradient-to-r from-teal to-coral" style={{ width: `${status.progress}%` }} />
                </div>
              </div>
              <div className="grid gap-2 rounded-2xl bg-mist p-4">
                <p className="font-medium text-ink">{status.raw_request}</p>
                <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                  <span>Results: {status.result_count}</span>
                  <span>Artifacts: {status.artifact_count}</span>
                  <span>Reflections: {status.reflection_count}</span>
                  <span>Fallback: {status.fallback_mode ?? "none"}</span>
                </div>
              </div>
              {status.error_message ? <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{status.error_message}</p> : null}
            </div>
          ) : (
            <p className="text-slate-600">Loading job status...</p>
          )}
          {error ? <p className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
        </div>

        {results ? (
          <ResultsTable results={results.results} artifacts={results.artifacts} />
        ) : (
          <div className="rounded-[28px] bg-white/70 p-6 shadow-panel">
            <p className="text-slate-600">Results will appear once the job reaches a terminal state.</p>
          </div>
        )}
      </div>
      <JobTimeline events={status?.events ?? []} />
    </div>
  );
}

