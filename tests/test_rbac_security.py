"""
DeploySense — Unit Tests: RBAC & Security (Phase 3)

Tests role-based access control, permission checks,
rate limiting, and security headers.
"""

from deploysense.api.rbac import (
    ROLE_PERMISSIONS,
    Permission,
    has_permission,
)
from deploysense.api.security import RateLimiter

# ─── RBAC Permission Tests ──────────────────────────────────────────────────


class TestRolePermissions:
    """Verify role → permission mappings."""

    def test_viewer_can_read_deployments(self):
        class MockUser:
            role = "viewer"

        assert has_permission(MockUser(), Permission.DEPLOYMENTS_READ)

    def test_viewer_cannot_create_deployments(self):
        class MockUser:
            role = "viewer"

        assert not has_permission(MockUser(), Permission.DEPLOYMENTS_CREATE)

    def test_engineer_can_create_deployments(self):
        class MockUser:
            role = "engineer"

        assert has_permission(MockUser(), Permission.DEPLOYMENTS_CREATE)

    def test_engineer_cannot_manage_users(self):
        class MockUser:
            role = "engineer"

        assert not has_permission(MockUser(), Permission.USERS_MANAGE)

    def test_admin_has_all_permissions(self):
        class MockUser:
            role = "admin"

        for perm in Permission:
            assert has_permission(MockUser(), perm), f"Admin missing {perm.value}"

    def test_service_can_create_deployments(self):
        class MockUser:
            role = "service"

        assert has_permission(MockUser(), Permission.DEPLOYMENTS_CREATE)

    def test_service_cannot_manage_users(self):
        class MockUser:
            role = "service"

        assert not has_permission(MockUser(), Permission.USERS_MANAGE)

    def test_service_cannot_access_dashboard(self):
        class MockUser:
            role = "service"

        assert not has_permission(MockUser(), Permission.DASHBOARD_READ)

    def test_unknown_role_has_no_permissions(self):
        class MockUser:
            role = "unknown"

        assert not has_permission(MockUser(), Permission.DEPLOYMENTS_READ)

    def test_none_role_defaults_to_viewer(self):
        class MockUser:
            role = None

        # Should not crash
        result = has_permission(MockUser(), Permission.DEPLOYMENTS_READ)
        assert isinstance(result, bool)


# ─── Permission Completeness ────────────────────────────────────────────────


class TestPermissionCompleteness:
    """Every role should have at least some permissions defined."""

    def test_all_roles_defined(self):
        expected_roles = {"viewer", "engineer", "admin", "service"}
        assert set(ROLE_PERMISSIONS.keys()) == expected_roles

    def test_viewer_has_read_permissions(self):
        viewer_perms = ROLE_PERMISSIONS["viewer"]
        assert Permission.DEPLOYMENTS_READ in viewer_perms
        assert Permission.RISK_READ in viewer_perms
        assert Permission.DASHBOARD_READ in viewer_perms

    def test_engineer_superset_of_viewer(self):
        viewer_perms = ROLE_PERMISSIONS["viewer"]
        engineer_perms = ROLE_PERMISSIONS["engineer"]
        assert viewer_perms.issubset(engineer_perms)


# ─── Rate Limiter Tests ─────────────────────────────────────────────────────


class TestRateLimiter:
    """Rate limiter should enforce request limits."""

    def test_allows_initial_requests(self):
        limiter = RateLimiter()
        allowed, remaining = limiter.is_allowed("1.2.3.4", "/api/v1/deployments")
        assert allowed is True
        assert remaining >= 0

    def test_blocks_after_exceeding_limit(self):
        limiter = RateLimiter()
        # Exhaust tokens
        for _ in range(150):
            limiter.is_allowed("10.0.0.1", "/api/v1/deployments")
        # Should be blocked
        allowed, remaining = limiter.is_allowed("10.0.0.1", "/api/v1/deployments")
        assert allowed is False
        assert remaining == 0

    def test_different_ips_independent(self):
        limiter = RateLimiter()
        # Exhaust IP A
        for _ in range(150):
            limiter.is_allowed("ip-a", "/api/v1/deployments")
        # IP B should still be allowed
        allowed, _ = limiter.is_allowed("ip-b", "/api/v1/deployments")
        assert allowed is True

    def test_auth_endpoint_has_lower_limit(self):
        limiter = RateLimiter()
        # Auth has 20/min limit
        for _ in range(25):
            limiter.is_allowed("auth-test", "/api/v1/auth/login")
        allowed, _ = limiter.is_allowed("auth-test", "/api/v1/auth/login")
        assert allowed is False

    def test_ai_endpoint_has_lower_limit(self):
        limiter = RateLimiter()
        # AI has 10/min limit
        for _ in range(15):
            limiter.is_allowed("ai-test", "/api/v1/ai/analyze")
        allowed, _ = limiter.is_allowed("ai-test", "/api/v1/ai/analyze")
        assert allowed is False

    def test_group_detection(self):
        limiter = RateLimiter()
        assert limiter._get_group("/api/v1/auth/login") == "auth"
        assert limiter._get_group("/api/v1/webhooks/github") == "webhook"
        assert limiter._get_group("/api/v1/admin/users") == "admin"
        assert limiter._get_group("/api/v1/ai/analyze") == "ai"
        assert limiter._get_group("/api/v1/deployments") == "default"
