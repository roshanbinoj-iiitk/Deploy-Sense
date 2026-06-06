export default function Loading() {
  return (
    <div className="flex flex-col gap-8 p-8 animate-fadein">
      {/* Header skeleton */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="h-8 w-64 rounded-lg bg-white/[0.06] animate-pulse" />
          <div className="mt-3 h-4 w-80 rounded-md bg-white/[0.04] animate-pulse" />
        </div>
        <div className="h-8 w-36 rounded-full bg-white/[0.04] animate-pulse" />
      </div>

      {/* Stat card skeletons */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="relative overflow-hidden rounded-[14px] border border-white/[0.06] bg-[#0d1117]/70 px-5 py-5"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-cyan-500/10 to-emerald-500/5" />
            <div className="mb-3 h-3 w-24 rounded bg-white/[0.06] animate-pulse" />
            <div className="h-9 w-16 rounded-lg bg-white/[0.08] animate-pulse" />
            <div className="mt-3 h-3 w-20 rounded bg-white/[0.04] animate-pulse" />
          </div>
        ))}
      </div>

      {/* Panel skeleton */}
      <div className="overflow-hidden rounded-[14px] border border-white/[0.06] bg-[#0d1117]/70">
        <div className="border-b border-white/[0.06] px-5 py-4">
          <div className="h-4 w-40 rounded bg-white/[0.06] animate-pulse" />
        </div>
        <div className="p-5 space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <div className="h-4 w-20 rounded bg-white/[0.04] animate-pulse" />
              <div className="h-4 w-16 rounded-full bg-white/[0.04] animate-pulse" />
              <div className="h-4 flex-1 rounded bg-white/[0.03] animate-pulse" />
              <div className="h-4 w-16 rounded-full bg-white/[0.04] animate-pulse" />
              <div className="h-4 w-12 rounded bg-white/[0.03] animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
