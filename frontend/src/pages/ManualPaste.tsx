import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function ManualPaste() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", company: "", location: "Chennai", source_url: "", description: "" });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const job = await api.createManualJob(form);
    setSubmitting(false);
    navigate(`/jobs/${job.id}`);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <h1 className="text-2xl font-semibold text-slate-900">Add a job manually</h1>
      {(["title", "company", "location", "source_url"] as const).map((field) => (
        <div key={field}>
          <label className="block text-sm font-medium text-slate-700 capitalize">
            {field.replace("_", " ")}
          </label>
          <input
            required={field !== "location"}
            className="mt-1 w-full border border-slate-300 rounded-md p-2 text-sm"
            value={form[field]}
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
          />
        </div>
      ))}
      <div>
        <label className="block text-sm font-medium text-slate-700">Job description (paste full text)</label>
        <textarea
          className="mt-1 w-full h-48 border border-slate-300 rounded-md p-2 text-sm"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
      >
        {submitting ? "Adding..." : "Add job"}
      </button>
    </form>
  );
}
