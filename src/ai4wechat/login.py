"""
WeChat QR code login — supports both local terminal and remote server (web mode).

Usage:
  # Terminal mode (scan QR in terminal)
  ai4wechat-login

  # Web mode (remote server — opens a web page for scanning)
  ai4wechat-login --web --port 18891

  # Custom token directory
  ai4wechat-login --token-dir /path/to/dir
"""

import asyncio
import json
import sys
import urllib.parse
from pathlib import Path
from typing import Optional

from .client import ILinkClient

DEFAULT_TOKEN_DIR = Path.home() / ".ai4wechat"
MAX_QR_REFRESH = 3
LOGIN_TIMEOUT = 300


def _print_qrcode_ascii(url: str) -> None:
    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(out=sys.stderr, invert=True)
    except ImportError:
        sys.stderr.write(
            f"\nScan this URL with WeChat:\n{url}\n"
            "(pip install 'ai4wechat[qrcode]' to display QR in terminal)\n\n"
        )


async def login(token_dir: Path = DEFAULT_TOKEN_DIR) -> bool:
    """Terminal QR login flow. Returns True on success."""
    client = ILinkClient()

    for attempt in range(MAX_QR_REFRESH):
        qr = await client.get_qrcode()
        if not qr.qrcode_img_content:
            sys.stderr.write("Failed to get QR code\n")
            return False

        sys.stderr.write("\n")
        _print_qrcode_ascii(qr.qrcode_img_content)
        sys.stderr.write("\nScan the QR code above with WeChat to log in\n\n")

        result = await _poll_until_confirmed(client, qr.qrcode)
        if result:
            _save_account(result, token_dir)
            await client.close()
            return True

        sys.stderr.write("QR code expired, refreshing...\n")

    sys.stderr.write(f"QR code refreshed {MAX_QR_REFRESH} times without login\n")
    await client.close()
    return False


async def login_web(token_dir: Path = DEFAULT_TOKEN_DIR, port: int = 18891) -> bool:
    """Web-based QR login — for remote servers (GCP, AWS, etc.).

    Starts a temporary HTTP server at the given port.
    Open http://YOUR_SERVER_IP:{port} in a browser to scan.
    """
    from aiohttp import web

    client = ILinkClient()
    state = {"status": "init", "qr_url": "", "qrcode": "", "done": False, "result": None}

    async def _refresh_qr():
        qr = await client.get_qrcode()
        state["qr_url"] = qr.qrcode_img_content
        state["qrcode"] = qr.qrcode
        state["status"] = "wait"

    await _refresh_qr()

    async def handle_index(request):
        return web.Response(text=_build_login_html(state["qr_url"]), content_type="text/html")

    async def handle_status(request):
        return web.json_response({"status": state["status"]})

    async def handle_qr(request):
        return web.json_response({"url": state["qr_url"]})

    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/qr", handle_qr)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    sys.stderr.write(f"\nLogin page started: http://0.0.0.0:{port}\n")
    sys.stderr.write(f"Open http://YOUR_SERVER_IP:{port} in your browser to scan\n\n")

    try:
        for attempt in range(MAX_QR_REFRESH):
            deadline = asyncio.get_event_loop().time() + LOGIN_TIMEOUT

            while asyncio.get_event_loop().time() < deadline:
                status_result = await client.poll_qr_status(state["qrcode"])

                if status_result.status == "scaned":
                    state["status"] = "scaned"
                elif status_result.status == "expired":
                    state["status"] = "expired"
                    break
                elif status_result.status == "confirmed":
                    if status_result.bot_token:
                        state["status"] = "success"
                        _save_account(
                            {
                                "token": status_result.bot_token,
                                "botId": status_result.bot_id,
                                "baseUrl": status_result.base_url,
                                "userId": status_result.user_id,
                            },
                            token_dir,
                        )
                        await asyncio.sleep(2)
                        return True

                await asyncio.sleep(1)

            if state["status"] == "expired":
                await _refresh_qr()

        sys.stderr.write("Login timed out\n")
        return False

    finally:
        await runner.cleanup()
        await client.close()


