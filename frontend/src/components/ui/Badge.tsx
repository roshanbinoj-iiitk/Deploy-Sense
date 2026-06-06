import type { RiskLevel, DeploymentStatus } from '@/lib/types';

// ── Risk badge ────────────────────────────────────────────────────────────────
const riskStyles: Record<RiskLevel, { bg: string; text: string; border: string }> = {
  LOW:      { bg: 'bg-emerald-500/8', text: 'text-emerald-400', border: 'border-emerald-500/15' },
  MODERATE: { bg: 'bg-yellow-500/8', text: 'text-yellow-400', border: 'border-yellow-500/15' },
  HIGH:     { bg: 'bg-orange-500/8', text: 'text-orange-400', border: 'border-orange-500/15' },
  CRITICAL: { bg: 'bg-red-500/8', text: 'text-red-400', border: 'border-red-500/15' },
};

export function RiskBadge({ level, score }: { level: RiskLevel; score?: number | null }) {
  const style = riskStyles[level];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-semibold tracking-wide ${style.bg} ${style.text} ${style.border}`}>
      {score !== undefined && score !== null && <span className="font-mono font-bold">{score}</span>}
      {level}
    </span>
  );
}

// ── Status pill ───────────────────────────────────────────────────────────────
const statusStyles: Partial<Record<DeploymentStatus, { bg: string; text: string; border: string }>> = {
  STABLE:       { bg: 'bg-emerald-500/8', text: 'text-emerald-400', border: 'border-emerald-500/15' },
  DEPLOYED:     { bg: 'bg-blue-500/8', text: 'text-blue-400', border: 'border-blue-500/15' },
  DEPLOYING:    { bg: 'bg-blue-500/8', text: 'text-blue-400', border: 'border-blue-500/15' },
  MONITORING:   { bg: 'bg-yellow-500/8', text: 'text-yellow-400', border: 'border-yellow-500/15' },
  FAILED:       { bg: 'bg-red-500/8', text: 'text-red-400', border: 'border-red-500/15' },
  ROLLED_BACK:  { bg: 'bg-red-500/8', text: 'text-red-400', border: 'border-red-500/15' },
  BLOCKED:      { bg: 'bg-red-500/8', text: 'text-red-400', border: 'border-red-500/15' },
  PENDING:      { bg: 'bg-slate-500/8', text: 'text-slate-400', border: 'border-slate-500/15' },
  RISK_ASSESSED:{ bg: 'bg-yellow-500/8', text: 'text-yellow-400', border: 'border-yellow-500/15' },
  APPROVED:     { bg: 'bg-emerald-500/8', text: 'text-emerald-400', border: 'border-emerald-500/15' },
  DEGRADED:     { bg: 'bg-orange-500/8', text: 'text-orange-400', border: 'border-orange-500/15' },
};

const pulseStatuses = new Set<DeploymentStatus>(['DEPLOYING', 'MONITORING', 'STABLE']);

export function StatusPill({ status }: { status: DeploymentStatus }) {
  const style = statusStyles[status] ?? { bg: 'bg-slate-500/8', text: 'text-slate-400', border: 'border-slate-500/15' };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-semibold tracking-wide ${style.bg} ${style.text} ${style.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full bg-current ${pulseStatuses.has(status) ? 'animate-pulse' : ''}`} />
      {status}
    </span>
  );
}

// ── Environment badge ─────────────────────────────────────────────────────────
export function EnvBadge({ env }: { env: string }) {
  const style =
    env === 'production' ? { bg: 'bg-red-500/8', text: 'text-red-400', border: 'border-red-500/15' } :
    env === 'staging'    ? { bg: 'bg-yellow-500/8', text: 'text-yellow-400', border: 'border-yellow-500/15' } :
                           { bg: 'bg-blue-500/8', text: 'text-blue-400', border: 'border-blue-500/15' };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg border text-[11px] font-semibold tracking-wide ${style.bg} ${style.text} ${style.border}`}>
      {env}
    </span>
  );
}

// ── Alert severity badge ──────────────────────────────────────────────────────
export function SeverityBadge({ severity }: { severity: string }) {
  const style =
    severity === 'CRITICAL' ? { bg: 'bg-red-500/8', text: 'text-red-400', border: 'border-red-500/15' } :
    severity === 'HIGH'     ? { bg: 'bg-orange-500/8', text: 'text-orange-400', border: 'border-orange-500/15' } :
    severity === 'WARNING'  ? { bg: 'bg-yellow-500/8', text: 'text-yellow-400', border: 'border-yellow-500/15' } :
                              { bg: 'bg-blue-500/8', text: 'text-blue-400', border: 'border-blue-500/15' };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg border text-[11px] font-semibold tracking-wide ${style.bg} ${style.text} ${style.border}`}>
      {severity}
    </span>
  );
}
