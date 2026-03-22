"""
WeChat output formatter — converts Markdown / HTML to WeChat-friendly plain text.

WeChat limitations:
- Does not render Markdown (# ** `` etc.)
- No HTML/SVG support
- Plain text message limit is ~4096 bytes
- Images/videos/files require separate CDN upload
"""

import re
from typing import List, Tuple


def format_for_wechat(text: str) -> str:
    """Convert Markdown/HTML output to WeChat-readable plain text.

    Handles: headings, bold, italic, code blocks, tables,
    links, images, lists, and excess whitespace.
    """
    if not text:
        return text

    result = text

    result = re.sub(r"<[^>]+>", "", result)
    result = re.sub(r"^#{1,6}\s+(.+)$", r"【\1】", result, flags=re.MULTILINE)
    result = re.sub(r"\*\*(.+?)\*\*", r"\1", result)
    result = re.sub(r"__(.+?)__", r"\1", result)
    result = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", result)
    result = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", result)

    def _format_code_block(m: re.Match) -> str:
        lang = m.group(1) or ""
        code = m.group(2).strip()
        header = f"---- {lang} ----" if lang else "----"
        return f"\n{header}\n{code}\n----"

    result = re.sub(r"```(\w*)\n(.*?)```", _format_code_block, result, flags=re.DOTALL)
    result = re.sub(r"`([^`]+)`", r"\1", result)
    result = _convert_tables(result)
    result = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"[Image: \1]", result)
    result = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", result)
    result = re.sub(r"^[\-\*]\s+", "· ", result, flags=re.MULTILINE)
    result = re.sub(r"^(\d+)\.\s+", r"\1) ", result, flags=re.MULTILINE)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


def _convert_tables(text: str) -> str:
    """Convert Markdown tables to plain-text lists."""
    lines = text.split("\n")
    output: List[str] = []
    table_headers: List[str] = []
    in_table = False

    for line in lines:
        stripped = line.strip()

        if "|" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]

            if all(re.match(r"^[-:]+$", c) for c in cells if c):
                in_table = True
                continue

            if not in_table:
                table_headers = cells
                in_table = True
                continue

            pairs = []
            for i, cell in enumerate(cells):
                if i < len(table_headers) and table_headers[i]:
                    pairs.append(f"{table_headers[i]}: {cell}")
                else:
                    pairs.append(cell)
            output.append("· " + " | ".join(pairs))
        else:
            if in_table:
                in_table = False
                table_headers = []
            output.append(line)

    return "\n".join(output)


def extract_file_references(text: str) -> Tuple[str, List[str]]:
    """Extract file path references from text.

    Returns (cleaned_text, list_of_file_paths).
    """
    file_pattern = re.compile(
        r"(?:generated|saved|output|created|download)(?:ed)?(?:\s+file)?[：:]\s*"
        r"[`\"']?(/[\w/\-\.]+\.(?:png|jpg|jpeg|gif|mp4|mp3|wav|pdf|docx|xlsx|pptx|zip|csv|txt|py|js|html))[`\"']?",
        re.IGNORECASE,
    )
    files = file_pattern.findall(text)
    return text, files


def truncate_for_wechat(text: str, max_bytes: int = 3900) -> List[str]:
    """Split long text into chunks that fit within WeChat's message limit.

    Splits at paragraph and sentence boundaries when possible.
    Adds page numbers (1/N) when splitting.
    """
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks: List[str] = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para

        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            if len(para.encode("utf-8")) > max_bytes:
                sentences = re.split(r"(?<=[。！？.!?\n])", para)
                current = ""
                for sent in sentences:
                    cand = current + sent
                    if len(cand.encode("utf-8")) <= max_bytes:
                        current = cand
                    else:
                        if current:
                            chunks.append(current.strip())
                        while len(sent.encode("utf-8")) > max_bytes:
                            cut = max_bytes // 4
                            chunks.append(sent[:cut].strip())
                            sent = sent[cut:]
                        current = sent
            else:
                current = para

    if current.strip():
        chunks.append(current.strip())

    if len(chunks) > 1:
        chunks = [f"({i + 1}/{len(chunks)})\n{chunk}" for i, chunk in enumerate(chunks)]

    return chunks
