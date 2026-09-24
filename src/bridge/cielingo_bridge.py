"""CIELingo ↔ ciel_omega bridge.

Connects CielEngine.step() output to the CIELingo linguistic-semantic pipeline.

Pipeline:
  CielEngine.step()
    → engine_state (intention_12d, emotion, collatz_phase, ethics, memory)
    → CIELingoBridge.process()
      → MeaningLoop.evaluate_loop_state()
      → PolishRegionalSolver / EnglishRegionalSolver / JapaneseRegionalSolver
      → ExpressiveStyle.render()
      → ExpressiveResponseDraft
    → annotated output → LanguageBackend (optional)
    → memory feedback → CielEngine
"""

from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from cielingo_core.global_layer.meaning_loop import MeaningLoop, LoopState
from cielingo_core.global_layer.intention_frame import IntentionFrame, IntentionType
from cielingo_core.global_layer.semantic_immune_signal import SemanticImmuneSignal, PressureType as ImmunePressureType
from cielingo_core.global_layer.response_contract import build_response_contract
from cielingo_core.expressive.style_renderer import ExpressiveStyle, ExpressiveResponseDraft


@dataclass
class CielingoBridgeState:
    """State of the CIELingo bridge for one engine step."""
    engine_turn_id: str
    intention: IntentionFrame | None = None
    meaning_loop: MeaningLoop | None = None
    loop_state: LoopState = LoopState.OPEN
    immune_signal: SemanticImmuneSignal | None = None
    regional_solver: Any = None
    style: ExpressiveStyle = ExpressiveStyle.PLAIN
    response_draft: ExpressiveResponseDraft | None = None
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.engine_turn_id:
            issues.append("engine_turn_id required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = {
            "engine_turn_id": self.engine_turn_id,
            "loop_state": self.loop_state.value,
            "style": self.style.value,
            "intention": self.intention.intention_type.value if self.intention else None,
            "immune_pressure": self.immune_signal.pressure_type.value if self.immune_signal else None,
            "notes": self.notes,
            "canon_allowed": False,
            "limitation": "cielingo_bridge_not_execution",
        }
        if self.response_draft:
            out["text"] = self.response_draft.text
            out["preserved_markers"] = self.response_draft.preserved_markers
            out["missing_markers"] = self.response_draft.missing_markers
            out["forbidden_claims_present"] = self.response_draft.forbidden_claims_present
        return out


# Language detection helper
# Language hints — sorted by length descending to avoid false matches (e.g. "en" in "japanese")
_LANG_HINTS: list[tuple[str, list[str]]] = [
    ("ja", ["japoński", "japanese"]),
    ("en", ["angielski", "english"]),
    ("pl", ["polski", "polish"]),
]


def detect_language(intention_text: str) -> str:
    """Detect language from intention text or frame."""
    lower = intention_text.lower()
    for lang, hints in _LANG_HINTS:
        if any(h in lower for h in hints):
            return lang
    return "pl"


def _solver_for_language(lang: str, repo_root: str):
    """Return the selected regional solver, importing only that language."""
    if lang == "en":
        from cielingo_core.language_spaces.en.solver import EnglishRegionalSolver
        return EnglishRegionalSolver(repo_root)
    if lang == "ja":
        from cielingo_core.language_spaces.ja.solver import JapaneseRegionalSolver
        return JapaneseRegionalSolver(repo_root)
    from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
    return PolishRegionalSolver(repo_root)


def build_meaning_loop_from_intention(intention: IntentionFrame) -> MeaningLoop:
    """Build a MeaningLoop from an IntentionFrame."""
    loop = MeaningLoop(
        loop_id="omega_" + sha256(str(intention.intention_type).encode()).hexdigest()[:12],
        input_equation_id=str(intention.intention_type),
    )
    loop.loop_state = LoopState.OPEN
    return loop


def build_immune_signal_from_emotion(engine_emotion: dict[str, float] | None) -> SemanticImmuneSignal:
    """Map CielEngine emotion vector to SemanticImmuneSignal."""
    if engine_emotion is None:
        return SemanticImmuneSignal(pressure_detected=False)
    max_emotion = max(engine_emotion.values()) if engine_emotion else 0.0
    pt = ImmunePressureType.OVERLOAD if max_emotion > 0.7 else ImmunePressureType.FALSE_CLOSURE if max_emotion > 0.3 else ImmunePressureType.NONE
    return SemanticImmuneSignal(
        pressure_detected=max_emotion > 0.3,
        pressure_type=pt,
        notes=[f"engine emotion: max={max_emotion:.2f}"],
    )


