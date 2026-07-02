"""Local NOEMA Surface command-prompt layer.

This is a local execution surface. It is not NOEMA SoT, not packet ACK,
not memory writeback, and not CURRENT update.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import ast
import subprocess
import sys
import os
from typing import Any


@dataclass
class NoemaSurfaceResult:
    command: str
    ok: bool
    payload: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NoemaSurface:
    """Local command-prompt-like surface over a repository root."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def path(self, relative_path: str | Path) -> Path:
        target = (self.root / relative_path).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError(f"path escapes NOEMA surface root: {relative_path}")
        return target

    def ls(self, relative_path: str | Path = ".", *, recursive: bool = False, pattern: str | None = None) -> NoemaSurfaceResult:
        path = self.path(relative_path)
        if not path.exists():
            return NoemaSurfaceResult("ls", False, issues=[f"missing: {relative_path}"])
        if not path.is_dir():
            return NoemaSurfaceResult("ls", False, issues=[f"not a directory: {relative_path}"])

        iterator = path.rglob(pattern or "*") if recursive else path.glob(pattern or "*")
        entries = []
        for item in sorted(iterator):
            entries.append({
                "path": str(item.relative_to(self.root)),
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return NoemaSurfaceResult(
            "ls",
            True,
            payload={"root": str(relative_path), "recursive": recursive, "pattern": pattern, "entries": entries},
        )

    def read_text(self, relative_path: str | Path) -> NoemaSurfaceResult:
        path = self.path(relative_path)
        if not path.exists():
            return NoemaSurfaceResult("read_text", False, issues=[f"missing: {relative_path}"])
        return NoemaSurfaceResult("read_text", True, payload={"text": path.read_text(encoding="utf-8")})

    def write_text(self, relative_path: str | Path, text: str) -> NoemaSurfaceResult:
        path = self.path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return NoemaSurfaceResult("write_text", True, payload={"path": str(relative_path), "bytes": len(text.encode("utf-8"))})

    def ast_imports(self, relative_path: str | Path) -> NoemaSurfaceResult:
        result = self.read_text(relative_path)
        if not result.ok:
            return result
        tree = ast.parse(result.payload["text"])
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
        return NoemaSurfaceResult("ast_imports", True, payload={"imports": imports})

    def assert_router_boundary(self, relative_path: str | Path) -> NoemaSurfaceResult:
        result = self.ast_imports(relative_path)
        if not result.ok:
            return result
        imports = result.payload["imports"]
        issues: list[str] = []
        required = {
            "cielingo_core.language_spaces.pl.sentence_equation",
            "cielingo_core.language_spaces.en.sentence_equation",
            "cielingo_core.language_spaces.ja.sentence_equation",
        }
        missing = sorted(required - set(imports))
        if missing:
            issues.append(f"router missing endpoint imports: {missing}")
        for imp in imports:
            if imp.endswith(".solver") or imp.endswith(".grammar") or imp.endswith(".j_holonomy"):
                issues.append(f"router imports forbidden regional internals: {imp}")
        return NoemaSurfaceResult("assert_router_boundary", not issues, payload={"imports": imports}, issues=issues)

    def run_pytest(self, timeout_s: int = 60) -> NoemaSurfaceResult:
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return NoemaSurfaceResult(
            "run_pytest",
            proc.returncode == 0,
            payload={"return_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
        )
