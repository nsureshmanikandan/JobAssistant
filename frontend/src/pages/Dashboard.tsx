import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw, AlertTriangle, CheckCircle2, MapPin, Building2, Inbox } from "lucide-react";
import { api } from "../api/client";
import type { Job } from "../types";

type SearchBanner = { kind: "success" | "error"; message: string } | null;

function MatchBadge({ job }: { job: Job }) {
  if (job.status === "scoring_failed") {
    return (
      <span className="inline-flex items-center gap-1 bg-red-50 text-red-700 text-xs font-medium px-2.5 py-1 rounded-full">
        <AlertTriangle className="h-3.5 w-3.5" /> Scoring failed
      </span>
    );
  }
  if (job.match_percentage === null) {
    return (
      <span className="inline-flex items-center bg-slate-100 text-slate-600 text-xs font-medium px-2.5 py-1 rounded-full">
        Not scored yet
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs font-semibold px-2.5 py-1 rounded-full">
      <CheckCircle2 className="h-3.5 w-3.5" /> {job.match_percentage}% match
    </span>
  );
}

const FRESHNESS_OPTIONS = [
  { hours: 24, label: "Last 24 hours" },
  { hours: 48, label: "Last 48 hours" },
  { hours: 72, label: "Last 72 hours" },
  { hours: 168, label: "Last 7 days" },
];

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [banner, setBanner] = useState<SearchBanner>(null);
  const [freshnessHours, setFreshnessHours] = useState(24);

  const loadJobs = () => api.listJobs().then(setJobs);

  useEffect(() => {
    loadJobs().finally(() => setLoading(false));
  }, []);

  const handleRunSearch = async () => {
    setSearching(true);
    setBanner(null);
    try {
      const run = await api.runSearchNow(freshnessHours);
      // A 200 response only means the request succeeded, not that the search
      // itself did — the backend can return status: "failed" (e.g. no search
      // API key configured) with an HTTP 200. Check run.status explicitly.
      if (run.status === "failed") {
        setBanner({ kind: "error", message: run.error || "Search run failed." });
      } else {
        setBanner({
          kind: "success",
          message: `Search complete — found ${run.jobs_found} posting(s), ${run.jobs_new} new.`,
        });
      }
      await loadJobs();
    } catch (err) {
      setBanner({ kind: "error", message: err instanceof Error ? err.message : "Search run failed." });
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-8 w-56 bg-slate-200 rounded" />
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-20 bg-white border border-slate-200 rounded-xl" />
        ))}
      </div>
    );
  }

  const pending = jobs.filter((j) => j.status === "pending_review" || j.status === "scoring_failed");

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-indigo-950 tracking-tight">Pending Review</h1>
          <p className="text-sm text-slate-500 mt-0.5">{pending.length} role{pending.length === 1 ? "" : "s"} waiting on you</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="border border-slate-300 rounded-lg text-sm px-3 py-2.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
            value={freshnessHours}
            onChange={(e) => setFreshnessHours(Number(e.target.value))}
            disabled={searching}
          >
            {FRESHNESS_OPTIONS.map((opt) => (
              <option key={opt.hours} value={opt.hours}>{opt.label}</option>
            ))}
          </select>
          <button
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            onClick={handleRunSearch}
            disabled={searching}
          >
            <RefreshCw className={`h-4 w-4 ${searching ? "animate-spin" : ""}`} />
            {searching ? "Searching..." : "Run search now"}
          </button>
        </div>
      </div>

      {banner && (
        <div
          role="status"
          className={`flex items-start gap-2 rounded-lg px-4 py-3 text-sm ${
            banner.kind === "success" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"
          }`}
        >
          {banner.kind === "success" ? (
            <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
          ) : (
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          )}
          <span>{banner.message}</span>
        </div>
      )}

      <div className="grid gap-3">
        {pending.map((job) => (
          <Link
            key={job.id}
            to={`/jobs/${job.id}`}
            className="group block bg-white border border-slate-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-md transition-all duration-150"
          >
            <div className="flex justify-between items-start gap-4">
              <div className="min-w-0">
                <p className="font-semibold text-indigo-950 group-hover:text-indigo-600 transition-colors">
                  {job.title}
                </p>
                <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                  <span className="inline-flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{job.company}</span>
                  <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{job.location}</span>
                </div>
              </div>
              <div className="text-right shrink-0 space-y-1">
                <MatchBadge job={job} />
                {job.needs_manual_paste && (
                  <p className="text-xs text-amber-600 flex items-center gap-1 justify-end">
                    <AlertTriangle className="h-3 w-3" /> Needs description pasted in
                  </p>
                )}
              </div>
            </div>
          </Link>
        ))}
        {pending.length === 0 && (
          <div className="flex flex-col items-center text-center gap-3 bg-white border border-dashed border-slate-300 rounded-xl py-14">
            <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center">
              <Inbox className="h-6 w-6 text-indigo-400" />
            </div>
            <div>
              <p className="font-medium text-indigo-950">No pending matches yet</p>
              <p className="text-sm text-slate-500 mt-1">Run a search or add a job manually to get started.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
