'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LogIn, Linkedin, Loader2, History, Search } from 'lucide-react';
import SearchPanel from './SearchPanel';
import LeadGrid from './LeadGrid';
import LoadMoreBtn from './LoadMoreBtn';
import StatsBar from './StatsBar';
import HistoryTab from './HistoryTab';
import { searchLeads, loadMoreLeads, getSessionStatus, triggerLogin } from '../lib/api';
import type { Lead, LeadState, TimeFilter } from '../lib/types';

type LoginState = "checking" | "needed" | "logging_in" | "ready" | "failed";
type TabType = "search" | "history";

export default function LeadDashboard() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [state, setState] = useState<LeadState>('idle');
  const [keyword, setKeyword] = useState('');
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('latest');
  const [sessionId, setSessionId] = useState('');
  const [hasMore, setHasMore] = useState(true);
  const [loginState, setLoginState] = useState<LoginState>("checking");
  const [loginError, setLoginError] = useState("");
  const [tab, setTab] = useState<TabType>("search");

  useEffect(() => {
    getSessionStatus()
      .then((s) => setLoginState(s.logged_in ? "ready" : "needed"))
      .catch(() => setLoginState("needed"));
  }, []);

  const handleLogin = useCallback(async () => {
    setLoginState("logging_in");
    setLoginError("");
    try {
      const res = await triggerLogin();
      if (res.success) {
        setLoginState("ready");
      } else {
        setLoginState("failed");
        setLoginError(res.message || "Login failed");
      }
    } catch (e: any) {
      setLoginState("failed");
      setLoginError(e.message || "Could not connect to backend");
    }
  }, []);

  const handleSearch = useCallback(async (kw: string, tf: TimeFilter) => {
    setKeyword(kw);
    setTimeFilter(tf);
    setState('loading');
    setLeads([]);
    setHasMore(true);
    setSessionId('');

    try {
      const res = await searchLeads(kw, tf);
      if (res.session_valid === false) {
        setLoginState("needed");
        setState('error');
        return;
      }
      setLeads(res.leads);
      setSessionId(res.session_id);
      setHasMore(res.has_more);
      setState(res.leads.length === 0 ? 'empty' : 'success');
    } catch {
      setState('error');
    }
  }, []);

  const handleLoadMore = useCallback(async () => {
    if (state === 'loading' || !sessionId) return;
    setState('loading');
    try {
      const res = await loadMoreLeads(sessionId);
      if (res.session_valid === false) {
        setLoginState("needed");
        setState('error');
        return;
      }
      setLeads((prev) => [...prev, ...res.leads]);
      setHasMore(res.has_more);
      setState(res.leads.length === 0 ? 'empty' : 'success');
    } catch {
      setState('error');
    }
  }, [sessionId, state]);

  if (loginState === "checking") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
      </div>
    );
  }

  if (loginState === "needed" || loginState === "logging_in" || loginState === "failed") {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass rounded-2xl p-8 md:p-12 max-w-md w-full text-center"
        >
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center mx-auto mb-5">
            <Linkedin className="w-8 h-8 text-accent-cyan" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">LinkedIn Login Required</h2>
          <p className="text-sm text-gray-400 mb-6 leading-relaxed">
            To scrape search results, you need to log in to LinkedIn once.
            A browser window will open — complete the login there, then return here.
          </p>

          {loginState === "logging_in" && (
            <div className="flex flex-col items-center gap-3 mb-4">
              <Loader2 className="w-6 h-6 text-accent-cyan animate-spin" />
              <p className="text-sm text-gray-400">Login window opened. Complete login in the browser...</p>
            </div>
          )}

          {loginState === "failed" && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-400">{loginError || "Login failed. Try again."}</p>
            </div>
          )}

          <motion.button
            onClick={handleLogin}
            disabled={loginState === "logging_in"}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full h-11 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 bg-gradient-to-r from-accent-cyan to-accent-purple text-white hover:opacity-90 shadow-lg shadow-accent-cyan/20 disabled:opacity-50 transition-all"
          >
            {loginState === "logging_in" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Waiting for login...
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                Login to LinkedIn
              </>
            )}
          </motion.button>

          <p className="text-xs text-gray-600 mt-4">
            Your session is saved securely for future use. Re-login anytime if it expires.
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full">
      <div className="max-w-6xl mx-auto px-4 py-6 md:py-10">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center">
              <Linkedin className="w-5 h-5 text-accent-cyan" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">LinkedIn LeadGen</h1>
              <p className="text-xs text-gray-500">AI-powered intent-based lead discovery</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex bg-white/5 rounded-lg p-0.5">
              <button
                onClick={() => setTab("search")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${tab === "search" ? "bg-accent-cyan/20 text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                <Search className="w-3.5 h-3.5" />
                Search
              </button>
              <button
                onClick={() => setTab("history")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${tab === "history" ? "bg-accent-cyan/20 text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                <History className="w-3.5 h-3.5" />
                History
              </button>
            </div>
            <button
              onClick={() => { setLoginState("needed"); handleLogin(); }}
              className="glass rounded-lg px-3 py-1.5 text-xs text-gray-400 hover:text-white flex items-center gap-1.5 transition-all"
            >
              <LogIn className="w-3.5 h-3.5" />
              Re-login
            </button>
          </div>
        </div>

        {tab === "history" ? (
          <HistoryTab />
        ) : (
          <>
            <SearchPanel onSearch={handleSearch} state={state} />

            {leads.length > 0 && (
              <StatsBar leadCount={leads.length} state={state} keyword={keyword} />
            )}

            <LeadGrid leads={leads} state={state} keyword={keyword} />

            <LoadMoreBtn
              onLoadMore={handleLoadMore}
              state={state}
              hasMore={hasMore}
              total={leads.length}
            />
          </>
        )}

        <footer className="text-center py-8 text-xs text-gray-700">
          LinkedIn LeadGen Dashboard — AI-powered intent scoring via DeepSeek
        </footer>
      </div>
    </div>
  );
}
