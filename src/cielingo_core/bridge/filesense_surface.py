"""FileSense surface for CIELingo GLOBAL v0.4.

FileSense is treated as a fast search/execution surface:
- local file scanning,
- grep-like retrieval,
- JSONL card loading,
- no SOURCE promotion,
- no NOEMA CURRENT update,
- no memory writeback.

This module is intentionally dependency-free. It can use Python fallback
search everywhere; shell grep/rg can be added later behind the same ABI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import re


@dataclass
class FileSenseHit:
    path: str
    line_no: int
    text: str
    score: float
    hit_type: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FileSenseReport:
    query: str
    root: str
    hits: list[FileSenseHit]
    backend: str = "python-fallback"
    noema_writeback_performed: bool = False
    current_update_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FileSenseSurface:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def iter_text_files(self, globs: list[str] | None = None):
        globs = globs or ["*.jsonl", "*.json", "*.md", "*.txt", "*.py"]
        seen: set[Path] = set()
        for pattern in globs:
            for path in self.root.rglob(pattern):
                if path.is_file() and path not in seen:
                    seen.add(path)
                    yield path

    @staticmethod
    def score_line(query_terms: list[str], line: str) -> float:
        lower = line.lower()
        if not query_terms:
            return 0.0
        hits = sum(1 for term in query_terms if term and term in lower)
        exact_bonus = 0.25 if " ".join(query_terms) in lower else 0.0
        return min(1.0, hits / len(query_terms) + exact_bonus)

    def search(self, query: str, *, max_hits: int = 50, globs: list[str] | None = None) -> FileSenseReport:
        terms = [t.lower() for t in re.findall(r"\w+|[\u3040-\u30ff\u3400-\u9fff]+", query, re.UNICODE)]
        hits: list[FileSenseHit] = []
        for path in self.iter_text_files(globs):
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines, start=1):
                score = self.score_line(terms, line)
                if score > 0:
                    hits.append(FileSenseHit(
                        path=str(path.relative_to(self.root)),
                        line_no=idx,
                        text=line[:1000],
                        score=score,
                        hit_type="grep_line",
                    ))
        hits.sort(key=lambda h: h.score, reverse=True)
        return FileSenseReport(query=query, root=str(self.root), hits=hits[:max_hits])

    def load_jsonl(self, rel_path: str | Path) -> list[dict[str, Any]]:
        path = self.root / rel_path
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                row = json.loads(stripped)
                row["_filesense"] = {"path": str(rel_path), "line_no": line_no}
                rows.append(row)
        return rows

    def search_cards(self, query: str, rel_path: str = "cards/generated_examples/trilingual_runtime_cards_v0_3b.jsonl") -> list[dict[str, Any]]:
        rows = self.load_jsonl(rel_path)
        q = query.lower()
        terms = [t.lower() for t in re.findall(r"\w+|[\u3040-\u30ff\u3400-\u9fff]+", query, re.UNICODE)]
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            haystack = json.dumps(row, ensure_ascii=False).lower()
            score = 0.0
            if q and q in haystack:
                score += 0.35
            if terms:
                score += sum(1 for t in terms if t in haystack) / len(terms)
            if score > 0:
                row = dict(row)
                row["_filesense_score"] = min(1.0, score)
                scored.append((row["_filesense_score"], row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [row for _, row in scored]
