-- LinkedIn LeadGen Dashboard — Supabase Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Leads table: stores every scraped lead
CREATE TABLE IF NOT EXISTS leads (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  keyword     TEXT NOT NULL,
  post_url    TEXT NOT NULL UNIQUE,
  post_text   TEXT,
  author_name TEXT,
  author_profile TEXT,
  top_comment TEXT,
  timestamp   TIMESTAMPTZ DEFAULT NOW(),
  intent_score FLOAT DEFAULT 0.0,
  intent_reason TEXT,
  source      TEXT DEFAULT 'linkedin',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_leads_keyword ON leads (keyword);
CREATE INDEX IF NOT EXISTS idx_leads_intent_score ON leads (intent_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at DESC);

-- Enable Row Level Security (default for new tables)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access (dashboard queries)
CREATE POLICY "Allow anonymous SELECT" ON leads
  FOR SELECT USING (true);

-- Allow service_role full access (backend inserts/updates)
CREATE POLICY "Allow service_role all" ON leads
  FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Stats view for quick dashboard metrics
CREATE OR REPLACE VIEW lead_stats AS
SELECT
  COUNT(*) AS total_leads,
  COUNT(DISTINCT keyword) AS unique_keywords,
  NOW()::TEXT AS last_updated
FROM leads;

-- Keyword breakdown view
CREATE OR REPLACE VIEW keyword_breakdown AS
SELECT
  keyword,
  COUNT(*) AS count,
  ROUND(AVG(intent_score)::NUMERIC, 2) AS avg_intent_score
FROM leads
GROUP BY keyword
ORDER BY count DESC;
