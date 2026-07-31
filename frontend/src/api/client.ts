import type { Job, Application, LLMCallLogEntry } from "../types";

const BASE_URL = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed: ${response.status}`);
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
  resumePdfUrl: (id: number) => `${BASE_URL}/jobs/${id}/resume.pdf`,
  coverLetterPdfUrl: (id: number) => `${BASE_URL}/jobs/${id}/cover-letter.pdf`,
  listApplications: () => request<Application[]>("/applications"),
  updateApplicationStatus: (id: number, status: string) =>
    request<Application>(`/applications/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) }),
  runSearchNow: () => request<unknown>("/search/run", { method: "POST" }),
  listLlmCalls: () => request<LLMCallLogEntry[]>("/observability/llm-calls"),
};
