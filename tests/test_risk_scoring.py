"""
DeploySense — Unit Tests: Enhanced Risk Scoring Engine (Sprint 2)

Tests the new historical and contextual features added in Sprint 2.
"""

import uuid

from deploysense.api.schemas import RiskEvaluationRequest
from deploysense.risk_engine.scoring import (
    RiskFeatures,
    _compute_time_risk,
    _logistic_probability,
    compute_enhanced_risk,
    compute_risk_score,
)


def _make_request(**kwargs) -> RiskEvaluationRequest:
    defaults = {
        "deployment_id": uuid.uuid4(),
        "service_name": "test-service",
        "environment": "production",
        "git_sha": "abc1234",
        "files_changed": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "has_db_migration": False,
        "has_infra_change": False,
    }
    defaults.update(kwargs)
    return RiskEvaluationRequest(**defaults)


# ─── Sprint 1 Backward Compatibility ────────────────────────────────────────


class TestBackwardCompatibility:
    """Sprint 1 API must still work with the enhanced engine."""

    def test_empty_deployment_is_low_risk(self):
        result = compute_risk_score(_make_request())
        assert result.risk_score <= 5  # May get time-of-day modifier
        assert result.risk_level == "LOW"

    def test_migration_still_adds_risk(self):
        result = compute_risk_score(_make_request(has_db_migration=True))
        assert result.risk_score >= 20

    def test_combined_factors_still_work(self):
        result = compute_risk_score(
            _make_request(
                has_db_migration=True,
                has_infra_change=True,
                files_changed=30,
            )
        )
        assert result.risk_score >= 45
        assert result.risk_level in ("MODERATE", "HIGH")


# ─── Enhanced Engine: Historical Features ────────────────────────────────────


class TestRecentFailures:
    """Recent failures should increase risk significantly."""

    def test_one_recent_failure(self):
        features = RiskFeatures(recent_failure_count=1, deploy_hour_utc=12, deploy_day_of_week=1)
        result = compute_enhanced_risk(features)
        assert result.risk_score >= 5

    def test_three_recent_failures_is_high(self):
        features = RiskFeatures(recent_failure_count=3, deploy_hour_utc=12, deploy_day_of_week=1)
        result = compute_enhanced_risk(features)
        assert result.risk_score >= 15
        factor_names = [f.name for f in result.factors]
        assert "recent_failures" in factor_names

    def test_failures_with_migration_compounds(self):
        features = RiskFeatures(
            has_db_migration=True,
            recent_failure_count=3,
            deploy_hour_utc=12,
            deploy_day_of_week=1,
        )
        result = compute_enhanced_risk(features)
        assert result.risk_score >= 35


class TestDeploymentFrequency:
    """Too many deploys in 24h indicates churn."""

    def test_normal_frequency_no_risk(self):
        features = RiskFeatures(deployments_last_24h=2, deploy_hour_utc=12, deploy_day_of_week=1)
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "deployment_frequency" not in factor_names

    def test_high_frequency_adds_risk(self):
        features = RiskFeatures(deployments_last_24h=6, deploy_hour_utc=12, deploy_day_of_week=1)
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "deployment_frequency" in factor_names


class TestServiceStability:
    """Low stability score should increase risk."""

    def test_stable_service_no_risk(self):
        features = RiskFeatures(
            service_stability_score=95, deploy_hour_utc=12, deploy_day_of_week=1
        )
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "service_instability" not in factor_names

    def test_unstable_service_adds_risk(self):
        features = RiskFeatures(
            service_stability_score=50, deploy_hour_utc=12, deploy_day_of_week=1
        )
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "service_instability" in factor_names


