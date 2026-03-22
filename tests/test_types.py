"""Tests for types module."""

from ai4wechat.types import Message, MessageType, _classify_items


class TestClassifyItems:
    def test_text(self):
        assert _classify_items([{"type": 1}]) == MessageType.TEXT

    def test_image(self):
        assert _classify_items([{"type": 2}]) == MessageType.IMAGE

    def test_voice(self):
        assert _classify_items([{"type": 3}]) == MessageType.VOICE

    def test_file(self):
        assert _classify_items([{"type": 4}]) == MessageType.FILE

    def test_video(self):
        assert _classify_items([{"type": 5}]) == MessageType.VIDEO

    def test_empty(self):
        assert _classify_items([]) == MessageType.TEXT


class TestMessage:
    def test_creation(self):
        msg = Message(id="1", text="hello", sender="u1", receiver="u2")
        assert msg.text == "hello"
        assert msg.type == MessageType.TEXT
        assert msg.is_group is False
