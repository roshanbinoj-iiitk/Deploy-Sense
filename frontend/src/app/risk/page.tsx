import Link from 'next/link';
import { getDeployments } from '@/lib/api';
import { RiskBadge } from '@/components/ui/Badge';
import StatCard from '@/components/ui/StatCard';
import PageHeader from '@/components/ui/PageHeader';
import Panel from '@/components/ui/Panel';
import EmptyState from '@/components/ui/EmptyState';
import type { Deployment, RiskLevel } from '@/lib/types';
import { Shield } from 'lucide-react';

export default async function RiskPage() {
  let deployments: Deployment[] = [];
  try {
    const res = await getDeployments(1, 100);
    deployments = res.data;
  } catch {}

  const withRisk = deployments.filter(d => d.risk_level !== null);

  const dist: Record<RiskLevel, number> = { LOW: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 };
  for (const d of withRisk) {
    if (d.risk_level) dist[d.risk_level]++;
  }

  const avgScore = withRisk.length
    ? Math.round(withRisk.reduce((s, d) => s + (d.risk_score ?? 0), 0) / withRisk.length)
    : 0;

  const total = withRisk.length;

  const distBars: { level: RiskLevel; color: string }[] = [
    { level: 'LOW',      color: '#10b981' },
    { level: 'MODERATE', color: '#fbbf24' },
    { level: 'HIGH',     color: '#f97316' },
    { level: 'CRITICAL', color: '#f87171' },
  ];

  function fmt(iso: string) {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
      new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  }

  return (
    <div className="flex flex-col gap-7 p-8 animate-fadein">
      {/* Header */}
      <PageHeader
        title="Risk Analysis"
        subtitle={`${withRisk.length} evaluated — avg score ${avgScore}`}
      >
        {(dist.HIGH + dist.CRITICAL) > 0 && (
          <span className="rounded-full border border-red-500/15 bg-red-500/[0.04] px-4 py-2 text-xs font-bold text-red-400">
            {dist.HIGH + dist.CRITICAL} high/critical
          </span>
        )}
        <span className="rounded-full border border-emerald-500/15 bg-emerald-500/[0.04] px-4 py-2 text-xs font-bold text-emerald-400">
          {dist.LOW} low risk
        </span>
      </PageHeader>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4 stagger-children">
        <StatCard
          label="Avg Risk Score"
          value={avgScore}
          color={avgScore <= 25 ? 'green' : avgScore <= 50 ? 'yellow' : 'red'}
          sub="Last 100 deployments"
        />
        <StatCard label="Evaluated" value={withRisk.length} sub="With risk data" />
        <StatCard label="High / Critical" value={dist.HIGH + dist.CRITICAL} color={dist.HIGH + dist.CRITICAL > 0 ? 'red' : 'default'} sub="Needs review" />
        <StatCard label="Low Risk" value={dist.LOW} color="green" sub="Safe to proceed" />
      </div>

      {/* Distribution */}
      <Panel title="Risk Level Distribution">
        <div className="p-6">
          {total === 0 ? (
            <EmptyState
              icon={<Shield className="h-5 w-5 text-cyan-400" />}
              title="No risk data yet"
              description="Risk scores appear after deployments are evaluated."
            />
          ) : (
            <>
              {/* Stacked bar */}
              <div className="flex h-8 overflow-hidden rounded-[10px] border border-white/[0.08] bg-white/[0.03]">
                {distBars.map(({ level, color }) => {
                  const pct = total > 0 ? (dist[level] / total) * 100 : 0;
                  if (pct === 0) return null;
                  return (
                    <div
                      key={level}
                      className="flex items-center justify-center text-[11px] font-black text-[#060a10] transition-all duration-700"
                      style={{ width: `${pct}%`, background: color }}
                    >
                      {pct >= 8 ? `${Math.round(pct)}%` : ''}
                    </div>
                  );
                })}
              </div>

              {/* Legend + donut */}
              <div className="mt-7 flex flex-wrap items-center gap-10">
                {/* SVG donut */}
                <svg width="130" height="130" viewBox="0 0 130 130" className="flex-shrink-0">
                  {(() => {
                    const cx = 65, cy = 65, r = 50, stroke = 20;
                    const circumference = 2 * Math.PI * r;
                    let offset = 0;
                    const colors = ['#10b981', '#fbbf24', '#f97316', '#f87171'];
                    return distBars.map(({ level }, i) => {
                      const pct = dist[level] / total;
                      const dash = circumference * pct;
                      const gap = circumference - dash;
                      const rotation = (offset / total) * 360 - 90;
                      offset += dist[level];
                      if (pct === 0) return null;
                      return (
                        <circle
                          key={level}
                          cx={cx} cy={cy} r={r}
                          fill="none"
                          stroke={colors[i]}
                          strokeWidth={stroke}
                          strokeDasharray={`${dash} ${gap}`}
                          transform={`rotate(${rotation} ${cx} ${cy})`}
                          strokeLinecap="butt"
                          className="transition-all duration-700"
                        />
                      );
                    });
                  })()}
                  <text x="65" y="60" textAnchor="middle" fill="#f0f4f8" fontSize="20" fontWeight="800" fontFamily="monospace">{total}</text>
                  <text x="65" y="76" textAnchor="middle" fill="#4e5d73" fontSize="11" fontFamily="Inter, sans-serif">evals</text>
                </svg>

                {/* Legend */}
                <div className="grid grid-cols-2 gap-x-10 gap-y-3.5">
                  {distBars.map(({ level, color }) => (
                    <div key={level} className="flex items-center gap-2.5">
                      <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full shadow-[0_0_6px_currentColor]" style={{ background: color, color }} />
                      <span className="text-sm text-slate-300">
                        {level}
                        <span className="ml-2 font-bold text-white">{dist[level]}</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </Panel>

      {/* Assessments list */}
      <Panel title="Recent Assessments">
        {withRisk.length === 0 ? (
          <EmptyState
            icon={<Shield className="h-5 w-5 text-cyan-400" />}
            title="No risk data yet"
          />
        ) : (
          <div className="divide-y divide-white/[0.04]">
            {withRisk.slice(0, 30).map(d => {
              const color =
                d.risk_score! <= 25 ? '#10b981' :
                d.risk_score! <= 50 ? '#fbbf24' :
                d.risk_score! <= 75 ? '#f97316' : '#f87171';
              return (
                <div key={d.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-cyan-500/[0.03] transition-colors">
                  <div
                    className="grid h-12 w-12 flex-shrink-0 place-items-center rounded-full border-[2.5px] font-mono text-[15px] font-extrabold transition-shadow hover:shadow-[0_0_16px_currentColor]"
                    style={{ borderColor: color, color, background: `${color}12` }}
                  >
                    {d.risk_score}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-0.5">
                      <Link href={`/deployments/${d.id}`} className="font-mono text-xs text-cyan-400 hover:text-white transition-colors">
                        {d.id.slice(0, 8)}…
                      </Link>
                      <RiskBadge level={d.risk_level!} />
                      {d.failure_probability !== null && (
                        <span className="text-xs text-slate-500">
                          {(d.failure_probability * 100).toFixed(1)}% fail prob
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">{d.environment} — {d.deployed_by ?? 'unknown'}</p>
                  </div>
                  <p className="font-mono text-xs text-slate-600 flex-shrink-0">{fmt(d.created_at)}</p>
                </div>
              );
            })}
          </div>
        )}
      </Panel>
    </div>
  );
}
