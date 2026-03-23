"""Tests for types module."""

from ai4wechat.types import Message, MessageType, _classify_items, _extract_media_items


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
        assert msg.media == []
        assert msg.is_group is False


class TestExtractMediaItems:
    def test_extract_image(self):
        media = _extract_media_items([{"type": 2, "image_item": {"foo": "bar"}}])
        assert media == [{"type": "image", "raw": {"foo": "bar"}}]

    def test_extract_voice(self):
        media = _extract_media_items([{"type": 3, "voice_item": {"text": "hello"}}])
        assert media == [{"type": "voice", "text": "hello", "raw": {"text": "hello"}}]

    def test_extract_file(self):
        media = _extract_media_items(
            [{"type": 4, "file_item": {"file_name": "report.pdf"}}]
        )
        assert media == [
            {"type": "file", "file_name": "report.pdf", "raw": {"file_name": "report.pdf"}}
        ]

    def test_extract_video(self):
        media = _extract_media_items([{"type": 5, "video_item": {"duration": 10}}])
        assert media == [{"type": "video", "raw": {"duration": 10}}]

    def test_extract_multiple_media(self):
        media = _extract_media_items(
            [
                {"type": 2, "image_item": {"id": "img"}},
                {"type": 3, "voice_item": {"text": "voice text"}},
            ]
        )
        assert media == [
            {"type": "image", "raw": {"id": "img"}},
            {"type": "voice", "text": "voice text", "raw": {"text": "voice text"}},
        ]
