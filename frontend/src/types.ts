export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary_text: string | null;
  source_url: string;
  source_site: string;
  description: string | null;
  needs_manual_paste: boolean;
  match_percentage: number | null;
  matched_skills: string | null;
  missing_skills: string | null;
  sponsorship_required: boolean | null;
  company_size_estimate: string | null;
  scoring_reasoning: string | null;
  status: string;
  tailored_resume: string | null;
  tailored_cover_letter: string | null;
  created_at: string;
}

export interface Application {
  id: number;
  job_id: number;
  status: string;
  applied_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface LLMCallLogEntry {
  id: number;
  provider: string;
  model: string;
  prompt_id: string;
  job_id: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  latency_ms: number | null;
  success: boolean;
  created_at: string;
}
