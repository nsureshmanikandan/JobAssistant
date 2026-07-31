import { useEffect, useRef, useState } from "react";
import { Upload, CheckCircle2, XCircle, Cpu, Search, Target, Clock, Pencil, Eye, SlidersHorizontal } from "lucide-react";
import { api } from "../api/client";
import ResumePreview from "../components/ResumePreview";
import TagInput from "../components/TagInput";
import type { SearchCriteria } from "../types";

interface SettingsResponse {
  llm_provider: string;
  search_provider: string;
  match_threshold: number;
  scheduler_hour: number;
}

const SETTINGS_TILES = [
  { key: "llm_provider" as const, label: "LLM provider", icon: Cpu },
  { key: "search_provider" as const, label: "Search provider", icon: Search },
  { key: "match_threshold" as const, label: "Match threshold", icon: Target, suffix: "%" },
  { key: "scheduler_hour" as const, label: "Daily search hour", icon: Clock, suffix: ":00" },
];

type Feedback = { kind: "success" | "error"; message: string } | null;

export default function Settings() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);
  const [viewMode, setViewMode] = useState<"edit" | "preview">("preview");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [criteria, setCriteria] = useState<SearchCriteria | null>(null);
  const [savingCriteria, setSavingCriteria] = useState(false);
  const [criteriaFeedback, setCriteriaFeedback] = useState<Feedback>(null);

  useEffect(() => {
    api.getSettings().then(setSettings);
    api.getMasterResume().then((resume) => {
      if (resume) setResumeText(resume.content);
    }).catch(() => {});
    api.getCriteria().then(setCriteria);
  }, []);

  const saveResume = async () => {
    setSaving(true);
    setFeedback(null);
    try {
      await api.saveMasterResume(resumeText);
      setFeedback({ kind: "success", message: "Master resume saved." });
    } catch (err) {
      setFeedback({ kind: "error", message: err instanceof Error ? err.message : "Save failed." });
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setFeedback(null);
    try {
      const resume = await api.uploadMasterResume(file);
      setResumeText(resume.content);
      setViewMode("preview");
      setFeedback({ kind: "success", message: `Extracted text from ${file.name} and set it as your master resume.` });
    } catch (err) {
      setFeedback({ kind: "error", message: err instanceof Error ? err.message : "Upload failed." });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const saveCriteria = async () => {
    if (!criteria) return;
    setSavingCriteria(true);
    setCriteriaFeedback(null);
    try {
      const updated = await api.saveCriteria(criteria);
      setCriteria(updated);
      setCriteriaFeedback({ kind: "success", message: "Search criteria saved — used for the next search run." });
    } catch (err) {
      setCriteriaFeedback({ kind: "error", message: err instanceof Error ? err.message : "Save failed." });
    } finally {
      setSavingCriteria(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold text-indigo-950 tracking-tight">Settings</h1>

      {settings && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {SETTINGS_TILES.map(({ key, label, icon: Icon, suffix }) => (
            <div key={key} className="min-w-0 bg-white border border-slate-200 rounded-xl p-4">
              <div className="flex items-center gap-1.5 text-slate-500 text-xs font-medium uppercase tracking-wide truncate">
                <Icon className="h-3.5 w-3.5 shrink-0" /> <span className="truncate">{label}</span>
              </div>
              <p className="mt-1 text-lg font-semibold text-indigo-950 truncate">
                {settings[key]}
                {suffix ?? ""}
              </p>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-slate-400 -mt-3">Providers are configured via the backend .env file, not editable here.</p>

      {criteria && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-indigo-600" />
            <h2 className="font-semibold text-indigo-950">Search Criteria</h2>
          </div>
          <p className="text-sm text-slate-500 -mt-2">
            Drives both daily discovery and manual scoring — job titles, location, and salary range to match against.
          </p>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-indigo-950 mb-1">
                Job titles <span className="text-slate-400 font-normal">(type and press Enter)</span>
              </label>
              <TagInput
                value={criteria.titles}
                onChange={(titles) => setCriteria({ ...criteria, titles })}
                placeholder="e.g. GenAI Architect"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-indigo-950 mb-1">
                Locations <span className="text-slate-400 font-normal">(type and press Enter)</span>
              </label>
              <TagInput
                value={criteria.location}
                onChange={(location) => setCriteria({ ...criteria, location })}
                placeholder="e.g. Chennai"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-indigo-950 mb-1">Industry</label>
              <input
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                value={criteria.industry}
                onChange={(e) => setCriteria({ ...criteria, industry: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-indigo-950 mb-1">Salary min (₹ lakhs)</label>
              <input
                type="number"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                value={criteria.salary_min_lakhs}
                onChange={(e) => setCriteria({ ...criteria, salary_min_lakhs: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-indigo-950 mb-1">Salary max (₹ lakhs)</label>
              <input
                type="number"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                value={criteria.salary_max_lakhs}
                onChange={(e) => setCriteria({ ...criteria, salary_max_lakhs: Number(e.target.value) })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-indigo-950 mb-1">Min company size (employees)</label>
              <input
                type="number"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                value={criteria.min_company_size}
                onChange={(e) => setCriteria({ ...criteria, min_company_size: Number(e.target.value) })}
              />
            </div>
            <div className="flex flex-col justify-end gap-2 pb-1">
              <label className="inline-flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  checked={criteria.fte_only}
                  onChange={(e) => setCriteria({ ...criteria, fte_only: e.target.checked })}
                />
                FTE only
              </label>
              <label className="inline-flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  checked={criteria.exclude_sponsorship}
                  onChange={(e) => setCriteria({ ...criteria, exclude_sponsorship: e.target.checked })}
                />
                Skip roles requiring sponsorship
              </label>
            </div>
          </div>

          {criteriaFeedback && (
            <div
              className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm ${
                criteriaFeedback.kind === "success" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"
              }`}
            >
              {criteriaFeedback.kind === "success" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 shrink-0" />
              )}
              {criteriaFeedback.message}
            </div>
          )}

          <button
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors duration-150 disabled:opacity-60 cursor-pointer"
            onClick={saveCriteria}
            disabled={savingCriteria}
          >
            {savingCriteria ? "Saving..." : "Save search criteria"}
          </button>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="flex justify-between items-center flex-wrap gap-2">
          <h2 className="font-semibold text-indigo-950">Master Resume</h2>
          <div className="flex items-center gap-2">
            <div className="inline-flex bg-slate-100 rounded-lg p-1">
              <button
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors duration-150 cursor-pointer ${
                  viewMode === "preview" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
                onClick={() => setViewMode("preview")}
              >
                <Eye className="h-3.5 w-3.5" /> Preview
              </button>
              <button
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors duration-150 cursor-pointer ${
                  viewMode === "edit" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
                onClick={() => setViewMode("edit")}
              >
                <Pencil className="h-3.5 w-3.5" /> Edit
              </button>
            </div>
            <label className="inline-flex items-center gap-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors duration-150">
              <Upload className="h-4 w-4" />
              {uploading ? "Uploading..." : "Upload .docx / .pdf"}
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx,.pdf"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </label>
          </div>
        </div>

        {feedback && (
          <div
            className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm ${
              feedback.kind === "success" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"
            }`}
          >
            {feedback.kind === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 shrink-0" />
            )}
            {feedback.message}
          </div>
        )}

        {viewMode === "preview" ? (
          <div className="w-full max-h-[36rem] overflow-y-auto bg-slate-100 rounded-lg p-6">
            <div className="max-w-[720px] mx-auto bg-white rounded-md shadow-sm border border-slate-200 px-10 py-10">
              <ResumePreview content={resumeText} />
            </div>
          </div>
        ) : (
          <textarea
            className="w-full h-96 border border-slate-300 rounded-lg p-4 text-sm font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Upload a file above, or paste your resume text directly."
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
          />
        )}
        <button
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors duration-150 disabled:opacity-60 cursor-pointer"
          onClick={saveResume}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save master resume"}
        </button>
      </div>
    </div>
  );
}
