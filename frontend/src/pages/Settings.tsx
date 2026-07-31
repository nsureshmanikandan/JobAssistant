import { useEffect, useState } from "react";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface SettingsResponse {
  llm_provider: string;
  search_provider: string;
  match_threshold: number;
  scheduler_hour: number;
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/settings`).then((r) => r.json()).then(setSettings);
    fetch(`${BASE_URL}/settings/resume`).then((r) => (r.ok ? r.json() : null)).then((r) => {
      if (r) setResumeText(r.content);
    });
  }, []);

  const saveResume = async () => {
    setSaving(true);
    await fetch(`${BASE_URL}/settings/resume`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: "master", content: resumeText }),
    });
    setSaving(false);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>

      {settings && (
        <div className="bg-white border border-slate-200 rounded-lg p-4 text-sm space-y-1">
          <p><span className="font-medium">LLM provider:</span> {settings.llm_provider}</p>
          <p><span className="font-medium">Search provider:</span> {settings.search_provider}</p>
          <p><span className="font-medium">Match threshold:</span> {settings.match_threshold}%</p>
          <p><span className="font-medium">Daily search hour:</span> {settings.scheduler_hour}:00</p>
          <p className="text-slate-400 text-xs mt-2">
            Providers are configured via the backend .env file, not editable here.
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Master Resume</label>
        <textarea
          className="w-full h-64 border border-slate-300 rounded-md p-2 text-sm font-mono"
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
        />
        <button
          className="mt-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
          onClick={saveResume}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save master resume"}
        </button>
      </div>
    </div>
  );
}
