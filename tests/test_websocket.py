"""
DeploySense — Unit Tests: WebSocket Manager (Phase 2)

Tests the WebSocket connection manager's broadcast behavior.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from deploysense.api.websocket import (
    ConnectionManager,
)


class TestConnectionManager:
    """WebSocket connection manager tests."""

    def test_initial_state(self):
        mgr = ConnectionManager()
        assert mgr.active_connections == 0

    @pytest.mark.asyncio
    async def test_connect(self):
        mgr = ConnectionManager()
        ws = AsyncMock()
        await mgr.connect(ws)
        assert mgr.active_connections == 1
        ws.accept.assert_awaited_once()

    def test_disconnect(self):
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr._connections.add(ws)
        mgr.disconnect(ws)
        assert mgr.active_connections == 0

    def test_disconnect_missing_ws(self):
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.disconnect(ws)  # Should not raise
        assert mgr.active_connections == 0

    @pytest.mark.asyncio
    async def test_broadcast_empty(self):
        mgr = ConnectionManager()
        # Should not raise with no connections
        await mgr.broadcast({"event": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_sends_json(self):
        mgr = ConnectionManager()
        ws = AsyncMock()
        ws.client_state = MagicMock()
        ws.client_state.name = "CONNECTED"
        # Patch the enum comparison
        from starlette.websockets import WebSocketState

        ws.client_state = WebSocketState.CONNECTED
        mgr._connections.add(ws)

        await mgr.broadcast({"event": "test.event"})

        ws.send_text.assert_awaited_once()
        sent = json.loads(ws.send_text.call_args[0][0])
        assert sent["event"] == "test.event"
        assert "timestamp" in sent
