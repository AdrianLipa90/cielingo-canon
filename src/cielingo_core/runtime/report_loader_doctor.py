from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReportResolution:
    requested: str
    resolved_path: str | None
    found: bool
    strategy: str


class ReportLoaderDoctor:
    """Resolve runtime reports after flat-patch refactors.

    Flat patching should expose key reports at repo-root results/, but older bundles keep
    them under runtime_reports/ or runtime_surfaces/. This Doctor locates the best
    available report without treating a missing root projection as a semantic failure.
    """

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def resolve(self, filename: str) -> ReportResolution:
        candidates = [self.root / "results" / filename]
        candidates += sorted(self.root.glob(f"runtime_reports/**/{filename}"))
        candidates += sorted(self.root.glob(f"runtime_surfaces/**/{filename}"))
        candidates += sorted(self.root.glob(f"noema_surface/**/{filename}"))
        for path in candidates:
            if path.exists():
                strategy = "root_results" if path.parent.name == "results" and path.parent.parent == self.root else "fallback_search"
                return ReportResolution(filename, str(path), True, strategy)
        return ReportResolution(filename, None, False, "missing")

    def load_json(self, filename: str) -> dict[str, Any]:
        resolution = self.resolve(filename)
        if not resolution.found or not resolution.resolved_path:
            raise FileNotFoundError(filename)
        return json.loads(Path(resolution.resolved_path).read_text(encoding="utf-8"))
