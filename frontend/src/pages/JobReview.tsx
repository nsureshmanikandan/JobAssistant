import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../types";

export default function JobReview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const jobId = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [tailoring, setTailoring] = useState(false);

  useEffect(() => {
    api.getJob(jobId).then(setJob);
  }, [jobId]);

  if (!job) return <p className="text-slate-500">Loading...</p>;

  const handleTailor = async () => {
    setTailoring(true);
    const updated = await api.tailorJob(jobId);
    setJob(updated);
    setTailoring(false);
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{job.title}</h1>
        <p className="text-slate-500">{job.company} — {job.location} — {job.match_percentage}% match</p>
      </div>

      <section>
        <h2 className="font-medium text-slate-800 mb-2">Job Description</h2>
        <pre className="whitespace-pre-wrap bg-white border border-slate-200 rounded-lg p-4 text-sm">
          {job.description}
        </pre>
      </section>

      {!job.tailored_resume && (
        <button
          className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
          onClick={handleTailor}
          disabled={tailoring}
        >
          {tailoring ? "Generating..." : "Generate tailored resume"}
        </button>
      )}

      {job.tailored_resume && (
        <>
          <section>
            <div className="flex justify-between items-center mb-2">
              <h2 className="font-medium text-slate-800">Tailored Resume</h2>
              <button className="text-sm text-slate-500" onClick={handleTailor}>Regenerate</button>
            </div>
            <textarea
              className="w-full h-64 border border-slate-200 rounded-lg p-3 text-sm font-mono"
              value={job.tailored_resume}
              onChange={(e) => setJob({ ...job, tailored_resume: e.target.value })}
            />
            <a
              className="inline-block mt-2 text-sm text-blue-600 underline"
              href={api.resumePdfUrl(jobId)}
              target="_blank"
              rel="noreferrer"
            >
              Download Resume PDF
            </a>
          </section>

          <section>
            <h2 className="font-medium text-slate-800 mb-2">Cover Letter</h2>
            <textarea
              className="w-full h-48 border border-slate-200 rounded-lg p-3 text-sm"
              value={job.tailored_cover_letter ?? ""}
              onChange={(e) => setJob({ ...job, tailored_cover_letter: e.target.value })}
            />
            <a
              className="inline-block mt-2 text-sm text-blue-600 underline"
              href={api.coverLetterPdfUrl(jobId)}
              target="_blank"
              rel="noreferrer"
            >
              Download Cover Letter PDF
            </a>
          </section>

          <div className="flex gap-3">
            <button className="bg-green-600 text-white px-4 py-2 rounded-md text-sm" onClick={handleApprove}>
              Approve — open application page
            </button>
            <button className="bg-slate-200 text-slate-800 px-4 py-2 rounded-md text-sm" onClick={handleReject}>
              Reject
            </button>
            <a
              className="ml-auto text-sm text-slate-500 self-center underline"
              href={job.source_url}
              target="_blank"
              rel="noreferrer"
            >
              View original posting
            </a>
          </div>
        </>
      )}
    </div>
  );
}
