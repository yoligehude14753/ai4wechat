"""Minimal HTTP service that handles text, image, voice, and file inputs.

Run:
    python examples/http_media_echo.py

Then bridge WeChat to it:
    ai4wechat-serve --target-url http://localhost:8000/chat

What it demonstrates:
    - plain text handling
    - voice handling via media[0].text
    - image detection
    - file name extraction
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")

        text = payload.get("text", "")
        media = payload.get("media", [])

        reply = "I didn't understand the message."

        if media:
            first = media[0]
            media_type = first.get("type")

            if media_type == "voice":
                transcribed = first.get("text") or "(no transcription)"
                reply = f"I received a voice message: {transcribed}"
            elif media_type == "image":
                reply = "I received an image."
            elif media_type == "file":
                file_name = first.get("file_name") or "unknown file"
                reply = f"I received a file: {file_name}"
            elif media_type == "video":
                reply = "I received a video."
        elif text:
            reply = f"You said: {text}"

        response = json.dumps({"text": reply}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, fmt, *args):
        # Keep the example quiet.
        return


def main():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Listening on http://localhost:8000/chat")
    server.serve_forever()


if __name__ == "__main__":
    main()
