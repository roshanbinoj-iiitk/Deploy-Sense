"""
DeploySense — AI Analysis Engine (Phase 2)

WHY THIS EXISTS:
The heuristic risk engine (Sprint 1-2) answers "how risky is this deployment?"
The AI engine answers deeper questions:
  1. "WHY is this deployment risky?" — Root cause analysis
  2. "What will likely fail?" — Failure pattern detection
  3. "What should we do?" — Actionable recommendations
  4. "Have we seen this before?" — Historical pattern matching

ARCHITECTURE:
  The AI engine is a standalone module that:
    1. Receives deployment context (risk assessment, PR data, service history)
    2. Constructs a structured prompt
    3. Calls an LLM via REST API (OpenAI-compatible)
    4. Parses the structured response
    5. Stores the analysis in the ai_analyses table

WHY LLM (not classical ML):
  - Classical ML needs labeled training data (we don't have it yet)
  - LLMs can reason over deployment context without training
  - LLMs produce human-readable explanations (not just scores)
  - We can switch to fine-tuned models in Phase 3

WHY STRUCTURED OUTPUT:
  We use structured prompts that request JSON output.
  This ensures the AI response is machine-parseable AND human-readable.

PROVIDER FLEXIBILITY:
  The engine supports any OpenAI-compatible API:
    - OpenAI GPT-4
    - Google Gemini (via OpenAI compat endpoint)
    - Local models (Ollama, vLLM)
    - Azure OpenAI
  Just set AI_API_BASE and AI_API_KEY in .env
"""

import json
import time

import httpx

from deploysense.logging import get_logger

logger = get_logger(__name__)


# ─── Analysis Types ──────────────────────────────────────────────────────────

class DeploymentAnalysis:
    """Result of an AI deployment analysis."""

    def __init__(
        self,
        summary: str,
        risk_explanation: str,
        root_causes: list[dict],
        recommendations: list[dict],
        failure_patterns: list[dict],
        confidence: float,
        model_used: str,
        latency_ms: float,
        risk_score: int | None = None,
    ):
        self.summary = summary
        self.risk_explanation = risk_explanation
        self.root_causes = root_causes
        self.recommendations = recommendations
        self.failure_patterns = failure_patterns
        self.confidence = confidence
        self.model_used = model_used
        self.latency_ms = latency_ms
        self.risk_score = risk_score

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "risk_explanation": self.risk_explanation,
            "root_causes": self.root_causes,
            "recommendations": self.recommendations,
            "failure_patterns": self.failure_patterns,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "risk_score": self.risk_score,
        }


# ─── Prompt Builder ──────────────────────────────────────────────────────────

def build_deployment_prompt(context: dict) -> str:
    """
    Build a structured prompt for deployment analysis.

    WHY this structure:
      - System role: Sets the AI's persona and output format
      - Context section: Provides all deployment data
      - Analysis request: Specifies exactly what we want back
      - JSON schema: Ensures parseable output
    """
    return f"""You are DeploySense, a deployment intelligence system that analyzes
deployment risk and provides actionable recommendations.

Analyze the following deployment and provide a structured assessment.

## Deployment Context

- **Service**: {context.get('service_name', 'unknown')}
- **Environment**: {context.get('environment', 'unknown')}
- **Git SHA**: {context.get('git_sha', 'unknown')}
- **Risk Score**: {context.get('risk_score', 0)}/100
- **Risk Level**: {context.get('risk_level', 'LOW')}
- **Failure Probability**: {context.get('failure_probability', 0):.1%}

## Risk Factors
{_format_factors(context.get('factors', []))}

## Change Details
- Files Changed: {context.get('files_changed', 0)}
- Lines Added: {context.get('lines_added', 0)}
- Lines Deleted: {context.get('lines_deleted', 0)}
- Has DB Migration: {context.get('has_db_migration', False)}
- Has Infra Change: {context.get('has_infra_change', False)}

## Service History
- Recent Failures (7d): {context.get('recent_failure_count', 0)}
- Deployments (24h): {context.get('deployments_last_24h', 0)}
- Stability Score: {context.get('service_stability_score', 100)}/100
- Current Error Rate: {context.get('current_error_rate', 0):.4f}
- Baseline Error Rate: {context.get('baseline_error_rate', 0):.4f}

## Instructions

Respond with a JSON object containing:
1. "summary": A 1-2 sentence summary of the deployment risk
2. "risk_explanation": Why this deployment has this risk level (2-3 sentences)
3. "root_causes": Array of {{"cause": "...", "confidence": 0.0-1.0, "evidence": "..."}}
4. "recommendations": Array of {{"action": "...", "priority": "HIGH|MEDIUM|LOW", "reason": "..."}}
5. "failure_patterns": Array of {{"pattern": "...", "probability": 0.0-1.0, "mitigation": "..."}}

Respond ONLY with valid JSON. No markdown, no explanation outside JSON."""


def _format_factors(factors: list[dict]) -> str:
    if not factors:
        return "- No risk factors identified"
    return "\n".join(
        f"- **{f.get('name', 'unknown')}** (contribution: {f.get('contribution', 0):.0%}): "
        f"{f.get('description', '')}"
        for f in factors
    )


# ─── AI Engine ───────────────────────────────────────────────────────────────

