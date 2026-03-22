"""
Async client for the WeChat iLink Bot API.

Built on the protocol work from weixin-bot (github.com/epiral/weixin-bot).
"""

import os
import struct
import base64
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

import httpx

log = logging.getLogger("ai4wechat")

DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"
BOT_TYPE = "3"
CHANNEL_VERSION = "0.1.0"
LONG_POLL_TIMEOUT = 35.0
API_TIMEOUT = 15.0
CONFIG_TIMEOUT = 10.0


@dataclass
class ILinkMessage:
    """Raw message from the iLink API."""

    message_id: int = 0
    from_user_id: str = ""
    to_user_id: str = ""
    session_id: str = ""
    message_type: int = 0  # 1=user, 2=bot
    message_state: int = 0  # 0=new, 1=generating, 2=complete
    context_token: str = ""
    create_time_ms: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ILinkMessage":
        return cls(
            message_id=data.get("message_id", 0),
            from_user_id=data.get("from_user_id", ""),
            to_user_id=data.get("to_user_id", ""),
            session_id=data.get("session_id", ""),
            message_type=data.get("message_type", 0),
            message_state=data.get("message_state", 0),
            context_token=data.get("context_token", ""),
            create_time_ms=data.get("create_time_ms", 0),
            items=data.get("item_list", []),
        )

    def extract_text(self) -> str:
        """Extract human-readable text from message items."""
        parts: List[str] = []
        for item in self.items:
            t = item.get("type", 0)
            if t == 1 and item.get("text_item"):
                parts.append(item["text_item"].get("text", ""))
            elif t == 2:
                parts.append("[Image]")
            elif t == 3:
                voice = item.get("voice_item", {})
                parts.append(f"[Voice] {voice.get('text', '')}")
            elif t == 4:
                fi = item.get("file_item", {})
                parts.append(f"[File: {fi.get('file_name', 'unknown')}]")
            elif t == 5:
                parts.append("[Video]")
        return "\n".join(parts) or "[Empty message]"


@dataclass
class QRCodeResult:
    qrcode: str = ""
    qrcode_img_content: str = ""


@dataclass
class QRStatusResult:
    status: str = "wait"  # wait, scaned, confirmed, expired
    bot_token: str = ""
    bot_id: str = ""
    base_url: str = ""
    user_id: str = ""


@dataclass
class GetUpdatesResult:
    ret: int = 0
    errcode: int = 0
    errmsg: str = ""
    messages: List[ILinkMessage] = field(default_factory=list)
    sync_buf: str = ""
    longpolling_timeout_ms: int = 0


def _random_wechat_uin() -> str:
    num = struct.unpack(">I", os.urandom(4))[0]
    return base64.b64encode(str(num).encode()).decode()


def _base_info() -> Dict[str, str]:
    return {"channel_version": CHANNEL_VERSION}


