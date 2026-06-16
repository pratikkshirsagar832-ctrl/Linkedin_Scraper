'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { SearchX } from 'lucide-react';
import LeadCard from './LeadCard';
import type { Lead, LeadState } from '../lib/types';

interface LeadGridProps {
  leads: Lead[];
  state: LeadState;
  keyword: string;
}

function SkeletonCard() {
  return (
    <div className="glass-light rounded-xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-full skeleton" />
        <div className="flex-1">
          <div className="h-3 w-32 skeleton rounded mb-1" />
          <div className="h-2.5 w-20 skeleton rounded" />
        </div>
      </div>
      <div className="space-y-2 mb-3">
        <div className="h-2.5 w-full skeleton rounded" />
        <div className="h-2.5 w-5/6 skeleton rounded" />
        <div className="h-2.5 w-4/6 skeleton rounded" />
        <div className="h-2.5 w-3/6 skeleton rounded" />
      </div>
      <div className="h-3 w-24 skeleton rounded" />
    </div>
  );
}

export default function LeadGrid({ leads, state, keyword }: LeadGridProps) {
  if (state === 'loading' && leads.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (state === 'empty' || (state === 'success' && leads.length === 0)) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl p-12 text-center"
      >
        <SearchX className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-300 mb-2">No Leads Found</h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          {keyword
            ? `No intent-qualified leads found for "${keyword}". Try a different keyword or time range.`
            : 'Enter a keyword above to start finding leads.'}
        </p>
      </motion.div>
    );
  }

  if (state === 'error') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl p-12 text-center border border-red-500/20"
      >
        <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
          <SearchX className="w-6 h-6 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-300 mb-2">Search Failed</h3>
        <p className="text-sm text-gray-500">Something went wrong. Please try again or check your session status.</p>
      </motion.div>
    );
  }

  return (
    <AnimatePresence mode="popLayout">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {leads.map((lead, i) => (
          <LeadCard key={lead.id || i} lead={lead} index={i} />
        ))}
      </div>
    </AnimatePresence>
  );
}
