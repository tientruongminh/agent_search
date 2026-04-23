import { JobEvent } from "@/lib/api";

export function JobTimeline({ events }: { events: JobEvent[] }) {
  if (!events.length) {
    return <div className="rounded-2xl bg-white/70 p-5 shadow-panel">No events yet.</div>;
  }

  return (
    <div className="rounded-[28px] bg-white/70 p-6 shadow-panel">
      <h2 className="mb-4 text-lg font-semibold">Stage Timeline</h2>
      <div className="grid gap-3">
        {events.map((event) => (
          <div key={`${event.ts}-${event.event}`} className="grid gap-1 rounded-2xl border border-slate-100 bg-white/80 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="font-semibold text-ink">{event.event}</p>
              <span className="rounded-full bg-mist px-3 py-1 text-xs font-semibold text-teal">{event.stage}</span>
            </div>
            <p className="text-sm text-slate-600">{event.actor}</p>
            <p className="text-xs text-slate-500">{new Date(event.ts).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

