import type { Job, Application, LLMCallLogEntry, ResumeVersion, SearchCriteria } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Request to ${path} failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  listJobs: () => request<Job[]>("/jobs"),
  getJob: (id: number) => request<Job>(`/jobs/${id}`),
  createManualJob: (payload: Record<string, string>) =>
    request<Job>("/jobs/manual", { method: "POST", body: JSON.stringify(payload) }),
  tailorJob: (id: number) => request<Job>(`/jobs/${id}/tailor`, { method: "POST" }),
  approveJob: (id: number) => request<Job>(`/jobs/${id}/approve`, { method: "POST" }),
  rejectJob: (id: number) => request<Job>(`/jobs/${id}/reject`, { method: "POST" }),
  // "View" opens inline in a new tab (browser's own PDF viewer); "Download"
  // forces an actual file-save with no preview. Frontend/backend are
  // different origins, so this has to be a server-side Content-Disposition
  // switch (?download=true), not a client-side <a download> attribute.
  resumePdfUrl: (id: number) => `${BASE_URL}/jobs/${id}/resume.pdf`,
  resumePdfDownloadUrl: (id: number) => `${BASE_URL}/jobs/${id}/resume.pdf?download=true`,
  coverLetterPdfUrl: (id: number) => `${BASE_URL}/jobs/${id}/cover-letter.pdf`,
  coverLetterPdfDownloadUrl: (id: number) => `${BASE_URL}/jobs/${id}/cover-letter.pdf?download=true`,
  listApplications: () => request<Application[]>("/applications"),
  updateApplicationStatus: (id: number, status: string) =>
    request<Application>(`/applications/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) }),
  runSearchNow: (freshnessHours: number = 24) =>
    request<{ status: string; jobs_found: number; jobs_new: number; error: string | null }>(
      `/search/run?freshness_hours=${freshnessHours}`,
      { method: "POST" }
    ),
  listLlmCalls: () => request<LLMCallLogEntry[]>("/observability/llm-calls"),
  getSettings: () =>
    request<{ llm_provider: string; search_provider: string; match_threshold: number; scheduler_hour: number }>(
      "/settings"
    ),
  getMasterResume: () => request<ResumeVersion | null>("/settings/resume"),
  saveMasterResume: (content: string) =>
    request<ResumeVersion>("/settings/resume", {
      method: "PUT",
      body: JSON.stringify({ label: "master", content }),
    }),
  getCriteria: () => request<SearchCriteria>("/settings/criteria"),
  saveCriteria: (payload: Partial<SearchCriteria>) =>
    request<SearchCriteria>("/settings/criteria", { method: "PUT", body: JSON.stringify(payload) }),
  uploadMasterResume: async (file: File): Promise<ResumeVersion> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${BASE_URL}/settings/resume/upload`, { method: "POST", body: formData });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail || `Upload failed: ${response.status}`);
    }
    return response.json();
  },
};
