import { type ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
}

export default function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-[14px] border border-white/[0.08] bg-cyan-500/[0.06] shadow-[0_0_24px_rgba(34,211,238,0.1)] animate-[float_3s_ease-in-out_infinite]">
        {icon}
      </div>
      <div>
        <p className="text-sm font-semibold text-white">{title}</p>
        {description && (
          <p className="mt-1.5 text-xs text-slate-400 max-w-xs mx-auto">{description}</p>
        )}
      </div>
    </div>
  );
}
