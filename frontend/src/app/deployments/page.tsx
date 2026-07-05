import Link from 'next/link';
import { getDeployments } from '@/lib/api';
import { RiskBadge, StatusPill, EnvBadge } from '@/components/ui/Badge';
import PageHeader from '@/components/ui/PageHeader';
import Panel from '@/components/ui/Panel';
import EmptyState from '@/components/ui/EmptyState';
import Pagination from '@/components/ui/Pagination';
import SimulateDeploymentModal from '@/components/ui/SimulateDeploymentModal';
import { Rocket } from 'lucide-react';

const STATUSES = ['STABLE','DEPLOYING','MONITORING','FAILED','ROLLED_BACK','PENDING','BLOCKED'];
const ENVS = ['production', 'staging', 'development'];

function fmt(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
  });
}

export default async function DeploymentsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; status?: string; environment?: string }>;
}) {
  const params = await searchParams;
  const page   = Number(params.page ?? 1);
  const status = params.status;
  const env    = params.environment;

  let data = { data: [] as Awaited<ReturnType<typeof getDeployments>>['data'], pagination: { page: 1, per_page: 20, total: 0 } };
  try {
    data = await getDeployments(page, 20, status, env);
  } catch {}

  const { data: deployments, pagination } = data;
  const totalPages = Math.max(1, Math.ceil(pagination.total / pagination.per_page));

  function pageUrl(p: number) {
    const q = new URLSearchParams();
    q.set('page', String(p));
    if (status) q.set('status', status);
    if (env) q.set('environment', env);
    return `/deployments?${q}`;
  }

  return (
    <div className="flex flex-col gap-8 p-8 animate-fadein">
      {/* Header */}
      <div className="flex items-center justify-between">
        <PageHeader
          title="Deployments"
          subtitle={`${pagination.total} total — page ${page} of ${totalPages}`}
        />
        <SimulateDeploymentModal />
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <Link href="/deployments" className={`ds-filter-chip ${!status && !env ? 'active' : ''}`}>All</Link>
        {STATUSES.map(s => (
          <Link key={s} href={`/deployments?status=${s}`} className={`ds-filter-chip ${status === s ? 'active' : ''}`}>
            {s.replace('_', ' ')}
          </Link>
        ))}
        <span className="mx-1 text-slate-600">|</span>
        {ENVS.map(e => (
          <Link key={e} href={`/deployments?environment=${e}`} className={`ds-filter-chip ${env === e ? 'active' : ''}`}>
            {e}
          </Link>
        ))}
      </div>

      {/* Table */}
      <Panel
        title={`${pagination.total} Deployment${pagination.total !== 1 ? 's' : ''}${status ? ` — ${status}` : ''}${env ? ` — ${env}` : ''}`}
      >
        {deployments.length === 0 ? (
          <EmptyState
            icon={<Rocket className="h-5 w-5 text-cyan-400" />}
            title="No deployments match the current filter"
            description="Try adjusting the filters above."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.05] bg-white/[0.015]">
                  {['ID', 'Environment', 'Version', 'SHA', 'Status', 'Risk', 'Deployed By', 'Created'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.07em] text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {deployments.map(d => (
                  <tr key={d.id} className="border-b border-white/[0.04] transition-colors hover:bg-cyan-500/[0.03]">
                    <td className="px-5 py-3">
                      <Link href={`/deployments/${d.id}`} className="font-mono text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                        {d.id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td className="px-5 py-3"><EnvBadge env={d.environment} /></td>
                    <td className="px-5 py-3 font-mono text-xs text-slate-300">{d.version ?? '—'}</td>
                    <td className="px-5 py-3 font-mono text-xs text-slate-500">{d.git_sha?.slice(0, 7) ?? '—'}</td>
                    <td className="px-5 py-3"><StatusPill status={d.status} /></td>
                    <td className="px-5 py-3">
                      {d.risk_level
                        ? <RiskBadge level={d.risk_level} score={d.risk_score} />
                        : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-5 py-3 text-xs text-slate-300">{d.deployed_by ?? '—'}</td>
                    <td className="px-5 py-3 font-mono text-xs text-slate-500">{fmt(d.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {/* Pagination */}
      <Pagination page={page} totalPages={totalPages} buildUrl={pageUrl} />
    </div>
  );
}
