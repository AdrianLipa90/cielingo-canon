from __future__ import annotations
import hashlib, json, math, struct, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

_JSON_PATH = Path("/tmp/noema_surface_workspace/NOEMA_LOCAL_ROOT/head/NoemaSurface/runtime/phase_memory/state/PHASE_MEMORY_STORE.json")

ORBIT_DIMS = ["mass", "sin", "cos", "align", "tension", "j_bus", "visc", "afford", "word_int", "file_int", "tele_ctrl"]

@dataclass
class MemoryEntry:
    timestamp: float
    turn_id: str
    session_id: str
    prompt_hash: str
    response_hash: str
    orbit_vector: list[float]
    prompt_phase: float
    response_phase: float
    chain_hash: str
    tags: list[str] = field(default_factory=list)

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def prompt_to_phase(prompt: str) -> float:
    h = hashlib.sha256(prompt.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") / 2**32

def prompt_to_orbit(prompt: str) -> list[float]:
    h = hashlib.sha256(prompt.encode("utf-8")).digest()
    return [(int.from_bytes(h[i:i+2], "big") % 1000) / 1000.0 for i in range(0, 22, 2)]

def phase_distance(a: float, b: float) -> float:
    d = abs(a - b)
    return min(d, 1.0 - d)

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_np = np.array(a, dtype=np.float64)
    b_np = np.array(b, dtype=np.float64)
    na = np.linalg.norm(a_np)
    nb = np.linalg.norm(b_np)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a_np, b_np) / (na * nb))

class MemoryStore:
    def __init__(self, path: Path | None = None):
        self.path = path or _JSON_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: list[dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text("utf-8"))
            except Exception:
                self._data = []
        else:
            self._data = []

    def _save(self):
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), "utf-8")

    def store(self, entry: MemoryEntry) -> str:
        key = entry.prompt_hash[:16]
        self._data.append({
            "timestamp": entry.timestamp,
            "turn_id": entry.turn_id,
            "session_id": entry.session_id,
            "prompt_hash": entry.prompt_hash,
            "response_hash": entry.response_hash,
            "orbit_vector": entry.orbit_vector,
            "prompt_phase": entry.prompt_phase,
            "response_phase": entry.response_phase,
            "chain_hash": entry.chain_hash,
            "tags": entry.tags,
        })
        self._save()
        return key

    def recall(self, prompt: str, top_k: int = 3, min_score: float = 0.7) -> list[dict[str, Any]]:
        if not self._data:
            return []
        prompt_phase = prompt_to_phase(prompt)
        prompt_orbit = prompt_to_orbit(prompt)
        scored: list[tuple[float, dict]] = []
        for entry in self._data:
            stored_phase = entry.get("prompt_phase", 0.0)
            stored_orbit = entry.get("orbit_vector", prompt_orbit)
            cs = cosine_similarity(prompt_orbit, stored_orbit)
            pd = phase_distance(prompt_phase, stored_phase)
            score = cs * (1.0 - pd * 0.3)
            scored.append((score, entry))
        scored.sort(key=lambda x: -x[0])
        return [s[1] for s in scored[:top_k] if s[0] >= min_score]

    def recall_by_text(self, text: str, top_k: int = 3, min_score: float = 0.7) -> list[dict[str, Any]]:
        return self.recall(text, top_k, min_score)

    def count(self) -> int:
        return len(self._data)

    def all(self) -> list[dict[str, Any]]:
        return list(self._data)

    def clear(self):
        self._data = []
        self._save()
