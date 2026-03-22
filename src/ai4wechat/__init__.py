"""ai4wechat — Make your AI product usable inside WeChat."""

from .bot import Bot
from .types import Message, MessageType
from .formatter import format_for_wechat, truncate_for_wechat
from .client import ILinkClient
from .http_adapter import serve

__version__ = "0.1.0"
__all__ = [
    "Bot",
    "Message",
    "MessageType",
    "format_for_wechat",
    "truncate_for_wechat",
    "ILinkClient",
    "serve",
]
