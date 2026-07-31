import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Mail, ExternalLink, Inbox, Download } from "lucide-react";
import { api } from "../api/client";
import type { Application } from "../types";

const STATUSES = ["approved", "applied", "skipped"];

const STATUS_STYLES: Record<string, string> = {
  approved: "bg-indigo-50 text-indigo-700",
  applied: "bg-emerald-50 text-emerald-700",
  skipped: "bg-slate-100 text-slate-600",
};

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listApplications().then(setApplications).finally(() => setLoading(false));
  }, []);

  const handleStatusChange = async (id: number, status: string) => {
    const updated = await api.updateApplicationStatus(id, status);
    setApplications((prev) => prev.map((a) => (a.id === id ? { ...a, ...updated } : a)));
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-indigo-950 tracking-tight">Application History</h1>

      {!loading && applications.length === 0 && (
        <div className="flex flex-col items-center text-center gap-3 bg-white border border-dashed border-slate-300 rounded-xl py-14">
          <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center">
            <Inbox className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <p className="font-medium text-indigo-950">No applications yet</p>
            <p className="text-sm text-slate-500 mt-1">Approve a job from the Dashboard to see it here.</p>
          </div>
        </div>
      )}

      <div className="grid gap-3">
        {applications.map((application) => (
          <div key={application.id} className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="flex justify-between items-start gap-4">
              <div className="min-w-0">
                <Link to={`/jobs/${application.job_id}`} className="font-semibold text-indigo-950 hover:text-indigo-600">
                  {application.job_title ?? `Job #${application.job_id}`}
                </Link>
                <p className="text-sm text-slate-500 mt-0.5">{application.job_company}</p>
                <p className="text-xs text-slate-400 mt-1">
                  Applied: {application.applied_at ? new Date(application.applied_at).toLocaleDateString() : "—"}
                </p>
              </div>
              <select
                className={`text-xs font-semibold px-3 py-1.5 rounded-full border-0 cursor-pointer ${STATUS_STYLES[application.status] ?? "bg-slate-100 text-slate-600"}`}
                value={application.status}
                onChange={(e) => handleStatusChange(application.id, e.target.value)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-4 mt-4 pt-3 border-t border-slate-100 text-sm">
              {application.has_tailored_resume && (
                <span className="inline-flex items-center gap-1">
                  <a
                    className="inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 font-medium"
                    href={api.resumePdfUrl(application.job_id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <FileText className="h-4 w-4" /> Resume PDF
                  </a>
                  <a
                    className="text-slate-400 hover:text-indigo-600 p-1"
                    href={api.resumePdfDownloadUrl(application.job_id)}
                    aria-label="Download Resume PDF"
                    title="Download"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </a>
                </span>
              )}
              {application.has_tailored_cover_letter && (
                <span className="inline-flex items-center gap-1">
                  <a
                    className="inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 font-medium"
                    href={api.coverLetterPdfUrl(application.job_id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Mail className="h-4 w-4" /> Cover Letter PDF
                  </a>
                  <a
                    className="text-slate-400 hover:text-indigo-600 p-1"
                    href={api.coverLetterPdfDownloadUrl(application.job_id)}
                    aria-label="Download Cover Letter PDF"
                    title="Download"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </a>
                </span>
              )}
              {application.job_source_url && (
                <a
                  className="inline-flex items-center gap-1.5 text-slate-500 hover:text-indigo-600 ml-auto"
                  href={application.job_source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Original posting <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
