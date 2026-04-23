"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState, useTransition } from "react";

import { createSearchJob } from "@/lib/api";

const goals = [
  { value: "exam_preparation", label: "Exam preparation" },
  { value: "lecture_material", label: "Lecture material" },
  { value: "research_reference", label: "Research reference" },
  { value: "project_implementation", label: "Project implementation" },
  { value: "general_search", label: "General search" }
];

export function SearchForm() {
  const router = useRouter();
  const [rawRequest, setRawRequest] = useState("machine learning hcmus pdf");
  const [goal, setGoal] = useState("exam_preparation");
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        const payload = await createSearchJob({
          raw_request: rawRequest,
          goal,
          preferred_formats: ["pdf"],
          max_downloads: 10
        });
        router.push(`/jobs/${payload.job_id}`);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Unknown error");
      }
    });
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-5">
      <div className="grid gap-2">
        <label className="text-sm font-semibold uppercase tracking-[0.16em] text-teal">Search Request</label>
        <textarea
          value={rawRequest}
          onChange={(event) => setRawRequest(event.target.value)}
          rows={4}
          className="rounded-2xl border border-white/60 bg-white/80 px-4 py-3 text-base shadow-panel outline-none ring-0 backdrop-blur"
          placeholder="machine learning hcmus pdf"
        />
      </div>
      <div className="grid gap-2 sm:max-w-xs">
        <label className="text-sm font-semibold uppercase tracking-[0.16em] text-teal">Goal Profile</label>
        <select
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          className="rounded-xl border border-white/60 bg-white/80 px-4 py-3 shadow-panel outline-none"
        >
          {goals.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <button
          type="submit"
          disabled={isPending}
          className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-70"
        >
          {isPending ? "Submitting..." : "Launch Search Job"}
        </button>
        <span className="text-sm text-slate-600">Single-tenant baseline with polling UI and packaged outputs.</span>
      </div>
      {error ? <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
    </form>
  );
}

