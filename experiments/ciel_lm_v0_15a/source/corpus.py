from __future__ import annotations
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[2]

def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)

def _clean(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#*_`|=<>\\]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def build_reference_corpus(limit_chars: int = 450_000) -> str:
    """Build prose-oriented multilingual corpus from CIELingo corpora/docs."""
    parts: list[str] = []
    for p in sorted((ROOT / "vendor" / "cielingo" / "corpus").glob("*.json")):
        try:
            data=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        vals=[_clean(s) for s in _strings(data) if len(s.strip())>1]
        parts.extend(v for v in vals if v)
    for dr in [ROOT/"vendor"/"cielingo"/"docs", ROOT/"vendor"/"lingophysics"/"docs"]:
        if not dr.exists():
            continue
        for p in sorted(dr.rglob("*.md")):
            text=_clean(p.read_text(encoding="utf-8",errors="ignore"))
            if text:
                parts.append(text)
    return "\n".join(parts)[:limit_chars]
