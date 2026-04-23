import { JobStatusView } from "@/components/job-status-view";

export default function JobPage({ params }: { params: { jobId: string } }) {
  return <JobStatusView jobId={params.jobId} />;
}
