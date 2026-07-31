import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  RefreshCw, AlertTriangle, CheckCircle2, MapPin, Building2, Inbox, ChevronLeft, ChevronRight,
} from "lucide-react";
import { api } from "../api/client";
import type { Job } from "../types";

const PAGE_SIZE = 10;

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
  const [page, setPage] = useState(0);

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
      setPage(0);
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

  // Highest match first; unscored/failed jobs (null score) sort to the bottom.
  const pending = jobs
    .filter((j) => j.status === "pending_review" || j.status === "scoring_failed")
    .sort((a, b) => (b.match_percentage ?? -1) - (a.match_percentage ?? -1));

  const pageCount = Math.max(1, Math.ceil(pending.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const pageStart = currentPage * PAGE_SIZE;
  const pageItems = pending.slice(pageStart, pageStart + PAGE_SIZE);

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

      {pending.length === 0 ? (
        <div className="flex flex-col items-center text-center gap-3 bg-white border border-dashed border-slate-300 rounded-xl py-14">
          <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center">
            <Inbox className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <p className="font-medium text-indigo-950">No pending matches yet</p>
            <p className="text-sm text-slate-500 mt-1">Run a search or add a job manually to get started.</p>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100 overflow-hidden">
          {pageItems.map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="group flex items-center gap-3 px-4 py-2.5 hover:bg-indigo-50/50 transition-colors duration-150"
            >
              <p className="font-medium text-indigo-950 group-hover:text-indigo-600 transition-colors truncate flex-1 min-w-0">
                {job.title}
              </p>
              <span className="hidden sm:inline-flex items-center gap-1 text-sm text-slate-500 shrink-0 w-40 truncate">
                <Building2 className="h-3.5 w-3.5 shrink-0" />{job.company}
              </span>
              <span className="hidden md:inline-flex items-center gap-1 text-sm text-slate-500 shrink-0 w-28 truncate">
                <MapPin className="h-3.5 w-3.5 shrink-0" />{job.location}
              </span>
              {job.needs_manual_paste && (
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600 shrink-0" aria-label="Needs description pasted in" />
              )}
              <div className="shrink-0">
                <MatchBadge job={job} />
              </div>
            </Link>
          ))}
        </div>
      )}

      {pending.length > PAGE_SIZE && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-sm text-slate-500">
            Showing {pageStart + 1}-{Math.min(pageStart + PAGE_SIZE, pending.length)} of {pending.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              className="inline-flex items-center gap-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
            >
              <ChevronLeft className="h-4 w-4" /> Previous
            </button>
            <span className="text-sm text-slate-500 px-1">
              Page {currentPage + 1} of {pageCount}
            </span>
            <button
              className="inline-flex items-center gap-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              disabled={currentPage >= pageCount - 1}
            >
              Next <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
