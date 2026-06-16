'use client';

import { motion } from 'framer-motion';
import { Plus, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import type { LeadState } from '../lib/types';

interface LoadMoreBtnProps {
  onLoadMore: () => void;
  state: LeadState;
  hasMore: boolean;
  total: number;
}

export default function LoadMoreBtn({ onLoadMore, state, hasMore, total }: LoadMoreBtnProps) {
  if (total === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center gap-3 mt-8 mb-8"
    >
      {hasMore && state !== 'loading' && (
        <motion.button
          onClick={onLoadMore}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="glass rounded-xl px-8 py-3 flex items-center gap-2 text-sm font-medium text-gray-300 hover:text-white hover:border-accent-cyan/30 transition-all group"
        >
          <Plus className="w-4 h-4 text-accent-cyan group-hover:rotate-90 transition-transform" />
          Load 10 More Leads
        </motion.button>
      )}

      {state === 'loading' && total > 0 && (
        <div className="glass rounded-xl px-8 py-3 flex items-center gap-2 text-sm text-gray-400">
          <Loader2 className="w-4 h-4 animate-spin text-accent-cyan" />
          Searching for more...
        </div>
      )}

      {!hasMore && total > 0 && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <CheckCircle2 className="w-4 h-4 text-green-400" />
          All available leads loaded ({total} total)
        </div>
      )}

      {state === 'error' && total > 0 && (
        <motion.button
          onClick={onLoadMore}
          whileHover={{ scale: 1.02 }}
          className="glass rounded-xl px-8 py-3 flex items-center gap-2 text-sm text-red-400 border border-red-500/20 hover:border-red-500/40 transition-all"
        >
          <AlertCircle className="w-4 h-4" />
          Failed — Retry
        </motion.button>
      )}

      <p className="text-xs text-gray-600">
        {total} lead{total !== 1 ? 's' : ''} shown
      </p>
    </motion.div>
  );
}
