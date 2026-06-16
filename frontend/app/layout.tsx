import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'LeadGen — AI LinkedIn Lead Dashboard',
  description: 'AI-powered LinkedIn lead generation engine with real-time streaming',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
