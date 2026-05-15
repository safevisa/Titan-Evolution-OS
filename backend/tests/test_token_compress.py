"""M01: token_compress unit tests."""
from app.memory.token_compress import compress_for_llm, compress_html


def test_compress_for_llm_truncates_long_text() -> None:
    text = "x" * 20_000
    out = compress_for_llm(text, max_chars=1000)
    assert len(out) <= 1100
    assert "truncated" in out


def test_compress_html_strips_tags() -> None:
    html = "<p>Hello <b>world</b></p>"
    out = compress_html(html)
    assert "Hello" in out
    assert "<" not in out
