import type { SearchResponse, LoadMoreResponse, SessionStatus, Stats, TimeFilter } from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function searchLeads(keyword: string, timeFilter: TimeFilter): Promise<SearchResponse> {
  return fetcher<SearchResponse>(`${BASE}/search`, {
    method: 'POST',
    body: JSON.stringify({ keyword, time_filter: timeFilter }),
  });
}

export async function loadMoreLeads(sessionId: string): Promise<LoadMoreResponse> {
  return fetcher<LoadMoreResponse>(`${BASE}/load-more`, {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function getSessionStatus(): Promise<SessionStatus> {
  return fetcher<SessionStatus>(`${BASE}/session/status`);
}

export async function triggerLogin(email: string, password: string): Promise<{ success: boolean; message: string }> {
  const start = await fetcher<{ success: boolean; message: string }>(`${BASE}/session/login`, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (!start.success) return start;

  for (let i = 0; i < 150; i++) {
    await new Promise((r) => setTimeout(r, 2000));
    try {
      const status = await fetcher<{ running: boolean; done: boolean; success: boolean | null }>(`${BASE}/session/login-status`);
      if (status.done) {
        return { success: status.success === true, message: status.success ? "Login completed" : "Login failed" };
      }
    } catch {
      // retry
    }
  }
  return { success: false, message: "Login timed out" };
}

export async function importCookies(cookies: any[]): Promise<{ success: boolean; message: string }> {
  return fetcher(`${BASE}/session/import-cookies`, {
    method: 'POST',
    body: JSON.stringify({ cookies }),
  });
}

export async function getStats(): Promise<Stats> {
  return fetcher<Stats>(`${BASE}/stats`);
}

export async function getLeadHistory(limit = 50): Promise<{ leads: any[] }> {
  return fetcher<{ leads: any[] }>(`${BASE}/leads/history?limit=${limit}`);
}
