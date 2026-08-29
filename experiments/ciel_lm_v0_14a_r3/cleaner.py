from __future__ import annotations

import re

_WS = re.compile(r"\s+", flags=re.UNICODE)


def clean_markdown_bytes(raw: bytes) -> str:
    """Decode deterministically, collapse Unicode whitespace, and strip."""
    text = raw.decode("utf-8", errors="replace")
    return _WS.sub(" ", text).strip()


def tokens_from_markdown_bytes(raw: bytes) -> list[str]:
    cleaned = clean_markdown_bytes(raw)
    return cleaned.split() if cleaned else []
