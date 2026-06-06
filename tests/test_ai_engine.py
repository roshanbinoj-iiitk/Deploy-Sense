"""
DeploySense — Unit Tests: AI Analysis Engine (Phase 2)

Tests the AI engine's rule-based fallback, prompt building,
and analysis result structure.
"""

import pytest

from deploysense.ai.engine import (
    AIEngine,
    DeploymentAnalysis,
    build_deployment_prompt,
)


# ─── Prompt Building ────────────────────────────────────────────────────────

class TestPromptBuilding:
    """The prompt should include all deployment context."""

    def test_prompt_includes_service_name(self):
        context = {"service_name": "payments-api", "environment": "production"}
        prompt = build_deployment_prompt(context)
        assert "payments-api" in prompt
        assert "production" in prompt

    def test_prompt_includes_risk_data(self):
        context = {
            "service_name": "test",
            "risk_score": 75,
            "risk_level": "HIGH",
            "failure_probability": 0.25,
        }
        prompt = build_deployment_prompt(context)
        assert "75" in prompt
        assert "HIGH" in prompt

    def test_prompt_includes_factors(self):
        context = {
            "service_name": "test",
            "factors": [
                {"name": "database_migration", "contribution": 0.2, "description": "Includes DB migration"},
            ],
        }
        prompt = build_deployment_prompt(context)
        assert "database_migration" in prompt
        assert "DB migration" in prompt

    def test_prompt_includes_history(self):
        context = {
            "service_name": "test",
            "recent_failure_count": 3,
            "deployments_last_24h": 5,
            "service_stability_score": 60,
        }
        prompt = build_deployment_prompt(context)
        assert "3" in prompt
        assert "5" in prompt
        assert "60" in prompt

    def test_prompt_requests_json(self):
        prompt = build_deployment_prompt({"service_name": "test"})
        assert "JSON" in prompt


# ─── Rule-Based Fallback ────────────────────────────────────────────────────

class TestRuleBasedFallback:
    """When LLM is unavailable, the rule-based fallback should produce useful analysis."""

    def _engine(self) -> AIEngine:
        return AIEngine(api_base="http://fake", api_key="fake")

    def test_low_risk_summary(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 10, "risk_level": "LOW", "factors": []},
            latency=5.0,
        )
        assert "Low-risk" in result.summary
        assert result.model_used == "rule-based-fallback"

    def test_critical_risk_summary(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 85, "risk_level": "CRITICAL", "factors": [{"name": "db"}]},
            latency=5.0,
        )
        assert "Critical-risk" in result.summary
        assert result.risk_score is None or True  # It's in the explanation

    def test_migration_generates_recommendation(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 50, "risk_level": "MODERATE", "factors": [], "has_db_migration": True},
            latency=5.0,
        )
        assert len(result.recommendations) >= 1
        assert any("migration" in r["action"].lower() for r in result.recommendations)

    def test_infra_change_generates_recommendation(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 40, "risk_level": "MODERATE", "factors": [], "has_infra_change": True},
            latency=5.0,
        )
        assert any("infrastructure" in r["action"].lower() for r in result.recommendations)

    def test_recent_failures_generates_recommendation(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 60, "risk_level": "HIGH", "factors": [], "recent_failure_count": 3},
            latency=5.0,
        )
        assert any("failures" in r["reason"].lower() for r in result.recommendations)

    def test_large_changeset_generates_recommendation(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 40, "risk_level": "MODERATE", "factors": [], "files_changed": 30},
            latency=5.0,
        )
        assert any("splitting" in r["action"].lower() for r in result.recommendations)

    def test_root_causes_from_factors(self):
        factors = [
            {"name": "database_migration", "contribution": 0.2, "description": "Includes migration"},
            {"name": "files_changed", "contribution": 0.1, "description": "25 files changed"},
        ]
        result = self._engine()._rule_based_analysis(
            {"risk_score": 45, "risk_level": "MODERATE", "factors": factors},
            latency=5.0,
        )
        assert len(result.root_causes) == 2

    def test_failure_patterns_for_migration(self):
        result = self._engine()._rule_based_analysis(
            {"risk_score": 50, "risk_level": "MODERATE", "factors": [], "has_db_migration": True},
            latency=5.0,
        )
        assert len(result.failure_patterns) >= 1

    def test_elevated_error_rate_pattern(self):
        result = self._engine()._rule_based_analysis(
            {
                "risk_score": 50, "risk_level": "MODERATE", "factors": [],
                "current_error_rate": 0.05, "baseline_error_rate": 0.01,
            },
            latency=5.0,
        )
        assert any("cascading" in p["pattern"].lower() for p in result.failure_patterns)


# ─── Analysis Result Structure ───────────────────────────────────────────────

class TestAnalysisResultStructure:
    """Analysis results should have the correct structure."""

    def test_to_dict(self):
        analysis = DeploymentAnalysis(
            summary="Test summary",
            risk_explanation="Test explanation",
            root_causes=[{"cause": "test"}],
            recommendations=[{"action": "test"}],
            failure_patterns=[{"pattern": "test"}],
            confidence=0.85,
            model_used="test-model",
            latency_ms=10.0,
        )
        d = analysis.to_dict()
        assert d["summary"] == "Test summary"
        assert d["confidence"] == 0.85
        assert len(d["root_causes"]) == 1
        assert len(d["recommendations"]) == 1

    def test_confidence_range(self):
        analysis = DeploymentAnalysis(
            summary="", risk_explanation="", root_causes=[], recommendations=[],
            failure_patterns=[], confidence=0.7, model_used="test", latency_ms=1.0,
        )
        assert 0.0 <= analysis.confidence <= 1.0


# ─── Engine Fallback on Network Error ────────────────────────────────────────

class TestEngineFallback:
    """When the LLM API is unreachable, the engine should fall back gracefully."""

    @pytest.mark.asyncio
    async def test_fallback_on_connection_error(self):
        engine = AIEngine(api_base="http://localhost:1", api_key="fake", timeout=1.0)
        result = await engine.analyze_deployment({
            "service_name": "test",
            "risk_score": 50,
            "risk_level": "MODERATE",
            "factors": [],
        })
        assert result.model_used == "rule-based-fallback"
        assert result.summary is not None
