'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Clock, Users } from 'lucide-react';
import type { TimeFilter, LeadState, LeadType } from '../lib/types';

interface SearchPanelProps {
  onSearch: (keyword: string, timeFilter: TimeFilter, leadType: LeadType) => void;
  state: LeadState;
}

const TIME_OPTIONS: { label: string; value: TimeFilter }[] = [
  { label: 'Latest', value: 'latest' },
  { label: '7 Days', value: '7_days' },
  { label: '14 Days', value: '14_days' },
  { label: '27 Days', value: '27_days' },
  { label: '2 Months', value: '2_months' },
];

const LEAD_TYPE_OPTIONS: { label: string; value: LeadType; desc: string }[] = [
  { label: 'All', value: 'all', desc: 'Any buying intent' },
  { label: 'Intern', value: 'intern', desc: 'Internship / entry-level' },
  { label: 'Agency', value: 'agency', desc: 'Looking for agency' },
  { label: 'Company', value: 'company', desc: 'Full-time hiring' },
  { label: 'One Client', value: 'one_client', desc: 'One-time project' },
];

export default function SearchPanel({ onSearch, state }: SearchPanelProps) {
  const [keyword, setKeyword] = useState('');
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('latest');
  const [leadType, setLeadType] = useState<LeadType>('all');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;
    onSearch(keyword.trim(), timeFilter, leadType);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6 md:p-8 mb-8"
    >
      <form onSubmit={handleSubmit}>
        <div className="relative mb-5">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Enter keyword... e.g., AI automation, website development..."
            className="w-full h-12 pl-12 pr-4 rounded-xl bg-dark-900 border border-white/5 text-white placeholder-gray-600 focus:outline-none focus:border-accent-cyan/30 focus:ring-1 focus:ring-accent-cyan/20 transition-all text-sm"
            disabled={state === 'loading'}
          />
        </div>

        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Lead Type</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {LEAD_TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setLeadType(opt.value)}
                disabled={state === 'loading'}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  leadType === opt.value
                    ? 'bg-accent-purple/15 text-accent-purple border border-accent-purple/30'
                    : 'bg-dark-800 text-gray-400 border border-white/5 hover:border-white/10'
                }`}
                title={opt.desc}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-5">
          <Clock className="w-4 h-4 text-gray-500 self-center mr-1" />
          {TIME_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setTimeFilter(opt.value)}
              disabled={state === 'loading'}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                timeFilter === opt.value
                  ? 'bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/30'
                  : 'bg-dark-800 text-gray-400 border border-white/5 hover:border-white/10'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <motion.button
          type="submit"
          disabled={!keyword.trim() || state === 'loading'}
          whileHover={{ scale: keyword.trim() ? 1.01 : 1 }}
          whileTap={{ scale: keyword.trim() ? 0.99 : 1 }}
          className={`w-full h-11 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
            state === 'loading'
              ? 'bg-accent-cyan/10 text-accent-cyan/50 cursor-not-allowed'
              : keyword.trim()
              ? 'bg-gradient-to-r from-accent-cyan to-accent-purple text-white hover:opacity-90 shadow-lg shadow-accent-cyan/20'
              : 'bg-dark-800 text-gray-500 cursor-not-allowed'
          }`}
        >
          {state === 'loading' ? (
            <>
              <div className="w-4 h-4 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Find {leadType === 'all' ? 'Leads' : `${LEAD_TYPE_OPTIONS.find(o => o.value === leadType)?.label} Leads`}
            </>
          )}
        </motion.button>
      </form>
    </motion.div>
  );
}
