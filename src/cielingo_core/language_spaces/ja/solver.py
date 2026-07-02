from __future__ import annotations
from pathlib import Path
from cielingo_core.global_layer.contracts import SurfaceSolution
from cielingo_core.regional.base import RegionalSolveResult, SurfaceSegments
from cielingo_core.regional.simple_solver_utils import build_local_j, build_projection, load_atlas_cards, match_cards_to_tokens, simple_space_segment, japanese_segment_known_forms

class JapaneseRegionalSolver:
    language_id = "ja"

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.cards = load_atlas_cards(self.repo_root, self.language_id)

    def segment(self, text: str) -> SurfaceSegments:
        tokens = japanese_segment_known_forms(text, self.cards)
        return SurfaceSegments(language_id=self.language_id, text=text, tokens=tokens, notes=["Minimal ja solver; no full regional grammar."])

    def solve(self, text: str) -> RegionalSolveResult:
        segments = self.segment(text)
        candidates = match_cards_to_tokens(self.cards, segments.tokens, self.language_id)
        low = [t.lower() for t in segments.tokens]
        slot_projection = build_projection(candidates)
        local_j = build_local_j(0.55, 0.65, 0.45 if ("ない" in segments.tokens or "ではない" in segments.tokens) else 0.25, 0.40 if len(candidates) < len(segments.tokens) else 0.10)
        solution = SurfaceSolution(
            language_id=self.language_id,
            equation_id="surface_ja_" + str(abs(hash(text)) % 10000000),
            tokens=segments.tokens,
            slot_projection=slot_projection,
            local_j=local_j,
            confidence=0.50 if candidates else 0.20,
        )
        notes = ["JA minimal solver: lexical/operator seed only."]
        notes.append("Native review required; no validation promotion.")
        return RegionalSolveResult(
            language_id=self.language_id, text=text, segments=segments, candidates=candidates,
            surface_solution=solution, notes=notes
        )
