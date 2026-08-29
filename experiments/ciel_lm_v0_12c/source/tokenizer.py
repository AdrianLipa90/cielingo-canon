from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

SPECIAL = ("<pad>", "<unk>")

@dataclass
class WordTokenizer:
    stoi: dict[str, int]
    itos: list[str]

    @classmethod
    def build(cls, text: str, *, min_freq: int = 1, max_vocab: int = 8000) -> "WordTokenizer":
        counts = Counter(text.split())
        ordered = sorted((w, c) for w, c in counts.items() if c >= min_freq)
        ordered.sort(key=lambda x: (-x[1], x[0]))
        words = list(SPECIAL) + [w for w, _ in ordered[: max(0, max_vocab - len(SPECIAL))]]
        return cls({w: i for i, w in enumerate(words)}, words)

    def encode(self, text: str) -> list[int]:
        unk = self.stoi["<unk>"]
        return [self.stoi.get(tok, unk) for tok in text.split()]

    def encode_tokens(self, tokens: list[str]) -> list[int]:
        unk = self.stoi["<unk>"]
        return [self.stoi.get(tok, unk) for tok in tokens]

    def decode(self, ids: list[int]) -> str:
        return " ".join(self.itos[i] if 0 <= i < len(self.itos) else "<unk>" for i in ids)

    def tokens(self, ids: list[int]) -> list[str]:
        return [self.itos[i] if 0 <= i < len(self.itos) else "<unk>" for i in ids]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({"itos": self.itos}, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "WordTokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        itos = list(data["itos"])
        return cls({w: i for i, w in enumerate(itos)}, itos)

    @property
    def vocab_size(self) -> int:
        return len(self.itos)
