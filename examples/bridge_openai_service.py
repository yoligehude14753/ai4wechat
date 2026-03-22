"""
Example: a simple OpenAI-based AI service + ai4wechat bridge.

This simulates the common scenario where you have an existing AI service
(here a simple Flask/FastAPI app wrapping OpenAI) and want to make it
usable inside WeChat without modifying the service itself.

Step 1: Start your AI service (e.g. on port 8000)
Step 2: Run this script to bridge it to WeChat

For this example, we start a minimal AI service and the bridge together.
"""

import asyncio
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

AI_SERVICE_PORT = 18900


class AIServiceHandler(BaseHTTPRequestHandler):
    """Minimal AI service that wraps OpenAI."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        user_text = body.get("text", "")

        try:
            from openai import OpenAI

            client = OpenAI()
            r = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_text}],
            )
            reply = r.choices[0].message.content
        except Exception as e:
            reply = f"AI service error: {e}"

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"text": reply}).encode())

    def log_message(self, format, *args):
        logging.getLogger("ai-service").info(format % args)


def start_ai_service():
    server = HTTPServer(("127.0.0.1", AI_SERVICE_PORT), AIServiceHandler)
    logging.info(f"AI service running at http://127.0.0.1:{AI_SERVICE_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=start_ai_service, daemon=True).start()

    from ai4wechat import serve

    serve(f"http://127.0.0.1:{AI_SERVICE_PORT}")
