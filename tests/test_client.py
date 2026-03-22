"""Tests for the ILinkClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai4wechat.client import (
    ILinkClient,
    ILinkMessage,
    _random_wechat_uin,
    _base_info,
)


class TestILinkMessage:
    def test_from_dict_text(self):
        data = {
            "message_id": 123,
            "from_user_id": "user1",
            "to_user_id": "bot1",
            "session_id": "sess1",
            "message_type": 1,
            "message_state": 0,
            "context_token": "ctx123",
            "create_time_ms": 1711152000000,
            "item_list": [{"type": 1, "text_item": {"text": "hello"}}],
        }
        msg = ILinkMessage.from_dict(data)
        assert msg.message_id == 123
        assert msg.from_user_id == "user1"
        assert msg.context_token == "ctx123"
        assert msg.extract_text() == "hello"

    def test_from_dict_image(self):
        data = {"item_list": [{"type": 2}]}
        msg = ILinkMessage.from_dict(data)
        assert msg.extract_text() == "[Image]"

    def test_from_dict_voice(self):
        data = {"item_list": [{"type": 3, "voice_item": {"text": "transcribed"}}]}
        msg = ILinkMessage.from_dict(data)
        assert "[Voice] transcribed" in msg.extract_text()

    def test_from_dict_file(self):
        data = {"item_list": [{"type": 4, "file_item": {"file_name": "doc.pdf"}}]}
        msg = ILinkMessage.from_dict(data)
        assert "[File: doc.pdf]" in msg.extract_text()

    def test_from_dict_video(self):
        data = {"item_list": [{"type": 5}]}
        msg = ILinkMessage.from_dict(data)
        assert msg.extract_text() == "[Video]"

    def test_from_dict_empty(self):
        msg = ILinkMessage.from_dict({})
        assert msg.extract_text() == "[Empty message]"

    def test_from_dict_missing_fields(self):
        msg = ILinkMessage.from_dict({"message_id": 1})
        assert msg.message_id == 1
        assert msg.from_user_id == ""
        assert msg.items == []


class TestHelpers:
    def test_random_wechat_uin_is_string(self):
        uin = _random_wechat_uin()
        assert isinstance(uin, str)
        assert len(uin) > 0

    def test_random_wechat_uin_varies(self):
        uins = {_random_wechat_uin() for _ in range(10)}
        assert len(uins) > 1

    def test_base_info(self):
        info = _base_info()
        assert "channel_version" in info


class TestILinkClientInit:
    def test_defaults(self):
        client = ILinkClient()
        assert client.token == ""
        assert "ilinkai.weixin.qq.com" in client.base_url

    def test_custom(self):
        client = ILinkClient(token="tok", base_url="https://example.com/")
        assert client.token == "tok"
        assert client.base_url == "https://example.com"

    def test_trailing_slash_stripped(self):
        client = ILinkClient(base_url="https://example.com///")
        assert not client.base_url.endswith("/")


class TestSendMessageReturnValue:
    @pytest.mark.asyncio
    async def test_send_message_returns_dict(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"ret": 0}

        with patch("ai4wechat.client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value = mock_client
            mock_client.is_closed = False

            client = ILinkClient(token="tok", base_url="https://example.com")
            client._client = mock_client

            result = await client.send_message("user1", "hello", "ctx")
            assert isinstance(result, dict)
            assert result["ret"] == 0

    @pytest.mark.asyncio
    async def test_send_message_logs_nonzero_ret(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"ret": -2}

        with patch("ai4wechat.client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value = mock_client
            mock_client.is_closed = False

            client = ILinkClient(token="tok", base_url="https://example.com")
            client._client = mock_client

            result = await client.send_message("user1", "hello", "ctx")
            assert result["ret"] == -2


class TestGetUploadUrl:
    @pytest.mark.asyncio
    async def test_get_upload_url_sends_correct_body(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"upload_url": "https://cdn.example.com/upload"}

        with patch("ai4wechat.client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value = mock_client
            mock_client.is_closed = False

            client = ILinkClient(token="tok", base_url="https://example.com")
            client._client = mock_client

            result = await client.get_upload_url(
                filekey="file123",
                media_type=1,
                rawsize=1024,
                rawfilemd5="abc123",
                filesize=1040,
                aeskey="deadbeef",
            )

            call_args = mock_client.post.call_args
            body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert body["filekey"] == "file123"
            assert body["media_type"] == 1
            assert body["rawsize"] == 1024
            assert body["aeskey"] == "deadbeef"
            assert body["no_need_thumb"] is True
            assert result["upload_url"] == "https://cdn.example.com/upload"
