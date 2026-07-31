import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Sparkles, Download, CheckCircle2, XCircle, ExternalLink, Building2, MapPin, RotateCw, ArrowLeft,
} from "lucide-react";
import { api } from "../api/client";
import type { Job } from "../types";

export default function JobReview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const jobId = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [tailoring, setTailoring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getJob(jobId).then(setJob);
  }, [jobId]);

  if (!job) return <p className="text-slate-500">Loading...</p>;

  const handleTailor = async () => {
    setTailoring(true);
    setError(null);
    try {
      const updated = await api.tailorJob(jobId);
      setJob(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tailoring failed.");
    } finally {
      setTailoring(false);
    }
  };

  const handleApprove = async () => {
    await api.approveJob(jobId);
    navigate("/");
  };

  const handleReject = async () => {
    await api.rejectJob(jobId);
    navigate("/");
  };

  return (
    <div className="space-y-6 pb-10">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-indigo-600 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Dashboard
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-indigo-950 tracking-tight">{job.title}</h1>
        <div className="flex items-center gap-3 mt-1.5 text-sm text-slate-500">
          <span className="inline-flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{job.company}</span>
          <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{job.location}</span>
          {job.match_percentage !== null && (
            <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-2 py-0.5 rounded-full">
              {job.match_percentage}% match
            </span>
          )}
        </div>
      </div>

      <section className="bg-white border border-slate-200 rounded-xl p-5">
        <h2 className="font-semibold text-indigo-950 mb-2">Job Description</h2>
        <div className="whitespace-pre-wrap text-sm text-slate-700 leading-relaxed">
          {job.description}
        </div>
      </section>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 text-red-800 rounded-lg px-4 py-3 text-sm">
          <XCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {!job.tailored_resume && (
        <button
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors duration-150 disabled:opacity-60 cursor-pointer"
          onClick={handleTailor}
          disabled={tailoring}
        >
          <Sparkles className={`h-4 w-4 ${tailoring ? "animate-pulse" : ""}`} />
          {tailoring ? "Generating..." : "Generate tailored resume"}
        </button>
      )}

      {job.tailored_resume && (
        <>
          <section className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="flex justify-between items-center mb-3">
              <h2 className="font-semibold text-indigo-950">Tailored Resume</h2>
              <button
                className="inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 font-medium cursor-pointer"
                onClick={handleTailor}
                disabled={tailoring}
              >
                <RotateCw className={`h-3.5 w-3.5 ${tailoring ? "animate-spin" : ""}`} /> Regenerate
              </button>
            </div>
            <textarea
              className="w-full h-64 border border-slate-200 rounded-lg p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              value={job.tailored_resume}
              onChange={(e) => setJob({ ...job, tailored_resume: e.target.value })}
            />
            <a
              className="inline-flex items-center gap-1.5 mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-700 cursor-pointer"
              href={api.resumePdfUrl(jobId)}
              target="_blank"
              rel="noreferrer"
            >
              <Download className="h-4 w-4" /> Download Resume PDF
            </a>
          </section>

          <section className="bg-white border border-slate-200 rounded-xl p-5">
            <h2 className="font-semibold text-indigo-950 mb-3">Cover Letter</h2>
            <textarea
              className="w-full h-48 border border-slate-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              value={job.tailored_cover_letter ?? ""}
              onChange={(e) => setJob({ ...job, tailored_cover_letter: e.target.value })}
            />
            <a
              className="inline-flex items-center gap-1.5 mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-700 cursor-pointer"
              href={api.coverLetterPdfUrl(jobId)}
              target="_blank"
              rel="noreferrer"
            >
              <Download className="h-4 w-4" /> Download Cover Letter PDF
            </a>
          </section>

          <div className="flex items-center gap-3">
            <button
              className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors duration-150 cursor-pointer"
              onClick={handleApprove}
            >
              <CheckCircle2 className="h-4 w-4" /> Approve — open application page
            </button>
            <button
              className="inline-flex items-center gap-2 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors duration-150 cursor-pointer"
              onClick={handleReject}
            >
              <XCircle className="h-4 w-4" /> Reject
            </button>
            <a
              className="ml-auto inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-indigo-600"
              href={job.source_url}
              target="_blank"
              rel="noreferrer"
            >
              View original posting <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </>
      )}
    </div>
  );
}
