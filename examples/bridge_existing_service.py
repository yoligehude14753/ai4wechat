"""
Bridge an existing AI service to WeChat.

This is the primary use case: you already have an AI service running
at an HTTP endpoint, and you want users to use it inside WeChat.

Usage:
    python bridge_existing_service.py

Make sure your AI service is running and accepts POST requests.
"""

from ai4wechat import serve

# Point this at your existing AI service.
# It should accept POST with JSON {"text": "..."} and return {"text": "..."}.
TARGET_URL = "http://localhost:8000/chat"

serve(TARGET_URL)
