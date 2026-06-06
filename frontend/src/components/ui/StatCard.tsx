interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: 'default' | 'green' | 'red' | 'yellow' | 'blue' | 'orange';
}

const colorMap = {
  default: { text: 'text-white',        accent: 'from-cyan-500/20 to-emerald-500/10', glow: 'group-hover:shadow-cyan-500/8' },
  green:   { text: 'text-emerald-400',  accent: 'from-emerald-500/20 to-green-500/10', glow: 'group-hover:shadow-emerald-500/8' },
  red:     { text: 'text-red-400',      accent: 'from-red-500/20 to-rose-500/10', glow: 'group-hover:shadow-red-500/8' },
  yellow:  { text: 'text-yellow-400',   accent: 'from-yellow-500/20 to-amber-500/10', glow: 'group-hover:shadow-yellow-500/8' },
  blue:    { text: 'text-blue-400',     accent: 'from-blue-500/20 to-cyan-500/10', glow: 'group-hover:shadow-blue-500/8' },
  orange:  { text: 'text-orange-400',   accent: 'from-orange-500/20 to-amber-500/10', glow: 'group-hover:shadow-orange-500/8' },
};

export default function StatCard({ label, value, sub, color = 'default' }: StatCardProps) {
  const c = colorMap[color];
  return (
    <div className={`group relative overflow-hidden rounded-[14px] border border-white/[0.08] bg-[#0d1117]/70 backdrop-blur-md px-5 py-5 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:border-white/[0.12] hover:shadow-xl ${c.glow}`}>
      {/* Animated top accent gradient */}
      <div className={`absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r ${c.accent} opacity-60 group-hover:opacity-100 transition-opacity`} />

      {/* Corner glow on hover */}
      <div className={`absolute -top-6 -right-6 h-24 w-24 rounded-full bg-gradient-to-br ${c.accent} opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-60`} />

      <div className="relative">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400">
          {label}
        </p>
        <p className={`text-[2.1rem] font-extrabold leading-none tracking-tight tabular-nums ${c.text}`}>
          {value}
        </p>
        {sub && (
          <p className="mt-2.5 text-[11px] text-slate-500">{sub}</p>
        )}
      </div>
    </div>
  );
}
