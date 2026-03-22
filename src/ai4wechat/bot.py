"""
High-level Bot class — the main entry point for ai4wechat.

Usage:
    from ai4wechat import Bot

    bot = Bot()

    @bot.on_message
    async def handle(msg):
        return f"You said: {msg.text}"

    bot.run()
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from .client import ILinkClient, ILinkMessage
from .formatter import format_for_wechat, truncate_for_wechat
from .login import login, login_web, DEFAULT_TOKEN_DIR
from .types import Message, _classify_items

log = logging.getLogger("ai4wechat")

SESSION_EXPIRED_ERRCODE = -14
MAX_CONSECUTIVE_FAILURES = 5
INITIAL_RETRY_DELAY = 2.0
MAX_RETRY_DELAY = 30.0
SESSION_PAUSE = 300.0
MAX_TEXT_CHUNK = 3900


class Bot:
    """WeChat bot powered by the iLink Bot API.

    Args:
        token_dir: Directory for storing login credentials.
            Defaults to ``~/.ai4wechat``.
        auto_format: Automatically apply ``format_for_wechat`` to
            string responses before sending. Defaults to True.

    Example::

        from ai4wechat import Bot

        bot = Bot()

        @bot.on_message
        async def handle(msg):
            return f"Echo: {msg.text}"

        bot.run()
    """

    def __init__(
        self,
        token_dir: Union[str, Path] = DEFAULT_TOKEN_DIR,
        auto_format: bool = True,
    ):
        self.token_dir = Path(token_dir).expanduser()
        self.auto_format = auto_format

        self._message_handler: Optional[Callable] = None
        self._login_handler: Optional[Callable] = None
        self._error_handler: Optional[Callable] = None

        self._client: Optional[ILinkClient] = None
        self._context_tokens: Dict[str, str] = {}
        self._typing_tickets: Dict[str, str] = {}
        self._running = False

    # -- Decorators --

    def on_message(self, func: Callable) -> Callable:
        """Register a message handler.

        The handler receives a :class:`Message` and may return a string
        (which will be sent as a reply) or ``None``.

        Can be sync or async::

            @bot.on_message
            async def handle(msg):
                return "Hello!"
        """
        self._message_handler = func
        return func

    def on_login(self, func: Callable) -> Callable:
        """Register a callback for successful login.

        ::

            @bot.on_login
            def on_ready():
                print("Bot is online!")
        """
        self._login_handler = func
        return func

    def on_error(self, func: Callable) -> Callable:
        """Register an error handler.

        ::

            @bot.on_error
            def handle_err(error, msg=None):
                print(f"Error: {error}")
        """
        self._error_handler = func
        return func

    # -- Public API --

    def run(self, web_login: bool = False, web_port: int = 18891) -> None:
        """Start the bot: login -> poll -> handle -> reply.

        This blocks until the bot is stopped (Ctrl+C).

        Args:
            web_login: Use web-based QR login (for remote servers).
            web_port: Port for the web login page.
        """
        try:
            asyncio.run(self._run_async(web_login, web_port))
        except KeyboardInterrupt:
            log.info("Bot stopped by user")

    async def send(self, to: str, text: str, context_token: str = "") -> None:
        """Send a message to a user proactively.

        Args:
            to: Recipient user ID.
            text: Message text.
            context_token: iLink context token (uses cached value if omitted).
        """
        if not self._client:
            raise RuntimeError("Bot is not running. Call bot.run() first.")

        ctx = context_token or self._context_tokens.get(to, "")
        send_text = format_for_wechat(text) if self.auto_format else text
        chunks = truncate_for_wechat(send_text, MAX_TEXT_CHUNK)

        for i, chunk in enumerate(chunks):
            if i > 0:
                await asyncio.sleep(0.5)
            await self._client.send_message(to, chunk, ctx)

    async def send_typing(self, to: str) -> None:
        """Send a typing indicator to a user."""
        if not self._client:
            return

        ticket = self._typing_tickets.get(to)
        if not ticket:
            ctx = self._context_tokens.get(to, "")
            try:
                config = await self._client.get_config(to, ctx)
                ticket = config.get("typing_ticket", "")
                if ticket:
                    self._typing_tickets[to] = ticket
            except Exception:
                return

        if ticket:
            await self._client.send_typing(to, ticket, 1)

    # -- Internal --

    async def _run_async(self, web_login: bool, web_port: int) -> None:
        account = self._load_account()

        if not account:
            log.info("No credentials found. Starting login...")
            if web_login:
                success = await login_web(self.token_dir, web_port)
            else:
                success = await login(self.token_dir)

            if not success:
                log.error("Login failed. Exiting.")
                return

            account = self._load_account()
            if not account:
                log.error("Login succeeded but credentials not found. Exiting.")
                return

        self._client = ILinkClient(
            token=account["token"],
            base_url=account.get("baseUrl", ""),
        )
        self._running = True

        log.info("Bot is online! Listening for messages...")

        if self._login_handler:
            result = self._login_handler()
            if asyncio.iscoroutine(result):
                await result

        try:
            await self._poll_loop()
        finally:
            self._running = False
            if self._client:
                await self._client.close()
                self._client = None

    async def _poll_loop(self) -> None:
        sync_buf = self._load_sync_buf()
        consecutive_failures = 0
        retry_delay = INITIAL_RETRY_DELAY

        while self._running:
            try:
                result = await self._client.get_updates(sync_buf)

                if result.errcode == SESSION_EXPIRED_ERRCODE or result.ret == SESSION_EXPIRED_ERRCODE:
                    log.error(
                        "Session expired. Please re-login: ai4wechat-login"
                    )
                    await asyncio.sleep(SESSION_PAUSE)
                    continue

                if (result.ret and result.ret != 0) or (
                    result.errcode and result.errcode != 0
                ):
                    consecutive_failures += 1
                    log.warning(
                        f"API error ret={result.ret} errcode={result.errcode} "
                        f"msg={result.errmsg} ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})"
                    )
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        log.warning(f"Too many failures, pausing {SESSION_PAUSE}s")
                        await asyncio.sleep(SESSION_PAUSE)
                        consecutive_failures = 0
                    else:
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                    continue

                consecutive_failures = 0
                retry_delay = INITIAL_RETRY_DELAY

                if result.sync_buf:
                    sync_buf = result.sync_buf
                    self._save_sync_buf(sync_buf)

                for msg in result.messages:
                    if msg.message_type != 1:  # only user messages
                        continue
                    await self._handle_message(msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_failures += 1
                log.error(f"Poll error: {e} ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    await asyncio.sleep(SESSION_PAUSE)
                    consecutive_failures = 0
                else:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

    async def _handle_message(self, raw_msg: ILinkMessage) -> None:
        from_user = raw_msg.from_user_id
        text = raw_msg.extract_text()

        if raw_msg.context_token:
            self._context_tokens[from_user] = raw_msg.context_token

        try:
            config = await self._client.get_config(from_user, raw_msg.context_token)
            ticket = config.get("typing_ticket", "")
            if ticket:
                self._typing_tickets[from_user] = ticket
        except Exception:
            pass

        msg = Message(
            id=str(raw_msg.message_id),
            text=text,
            sender=from_user,
            receiver=raw_msg.to_user_id,
            type=_classify_items(raw_msg.items),
            is_group=False,
            timestamp=datetime.fromtimestamp(
                raw_msg.create_time_ms / 1000, tz=timezone.utc
            )
            if raw_msg.create_time_ms
            else datetime.now(timezone.utc),
            session_id=raw_msg.session_id,
            raw={
                "context_token": raw_msg.context_token,
                "session_id": raw_msg.session_id,
                "items": raw_msg.items,
            },
        )

        log.info(f"Message from {from_user}: {text[:80]}")

        if not self._message_handler:
            return

        try:
            await self.send_typing(from_user)

            result = self._message_handler(msg)
            if asyncio.iscoroutine(result):
                result = await result

            if result is not None:
                reply = str(result)
                ctx = self._context_tokens.get(from_user, raw_msg.context_token)
                send_text = format_for_wechat(reply) if self.auto_format else reply
                chunks = truncate_for_wechat(send_text, MAX_TEXT_CHUNK)

                for i, chunk in enumerate(chunks):
                    if i > 0:
                        await asyncio.sleep(0.5)
                    await self._client.send_message(from_user, chunk, ctx)

                log.info(f"Replied {len(chunks)} chunk(s) to {from_user}")

            await self._stop_typing(from_user)

        except Exception as e:
            log.error(f"Handler error: {e}")
            await self._stop_typing(from_user)
            if self._error_handler:
                try:
                    err_result = self._error_handler(e, msg)
                    if asyncio.iscoroutine(err_result):
                        await err_result
                except Exception:
                    pass

    async def _stop_typing(self, user_id: str) -> None:
        """Cancel typing indicator after sending reply."""
        ticket = self._typing_tickets.get(user_id)
        if ticket and self._client:
            await self._client.send_typing(user_id, ticket, 2)

    # -- Persistence --

    def _load_account(self) -> Optional[Dict[str, Any]]:
        account_file = self.token_dir / "account.json"
        if not account_file.exists():
            return None
        try:
            data = json.loads(account_file.read_text())
            if data.get("token"):
                return data
        except Exception as e:
            log.error(f"Failed to load account: {e}")
        return None

    def _load_sync_buf(self) -> str:
        buf_file = self.token_dir / "sync_buf.txt"
        try:
            if buf_file.exists():
                return buf_file.read_text().strip()
        except Exception:
            pass
        return ""

    def _save_sync_buf(self, buf: str) -> None:
        buf_file = self.token_dir / "sync_buf.txt"
        try:
            buf_file.parent.mkdir(parents=True, exist_ok=True)
            buf_file.write_text(buf)
        except Exception as e:
            log.warning(f"Failed to save sync buf: {e}")
