/**
 * API client — all calls go through Next.js rewrites to http://localhost:8000
 * so there are zero CORS issues. In production point NEXT_PUBLIC_API_URL at
 * your deployed backend.
 */

import type {
  Alert,
  Deployment,
  DeploymentListResponse,
  DeploymentStats,
  RiskAssessment,
  Service,
  TimelineEvent,
} from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    next: { revalidate: 15 }, // ISR: revalidate every 15s
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Deployments ──────────────────────────────────────────────────────────────

export async function getDeployments(
  page = 1,
  perPage = 20,
  status?: string,
  environment?: string,
): Promise<DeploymentListResponse> {
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  if (status) params.set('status', status);
  if (environment) params.set('environment', environment);
  return get<DeploymentListResponse>(`/api/v1/deployments?${params}`);
}

export async function getDeployment(id: string): Promise<Deployment> {
  return get<Deployment>(`/api/v1/deployments/${id}`);
}

export async function getDeploymentStats(): Promise<DeploymentStats> {
  return get<DeploymentStats>('/api/v1/deployments/stats');
}

export async function getDeploymentTimeline(id: string): Promise<TimelineEvent[]> {
  return get<TimelineEvent[]>(`/api/v1/deployments/${id}/timeline`);
}

export async function getDeploymentRisk(id: string): Promise<RiskAssessment[]> {
  return get<RiskAssessment[]>(`/api/v1/deployments/${id}/risk`);
}

// ── Services ─────────────────────────────────────────────────────────────────

export async function getServices(): Promise<Service[]> {
  return get<Service[]>('/api/v1/services');
}

// ── Alerts (dashboard routes — no auth token needed for Jinja2 counterpart) ──
// NOTE: /api/v1/alerts requires auth. The dashboard Jinja2 routes bypass auth.
// For the Next.js frontend we fetch from the dashboard JSON endpoint.
// Alternatively, implement a lightweight token. For now we use the public
// Jinja2 data indirectly via a dedicated public endpoint if added.
// We include it here to show the pattern; it will 401 without a token.

export async function getDashboardAlerts(): Promise<Alert[]> {
  // Reuse the dashboard-level data via the Python template endpoint response
  // by hitting a lightweight proxy. For now return empty on 401.
  try {
    return get<Alert[]>('/api/v1/alerts?per_page=50');
  } catch {
    return [];
  }
}
