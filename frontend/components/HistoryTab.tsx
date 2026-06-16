'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { History, Loader2, User, ExternalLink, Clock, Search } from 'lucide-react';
import { getLeadHistory } from '../lib/api';
import type { Lead } from '../lib/types';

export default function HistoryTab() {
  const [history, setHistory] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    getLeadHistory(100)
      .then((res) => {
        setHistory(res.leads || []);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message || 'Failed to load history');
        setLoading(false);
      });
  }, []);

  const filtered = searchTerm
    ? history.filter(
        (l) =>
          l.author_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          l.keyword?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          l.post_text?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : history;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 text-accent-cyan animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-xl p-6 text-center">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-white flex items-center gap-2">
          <History className="w-4 h-4 text-accent-cyan" />
          Lead History ({history.length})
        </h2>
        <div className="relative max-w-xs w-full">
          <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Filter history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-9 pl-9 pr-3 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent-cyan/40 transition-all"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="glass rounded-xl p-10 text-center">
          <Clock className="w-8 h-8 text-gray-600 mx-auto mb-3" />
          <p className="text-sm text-gray-500">{history.length === 0 ? 'No leads found yet. Run a search to get started.' : 'No leads match your filter.'}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((lead, i) => (
            <motion.div
              key={lead.id || i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02 }}
              className="glass-light rounded-lg p-4 flex items-start gap-3 hover:border-accent-cyan/20 transition-all"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-accent-cyan" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-white truncate">{lead.author_name}</span>
                  {lead.keyword && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan font-medium flex-shrink-0">
                      {lead.keyword}
                    </span>
                  )}
                  {lead.intent_score >= 0.7 && (
                    <span className="text-[10px] text-green-400 flex-shrink-0">
                      {Math.round(lead.intent_score * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400 line-clamp-2 mb-1">{lead.post_text}</p>
                <div className="flex items-center gap-3">
                  {lead.author_profile && (
                    <a
                      href={lead.author_profile}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <ExternalLink className="w-2.5 h-2.5" />
                      Profile
                    </a>
                  )}
                  {lead.post_url && (
                    <a
                      href={lead.post_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-accent-cyan hover:text-accent-cyan/80 flex items-center gap-1"
                    >
                      <ExternalLink className="w-2.5 h-2.5" />
                      Post
                    </a>
                  )}
                  {lead.intent_reason && (
                    <span className="text-[10px] text-gray-600 italic">{lead.intent_reason}</span>
                  )}
                  {lead.timestamp && (
                    <span className="text-[10px] text-gray-600 ml-auto">{new Date(lead.timestamp).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
