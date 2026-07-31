import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { FilePlus2, XCircle } from "lucide-react";
import { api } from "../api/client";

const FIELDS = [
  { key: "title", label: "Job title", required: true },
  { key: "company", label: "Company", required: true },
  { key: "location", label: "Location", required: false },
  { key: "source_url", label: "Job posting URL", required: true },
] as const;

export default function ManualPaste() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", company: "", location: "Chennai", source_url: "", description: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const job = await api.createManualJob(form);
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add job.");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-indigo-950 tracking-tight mb-1">Add a job manually</h1>
      <p className="text-sm text-slate-500 mb-6">
        For roles found outside the daily automated search — paste the full description so it gets scored right away.
      </p>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-6 space-y-5">
        {FIELDS.map(({ key, label, required }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-indigo-950 mb-1">
              {label} {required && <span className="text-red-500">*</span>}
            </label>
            <input
              required={required}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          </div>
        ))}
        <div>
          <label className="block text-sm font-medium text-indigo-950 mb-1">
            Job description <span className="text-slate-400 font-normal">(paste full text — enables scoring)</span>
          </label>
          <textarea
            className="w-full h-48 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-50 text-red-800 rounded-lg px-4 py-3 text-sm">
            <XCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors duration-150 disabled:opacity-60 cursor-pointer"
        >
          <FilePlus2 className="h-4 w-4" /> {submitting ? "Adding..." : "Add job"}
        </button>
      </form>
    </div>
  );
}
