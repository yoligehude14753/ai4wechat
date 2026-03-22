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
