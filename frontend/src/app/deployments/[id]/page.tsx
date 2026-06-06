import Link from 'next/link';
import { getDeployment, getDeploymentTimeline, getDeploymentRisk } from '@/lib/api';
import { RiskBadge, StatusPill, EnvBadge } from '@/components/ui/Badge';
import PageHeader from '@/components/ui/PageHeader';
import Panel from '@/components/ui/Panel';
import EmptyState from '@/components/ui/EmptyState';
import { Search, Activity, Shield } from 'lucide-react';

function fmt(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  });
}

export default async function DeploymentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let deployment, timeline, risks;
  let notFound = false;

  try {
    [deployment, timeline, risks] = await Promise.all([
      getDeployment(id),
      getDeploymentTimeline(id),
      getDeploymentRisk(id),
    ]);
  } catch {
    notFound = true;
  }

  if (notFound || !deployment) {
    return (
      <div className="flex flex-col items-center justify-center gap-5 p-20 text-center animate-fadein">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/[0.08] bg-cyan-500/[0.06] shadow-[0_0_24px_rgba(34,211,238,0.1)] animate-[float_3s_ease-in-out_infinite]">
          <Search className="h-7 w-7 text-cyan-400" />
        </div>
        <h1 className="text-xl font-bold text-white">Deployment not found</h1>
        <Link href="/deployments" className="text-sm text-cyan-400 hover:text-white transition-colors">
          ← Back to deployments
        </Link>
      </div>
    );
  }

  const riskColor =
    !deployment.risk_score ? '#8b9cb6' :
    deployment.risk_score <= 25 ? '#10b981' :
    deployment.risk_score <= 50 ? '#fbbf24' :
    deployment.risk_score <= 75 ? '#f97316' : '#f87171';

  return (
    <div className="flex flex-col gap-6 p-8 animate-fadein">
      {/* Header */}
      <div>
        <Link href="/deployments" className="mb-2 inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors">
          ← Deployments
        </Link>
        <PageHeader
          title={`${deployment.id.slice(0, 8)}…`}
          subtitle={`${deployment.service_name ?? 'Unknown service'} — ${deployment.environment}`}
        >
          <StatusPill status={deployment.status} />
        </PageHeader>
      </div>

      {/* Meta cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 stagger-children">
        {[
          { label: 'Environment', value: <EnvBadge env={deployment.environment} /> },
          { label: 'Status',      value: <StatusPill status={deployment.status} /> },
          {
            label: 'Risk Score',
            value: deployment.risk_score !== null
              ? <span className="text-2xl font-extrabold" style={{ color: riskColor }}>{deployment.risk_score}</span>
              : <span className="text-slate-500">—</span>,
            sub: deployment.risk_level ?? undefined,
          },
          { label: 'Version',   value: <span className="font-mono text-sm">{deployment.version ?? '—'}</span> },
          { label: 'SHA',       value: <span className="font-mono text-xs text-slate-300">{deployment.git_sha?.slice(0, 12) ?? '—'}</span> },
          { label: 'Deployed By', value: deployment.deployed_by ?? '—' },
        ].map(({ label, value, sub }) => (
          <div key={label} className="rounded-[12px] border border-white/[0.08] bg-[#0d1117]/70 backdrop-blur-sm px-4 py-3.5 transition-colors hover:border-white/[0.12]">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.08em] text-slate-500">{label}</p>
            <div className="text-sm font-semibold text-white">{value}</div>
            {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
          </div>
        ))}
      </div>

      {/* Two col: timeline + risk */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* Timeline */}
        <Panel
          title="Event Timeline"
          actions={<span className="text-xs text-slate-500">{(timeline ?? []).length} events</span>}
        >
          <div className="p-5">
            {!timeline || timeline.length === 0 ? (
              <EmptyState
                icon={<Activity className="h-5 w-5 text-cyan-400" />}
                title="No events recorded"
              />
            ) : (
              <div className="relative pl-7">
                <div className="absolute left-[7px] top-0 h-full w-[2px] bg-gradient-to-b from-cyan-500/50 to-transparent" />
                {timeline.map((e, i) => (
                  <div key={e.id} className={`relative ${i === timeline.length - 1 ? '' : 'pb-6'}`}>
                    <div className="absolute -left-[20px] top-[5px] h-3.5 w-3.5 rounded-full border-[2.5px] border-[#0d1117] bg-cyan-500 shadow-[0_0_12px_rgba(34,211,238,0.35)]" />
                    <p className="mb-0.5 font-mono text-[11px] text-slate-500">
                      {e.timestamp ? new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false }) : ''}
                    </p>
                    <p className="text-[13px] font-semibold text-white">{e.event_type}</p>
                    {(e.previous_state || e.current_state) && (
                      <p className="mt-0.5 text-xs text-slate-400">
                        {e.previous_state && <span className="text-slate-500">{e.previous_state} → </span>}
                        <span className="text-cyan-400">{e.current_state}</span>
                      </p>
                    )}
                    {e.message && <p className="mt-0.5 text-xs text-slate-500">{e.message}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Panel>

        {/* Risk assessments */}
        <Panel
          title="Risk Assessments"
          actions={<span className="text-xs text-slate-500">{(risks ?? []).length}</span>}
        >
          {!risks || risks.length === 0 ? (
            <EmptyState
              icon={<Shield className="h-5 w-5 text-cyan-400" />}
              title="No risk assessments yet"
            />
          ) : (
            <div className="divide-y divide-white/[0.04]">
              {risks.map(r => {
                const c =
                  r.risk_score <= 25 ? '#10b981' :
                  r.risk_score <= 50 ? '#fbbf24' :
                  r.risk_score <= 75 ? '#f97316' : '#f87171';
                return (
                  <div key={r.created_at} className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-cyan-500/[0.03]">
                    <div
                      className="grid h-12 w-12 flex-shrink-0 place-items-center rounded-full border-[2.5px] font-mono text-base font-extrabold transition-shadow hover:shadow-[0_0_16px_currentColor]"
                      style={{ borderColor: c, color: c, background: `${c}15` }}
                    >
                      {r.risk_score}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <RiskBadge level={r.risk_level} />
                        <span className="text-xs text-slate-500">
                          {r.failure_probability !== null
                            ? `${(r.failure_probability * 100).toFixed(1)}% fail prob`
                            : ''}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{r.recommendation ?? '—'}</p>
                    </div>
                    <p className="font-mono text-xs text-slate-600 flex-shrink-0">
                      {fmt(r.created_at)}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
