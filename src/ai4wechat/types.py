"""Core types for ai4wechat."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    FILE = "file"
    VIDEO = "video"


@dataclass
class Message:
    """A WeChat message received by the bot.

    Attributes:
        id: Unique message identifier.
        text: Extracted text content.
        sender: Sender's user ID.
        receiver: Receiver's user ID (usually the bot).
        type: Message type (text, image, voice, file, video).
        media: Structured media metadata extracted from the iLink item list.
        is_group: Whether the message is from a group chat.
        timestamp: When the message was created.
        session_id: iLink session identifier.
        raw: Full raw data from the iLink API.
    """

    id: str
    text: str
    sender: str
    receiver: str
    type: MessageType = MessageType.TEXT
    media: List[Dict[str, Any]] = field(default_factory=list)
    is_group: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


def _classify_items(items: List[Dict[str, Any]]) -> MessageType:
    """Determine message type from iLink item list."""
    for item in items:
        t = item.get("type", 0)
        if t == 2:
            return MessageType.IMAGE
        if t == 3:
            return MessageType.VOICE
        if t == 4:
            return MessageType.FILE
        if t == 5:
            return MessageType.VIDEO
    return MessageType.TEXT


def _extract_media_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract structured media metadata from iLink item list.

    This preserves image/voice/file/video information so downstream
    HTTP services can distinguish media inputs instead of only seeing
    placeholder text like ``[Image]`` or ``[Voice]``.
    """
    media: List[Dict[str, Any]] = []

    for item in items:
        t = item.get("type", 0)

        if t == 2:
            image_item = item.get("image_item", {})
            media.append(
                {
                    "type": MessageType.IMAGE.value,
                    "raw": image_item or item,
                }
            )
        elif t == 3:
            voice_item = item.get("voice_item", {})
            media.append(
                {
                    "type": MessageType.VOICE.value,
                    "text": voice_item.get("text", ""),
                    "raw": voice_item or item,
                }
            )
        elif t == 4:
            file_item = item.get("file_item", {})
            media.append(
                {
                    "type": MessageType.FILE.value,
                    "file_name": file_item.get("file_name", ""),
                    "raw": file_item or item,
                }
            )
        elif t == 5:
            video_item = item.get("video_item", {})
            media.append(
                {
                    "type": MessageType.VIDEO.value,
                    "raw": video_item or item,
                }
            )

    return media
