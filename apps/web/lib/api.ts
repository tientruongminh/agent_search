const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type JobStage =
  | "QUEUED"
  | "PLANNING"
  | "BUDGETING"
  | "DISCOVERING"
  | "EXPANDING"
  | "DEDUPING"
  | "VERIFYING"
  | "RANKING"
  | "PACKAGING"
  | "FEEDBACK_UPDATE"
  | "DONE"
  | "FAILED";

export type JobEvent = {
  ts: string;
  stage: JobStage;
  actor: string;
  event: string;
  payload: Record<string, unknown>;
};

export type JobStatus = {
  job_id: string;
  status: string;
  stage: JobStage;
  raw_request: string;
  fallback_mode?: string | null;
  reflection_count: number;
  progress: number;
  result_count: number;
  artifact_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  events: JobEvent[];
};

export type RankedFile = {
  id: string;
  title: string;
  local_path: string;
  download_url: string;
  sha256: string;
  file_type?: string | null;
  size_bytes: number;
  page_count?: number | null;
  source_domain?: string | null;
  summary?: string | null;
  why_selected: string[];
  verified_signals: string[];
  institution_score: number;
  topic_score: number;
  final_score: number;
  score_breakdown: Record<string, number>;
};

export type ArtifactItem = {
  id: string;
  name: string;
  kind: string;
  relative_path: string;
  download_url: string;
};

export type JobResults = {
  job_id: string;
  status: string;
  stage: JobStage;
  results: RankedFile[];
  artifacts: ArtifactItem[];
  fallback_explanation?: string | null;
  bundle_url?: string | null;
};

export type SearchPayload = {
  raw_request: string;
  goal?: string;
  preferred_formats?: string[];
  max_downloads?: number;
};

export async function createSearchJob(payload: SearchPayload) {
  const response = await fetch(`${API_BASE}/jobs/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to create search job");
  }
  return response.json() as Promise<{ job_id: string }>;
}

export async function fetchJobStatus(jobId: string) {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  return response.json() as Promise<JobStatus>;
}

export async function fetchJobResults(jobId: string) {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/results`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to fetch job results");
  }
  return response.json() as Promise<JobResults>;
}

export function buildArtifactUrl(path: string) {
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_BASE}${path}`;
}

