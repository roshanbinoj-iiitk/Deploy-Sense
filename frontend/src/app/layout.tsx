import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';
import { AuthProvider } from '@/lib/auth';

export const metadata: Metadata = {
  title: 'DeploySense — Deployment Intelligence Platform',
  description: 'Predict deployment risk, track releases in real-time, and maintain system stability with AI-powered insights.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="relative flex min-h-screen">
            <Sidebar />
            <div className="relative z-10 ml-[260px] flex flex-1 flex-col">
              {children}
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