class ILinkClient:
    """Async client for the WeChat iLink Bot API.

    Args:
        token: Bot authentication token (from QR login).
        base_url: iLink API base URL. Defaults to the official endpoint.
    """

    def __init__(self, token: str = "", base_url: str = ""):
        self.token = token
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=API_TIMEOUT)
        return self._client

    def _headers(self, with_auth: bool = True) -> Dict[str, str]:
        h: Dict[str, str] = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "X-WECHAT-UIN": _random_wechat_uin(),
        }
        if with_auth and self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # -- QR Login --

    async def get_qrcode(self) -> QRCodeResult:
        """Fetch a new QR code for WeChat login."""
        client = await self._ensure_client()
        headers = self._headers(with_auth=False)
        headers.pop("Content-Type", None)
        resp = await client.get(
            f"{self.base_url}/ilink/bot/get_bot_qrcode",
            params={"bot_type": BOT_TYPE},
            headers=headers,
            timeout=CONFIG_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return QRCodeResult(
            qrcode=data.get("qrcode", ""),
            qrcode_img_content=data.get("qrcode_img_content", ""),
        )

    async def poll_qr_status(self, qrcode: str) -> QRStatusResult:
        """Poll the QR code status until scanned/confirmed/expired."""
        client = await self._ensure_client()
        headers = self._headers(with_auth=False)
        headers.pop("Content-Type", None)
        headers["iLink-App-ClientVersion"] = "1"
        try:
            resp = await client.get(
                f"{self.base_url}/ilink/bot/get_qrcode_status",
                params={"qrcode": qrcode},
                headers=headers,
                timeout=LONG_POLL_TIMEOUT + 5,
            )
            resp.raise_for_status()
            data = resp.json()
            return QRStatusResult(
                status=data.get("status", "wait"),
                bot_token=data.get("bot_token", ""),
                bot_id=data.get("ilink_bot_id", ""),
                base_url=data.get("baseurl", ""),
                user_id=data.get("ilink_user_id", ""),
            )
        except httpx.TimeoutException:
            return QRStatusResult(status="wait")

    # -- Messaging --

    async def get_updates(self, sync_buf: str = "") -> GetUpdatesResult:
        """Long-poll for new messages."""
        client = await self._ensure_client()
        body = {"get_updates_buf": sync_buf, "base_info": _base_info()}
        try:
            resp = await client.post(
                f"{self.base_url}/ilink/bot/getupdates",
                json=body,
                headers=self._headers(),
                timeout=LONG_POLL_TIMEOUT + 5,
            )
            resp.raise_for_status()
            data = resp.json()
            messages = [ILinkMessage.from_dict(m) for m in data.get("msgs", [])]
            return GetUpdatesResult(
                ret=data.get("ret", 0),
                errcode=data.get("errcode", 0),
                errmsg=data.get("errmsg", ""),
                messages=messages,
                sync_buf=data.get("get_updates_buf", sync_buf),
                longpolling_timeout_ms=data.get("longpolling_timeout_ms", 0),
            )
        except httpx.TimeoutException:
            return GetUpdatesResult(sync_buf=sync_buf)

    async def send_message(self, to_user_id: str, text: str, context_token: str) -> Dict[str, Any]:
        """Send a text message to a user.

        Returns the API response dict. Raises on HTTP errors.
        Note: ret:-2 can occur when sending multiple messages too quickly.
        """
        client = await self._ensure_client()
        client_id = f"ai4wechat-{os.urandom(4).hex()}"
        body = {
            "msg": {
                "from_user_id": "",
                "to_user_id": to_user_id,
                "client_id": client_id,
                "message_type": 2,
                "message_state": 2,
                "item_list": [{"type": 1, "text_item": {"text": text}}],
                "context_token": context_token,
            },
            "base_info": _base_info(),
        }
        resp = await client.post(
            f"{self.base_url}/ilink/bot/sendmessage",
            json=body,
            headers=self._headers(),
            timeout=CONFIG_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        ret = data.get("ret", 0)
        if ret != 0:
            log.warning(f"sendmessage ret={ret} to={to_user_id}")
        return data

    async def send_typing(self, user_id: str, ticket: str, status: int = 1) -> None:
        """Send typing indicator. status: 1=start, 2=stop."""
        client = await self._ensure_client()
        body = {
            "user_id": user_id,
            "typing_ticket": ticket,
            "typing_status": status,
            "base_info": _base_info(),
        }
        try:
            resp = await client.post(
                f"{self.base_url}/ilink/bot/sendtyping",
                json=body,
                headers=self._headers(),
                timeout=5.0,
            )
            resp.raise_for_status()
        except Exception:
            pass  # typing is best-effort

    async def get_config(self, user_id: str, context_token: str = "") -> Dict[str, Any]:
        """Get bot config (includes typing ticket)."""
        client = await self._ensure_client()
        body: Dict[str, Any] = {"user_id": user_id, "base_info": _base_info()}
        if context_token:
            body["context_token"] = context_token
        resp = await client.post(
            f"{self.base_url}/ilink/bot/getconfig",
            json=body,
            headers=self._headers(),
            timeout=CONFIG_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_upload_url(
        self,
        filekey: str,
        media_type: int,
        rawsize: int,
        rawfilemd5: str,
        filesize: int,
        aeskey: str,
    ) -> Dict[str, Any]:
        """Get CDN upload URL for media files.

        Args:
            filekey: Unique file identifier.
            media_type: 1=image, 3=file.
            rawsize: Original file size in bytes.
            rawfilemd5: MD5 hash of the original file.
            filesize: Encrypted file size in bytes.
            aeskey: Hex-encoded AES-128 key used for encryption.
        """
        client = await self._ensure_client()
        body = {
            "filekey": filekey,
            "media_type": media_type,
            "rawsize": rawsize,
            "rawfilemd5": rawfilemd5,
            "filesize": filesize,
            "no_need_thumb": True,
            "aeskey": aeskey,
            "base_info": _base_info(),
        }
        resp = await client.post(
            f"{self.base_url}/ilink/bot/getuploadurl",
            json=body,
            headers=self._headers(),
            timeout=CONFIG_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
