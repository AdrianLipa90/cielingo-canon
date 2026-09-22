"""GREMLIN orchestration for the CIELingo genomic-grammar research surface."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from cielingo_core.bridge.gremlin_full_bridge import GremlinAuthorization, GremlinFullBridge
from .grammar import GenomicUnit

SCHEMA = "CIELINGO_GENOMIC_GREMLIN_PIPELINE_V0_1"
FULL_AUDIT_SPECIALISTS = ("SPIDER", "RAVEN", "HOUND", "MOLE", "OWL", "ANT", "MANTIS")


class GenomicPipelineMode(str, Enum):
    AUTO_ROUTE = "AUTO_ROUTE"
    FULL_AUDIT = "FULL_AUDIT"


@dataclass(frozen=True)
class GenomicDispatch:
    mode: GenomicPipelineMode
    request_id: str | None
    task_ids: tuple[str, ...]
    raw: Mapping[str, Any]


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{field} must be a mapping")
    return dict(value)


def _tool_result(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return _mapping(envelope.get("result"), "GREMLIN tool result")


def _task_ids(result: Mapping[str, Any]) -> tuple[str, ...]:
    rows = result.get("tasks", [])
    if not isinstance(rows, list):
        raise RuntimeError("GREMLIN fanout tasks must be a list")
    out: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise RuntimeError(f"GREMLIN task {index} must be a mapping")
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise RuntimeError(f"GREMLIN task {index} has no task_id")
        out.append(task_id.strip())
    if not out:
        raise RuntimeError("GREMLIN fanout returned no specialist tasks")
    return tuple(out)


class GenomicGremlinPipeline:
    """Route genomic grammar objects through GREMLIN without granting canon authority."""

    def __init__(self, bridge: GremlinFullBridge):
        self.bridge = bridge

    @staticmethod
    def payload(unit: GenomicUnit, question: str, *, hypothesis_id: str | None = None) -> dict[str, Any]:
        text = question.strip()
        if not text:
            raise ValueError("question must be non-empty")
        return {
            "schema": SCHEMA,
            "intent": "genomic_grammar_research",
            "question": text,
            "hypothesis_id": hypothesis_id,
            "genomic_unit": unit.to_dict(),
            "semantic_signature": unit.semantic_signature(),
            "epistemic_status": "COMPUTATIONAL_HYPOTHESIS",
            "canon_allowed": False,
        }

    async def preview_route(
        self,
        unit: GenomicUnit,
        question: str,
        *,
        max_species: int = 4,
        hypothesis_id: str | None = None,
    ) -> dict[str, Any]:
        if not 1 <= max_species <= len(FULL_AUDIT_SPECIALISTS):
            raise ValueError("max_species must be in [1, 7]")
        return await self.bridge.invoke(
            "gremlin_route",
            {
                "payload": self.payload(unit, question, hypothesis_id=hypothesis_id),
                "max_species": max_species,
            },
        )

    async def dispatch(
        self,
        unit: GenomicUnit,
        question: str,
        *,
        mode: GenomicPipelineMode = GenomicPipelineMode.AUTO_ROUTE,
        authorization: GremlinAuthorization,
        request_id: str | None = None,
        max_species: int = 4,
        hypothesis_id: str | None = None,
    ) -> GenomicDispatch:
        payload = self.payload(unit, question, hypothesis_id=hypothesis_id)
        if mode is GenomicPipelineMode.AUTO_ROUTE:
            if not 1 <= max_species <= len(FULL_AUDIT_SPECIALISTS):
                raise ValueError("max_species must be in [1, 7]")
            tool = "gremlin_auto_fanout"
            arguments = {"payload": payload, "request_id": request_id, "max_species": max_species}
        elif mode is GenomicPipelineMode.FULL_AUDIT:
            tool = "gremlin_fanout"
            arguments = {
                "payload": payload,
                "species": list(FULL_AUDIT_SPECIALISTS),
                "request_id": request_id,
            }
        else:
            raise ValueError(f"unsupported pipeline mode: {mode!r}")

        envelope = await self.bridge.invoke(tool, arguments, authorization=authorization)
        result = _tool_result(envelope)
        return GenomicDispatch(
            mode=mode,
            request_id=request_id,
            task_ids=_task_ids(result),
            raw=result,
        )

    async def collect(self, task_ids: Sequence[str]) -> dict[str, Any]:
        ids = [value.strip() for value in task_ids if isinstance(value, str) and value.strip()]
        if not ids:
            raise ValueError("task_ids must contain at least one non-empty id")
        return await self.bridge.invoke("gremlin_collect", {"task_ids": ids})

    async def synthesize_if_complete(
        self,
        task_ids: Sequence[str],
        *,
        authorization: GremlinAuthorization,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        collected_envelope = await self.collect(task_ids)
        collected = _tool_result(collected_envelope)
        if collected.get("complete") is not True:
            return {
                "schema": SCHEMA,
                "status": "WAITING_SPECIALISTS",
                "collection": collected,
                "authority": {"advisory_only": True, "canon_allowed": False},
            }

        synthesis = await self.bridge.invoke(
            "gremlin_synthesize",
            {"specialist_task_ids": list(task_ids), "request_id": request_id},
            authorization=authorization,
        )
        return {
            "schema": SCHEMA,
            "status": "SYNTHESIS_QUEUED",
            "collection": collected,
            "synthesis": _tool_result(synthesis),
            "authority": {"advisory_only": True, "canon_allowed": False},
        }
