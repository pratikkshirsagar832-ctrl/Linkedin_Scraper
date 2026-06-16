'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Hash, Clock, Zap } from 'lucide-react';
import type { Stats, LeadState } from '../lib/types';
import { getStats } from '../lib/api';

interface StatsBarProps {
  leadCount: number;
  state: LeadState;
  keyword: string;
}

function AnimatedNumber({ value, label, icon: Icon, color }: {
  value: number;
  label: string;
  icon: any;
  color: string;
}) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value === 0) { setDisplay(0); return; }
    const duration = 800;
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="flex items-center gap-2.5">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center`} style={{ background: `${color}15` }}>
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div>
        <p className="text-lg font-bold text-white tabular-nums">{display}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function StatsBar({ leadCount, state, keyword }: StatsBarProps) {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, [leadCount]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4 mb-6"
    >
      <div className="flex flex-wrap items-center gap-6 md:gap-10">
        <AnimatedNumber
          value={leadCount}
          label="This Search"
          icon={Zap}
          color="#00f0ff"
        />
        <AnimatedNumber
          value={stats?.total_leads ?? 0}
          label="Total Leads"
          icon={TrendingUp}
          color="#7c3aed"
        />
        <AnimatedNumber
          value={stats?.unique_keywords ?? 0}
          label="Keywords"
          icon={Hash}
          color="#ec4899"
        />
      </div>
    </motion.div>
  );
}
