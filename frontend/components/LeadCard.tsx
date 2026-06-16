'use client';

import { motion } from 'framer-motion';
import { ExternalLink, User, Quote, CheckCircle, ArrowUpRight } from 'lucide-react';
import type { Lead } from '../lib/types';

interface LeadCardProps {
  lead: Lead;
  index: number;
}

export default function LeadCard({ lead, index }: LeadCardProps) {
  const scorePercent = Math.round(lead.intent_score * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="glass-light rounded-xl p-5 hover:border-accent-cyan/20 transition-all duration-300 group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-accent-cyan" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">{lead.author_name}</p>
            {lead.author_profile && (
              <a
                href={lead.author_profile}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-500 hover:text-accent-cyan truncate block transition-colors"
              >
                View Profile
              </a>
            )}
          </div>
        </div>

        {lead.intent_score >= 0.7 && (
          <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-green-500/10 border border-green-500/20 flex-shrink-0">
            <CheckCircle className="w-3 h-3 text-green-400" />
            <span className="text-xs text-green-400 font-medium">{scorePercent}%</span>
          </div>
        )}
      </div>

      <div className="mb-3">
        <Quote className="w-3.5 h-3.5 text-gray-600 mb-1" />
        <p className="text-sm text-gray-300 leading-relaxed line-clamp-4">
          {lead.post_text}
        </p>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        <div className="flex items-center gap-3">
          {lead.post_url ? (
            <a
              href={lead.post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-accent-cyan hover:text-accent-cyan/80 transition-colors group/link"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>View Post</span>
              <ArrowUpRight className="w-3 h-3 opacity-0 -translate-y-1 group-hover/link:opacity-100 group-hover/link:translate-y-0 transition-all" />
            </a>
          ) : lead.author_profile ? (
            <a
              href={lead.author_profile}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>View Profile</span>
            </a>
          ) : null}
        </div>

        {lead.intent_reason && (
          <span className="text-xs text-gray-500 italic truncate ml-2">{lead.intent_reason}</span>
        )}
      </div>
    </motion.div>
  );
}
