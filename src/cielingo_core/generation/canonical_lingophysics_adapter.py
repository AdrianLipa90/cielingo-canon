"""Canonical Lingophysics adapter for native CIEL text round trips.

The adapter composes the existing Lingophysics reference modules stored under
``data/lingophysics``. It does not create a second parser, card ontology or
semantic-mass engine. A source invariant is returned unchanged only when the
independent surface, valency, polarity, TAM-E, deictic and scope gates pass.
Potential/orbit calculations are diagnostic computational observables only and
do not assert a physical interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from lingophysics.ciel_validator_loop import validate_expectations
from lingophysics.compute_metrics import consensus_holonomy, semantic_energy
from lingophysics.dynamic_deixis import classify_dynamic_surface
from lingophysics.predicate_valency import load_event_frames, validate_roles
from lingophysics.tame import compatible_tame, encode_tame_signature

from cielingo_core.generation.native_roundtrip import LingophysicsRoundTripVerdict
from cielingo_core.generation.native_surface_endpoint import canonical_sha256
from cielingo_core.regional.base import RegionalSolveResult


_PUNCTUATION = " \t\r\n.,!?;:%()[]{}<>\"'„”«»—–-"
_ROLE_ALIASES = {
    "agent": "Agent",
    "patient": "Patient",
    "theme": "Theme",
    "recipient": "Recipient",
    "experiencer": "Experiencer",
    "stimulus": "Stimulus",
    "instrument": "Instrument",
    "source": "Source",
    "goal": "Goal",
    "location": "Location",
    "identity": "Identity",
    "state": "State",
    "content": "Content",
    "entity": "Theme",
    "knower": "Experiencer",
}


@dataclass(frozen=True)
class CanonicalLingophysicsRoundTripAdapter:
    """Use the checked-in Lingophysics kernel as a round-trip authority."""

    lingophysics_data_root: Path
    source_commit: str = "cielingo-canon:lingophysics-v2.3"
    minimum_surface_recall: float = 0.95

    def __post_init__(self) -> None:
        root = Path(self.lingophysics_data_root)
        if not root.exists():
            raise ValueError(f"Lingophysics data root does not exist: {root}")
        if not 0.0 <= float(self.minimum_surface_recall) <= 1.0:
            raise ValueError("minimum_surface_recall must be in [0,1]")
        if not self.source_commit:
            raise ValueError("source_commit is required")
        object.__setattr__(self, "lingophysics_data_root", root)

    @classmethod
    def from_repo_root(
        cls,
        repo_root: str | Path,
        *,
        source_commit: str = "cielingo-canon:lingophysics-v2.3",
    ) -> "CanonicalLingophysicsRoundTripAdapter":
        return cls(
            Path(repo_root) / "data" / "lingophysics" / "data",
            source_commit=source_commit,
        )

    def validate_roundtrip(
        self,
        *,
        source_surface_plan: Mapping[str, Any],
        generated_regional_result: RegionalSolveResult,
        generated_sentence_equation: Any,
    ) -> LingophysicsRoundTripVerdict:
        source_invariant = _mapping(source_surface_plan.get("invariant"), "invariant")
        source_surface = _mapping(
            source_surface_plan.get("cielingo_surface"), "cielingo_surface"
        )
        meaning_state = _mapping(
            source_surface_plan.get("meaning_state", {}), "meaning_state"
        )

        source_tokens = _normalise_tokens(source_surface.get("tokens", ()))
        generated_tokens = _normalise_tokens(
            generated_regional_result.segments.tokens
        )
        surface_recall = _ordered_recall(source_tokens, generated_tokens)
        surface_preserved = surface_recall >= self.minimum_surface_recall

        argument_preserved, valency_reports = self._argument_structure_guard(
            source_surface_plan,
            source_invariant=source_invariant,
            surface_preserved=surface_preserved,
        )
        polarity_preserved, polarity_report = _polarity_guard(
            meaning_state,
            source_invariant,
            generated_regional_result,
        )
        tam_e_preserved, tame_report = self._tame_guard(
            meaning_state,
            generated_sentence_equation,
            source_tokens=source_tokens,
            generated_tokens=generated_tokens,
        )
        deictic_preserved, deictic_report = _deictic_guard(
            meaning_state,
            generated_tokens,
        )
        scope_preserved, scope_report = _scope_guard(
            meaning_state,
            generated_regional_result,
        )

        expected = (
            "surface_order",
            "operator_arguments",
            "polarity",
            "tam_e",
            "deictic_anchors",
            "scope",
        )
        observed = tuple(
            name
            for name, passed in (
                ("surface_order", surface_preserved),
                ("operator_arguments", argument_preserved),
                ("polarity", polarity_preserved),
                ("tam_e", tam_e_preserved),
                ("deictic_anchors", deictic_preserved),
                ("scope", scope_preserved),
            )
            if passed
        )
        invariant_validation = validate_expectations(expected, observed)

        diagnostics = _potential_orbit_diagnostics(source_surface_plan)
        gates = {
            "surface_order": surface_preserved,
            "operator_arguments": argument_preserved,
            "polarity": polarity_preserved,
            "tam_e": tam_e_preserved,
            "deictic_anchors": deictic_preserved,
            "scope": scope_preserved,
        }
        equivalence = _weighted_equivalence(gates, surface_recall, diagnostics)

        conflicts: list[dict[str, Any]] = []
        for gate, passed in gates.items():
            if not passed:
                conflicts.append(
                    {
                        "kind": "roundtrip_gate_failed",
                        "gate": gate,
                        "repair": f"repair:{gate}",
                    }
                )
        for missing in invariant_validation.missing_expectations:
            if not any(item.get("gate") == missing for item in conflicts):
                conflicts.append(
                    {
                        "kind": "invariant_expectation_missing",
                        "gate": missing,
                        "repair": f"repair:{missing}",
                    }
                )

        recovered_knot = {
            "schema": "CIEL_LINGOPHYSICS_RECOVERED_KNOT_V1",
            "source_semantic_knot_sha256": canonical_sha256(
                source_surface_plan.get("semantic_knot", {})
            ),
            "generated_sentence_equation_sha256": canonical_sha256(
                _to_dict(generated_sentence_equation)
            ),
            "source_tokens": source_tokens,
            "generated_tokens": generated_tokens,
            "surface_recall": surface_recall,
            "operator_valency": valency_reports,
            "polarity": polarity_report,
            "tam_e": tame_report,
            "deictic": deictic_report,
            "scope": scope_report,
            "potential_orbit": diagnostics,
            "gates": gates,
            "validation_status": invariant_validation.status,
        }

        if invariant_validation.accepted:
            recovered_invariant: Mapping[str, Any] = dict(source_invariant)
        else:
            recovered_invariant = {
                "schema": "CIEL_LINGOPHYSICS_UNRESOLVED_INVARIANT_V1",
                "source_invariant_sha256": canonical_sha256(source_invariant),
                "missing_expectations": list(
                    invariant_validation.missing_expectations
                ),
                "gates": gates,
            }

        return LingophysicsRoundTripVerdict(
            recovered_semantic_knot=recovered_knot,
            recovered_invariant=recovered_invariant,
            semantic_equivalence=equivalence,
            argument_structure_preserved=argument_preserved,
            polarity_preserved=polarity_preserved,
            tam_e_preserved=tam_e_preserved,
            deictic_anchors_preserved=deictic_preserved,
            conflicts=tuple(conflicts),
            source_commit=self.source_commit,
        )

    def _argument_structure_guard(
        self,
        surface_plan: Mapping[str, Any],
        *,
        source_invariant: Mapping[str, Any],
        surface_preserved: bool,
    ) -> tuple[bool, list[dict[str, Any]]]:
        cards = surface_plan.get("operator_cards", ())
        if not isinstance(cards, Sequence) or isinstance(cards, (str, bytes)):
            return False, [{"status": "invalid_operator_cards"}]

        frames = load_event_frames(
            self.lingophysics_data_root
            / "event_frames"
            / "predicate_valency_frames.json"
        )
        invariant_roles = {
            _canonical_role(key)
            for key in source_invariant
            if str(key).lower()
            not in {
                "predicate",
                "operator",
                "polarity",
                "tam_e",
                "tame",
                "deictic_anchors",
                "scope",
            }
        }
        reports: list[dict[str, Any]] = []
        all_valid = bool(cards)
        for raw_card in cards:
            if not isinstance(raw_card, Mapping):
                all_valid = False
                reports.append({"status": "invalid_operator_card"})
                continue
            signature = str(raw_card.get("signature", ""))
            operator, roles = _parse_signature(signature)
            canonical_roles = tuple(_canonical_role(role) for role in roles)
            card_arity = len(raw_card.get("argument_types", {}))
            signature_valid = bool(operator and roles) and card_arity == len(roles)
            invariant_valid = set(canonical_roles).issubset(invariant_roles)

            try:
                valency = validate_roles(operator, list(canonical_roles), frames)
                valency_valid = bool(valency.valid)
                valency_source = "EVENT_FRAME"
                valency_payload = {
                    "operator": valency.operator,
                    "missing_roles": list(valency.missing_roles),
                    "unexpected_roles": list(valency.unexpected_roles),
                    "compatibility": valency.compatibility,
                }
            except KeyError:
                # A signed OPERATOR_CARD remains authoritative when the curated
                # seed frame library does not yet contain that predicate.
                valency_valid = signature_valid
                valency_source = "OPERATOR_CARD_SIGNATURE"
                valency_payload = {
                    "operator": operator,
                    "missing_roles": [],
                    "unexpected_roles": [],
                    "compatibility": 1.0 if signature_valid else 0.0,
                }

            card_valid = (
                signature_valid
                and invariant_valid
                and valency_valid
                and surface_preserved
            )
            all_valid = all_valid and card_valid
            reports.append(
                {
                    "card_id": str(raw_card.get("card_id", "")),
                    "signature": signature,
                    "roles": list(canonical_roles),
                    "signature_valid": signature_valid,
                    "invariant_roles_valid": invariant_valid,
                    "surface_bound": surface_preserved,
                    "valency_source": valency_source,
                    "valency": valency_payload,
                    "valid": card_valid,
                }
            )
        return all_valid, reports

    def _tame_guard(
        self,
        meaning_state: Mapping[str, Any],
        generated_sentence_equation: Any,
        *,
        source_tokens: list[str],
        generated_tokens: list[str],
    ) -> tuple[bool, dict[str, Any]]:
        source_raw = meaning_state.get("tam_e", meaning_state.get("tame"))
        if not isinstance(source_raw, Mapping) or not source_raw:
            return True, {"status": "not_declared"}

        tame_system = _load_json(
            self.lingophysics_data_root / "tame" / "tame_operator_system.json"
        )
        source_values = _canonical_tame_values(source_raw, tame_system)
        generated_values = _generated_tame_values(generated_sentence_equation)
        if generated_values:
            generated_values = _canonical_tame_values(generated_values, tame_system)

        if generated_values and all(
            source_values.get(key) == generated_values.get(key)
            for key in ("tense", "aspect", "mood", "modality")
        ):
            source_sig = _encode_tame(source_values, tame_system)
            generated_sig = _encode_tame(generated_values, tame_system)
            preserved = compatible_tame(source_sig, generated_sig)
            mode = "sentence_equation"
        else:
            # Current PL solver exposes bounded hints rather than full TAM-E.
            # Exact source-token preservation is accepted only when no explicit
            # contradictory TAM-E cue is introduced on the generated surface.
            introduced = _introduced_tame_cues(
                source_tokens, generated_tokens, tame_system
            )
            preserved = source_tokens == generated_tokens and not introduced
            mode = "surface_bound_no_conflicting_cue"

        return preserved, {
            "status": "preserved" if preserved else "conflict",
            "mode": mode,
            "source": source_values,
            "generated": generated_values,
        }


def _polarity_guard(
    meaning_state: Mapping[str, Any],
    source_invariant: Mapping[str, Any],
    regional: RegionalSolveResult,
) -> tuple[bool, dict[str, Any]]:
    source = str(
        meaning_state.get("polarity", source_invariant.get("polarity", "positive"))
    ).strip().lower()
    negation_signal = float(
        regional.surface_solution.local_j.get("J_pl_negation_detected", 0.0)
    )
    generated = "negative" if negation_signal >= 0.5 else "positive"
    aliases = {
        "affirmative": "positive",
        "affirmed": "positive",
        "negated": "negative",
    }
    source = aliases.get(source, source)
    return source == generated, {
        "source": source,
        "generated": generated,
        "negation_signal": negation_signal,
    }


def _deictic_guard(
    meaning_state: Mapping[str, Any],
    generated_tokens: list[str],
) -> tuple[bool, dict[str, Any]]:
    source_raw = meaning_state.get("deictic_anchors", ())
    source_ops: set[str] = set()
    if isinstance(source_raw, Sequence) and not isinstance(source_raw, (str, bytes)):
        for item in source_raw:
            if isinstance(item, Mapping):
                value = item.get("operator", item.get("kind", item.get("value")))
            else:
                value = item
            if value:
                source_ops.add(str(value))

    generated_ops = {
        operator
        for token in generated_tokens
        if (operator := classify_dynamic_surface(token)) is not None
    }
    if not source_ops:
        preserved = not generated_ops
    else:
        preserved = generated_ops == source_ops
    return preserved, {
        "source_operators": sorted(source_ops),
        "generated_operators": sorted(generated_ops),
    }


def _scope_guard(
    meaning_state: Mapping[str, Any],
    regional: RegionalSolveResult,
) -> tuple[bool, dict[str, Any]]:
    source_scope = meaning_state.get("scope")
    generated_pressure = float(regional.surface_solution.local_j.get("J_scope", 0.0))
    if source_scope is None:
        return True, {
            "status": "not_declared",
            "generated_scope_pressure": generated_pressure,
        }
    # Full normalization remains owned by Lingophysics scope cards. Until the
    # regional solver emits a normalized expression, unresolved high pressure
    # cannot be promoted to an equivalence claim.
    source_status = (
        str(source_scope.get("scope_status", "resolved"))
        if isinstance(source_scope, Mapping)
        else "resolved"
    )
    preserved = source_status == "unresolved" or generated_pressure < 0.75
    return preserved, {
        "source_status": source_status,
        "generated_scope_pressure": generated_pressure,
    }


def _potential_orbit_diagnostics(plan: Mapping[str, Any]) -> dict[str, Any]:
    potential = plan.get("potential_components", {})
    potential_values = (
        [float(value) for value in potential.values()]
        if isinstance(potential, Mapping)
        else []
    )
    potential_norm = sum(abs(value) for value in potential_values)

    cards = plan.get("concept_cards", ())
    masses = [
        max(0.0, float(card.get("semantic_mass", 0.0)))
        for card in cards
        if isinstance(card, Mapping)
    ]
    mass = sum(masses) or 1.0
    consensus = plan.get("consensus", {})
    if not isinstance(consensus, Mapping):
        consensus = {}
    phase = float(consensus.get("holonomy_phase", 0.0))
    coherence = float(consensus.get("coherence", 0.0))
    holonomy, derived_coherence = consensus_holonomy(
        [phase], [max(coherence, 1.0e-9)]
    )

    orbit = plan.get("orbit", {})
    if not isinstance(orbit, Mapping):
        orbit = {}
    dimension = int(orbit.get("dimension", 0) or 0)
    energy = semantic_energy(
        mass=mass,
        velocity=abs(phase),
        attractor_mass=max(coherence, 1.0e-9),
        radius=1.0 + potential_norm,
    )
    return {
        "potential_norm": round(potential_norm, 8),
        "semantic_mass_total": round(mass, 8),
        "orbit_dimension": dimension,
        "phase_holonomy_real": round(float(holonomy.real), 8),
        "phase_holonomy_imag": round(float(holonomy.imag), 8),
        "derived_consensus_coherence": round(float(derived_coherence), 8),
        "semantic_energy_diagnostic": round(float(energy), 8),
        "computational_only": True,
        "physical_interpretation_asserted": False,
    }


def _weighted_equivalence(
    gates: Mapping[str, bool],
    surface_recall: float,
    diagnostics: Mapping[str, Any],
) -> float:
    score = 0.20 * max(0.0, min(1.0, surface_recall))
    score += 0.25 if gates["operator_arguments"] else 0.0
    score += 0.15 if gates["polarity"] else 0.0
    score += 0.15 if gates["tam_e"] else 0.0
    score += 0.10 if gates["deictic_anchors"] else 0.0
    score += 0.05 if gates["scope"] else 0.0
    score += 0.10 if int(diagnostics.get("orbit_dimension", 0)) == 36 else 0.0
    return round(max(0.0, min(1.0, score)), 6)


def _normalise_tokens(values: Sequence[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        token = str(value).strip(_PUNCTUATION).casefold()
        if token:
            out.append(token)
    return out


def _ordered_recall(source: list[str], generated: list[str]) -> float:
    if not source:
        return 0.0
    cursor = 0
    matched = 0
    for token in generated:
        if cursor < len(source) and token == source[cursor]:
            cursor += 1
            matched += 1
    return matched / len(source)


def _parse_signature(signature: str) -> tuple[str, tuple[str, ...]]:
    match = re.fullmatch(r"\s*([^()\s]+)\s*\((.*)\)\s*", signature)
    if not match:
        return "", ()
    operator = match.group(1).strip()
    roles = tuple(
        item.strip()
        for item in match.group(2).split(",")
        if item.strip()
    )
    return operator, roles


def _canonical_role(value: Any) -> str:
    raw = str(value).strip().casefold()
    return _ROLE_ALIASES.get(raw, raw[:1].upper() + raw[1:])


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_tame_values(
    values: Mapping[str, Any],
    system: Mapping[str, Any],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    aliases = {"tam-e": "tam_e", "evidence": "evidentiality"}
    for dimension in ("tense", "aspect", "mood", "modality", "evidentiality"):
        raw = values.get(dimension)
        if raw is None:
            raw = values.get(aliases.get(dimension, ""))
        if raw is None:
            if dimension == "mood":
                raw = "Indicative"
            elif dimension == "evidentiality":
                raw = "Unknown"
            else:
                out[dimension] = None
                continue
        options = system["dimensions"].get(dimension, {})
        lookup = {str(key).casefold(): key for key in options}
        canonical = lookup.get(str(raw).casefold())
        out[dimension] = canonical if canonical is not None else str(raw)
    return out


def _generated_tame_values(sentence_equation: Any) -> dict[str, Any]:
    meaning = getattr(sentence_equation, "meaning_equation", None)
    if meaning is None and isinstance(sentence_equation, Mapping):
        meaning = sentence_equation.get("meaning_equation")
    if meaning is None:
        return {}
    if isinstance(meaning, Mapping):
        temporality = dict(meaning.get("temporality", {}))
        modality = dict(meaning.get("modality", {}))
    else:
        temporality = dict(getattr(meaning, "temporality", {}) or {})
        modality = dict(getattr(meaning, "modality", {}) or {})
    return {
        **temporality,
        **modality,
    }


def _encode_tame(values: Mapping[str, Any], system: Mapping[str, Any]):
    return encode_tame_signature(
        tense=str(values.get("tense") or "Atemporal"),
        aspect=str(values.get("aspect") or "Imperfective"),
        mood=str(values.get("mood") or "Indicative"),
        modality=(
            None
            if values.get("modality") in {None, "None", ""}
            else str(values.get("modality"))
        ),
        evidentiality=str(values.get("evidentiality") or "Unknown"),
        tame=dict(system),
    )


def _introduced_tame_cues(
    source_tokens: list[str],
    generated_tokens: list[str],
    system: Mapping[str, Any],
) -> list[str]:
    source_text = " ".join(source_tokens)
    generated_text = " ".join(generated_tokens)
    introduced: list[str] = []
    for dimension, options in system["dimensions"].items():
        for value, meta in options.items():
            for surfaces in meta.get("operators", {}).values():
                for surface in surfaces:
                    cue = str(surface).casefold().strip()
                    if not cue or cue.startswith("-") or "/" in cue:
                        continue
                    if cue in generated_text and cue not in source_text:
                        introduced.append(f"{dimension}:{value}:{cue}")
    return introduced


def _to_dict(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return {"repr": repr(value)}
