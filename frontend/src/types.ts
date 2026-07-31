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
  job_title: string | null;
  job_company: string | null;
  job_source_url: string | null;
  has_tailored_resume: boolean;
  has_tailored_cover_letter: boolean;
}

export interface ResumeVersion {
  id: number;
  label: string;
  content: string;
  is_master: boolean;
  created_at: string;
}

export interface SearchCriteria {
  id: number;
  titles: string;
  location: string;
  fte_only: boolean;
  salary_min_lakhs: number;
  salary_max_lakhs: number;
  industry: string;
  min_company_size: number;
  exclude_sponsorship: boolean;
  updated_at: string;
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
