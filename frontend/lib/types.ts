export interface Lead {
  id: string;
  keyword: string;
  post_url: string;
  post_text: string;
  author_name: string;
  author_profile: string;
  top_comment?: string;
  timestamp: string;
  intent_score: number;
  intent_reason: string;
  source: string;
}

export interface SearchResponse {
  leads: Lead[];
  session_id: string;
  total_found: number;
  session_valid?: boolean;
  has_more: boolean;
}

export interface LoadMoreResponse {
  leads: Lead[];
  has_more: boolean;
  session_valid?: boolean;
}

export interface SessionStatus {
  logged_in: boolean;
  session_file_exists: boolean;
}

export type TimeFilter = "latest" | "7_days" | "14_days" | "27_days" | "2_months";

export interface Stats {
  total_leads: number;
  unique_keywords: number;
  keyword_breakdown: Record<string, number>;
  last_updated: string;
}

export type LeadState = "idle" | "loading" | "success" | "error" | "empty";