class TestMetricsAnomaly:
    """Error rate above baseline should increase risk."""

    def test_normal_error_rate_no_risk(self):
        features = RiskFeatures(
            current_error_rate=0.01,
            baseline_error_rate=0.01,
            deploy_hour_utc=12,
            deploy_day_of_week=1,
        )
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "error_rate_elevated" not in factor_names

    def test_elevated_error_rate_adds_risk(self):
        features = RiskFeatures(
            current_error_rate=0.05,
            baseline_error_rate=0.01,
            deploy_hour_utc=12,
            deploy_day_of_week=1,
        )
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "error_rate_elevated" in factor_names


# ─── Contextual Features ────────────────────────────────────────────────────


class TestTimeOfDayRisk:
    """Deployments outside business hours are riskier."""

    def test_business_hours_safe(self):
        assert _compute_time_risk(12, 2) == 0.0  # Noon Wednesday

    def test_late_night_risky(self):
        assert _compute_time_risk(23, 1) == 1.0  # 11pm Tuesday

    def test_friday_afternoon_risky(self):
        assert _compute_time_risk(15, 4) == 1.0  # 3pm Friday

    def test_weekend_risky(self):
        assert _compute_time_risk(12, 5) == 1.0  # Noon Saturday

    def test_early_morning_marginal(self):
        assert _compute_time_risk(8, 1) == 0.5  # 8am Tuesday

    def test_time_risk_integrated(self):
        features = RiskFeatures(deploy_hour_utc=23, deploy_day_of_week=4)
        result = compute_enhanced_risk(features)
        factor_names = [f.name for f in result.factors]
        assert "deployment_timing" in factor_names


# ─── Logistic Probability ───────────────────────────────────────────────────


class TestLogisticProbability:
    """Failure probability should follow a logistic curve."""

    def test_zero_score_low_probability(self):
        assert _logistic_probability(0) < 0.01

    def test_moderate_score_moderate_probability(self):
        p = _logistic_probability(50)
        assert 0.05 < p < 0.35

    def test_high_score_high_probability(self):
        p = _logistic_probability(80)
        assert p > 0.15

    def test_probability_capped(self):
        assert _logistic_probability(100) <= 0.5

    def test_probability_increases_with_score(self):
        p1 = _logistic_probability(20)
        p2 = _logistic_probability(50)
        p3 = _logistic_probability(80)
        assert p1 < p2 < p3


# ─── Factor Categories ──────────────────────────────────────────────────────


class TestFactorCategories:
    """Factors should be categorized correctly."""

    def test_static_factors_labeled(self):
        features = RiskFeatures(
            has_db_migration=True,
            deploy_hour_utc=12,
            deploy_day_of_week=1,
        )
        result = compute_enhanced_risk(features)
        migration_factor = next(f for f in result.factors if f.name == "database_migration")
        assert migration_factor.category == "static"

    def test_historical_factors_labeled(self):
        features = RiskFeatures(
            recent_failure_count=3,
            deploy_hour_utc=12,
            deploy_day_of_week=1,
        )
        result = compute_enhanced_risk(features)
        failure_factor = next(f for f in result.factors if f.name == "recent_failures")
        assert failure_factor.category == "historical"

    def test_contextual_factors_labeled(self):
        features = RiskFeatures(deploy_hour_utc=23, deploy_day_of_week=4)
        result = compute_enhanced_risk(features)
        time_factor = next(f for f in result.factors if f.name == "deployment_timing")
        assert time_factor.category == "contextual"


# ─── Feature Snapshot ────────────────────────────────────────────────────────


class TestFeatureSnapshot:
    """Risk result should include the complete feature vector."""

    def test_snapshot_contains_all_features(self):
        features = RiskFeatures(
            has_db_migration=True,
            files_changed=10,
            recent_failure_count=2,
            deploy_hour_utc=14,
            deploy_day_of_week=2,
        )
        result = compute_enhanced_risk(features)
        snap = result.feature_snapshot
        assert "has_db_migration" in snap
        assert "files_changed" in snap
        assert "recent_failure_count" in snap
        assert "deploy_hour_utc" in snap
        assert snap["has_db_migration"] is True
        assert snap["files_changed"] == 10
        assert snap["recent_failure_count"] == 2
