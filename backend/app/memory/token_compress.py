"""Compress text before LLM / vector ingest (TokenJuice-style). DEV-SPEC M01."""
from __future__ import annotations

import re
from html.parser import HTMLParser

_WS_RE = re.compile(r"\n{3,}")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\u200b-\u200f\ufeff]")
_URL_TRACKING_RE = re.compile(
    r"([?&])(utm_[^=&]+|fbclid|gclid|mc_eid)=[^&\s]+",
    re.IGNORECASE,
)


class _HTMLToText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._parts.append(data)

    def text(self) -> str:
        return " ".join(self._parts)


def compress_html(html: str) -> str:
    parser = _HTMLToText()
    try:
        parser.feed(html)
        text = parser.text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html)
    return compress_for_llm(text, max_chars=12_000)


def _strip_tracking_urls(text: str) -> str:
    return _URL_TRACKING_RE.sub(r"\1", text)


def compress_for_llm(text: str, *, max_chars: int = 12_000) -> str:
    if not text:
        return ""
    t = _CTRL_RE.sub("", text)
    t = _strip_tracking_urls(t)
    t = _WS_RE.sub("\n\n", t).strip()
    if len(t) <= max_chars:
        return t
    head_len = int(max_chars * 0.6)
    tail_len = int(max_chars * 0.2)
    omitted = len(t) - head_len - tail_len
    return (
        t[:head_len]
        + f"\n…[truncated {omitted} chars]…\n"
        + t[-tail_len:]
    )