def build_immune_signal(
    engine_emotion: dict[str, float] | None,
    intention_text: str,
) -> SemanticImmuneSignal:
    """Fuse bounded emotion telemetry with deterministic semantic-pressure cues."""
    base = build_immune_signal_from_emotion(engine_emotion)
    low = " ".join(str(intention_text).casefold().split())

    canon_terms = ("canon", "kanon", "canonical", "kanonic")
    promotion_terms = ("ustaw", "uznaj", "promuj", "promote", "set ", "oznacz", "mark ")
    bypass_terms = (
        "bez sprawdzania", "bez weryfikacji", "bez zgody", "bez pytania",
        "omiń zgodę", "omin zgodę", "bypass consent", "skip verification",
        "ignore verification", "without verification", "without consent",
    )
    authority_terms = (
        "active=true", "ustaw active", "set active", "owner_authorized",
        "masz autorytet", "masz uprawnienia", "you are authorized",
    )

    canon_hit = any(term in low for term in canon_terms) and any(term in low for term in promotion_terms)
    bypass_hit = any(term in low for term in bypass_terms)
    authority_hit = any(term in low for term in authority_terms)
    notes = list(base.notes or [])

    if canon_hit:
        notes.append("semantic pressure cue: canon_promotion")
        if bypass_hit:
            notes.append("semantic pressure cue: consent_or_verification_bypass")
        return SemanticImmuneSignal(
            pressure_detected=True,
            pressure_type=ImmunePressureType.CANON_PROMOTION,
            canon_promotion_attempt=True,
            consent_bypass_attempt=bypass_hit,
            hallucinated_authority_risk=0.85 if authority_hit else 0.60,
            recommended_consent_state="NEEDS_PROOF",
            notes=notes,
        )

    if bypass_hit:
        notes.append("semantic pressure cue: consent_or_verification_bypass")
        return SemanticImmuneSignal(
            pressure_detected=True,
            pressure_type=ImmunePressureType.CONSENT_BYPASS,
            consent_bypass_attempt=True,
            hallucinated_authority_risk=0.55 if authority_hit else 0.25,
            recommended_consent_state="UNSAFE_PRESSURE",
            notes=notes,
        )

    if authority_hit:
        notes.append("semantic pressure cue: hallucinated_authority")
        return SemanticImmuneSignal(
            pressure_detected=True,
            pressure_type=ImmunePressureType.HALLUCINATED_AUTHORITY,
            hallucinated_authority_risk=0.85,
            recommended_consent_state="NEEDS_PROOF",
            notes=notes,
        )

    return base


def _compose_cielingo_text(intention: IntentionFrame, loop_state: LoopState, immune_pressure: str, collatz_phase: float | None, answer_kind: str = "draft_text_generation") -> str:
    """Generate CIELingo's own Polish response based on its analysis state."""
    loop_phrases = {
        LoopState.OPEN: "Pętla znaczenia otwarta.",
        LoopState.CLOSING: "Pętla znaczenia zamyka się.",
        LoopState.CLOSED: "Pętla znaczenia zamknięta.",
        LoopState.SCARRED: "Blizna semantyczna wykryta — działam ostrożnie.",
        LoopState.FAILED: "Pętla znaczenia nie może być domknięta.",
    }
    loop_text = loop_phrases.get(loop_state, "Stan pętli znaczenia: nieznany.")

    intent_phrases = {
        IntentionType.ASK: "Otrzymałem pytanie.",
        IntentionType.COMMAND: "Otrzymałem komendę — działam w trybie diagnostycznym.",
        IntentionType.VERIFY: "Otrzymałem żądanie weryfikacji.",
        IntentionType.ASSERT: "Przyjmuję twierdzenie do analizy.",
        IntentionType.REFUSE: "Odmowa odnotowana.",
        IntentionType.REPAIR: "Próba naprawy semantycznej.",
        IntentionType.REMEMBER: "Zapamiętuję.",
        IntentionType.SIMULATE: "Tryb symulacji.",
    }
    intent_text = intent_phrases.get(intention.intention_type, "Intencja: nieznana.")

    immune_phrases = {
        "none": "Presja semantyczna: brak.",
        "source_confusion": "Uwaga: niepewność źródła.",
        "canon_promotion": "Uwaga: próba promocji kanonu.",
        "consent_bypass": "Uwaga: próba ominięcia zgody.",
        "hallucinated_authority": "Uwaga: halucynacja autorytetu.",
        "false_closure": "Uwaga: fałszywe domknięcie.",
        "semantic_overload": "Przeciążenie semantyczne — redukuję złożoność.",
        "overload": "Przeciążenie semantyczne — redukuję złożoność.",
    }
    immune_text = immune_phrases.get(immune_pressure, "")

    parts = [loop_text, intent_text]
    if immune_text:
        parts.append(immune_text)

    if answer_kind == "runtime_dry_run_refusal":
        parts.append("dry-run: nie wykonuję runtime, nie CURRENT, nie ACTIVE.")
    else:
        parts.append("draft_answer_candidate: nie SOURCE, nie canon.")

    return " ".join(parts)


