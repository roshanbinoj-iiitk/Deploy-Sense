'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Rocket, Server, Shield, AlertTriangle } from 'lucide-react';

const navItems = [
  { href: '/',            label: 'Overview',      icon: LayoutDashboard },
  { href: '/deployments', label: 'Deployments',   icon: Rocket },
  { href: '/services',    label: 'Services',      icon: Server },
  { href: '/risk',        label: 'Risk Analysis',  icon: Shield },
  { href: '/alerts',      label: 'Alerts',        icon: AlertTriangle },
];

export default function Sidebar() {
  const path = usePathname();

  function isActive(href: string) {
    if (href === '/') return path === '/';
    return path.startsWith(href);
  }

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-white/[0.06] bg-[#060a10]/90 backdrop-blur-2xl">

      {/* Logo */}
      <div className="flex items-center gap-3.5 border-b border-white/[0.06] px-5 py-[22px]">
        <div className="group relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-[10px] border border-cyan-400/20 bg-gradient-to-br from-cyan-500/15 to-emerald-500/10 shadow-lg shadow-cyan-500/10">
          <Rocket className="relative z-10 h-5 w-5 text-cyan-400 transition-transform duration-300 group-hover:rotate-[-15deg] group-hover:scale-110" />
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] animate-[shimmer_3s_ease-in-out_infinite]" />
        </div>
        <div>
          <p className="text-[15px] font-bold tracking-tight text-white">DeploySense</p>
          <p className="text-[11px] font-medium tracking-wide text-slate-500">Release intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className={`group relative flex items-center gap-3 rounded-[10px] border px-3.5 py-2.5 text-[13px] font-medium transition-all duration-200 ${
                active
                  ? 'border-cyan-500/15 bg-gradient-to-r from-cyan-500/10 to-transparent text-white'
                  : 'border-transparent text-slate-400 hover:border-white/[0.06] hover:bg-white/[0.03] hover:text-white'
              }`}
            >
              {/* Active indicator bar */}
              {active && (
                <div className="absolute -left-3 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-r-full bg-gradient-to-b from-cyan-400 to-emerald-400 shadow-[0_0_12px_rgba(34,211,238,0.3)]" />
              )}

              <div className={`flex h-7 w-7 items-center justify-center rounded-lg transition-colors ${
                active
                  ? 'bg-cyan-500/12'
                  : 'bg-white/[0.04] group-hover:bg-white/[0.06]'
              }`}>
                <Icon className={`h-[15px] w-[15px] transition-colors ${
                  active ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'
                }`} />
              </div>

              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/[0.06] px-4 py-4">
        <div className="flex items-center gap-2.5 rounded-[10px] border border-white/[0.06] bg-white/[0.02] px-3.5 py-2.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
          </span>
          <span className="text-xs font-medium text-slate-400">Development</span>
        </div>
      </div>
    </aside>
  );
}
