import Link from 'next/link';
import StatCard from '@/components/ui/StatCard';
import PageHeader from '@/components/ui/PageHeader';
import Panel from '@/components/ui/Panel';
import EmptyState from '@/components/ui/EmptyState';
import { AlertTriangle, CheckCircle } from 'lucide-react';

export default async function AlertsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const params = await searchParams;
  const statusFilter = params.status;

  let alerts: { id: string; severity: string; title: string; description: string; status: string; triggered_at: string }[] = [];
  let open = 0, acked = 0;
  let authRequired = false;

  try {
    const res = await fetch(
      `http://localhost:8000/api/v1/alerts?per_page=50${statusFilter ? `&status=${statusFilter}` : ''}`,
      { next: { revalidate: 10 } }
    );
    if (res.status === 401) {
      authRequired = true;
    } else if (res.ok) {
      const data = await res.json();
      alerts = data.data ?? [];
      open  = alerts.filter(a => a.status === 'OPEN').length;
      acked = alerts.filter(a => a.status === 'ACKNOWLEDGED').length;
    }
  } catch {}

  const STATUSES = ['OPEN', 'ACKNOWLEDGED', 'RESOLVED'];
  const sevColor = (s: string) =>
    s === 'CRITICAL' ? { bar: '#f87171', badge: 'border-red-500/15 bg-red-500/[0.06] text-red-400' } :
    s === 'HIGH'     ? { bar: '#f97316', badge: 'border-orange-500/15 bg-orange-500/[0.06] text-orange-400' } :
    s === 'WARNING'  ? { bar: '#fbbf24', badge: 'border-yellow-500/15 bg-yellow-500/[0.06] text-yellow-400' } :
                       { bar: '#60a5fa', badge: 'border-blue-500/15 bg-blue-500/[0.06] text-blue-400' };
  const statusBadge = (s: string) =>
    s === 'OPEN'         ? 'border-red-500/15 bg-red-500/[0.06] text-red-400' :
    s === 'ACKNOWLEDGED' ? 'border-yellow-500/15 bg-yellow-500/[0.06] text-yellow-400' :
                           'border-emerald-500/15 bg-emerald-500/[0.06] text-emerald-400';

  function fmt(iso: string) {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
      new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  }

  return (
    <div className="flex flex-col gap-7 p-8 animate-fadein">
      {/* Header */}
      <PageHeader
        title="Alerts"
        subtitle="Deployment incidents and risk events"
      >
        {open > 0 && (
          <span className="flex items-center gap-2 rounded-full border border-red-500/15 bg-red-500/[0.04] px-4 py-2 text-xs font-bold text-red-400 shadow-[0_0_16px_rgba(239,68,68,0.08)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
            </span>
            {open} open
          </span>
        )}
      </PageHeader>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 stagger-children">
        <StatCard label="Open"          value={open}            color={open > 0 ? 'red' : 'default'}    sub="Needs action" />
        <StatCard label="Acknowledged"  value={acked}           color={acked > 0 ? 'yellow' : 'default'} sub="In progress" />
        <StatCard label="Total Shown"   value={alerts.length}   sub="Last 50" />
      </div>

      {/* Auth notice or content */}
      {authRequired ? (
        <div className="rounded-[14px] border border-yellow-500/15 bg-yellow-500/[0.04] p-7">
          <h3 className="mb-2 font-semibold text-yellow-300">Authentication required</h3>
          <p className="mb-5 text-sm text-yellow-200/60">
            The <code className="rounded bg-white/[0.08] px-1.5 py-0.5 font-mono text-xs">
              /api/v1/alerts
            </code> endpoint requires a JWT token. You can:
          </p>
          <ul className="space-y-2.5 text-sm text-yellow-200/60">
            <li className="flex items-center gap-2">
              <span className="text-yellow-400">→</span>
              View alerts on the <a href="http://localhost:8000/dashboard/alerts" target="_blank" className="text-cyan-400 underline underline-offset-2 hover:text-cyan-300">Jinja2 dashboard</a>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-yellow-400">→</span>
              Add GitHub OAuth login to this frontend
            </li>
            <li className="flex items-center gap-2">
              <span className="text-yellow-400">→</span>
              Or add a public read-only alerts endpoint
            </li>
          </ul>
        </div>
      ) : (
        <>
          {/* Filter bar */}
          <div className="flex flex-wrap gap-2">
            <Link href="/alerts" className={`ds-filter-chip ${!statusFilter ? 'active' : ''}`}>All</Link>
            {STATUSES.map(s => (
              <Link key={s} href={`/alerts?status=${s}`} className={`ds-filter-chip ${statusFilter === s ? 'active' : ''}`}>
                {s}
              </Link>
            ))}
          </div>

          {/* Alert list */}
          <Panel
            title={`${alerts.length} Alert${alerts.length !== 1 ? 's' : ''}${statusFilter ? ` — ${statusFilter}` : ''}`}
          >
            {alerts.length === 0 ? (
              <EmptyState
                icon={<CheckCircle className="h-5 w-5 text-emerald-400" />}
                title={`No alerts${statusFilter ? ` with status ${statusFilter}` : ''}`}
                description="Alerts are created when deployment risk is HIGH or CRITICAL."
              />
            ) : (
              <div className="divide-y divide-white/[0.04]">
                {alerts.map(a => {
                  const { bar, badge } = sevColor(a.severity ?? 'INFO');
                  return (
                    <div key={a.id} className="flex items-start gap-3.5 px-5 py-4 hover:bg-cyan-500/[0.03] transition-colors">
                      {/* Severity bar with glow */}
                      <div
                        className="mt-1.5 h-12 w-[3px] flex-shrink-0 rounded-full"
                        style={{ background: bar, boxShadow: `0 0 8px ${bar}40` }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-[13.5px] font-semibold text-white">{a.title ?? 'Alert'}</p>
                        {a.description && (
                          <p className="mt-0.5 text-xs text-slate-400 line-clamp-2">{a.description}</p>
                        )}
                        <div className="mt-2.5 flex flex-wrap gap-2">
                          <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${badge}`}>
                            {a.severity ?? 'INFO'}
                          </span>
                          <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${statusBadge(a.status)}`}>
                            {a.status}
                          </span>
                        </div>
                      </div>
                      <p className="flex-shrink-0 font-mono text-[11px] text-slate-600">
                        {fmt(a.triggered_at)}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}