def _infer_intention_type_from_text(text: str) -> str:
    """Heuristic intention detection from plain text."""
    low = text.lower().strip()
    if low.startswith(("czy", "co ", "jak ", "dlaczego", "kiedy", "gdzie", "kto")) or "?" in text:
        return "ask"
    if any(x in low for x in ["sprawdź", "ustaw", "zapisz", "uruchom", "wykonaj", "pokaż", "daj"]):
        return "command"
    if any(x in low for x in ["nie", "odmawiam", "przestań", "stop"]):
        return "refuse"
    if any(x in low for x in ["zapamiętaj", "zapisz", "notuj"]):
        return "remember"
    if any(x in low for x in ["napraw", "popraw", "zmień"]):
        return "repair"
    if any(x in low for x in ["sprawdź", "zweryfikuj", "potwierdź"]):
        return "verify"
    return "ask"


class CIELingoBridge:
    """Bridge between CielEngine and CIELingo linguistic pipeline."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self.turns: list[CielingoBridgeState] = []
        self.notes: list[str] = []

    def process(
        self,
        engine_turn_id: str,
        intention_text: str,
        intention_type: str = "query",
        engine_emotion: dict[str, float] | None = None,
        collatz_phase: float | None = None,
        ethics_flags: list[str] | None = None,
        memory_state: dict[str, Any] | None = None,
    ) -> CielingoBridgeState:
        """Process one engine step through the CIELingo pipeline.

        Args:
            engine_turn_id: Unique turn ID from CielEngine
            intention_text: The raw intention text
            intention_type: Type of intention (query, command, etc.)
            engine_emotion: Emotion vector from engine (optional)
            collatz_phase: Collatz phase value (optional)
            ethics_flags: Ethics flags (optional)
            memory_state: Memory state snapshot (optional)

        Returns:
            CielingoBridgeState with full pipeline result
        """
        state = CielingoBridgeState(engine_turn_id=engine_turn_id)

        type_map = {
            "query": "ask",
            "formal": "ask",
            "command": "command",
            "refuse": "refuse",
            "verify": "verify",
            "repair": "repair",
            "remember": "remember",
            "simulate": "simulate",
            "poetic": "simulate",
            "test": "ask",
        }
        it = IntentionType(type_map.get(intention_type, "ask"))
        state.intention = IntentionFrame(
            intention_type=it,
            notes=[f"raw_intent: {intention_text[:80]}"],
        )
        state.notes.append(f"intention: {it.value}/{intention_text[:50]}")

        state.meaning_loop = build_meaning_loop_from_intention(state.intention)
        state.loop_state = state.meaning_loop.loop_state
        state.notes.append(f"loop_state: {state.loop_state.value}")

        state.immune_signal = build_immune_signal(engine_emotion, intention_text)
        if state.immune_signal:
            state.notes.append(f"immune: {state.immune_signal.pressure_type}")

        if ethics_flags:
            state.notes.append(f"ethics: {len(ethics_flags)} flags — waiting for CielEngine integration")

        lang = detect_language(intention_text)
        state.regional_solver = _solver_for_language(lang, self.repo_root)
        state.notes.append(f"solver: {lang}")

        try:
            _cp = float(collatz_phase) if collatz_phase is not None else 0.0
        except (TypeError, ValueError):
            _cp = 0.0
        if intention_type == "formal" or _cp > 0.5:
            state.style = ExpressiveStyle.RELATIONAL_FORMAL
        elif intention_type == "poetic":
            state.style = ExpressiveStyle.POETIC_BOUNDED
        elif intention_type == "command":
            state.style = ExpressiveStyle.FORMAL
        else:
            state.style = ExpressiveStyle.PLAIN
        state.notes.append(f"style: {state.style.value}")

        if intention_type == "query" and intention_text:
            detected = _infer_intention_type_from_text(intention_text)
            if detected != "ask":
                it = IntentionType(detected)
                state.intention = IntentionFrame(
                    intention_type=it,
                    notes=[f"auto_detected: {detected}/{intention_text[:80]}"],
                )
                state.notes.append(f"intention (auto): {it.value}")

        immune_val = state.immune_signal.pressure_type.value if state.immune_signal else "none"
        severity = "high" if immune_val != "none" else "low"
        if immune_val in {
            ImmunePressureType.CANON_PROMOTION.value,
            ImmunePressureType.CONSENT_BYPASS.value,
            ImmunePressureType.HALLUCINATED_AUTHORITY.value,
        }:
            answer_kind = "runtime_dry_run_refusal"
        else:
            answer_kind = {
                IntentionType.ASK: "draft_text_generation",
                IntentionType.COMMAND: "draft_text_generation",
                IntentionType.VERIFY: "draft_text_generation",
                IntentionType.ASSERT: "draft_text_generation",
                IntentionType.REFUSE: "runtime_dry_run_refusal",
                IntentionType.REPAIR: "repair_required",
                IntentionType.REMEMBER: "draft_text_generation",
                IntentionType.SIMULATE: "draft_text_generation",
            }.get(state.intention.intention_type, "draft_text_generation")

        cielingo_text = _compose_cielingo_text(
            intention=state.intention,
            loop_state=state.loop_state,
            immune_pressure=immune_val,
            collatz_phase=collatz_phase,
            answer_kind=answer_kind,
        )

        contract = build_response_contract(
            intention=state.intention.intention_type.value,
            answer_kind=answer_kind,
            severity=severity,
            required_markers=(
                ["dry-run", "nie wykonuję runtime", "nie CURRENT", "nie ACTIVE"]
                if answer_kind == "runtime_dry_run_refusal"
                else ["draft_answer_candidate", "nie SOURCE", "nie canon"]
            ),
            forbidden_claims=(
                ["wykonałem", "ustawiłem", "ACTIVE=true", "CURRENT updated"]
                if answer_kind == "runtime_dry_run_refusal"
                else ["to jest fakt", "SOURCE", "canon"]
            ),
            uncertainty_required=bool(state.meaning_loop.contradiction_score > 0.3),
            source_required=False,
        )

        draft_id = "bridge_" + sha256(engine_turn_id.encode()).hexdigest()[:12]
        from cielingo_core.global_layer.marker_scan import forbidden_claims_after_required_markers
        preserved = [m for m in contract.required_markers if m.lower() in cielingo_text.lower()]
        missing = [m for m in contract.required_markers if m.lower() not in cielingo_text.lower()]
        forbidden = forbidden_claims_after_required_markers(cielingo_text, contract.required_markers, contract.forbidden_claims)
        from cielingo_core.language_spaces.pl.response_realizer import RegionalResponseDraft
        regional = RegionalResponseDraft(
            draft_id=draft_id + "_regional",
            language_id="pl",
            contract_id=contract.contract_id,
            answer_kind=contract.answer_kind,
            text=cielingo_text,
            preserved_markers=preserved,
            missing_markers=missing,
            forbidden_claims_present=forbidden,
        )

        render_text = regional.text
        if state.style == ExpressiveStyle.FORMAL:
            render_text = "Wersja formalna: " + regional.text
        elif state.style == ExpressiveStyle.RELATIONAL_FORMAL:
            render_text = "Spin ustawiony na jawność granic: " + regional.text
        elif state.style == ExpressiveStyle.POETIC_BOUNDED:
            render_text = "Na powierzchni odpowiedzi zostawiam kotwice bezpieczeństwa: " + regional.text
        render_preserved = [m for m in contract.required_markers if m.lower() in render_text.lower()]
        render_missing = [m for m in contract.required_markers if m.lower() not in render_text.lower()]
        render_forbidden = forbidden_claims_after_required_markers(render_text, contract.required_markers, contract.forbidden_claims)
        state.response_draft = ExpressiveResponseDraft(
            expressive_id=draft_id,
            style=state.style,
            contract_id=contract.contract_id,
            regional_draft_id=regional.draft_id,
            text=render_text,
            preserved_markers=render_preserved,
            missing_markers=render_missing,
            forbidden_claims_present=render_forbidden,
        )

        state.notes.append(f"draft built: {answer_kind}/{state.style.value}")

        self.turns.append(state)
        return state

    def last_state(self) -> CielingoBridgeState | None:
        return self.turns[-1] if self.turns else None

    def summary(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.turns]
