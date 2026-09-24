from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+", flags=re.UNICODE)
_EDGE = re.compile(r"^[^\w]+|[^\w-]+$", flags=re.UNICODE)


def clean_markdown_bytes(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    return _WS.sub(" ", text).strip()


def tokens_from_markdown_bytes(raw: bytes) -> list[str]:
    text = clean_markdown_bytes(raw)
    return text.split() if text else []


def normalize_surface(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return _EDGE.sub("", text)
