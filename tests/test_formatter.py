"""Tests for the WeChat formatter."""

from ai4wechat.formatter import format_for_wechat, truncate_for_wechat


class TestFormatForWechat:
    def test_empty(self):
        assert format_for_wechat("") == ""

    def test_headings(self):
        assert "【Hello】" in format_for_wechat("## Hello")
        assert "【Deep】" in format_for_wechat("### Deep")

    def test_bold(self):
        assert format_for_wechat("**bold**") == "bold"
        assert format_for_wechat("__bold__") == "bold"

    def test_italic(self):
        assert format_for_wechat("*italic*") == "italic"

    def test_inline_code(self):
        assert format_for_wechat("`code`") == "code"

    def test_code_block(self):
        result = format_for_wechat("```python\nprint('hi')\n```")
        assert "---- python ----" in result
        assert "print('hi')" in result

    def test_links(self):
        result = format_for_wechat("[click](https://example.com)")
        assert "click (https://example.com)" in result

    def test_images(self):
        result = format_for_wechat("![alt](https://img.com/a.png)")
        assert "[Image: alt]" in result

    def test_unordered_list(self):
        result = format_for_wechat("- item1\n- item2")
        assert "· item1" in result

    def test_ordered_list(self):
        result = format_for_wechat("1. first\n2. second")
        assert "1) first" in result

    def test_table(self):
        table = "| Name | Age |\n|---|---|\n| Alice | 30 |"
        result = format_for_wechat(table)
        assert "Name: Alice" in result

    def test_html_stripped(self):
        assert format_for_wechat("<b>bold</b>") == "bold"

    def test_excess_newlines(self):
        result = format_for_wechat("a\n\n\n\n\nb")
        assert result == "a\n\nb"


class TestTruncateForWechat:
    def test_short_text(self):
        result = truncate_for_wechat("short text")
        assert result == ["short text"]

    def test_long_text_splits(self):
        text = "Hello world. " * 500
        chunks = truncate_for_wechat(text, max_bytes=200)
        assert len(chunks) > 1
        assert all("/" in c[:10] for c in chunks)  # page numbers

    def test_respects_max_bytes(self):
        text = "A" * 10000
        chunks = truncate_for_wechat(text, max_bytes=500)
        for chunk in chunks:
            assert len(chunk.encode("utf-8")) <= 600  # allow page number overhead
