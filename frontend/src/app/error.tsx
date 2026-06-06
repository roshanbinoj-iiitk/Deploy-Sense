'use client';

import { AlertTriangle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-6 p-20 text-center animate-fadein">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-red-500/15 bg-red-500/[0.06] shadow-[0_0_30px_rgba(239,68,68,0.1)]">
        <AlertTriangle className="h-7 w-7 text-red-400" />
      </div>
      <div>
        <h2 className="text-lg font-bold text-white">Something went wrong</h2>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          {error.message || 'An unexpected error occurred while loading this page.'}
        </p>
      </div>
      <button
        onClick={() => reset()}
        className="rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-6 py-2.5 text-sm font-semibold text-cyan-400 transition-all hover:bg-cyan-500/15 hover:shadow-lg hover:shadow-cyan-500/10"
      >
        Try again
      </button>
    </div>
  );
}
