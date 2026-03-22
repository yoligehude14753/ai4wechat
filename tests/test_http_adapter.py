"""Tests for the HTTP adapter bridge."""

import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from ai4wechat.http_adapter import _forward_to_service
from ai4wechat.types import Message, MessageType


@pytest.fixture
def sample_message():
    return Message(
        id="msg_123",
        text="What is the weather?",
        sender="user_abc",
        receiver="bot_xyz",
        type=MessageType.TEXT,
        timestamp=datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc),
        session_id="sess_001",
        raw={"context_token": "ctx_tok", "session_id": "sess_001"},
    )


class TestForwardToService:
    @pytest.mark.asyncio
    async def test_success_text_field(self, sample_message):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"text": "It's sunny!"}

        with patch("ai4wechat.http_adapter.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await _forward_to_service(
                "http://localhost:8000/chat", sample_message
            )
            assert result == "It's sunny!"

            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert payload["message_id"] == "msg_123"
            assert payload["conversation_id"] == "user_abc"
            assert payload["user_id"] == "user_abc"
            assert payload["text"] == "What is the weather?"
            assert payload["type"] == "text"

    @pytest.mark.asyncio
    async def test_success_reply_field(self, sample_message):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"reply": "It's cloudy!"}

        with patch("ai4wechat.http_adapter.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await _forward_to_service(
                "http://localhost:8000/chat", sample_message
            )
            assert result == "It's cloudy!"

    @pytest.mark.asyncio
    async def test_success_message_field(self, sample_message):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"message": "It's rainy!"}

        with patch("ai4wechat.http_adapter.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await _forward_to_service(
                "http://localhost:8000/chat", sample_message
            )
            assert result == "It's rainy!"

    @pytest.mark.asyncio
    async def test_empty_response(self, sample_message):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}

        with patch("ai4wechat.http_adapter.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await _forward_to_service(
                "http://localhost:8000/chat", sample_message
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_payload_structure(self, sample_message):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"text": "ok"}

        with patch("ai4wechat.http_adapter.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            await _forward_to_service("http://test/chat", sample_message)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")

            required_fields = [
                "message_id",
                "conversation_id",
                "user_id",
                "text",
                "type",
                "timestamp",
                "session_id",
                "raw",
            ]
            for field in required_fields:
                assert field in payload, f"Missing field: {field}"