class AIEngine:
    """
    LLM-powered deployment analysis engine.

    Supports any OpenAI-compatible API endpoint.
    """

    def __init__(
        self,
        api_base: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def analyze_deployment(self, context: dict) -> DeploymentAnalysis:
        """
        Analyze a deployment using the LLM.

        FLOW:
          1. Build structured prompt from deployment context
          2. Call LLM API
          3. Parse JSON response
          4. Validate and return analysis

        FALLBACK:
          If the LLM is unavailable or returns invalid JSON,
          we fall back to a rule-based analysis.
        """
        start = time.perf_counter()
        prompt = build_deployment_prompt(context)

        try:
            result = await self._call_llm(prompt)
            analysis_data = json.loads(result)
            latency = (time.perf_counter() - start) * 1000

            logger.info(
                "ai_analysis_completed",
                model=self.model,
                latency_ms=round(latency, 2),
                risk_score=context.get("risk_score"),
            )

            return DeploymentAnalysis(
                summary=analysis_data.get("summary", "Analysis completed."),
                risk_explanation=analysis_data.get("risk_explanation", ""),
                root_causes=analysis_data.get("root_causes", []),
                recommendations=analysis_data.get("recommendations", []),
                failure_patterns=analysis_data.get("failure_patterns", []),
                confidence=0.85,
                model_used=self.model,
                latency_ms=round(latency, 2),
                risk_score=context.get("risk_score"),
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.warning(
                "ai_analysis_fallback",
                error=str(e),
                latency_ms=round(latency, 2),
            )
            return self._rule_based_analysis(context, latency)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM API and return the response text."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a deployment risk analysis AI. "
                                "Respond only with valid JSON."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _rule_based_analysis(self, context: dict, latency: float) -> DeploymentAnalysis:
        """
        Fallback: Generate analysis using rules when LLM is unavailable.

        WHY a fallback:
          The AI engine should never block deployments. If the LLM is down,
          we still provide useful analysis based on the risk factors.
        """
        score = context.get("risk_score", 0)
        factors = context.get("factors", [])
        level = context.get("risk_level", "LOW")

        # Generate summary
        if score <= 25:
            summary = "Low-risk deployment. No significant risk factors detected."
        elif score <= 50:
            summary = (
                f"Moderate-risk deployment with {len(factors)} risk factor(s). "
                "Proceed with monitoring."
            )
        elif score <= 75:
            summary = (
                f"High-risk deployment. {len(factors)} risk factor(s) require "
                "manual review before proceeding."
            )
        else:
            summary = (
                f"Critical-risk deployment with {len(factors)} risk factor(s). "
                "Deployment should be blocked pending review."
            )

        # Generate root causes from factors
        root_causes = []
        for f in factors:
            root_causes.append({
                "cause": f.get("description", f.get("name", "Unknown")),
                "confidence": f.get("contribution", 0.5),
                "evidence": f"Risk factor: {f.get('name', 'unknown')} "
                            f"contributing {f.get('contribution', 0):.0%} to overall score",
            })

        # Generate recommendations
        recommendations = []
        if context.get("has_db_migration"):
            recommendations.append({
                "action": "Run migration in a maintenance window with rollback script ready",
                "priority": "HIGH",
                "reason": "Database migrations are the #1 cause of deployment failures",
            })
        if context.get("has_infra_change"):
            recommendations.append({
                "action": "Review infrastructure changes with SRE team before deploying",
                "priority": "HIGH",
                "reason": "Infrastructure changes affect service availability",
            })
        if context.get("recent_failure_count", 0) > 0:
            recommendations.append({
                "action": "Investigate and resolve recent failures before deploying",
                "priority": "HIGH",
                "reason": (
                    f"{context['recent_failure_count']} recent failures indicate "
                    "service instability"
                ),
            })
        if context.get("files_changed", 0) > 20:
            recommendations.append({
                "action": "Consider splitting this deployment into smaller, incremental releases",
                "priority": "MEDIUM",
                "reason": f"{context['files_changed']} files changed increases blast radius",
            })
        if score > 50:
            recommendations.append({
                "action": "Enable enhanced monitoring and alerting for this deployment",
                "priority": "HIGH",
                "reason": f"Risk score {score} exceeds safety threshold",
            })

        # Failure patterns
        failure_patterns = []
        if context.get("has_db_migration"):
            failure_patterns.append({
                "pattern": "Migration lock contention",
                "probability": 0.3,
                "mitigation": "Use online DDL tools (pt-online-schema-change or gh-ost)",
            })
        if context.get("current_error_rate", 0) > context.get("baseline_error_rate", 0) * 2:
            failure_patterns.append({
                "pattern": "Cascading failure from elevated error rate",
                "probability": 0.4,
                "mitigation": "Deploy circuit breakers and set error budget alerts",
            })

        return DeploymentAnalysis(
            summary=summary,
            risk_explanation=f"This deployment has a risk score of {score}/100 ({level}) "
                           f"with {len(factors)} contributing factor(s).",
            root_causes=root_causes,
            recommendations=recommendations,
            failure_patterns=failure_patterns,
            confidence=0.7,
            model_used="rule-based-fallback",
            latency_ms=round(latency, 2),
            risk_score=score,
        )


# ─── Factory ─────────────────────────────────────────────────────────────────

def get_ai_engine() -> AIEngine:
    """Create an AI engine instance from settings."""
    from deploysense.core import get_settings

    settings = get_settings()
    return AIEngine(
        api_base=getattr(settings, "ai_api_base", "https://api.openai.com/v1"),
        api_key=getattr(settings, "ai_api_key", ""),
        model=getattr(settings, "ai_model", "gpt-4o-mini"),
    )