async def _poll_until_confirmed(client: ILinkClient, qrcode: str) -> Optional[dict]:
    deadline = asyncio.get_event_loop().time() + LOGIN_TIMEOUT
    scanned_notified = False

    while asyncio.get_event_loop().time() < deadline:
        status = await client.poll_qr_status(qrcode)

        if status.status == "scaned" and not scanned_notified:
            sys.stderr.write("Scanned! Please confirm on your phone...\n")
            scanned_notified = True
        elif status.status == "expired":
            return None
        elif status.status == "confirmed":
            if not status.bot_token:
                sys.stderr.write("Login confirmed but missing token\n")
                return None
            return {
                "token": status.bot_token,
                "botId": status.bot_id,
                "baseUrl": status.base_url,
                "userId": status.user_id,
            }
        await asyncio.sleep(1)

    return None


def _save_account(data: dict, token_dir: Path) -> None:
    token_dir.mkdir(parents=True, exist_ok=True)
    account_file = token_dir / "account.json"
    data["savedAt"] = __import__("datetime").datetime.now().isoformat()
    account_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    sys.stderr.write(f"\nLogin successful! BotID={data.get('botId', '?')}\n")
    sys.stderr.write(f"Credentials saved to {account_file}\n")
    sys.stderr.write("You can now start your bot.\n\n")


def _build_login_html(qr_url: str) -> str:
    qr_img = (
        f"https://api.qrserver.com/v1/create-qr-code/?size=280x280"
        f"&data={urllib.parse.quote(qr_url)}"
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ai4wechat Login</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#1a1a2e;color:#e0e0e0;
display:flex;justify-content:center;align-items:center;min-height:100vh}}
.c{{text-align:center;padding:2rem}}
h1{{font-size:1.8rem;margin-bottom:.5rem;color:#fff}}
.sub{{color:#888;margin-bottom:2rem}}
.qr{{background:#fff;border-radius:16px;padding:20px;display:inline-block;margin-bottom:1.5rem}}
.qr img{{width:280px;height:280px;display:block}}
.st{{font-size:1.1rem;min-height:2rem}}
.st.scaned{{color:#f0a030}}.st.success{{color:#4caf50}}
</style></head><body>
<div class="c">
<h1>ai4wechat</h1>
<p class="sub">Scan with WeChat to connect your bot</p>
<div class="qr" id="qw"><img id="qi" src="{qr_img}"></div>
<div class="st" id="s">Waiting for scan...</div>
</div>
<script>
setInterval(async()=>{{
try{{const r=await fetch('/status');const d=await r.json();const s=document.getElementById('s');
s.className='st '+d.status;
if(d.status==='scaned')s.textContent='Scanned! Please confirm on your phone...';
else if(d.status==='success'){{s.textContent='Login successful! You can close this page.';
document.getElementById('qw').style.display='none'}}
else if(d.status==='expired'){{s.textContent='QR expired, refreshing...';
const q=await(await fetch('/qr')).json();
document.getElementById('qi').src='https://api.qrserver.com/v1/create-qr-code/?size=280x280&data='+encodeURIComponent(q.url);
s.textContent='Waiting for scan...'}}
}}catch{{}}
}},2000);
</script></body></html>"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ai4wechat QR code login")
    parser.add_argument(
        "--token-dir",
        type=Path,
        default=DEFAULT_TOKEN_DIR,
        help=f"Credentials directory (default: {DEFAULT_TOKEN_DIR})",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start a web page for QR scanning (for remote servers)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=18891,
        help="Web mode port (default: 18891)",
    )
    args = parser.parse_args()

    if args.web:
        success = asyncio.run(login_web(args.token_dir, args.port))
    else:
        success = asyncio.run(login(args.token_dir))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
