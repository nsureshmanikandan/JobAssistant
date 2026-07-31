import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../types";

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listJobs().then((data) => {
      setJobs(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <p className="text-slate-500">Loading jobs...</p>;

  const pending = jobs.filter((j) => j.status === "pending_review");

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-slate-900">Pending Review ({pending.length})</h1>
        <button
          className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
          onClick={() => api.runSearchNow()}
        >
          Run search now
        </button>
      </div>
      <div className="grid gap-3">
        {pending.map((job) => (
          <Link
            key={job.id}
            to={`/jobs/${job.id}`}
            className="block bg-white border border-slate-200 rounded-lg p-4 hover:border-slate-400"
          >
            <div className="flex justify-between">
              <div>
                <p className="font-medium text-slate-900">{job.title}</p>
                <p className="text-sm text-slate-500">{job.company} — {job.location}</p>
              </div>
              <div className="text-right">
                <span className="inline-block bg-green-100 text-green-800 text-sm font-medium px-2 py-1 rounded">
                  {job.match_percentage}% match
                </span>
                {job.needs_manual_paste && (
                  <p className="text-xs text-amber-600 mt-1">Needs description pasted in</p>
                )}
              </div>
            </div>
          </Link>
        ))}
        {pending.length === 0 && (
          <p className="text-slate-500">No pending matches yet. Run a search or add a job manually.</p>
        )}
      </div>
    </div>
  );
}
