'use client';

import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import LeadDashboard from '../components/LeadDashboard';

const ThreeBackground = dynamic(() => import('../components/ThreeBackground'), {
  ssr: false,
});

export default function Home() {
  return (
    <main className="relative min-h-screen w-full overflow-hidden">
      <Suspense fallback={null}>
        <ThreeBackground />
      </Suspense>
      <div className="relative z-10">
        <LeadDashboard />
      </div>
    </main>
  );
}
