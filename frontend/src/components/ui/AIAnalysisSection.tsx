'use client';

import { useState } from 'react';
import { analyzeDeployment } from '@/lib/api';
import type { AnalysisResponse } from '@/lib/types';
import Panel from './Panel';
import { Brain, AlertTriangle, ShieldAlert, CheckCircle, Activity, ServerCrash, ChevronRight, Sparkles } from 'lucide-react';

export default function AIAnalysisSection({ deploymentId }: { deploymentId: string }) {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeDeployment(deploymentId);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.message || 'Failed to run AI analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Panel
      title="AI Risk Analysis"
      actions={
        !analysis && !loading ? (
          <button
            onClick={runAnalysis}
            className="group relative flex items-center gap-2 overflow-hidden rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400 px-4 py-1.5 text-xs font-bold text-[#060a10] shadow-[0_0_15px_rgba(34,211,238,0.4)] transition-all hover:scale-105 hover:shadow-[0_0_25px_rgba(34,211,238,0.6)]"
          >
            <div className="absolute inset-0 bg-white/20 opacity-0 transition-opacity group-hover:opacity-100" />
            <Sparkles className="h-3.5 w-3.5" />
            Run Analysis
          </button>
        ) : analysis ? (
          <span className="flex items-center gap-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/[0.05] px-3 py-1 text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
            <CheckCircle className="h-3 w-3" /> Analysis Complete
          </span>
        ) : null
      }
    >
      <div className="p-5">
        {loading && (
          <div className="flex flex-col items-center justify-center py-10 animate-fadein">
            <div className="relative flex h-16 w-16 items-center justify-center">
              <div className="absolute inset-0 animate-ping rounded-full border-2 border-cyan-400/30" />
              <div className="absolute inset-2 animate-spin rounded-full border-b-2 border-t-2 border-cyan-400" />
              <Brain className="h-6 w-6 text-cyan-400 animate-pulse" />
            </div>
            <p className="mt-4 text-sm font-medium text-cyan-400 animate-pulse">Analyzing deployment context...</p>
            <p className="mt-1 text-xs text-slate-500">Checking risk factors, historical stability, and PR changes.</p>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            <div className="flex items-center gap-2 font-bold mb-1">
              <AlertTriangle className="h-4 w-4" />
              Analysis Failed
            </div>
            {error}
          </div>
        )}

        {!loading && !analysis && !error && (
          <div className="flex flex-col items-center justify-center py-12 text-center opacity-70">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] border border-white/[0.08]">
              <Brain className="h-6 w-6 text-slate-400" />
            </div>
            <h3 className="text-sm font-semibold text-white">No Analysis Available</h3>
            <p className="mt-1 max-w-xs text-xs text-slate-400">
              Run an AI analysis to deeply evaluate root causes, predict failure patterns, and get actionable recommendations.
            </p>
          </div>
        )}

        {analysis && (
          <div className="animate-fadein space-y-6">
            {/* Summary & Explanation */}
            <div className="rounded-2xl border border-cyan-500/15 bg-cyan-500/[0.03] p-5">
              <h3 className="text-lg font-semibold text-white mb-2">{analysis.summary}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{analysis.risk_explanation}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Root Causes */}
              {analysis.root_causes && analysis.root_causes.length > 0 && (
                <div className="space-y-3">
                  <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
                    <ShieldAlert className="h-3.5 w-3.5" /> Root Causes
                  </h4>
                  <div className="space-y-2">
                    {analysis.root_causes.map((rc, i) => (
                      <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5 transition-colors hover:bg-white/[0.04]">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-semibold text-sm text-white">{rc.cause}</span>
                          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded-full border border-cyan-400/20">
                            {Math.round(rc.confidence * 100)}% confidence
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">{rc.evidence}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <div className="space-y-3">
                  <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
                    <Activity className="h-3.5 w-3.5" /> Recommendations
                  </h4>
                  <div className="space-y-2">
                    {analysis.recommendations.map((rec, i) => (
                      <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5 transition-colors hover:bg-white/[0.04]">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            rec.priority === 'HIGH' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                            rec.priority === 'MEDIUM' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                            'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          }`}>
                            {rec.priority}
                          </span>
                          <span className="font-semibold text-sm text-white">{rec.action}</span>
                        </div>
                        <p className="text-xs text-slate-500">{rec.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Failure Patterns */}
            {analysis.failure_patterns && analysis.failure_patterns.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
                  <ServerCrash className="h-3.5 w-3.5" /> Likely Failure Patterns
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {analysis.failure_patterns.map((fp, i) => (
                    <div key={i} className="flex flex-col rounded-xl border border-white/[0.06] bg-gradient-to-br from-white/[0.03] to-transparent p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-sm text-white">{fp.pattern}</span>
                        <span className="text-[10px] font-mono text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded-full border border-orange-400/20">
                          {Math.round(fp.probability * 100)}% prob
                        </span>
                      </div>
                      <div className="mt-auto flex items-start gap-2 pt-3 border-t border-white/[0.04]">
                        <ChevronRight className="h-4 w-4 text-cyan-500 shrink-0 mt-0.5" />
                        <span className="text-xs text-slate-400">
                          <strong className="text-slate-300">Mitigation:</strong> {fp.mitigation}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Meta */}
            <div className="pt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>Model: {analysis.model_used}</span>
              <span>ID: {analysis.id.slice(0, 8)}</span>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
