// ── Core domain types matching the FastAPI schemas ──────────────────────────

export type DeploymentStatus =
  | 'PENDING' | 'RISK_ASSESSED' | 'APPROVED' | 'BLOCKED'
  | 'DEPLOYING' | 'DEPLOYED' | 'MONITORING'
  | 'STABLE' | 'DEGRADED' | 'ROLLED_BACK' | 'FAILED';

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type AlertSeverity = 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface Deployment {
  id: string;
  service_name: string | null;
  environment: string;
  version: string | null;
  git_sha: string;
  status: DeploymentStatus;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  failure_probability: number | null;
  deployed_by: string | null;
  initiated_at: string | null;
  deployed_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
}

export interface DeploymentListResponse {
  data: Deployment[];
  pagination: Pagination;
}

export interface Service {
  id: string;
  name: string;
  environment: string | null;
  status: string;
  stability_score: number;
  created_at: string;
}

export interface Alert {
  id: string;
  severity: AlertSeverity | null;
  title: string | null;
  description: string | null;
  status: AlertStatus;
  triggered_at: string;
  resolved_at: string | null;
}

export interface DeploymentStats {
  total_deployments: number;
  stable: number;
  failed: number;
  success_rate: number;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  previous_state: string | null;
  current_state: string | null;
  message: string | null;
  timestamp: string | null;
}

export interface RiskAssessment {
  deployment_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  failure_probability: number | null;
  recommendation: string | null;
  created_at: string;
}
