from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics.action_scope_condition import build_action_scope_condition_receipt
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    benchmark_root = repo_root / ".benchmark_checkout"
    dataset_path = benchmark_root / "dataset" / "golden_v0_1.jsonl"
    output_dir = repo_root / "artifacts" / "benchmark_worldstate_producer_v02"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "cielingo_producer_analysis_v02.jsonl"
    solver = PolishRegionalSolver(repo_root)

    rows = []
    pl_count = 0
    graph_count = 0
    card_receipt_count = 0
    scope_receipt_count = 0
    for raw_line in dataset_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        task = json.loads(raw_line)
        task_id = str(task["task_id"])
        language = str(task["language"])
        text = str(task["user_input"])
        if language.lower() not in {"pl", "polish"}:
            rows.append({
                "task_id": task_id,
                "analysis": {
                    "schema": "CIELINGO_PRODUCER_ANALYSIS_V0_2",
                    "language": language,
                    "text": text,
                    "status": "LANGUAGE_UNSUPPORTED_BY_PINNED_CIEL",
                    "ground_truth_used": False,
                },
            })
            continue

        pl_count += 1
        result = solver.solve(text)
        equation = calculate_sentence_equation(result)
        issues = equation.validate()
        if issues:
            raise RuntimeError(f"{task_id}: SentenceEquation validation failed: {'; '.join(issues)}")
        payload = equation.to_dict()
        scope = build_action_scope_condition_receipt(
            text,
            tokens=list(payload.get("tokens", [])),
            language_id="pl",
        )
        if payload.get("relation_hypergraph") is not None:
            graph_count += 1
        if payload.get("relation_entity_card_bindings") is not None:
            card_receipt_count += 1
        if scope is not None:
            scope_receipt_count += 1
        rows.append({
            "task_id": task_id,
            "analysis": {
                "schema": "CIELINGO_PRODUCER_ANALYSIS_V0_2",
                "language": language,
                "text": text,
                "status": "CIELINGO_ANALYSIS_COMPLETE",
                "sentence_equation": payload,
                "action_scope_condition": None if scope is None else scope.to_dict(),
                "ground_truth_used": False,
            },
        })

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_canonical(row) + "\n")
    sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    summary = {
        "schema": "CIELINGO_BENCHMARK_PRODUCER_ARTIFACT_V0_2",
        "task_count": len(rows),
        "pl_task_count": pl_count,
        "relation_hypergraph_count": graph_count,
        "relation_entity_card_receipt_count": card_receipt_count,
        "action_scope_receipt_count": scope_receipt_count,
        "ground_truth_used": False,
        "sha256": sha,
    }
    (output_dir / "summary.json").write_text(_canonical(summary) + "\n", encoding="utf-8")
    print(_canonical(summary))


if __name__ == "__main__":
    main()
