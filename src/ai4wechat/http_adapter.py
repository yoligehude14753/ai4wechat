"""
HTTP/Webhook bridge — forward WeChat messages to an existing AI service.

This is the primary integration path for ai4wechat. It lets any AI product
that exposes an HTTP endpoint become usable inside WeChat, without modifying
the AI service itself.

Usage (CLI):
    ai4wechat-serve --target-url http://localhost:8000/chat

Usage (Python):
    from ai4wechat import serve
    serve("http://localhost:8000/chat")
"""

import logging
from pathlib import Path
from typing import Optional, Union

import httpx

from .bot import Bot
from .formatter import format_for_wechat
from .login import DEFAULT_TOKEN_DIR
from .types import Message

log = logging.getLogger("ai4wechat")

DEFAULT_TIMEOUT = 120.0
MAX_TEXT_CHUNK = 3900


async def _forward_to_service(
    target_url: str,
    msg: Message,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """POST a WeChat message to the target AI service, return its reply text."""
    payload = {
        "message_id": msg.id,
        "conversation_id": msg.sender,
        "user_id": msg.sender,
        "text": msg.text,
        "type": msg.type.value,
        "timestamp": msg.timestamp.isoformat(),
        "session_id": msg.session_id,
        "raw": msg.raw,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(target_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    reply = data.get("text") or data.get("reply") or data.get("message")
    if reply and isinstance(reply, str):
        return reply
    return None


def serve(
    target_url: str,
    *,
    token_dir: Union[str, Path] = DEFAULT_TOKEN_DIR,
    auto_format: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
    web_login: bool = False,
    web_port: int = 18891,
) -> None:
    """Start the WeChat bridge: forward all messages to target_url.

    This is the main entry point for making an existing AI service
    usable inside WeChat.

    Args:
        target_url: HTTP endpoint of your existing AI service.
            ai4wechat will POST each WeChat message to this URL
            and send the response back to the user in WeChat.
        token_dir: Directory for storing WeChat login credentials.
        auto_format: Convert Markdown in responses to WeChat-friendly text.
        timeout: HTTP request timeout in seconds for the target service.
        web_login: Use web-based QR login (for remote servers).
        web_port: Port for the web login page.
    """
    bot = Bot(token_dir=token_dir, auto_format=False)

    @bot.on_message
    async def handle(msg: Message) -> Optional[str]:
        try:
            log.info(f"Forwarding to {target_url}: {msg.text[:80]}")
            reply = await _forward_to_service(target_url, msg, timeout)

            if reply:
                if auto_format:
                    reply = format_for_wechat(reply)
                return reply

            log.warning("Target service returned no text")
            return None

        except httpx.HTTPStatusError as e:
            log.error(f"Target service returned {e.response.status_code}: {e.response.text[:200]}")
            return None
        except httpx.ConnectError:
            log.error(f"Cannot reach target service at {target_url}")
            return None
        except Exception as e:
            log.error(f"Bridge error: {e}")
            return None

    @bot.on_login
    def on_ready():
        log.info(f"Bridge active: WeChat <-> {target_url}")

    bot.run(web_login=web_login, web_port=web_port)


def main():
    """CLI entry point for ai4wechat-serve."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ai4wechat] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="ai4wechat — Make your AI product usable inside WeChat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai4wechat-serve --target-url http://localhost:8000/chat
  ai4wechat-serve --target-url https://my-ai-service.com/api/chat --web
  ai4wechat-serve --target-url http://localhost:3000/v1/chat --timeout 60
        """,
    )
    parser.add_argument(
        "--target-url",
        required=True,
        help="HTTP endpoint of your AI service",
    )
    parser.add_argument(
        "--token-dir",
        type=Path,
        default=DEFAULT_TOKEN_DIR,
        help=f"Credentials directory (default: {DEFAULT_TOKEN_DIR})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Disable Markdown-to-WeChat text conversion",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Use web-based QR login (for remote servers)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=18891,
        help="Web login port (default: 18891)",
    )
    args = parser.parse_args()

    serve(
        target_url=args.target_url,
        token_dir=args.token_dir,
        auto_format=not args.no_format,
        timeout=args.timeout,
        web_login=args.web,
        web_port=args.port,
    )


if __name__ == "__main__":
    main()
