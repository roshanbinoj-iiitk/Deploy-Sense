import Link from 'next/link';
import { getServices } from '@/lib/api';
import { ArrowRight, Server } from 'lucide-react';
import PageHeader from '@/components/ui/PageHeader';
import Panel from '@/components/ui/Panel';
import EmptyState from '@/components/ui/EmptyState';

export default async function ServicesPage() {
  let services: Awaited<ReturnType<typeof getServices>> = [];
  try { services = await getServices(); } catch {}

  const healthy  = services.filter(s => (s.stability_score ?? 100) >= 80).length;
  const degraded = services.length - healthy;

  return (
    <div className="flex flex-col gap-8 p-8 animate-fadein">
      {/* Header */}
      <PageHeader
        title="Services"
        subtitle={`${services.length} registered service${services.length !== 1 ? 's' : ''}`}
      >
        {healthy > 0 && (
          <span className="flex items-center gap-2.5 rounded-full border border-emerald-500/15 bg-emerald-500/[0.04] px-4 py-2 text-xs font-semibold text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
            </span>
            {healthy} healthy
          </span>
        )}
        {degraded > 0 && (
          <span className="rounded-full border border-red-500/15 bg-red-500/[0.04] px-4 py-2 text-xs font-semibold text-red-400">
            {degraded} degraded
          </span>
        )}
      </PageHeader>

      {services.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-5 rounded-[14px] border border-white/[0.08] bg-[#0d1117]/70 py-24 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-[14px] border border-white/[0.08] bg-cyan-500/[0.06] shadow-[0_0_24px_rgba(34,211,238,0.1)] animate-[float_3s_ease-in-out_infinite]">
            <Server className="h-6 w-6 text-cyan-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">No services registered</p>
            <p className="mt-1.5 text-xs text-slate-400">Services are auto-discovered when deployments are created.</p>
          </div>
        </div>
      ) : (
        <>
          {/* Service cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 stagger-children">
            {services.map(s => {
              const score = s.stability_score ?? 100;
              const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
              const statusCls =
                s.status === 'ACTIVE'   ? 'border-emerald-500/15 bg-emerald-500/[0.06] text-emerald-400' :
                s.status === 'DEGRADED' ? 'border-red-500/15 bg-red-500/[0.06] text-red-400' :
                                          'border-white/[0.08] bg-white/[0.03] text-slate-400';
              return (
                <div key={s.id} className="group relative overflow-hidden rounded-[14px] border border-white/[0.08] bg-[#0d1117]/70 backdrop-blur-sm p-5 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:border-white/[0.12] hover:shadow-xl">
                  {/* Top accent line */}
                  <div className="absolute inset-x-0 top-0 h-[2px] opacity-60 group-hover:opacity-100 transition-opacity" style={{ background: `linear-gradient(90deg, ${color}, transparent)` }} />

                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{s.name}</p>
                      <p className="mt-1 text-[11px] text-slate-500">{s.environment ?? 'unknown env'}</p>
                    </div>
                    <span className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${statusCls}`}>
                      {s.status}
                    </span>
                  </div>

                  <div className="mb-4 grid grid-cols-2 gap-3">
                    <div>
                      <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500">Stability</p>
                      <p className="text-xl font-bold" style={{ color }}>{score}</p>
                    </div>
                    <div>
                      <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500">Risk</p>
                      <p className="text-sm font-semibold" style={{ color }}>
                        {score >= 80 ? 'LOW' : score >= 60 ? 'MODERATE' : 'HIGH'}
                      </p>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${score}%`, background: color, boxShadow: `0 0 8px ${color}40` }}
                    />
                  </div>

                  <div className="mt-3.5 flex items-center justify-between">
                    <span className="font-mono text-[10px] text-slate-600">{s.id.slice(0, 8)}…</span>
                    <Link href={`/deployments?service=${s.name}`} className="flex items-center gap-1 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors">
                      Deployments
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Table */}
          <Panel title="All Services">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.05] bg-white/[0.015]">
                    {['Name','Environment','Status','Stability','ID'].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.07em] text-slate-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {services.map(s => {
                    const score = s.stability_score ?? 100;
                    const color = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400';
                    const envCls =
                      s.environment === 'production' ? 'border-red-500/15 bg-red-500/[0.06] text-red-400' :
                      s.environment === 'staging'    ? 'border-yellow-500/15 bg-yellow-500/[0.06] text-yellow-400' :
                                                       'border-blue-500/15 bg-blue-500/[0.06] text-blue-400';
                    return (
                      <tr key={s.id} className="border-b border-white/[0.04] hover:bg-cyan-500/[0.03] transition-colors">
                        <td className="px-5 py-3 font-semibold text-white">{s.name}</td>
                        <td className="px-5 py-3">
                          <span className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${envCls}`}>
                            {s.environment ?? '—'}
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <span className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${
                            s.status === 'ACTIVE' ? 'border-emerald-500/15 bg-emerald-500/[0.06] text-emerald-400' :
                            'border-white/[0.08] bg-white/[0.03] text-slate-400'
                          }`}>{s.status}</span>
                        </td>
                        <td className="px-5 py-3">
                          <span className={`font-mono font-semibold ${color}`}>{score}</span>
                          <span className="text-slate-600"> / 100</span>
                        </td>
                        <td className="px-5 py-3 font-mono text-xs text-slate-500">{s.id.slice(0, 8)}…</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
