"""Executable Hebrew test codec for the CIELingo orbital-fractal candidate.

The adapter preserves Hebrew orthography while projecting consonantal carriers
and written vowel points into the candidate KAKU -> ORBITAL_CELL -> RADICAL
representation. It is a computational test codec, not evidence that Hebrew
encodes fundamental physics.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import cmath
import math
import unicodedata
from typing import Any

from .grammar import (
    TAU,
    KakuState,
    LatentPhaseReceipt,
    OrbitalCell,
    PhaseBranch,
    latent_phase_ensemble,
)

HEBREW_CODEC_SCHEMA = "CIELINGO_HEBREW_ORBITAL_CODEC_V0_1"

GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80,
    "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}
FINAL_TO_BASE = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
HEBREW_ORDER = tuple("אבגדהוזחטיכלמנסעפצקרשת")
LETTER_ORDINAL = {ch: i + 1 for i, ch in enumerate(HEBREW_ORDER)}

# Vowel points only. Dagesh, shin/sin dots, meteg and cantillation are excluded.
VOWEL_MARKS = (
    "\u05b0", "\u05b1", "\u05b2", "\u05b3", "\u05b4", "\u05b5", "\u05b6",
    "\u05b7", "\u05b8", "\u05b9", "\u05ba", "\u05bb", "\u05c7",
)
VOWEL_INDEX = {mark: i for i, mark in enumerate(VOWEL_MARKS)}
MATRES_CANDIDATES = frozenset({"ו", "י"})


def canonical_letter(ch: str) -> str:
    return FINAL_TO_BASE.get(ch, ch)


def consonant_skeleton(text: str) -> str:
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text):
        base = canonical_letter(ch)
        if base in GEMATRIA:
            out.append(base)
    return "".join(out)


def gematria_total(text: str) -> int:
    return sum(GEMATRIA[ch] for ch in consonant_skeleton(text))


def structural_mass_from_letter(letter: str) -> float:
    """Candidate normalized structural weight derived from standard gematria.

    This weight is not physical mass and is deliberately replaceable in null
    tests by shuffled or alternative mappings.
    """
    base = canonical_letter(letter)
    if base not in GEMATRIA:
        raise ValueError("unsupported Hebrew consonant")
    return math.log1p(GEMATRIA[base]) / math.log1p(400.0)


def vowel_phase(mark: str) -> float:
    """Predeclared computational coordinate; not a phonetic-distance claim."""
    if mark not in VOWEL_INDEX:
        raise ValueError("unsupported Hebrew vowel point")
    return TAU * VOWEL_INDEX[mark] / float(len(VOWEL_MARKS))


def latent_vowel_receipt() -> LatentPhaseReceipt:
    return latent_phase_ensemble([vowel_phase(mark) for mark in VOWEL_MARKS])


@dataclass(frozen=True)
class HebrewOrbitalSlot:
    position: int
    carrier: KakuState
    vowel_marks: tuple[str, ...]
    explicit_cell: OrbitalCell | None
    latent_phase: LatentPhaseReceipt | None
    mater_lectionis_candidate: bool

    @property
    def is_latent(self) -> bool:
        return self.explicit_cell is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "carrier": asdict(self.carrier),
            "vowel_marks": list(self.vowel_marks),
            "explicit_cell": None if self.explicit_cell is None else {
                "cell_id": self.explicit_cell.cell_id,
                "base_phase_rad": self.explicit_cell.base_phase_rad,
                "effective_phase_rad": self.explicit_cell.effective_phase_rad,
                "lambda_coupling": self.explicit_cell.lambda_coupling,
            },
            "latent_phase": None if self.latent_phase is None else asdict(self.latent_phase),
            "mater_lectionis_candidate": self.mater_lectionis_candidate,
        }


@dataclass(frozen=True)
class HebrewOrbitalSurface:
    surface: str
    consonantal_skeleton: str
    slots: tuple[HebrewOrbitalSlot, ...]
    gematria: int
    explicit_vowel_slots: int
    latent_vowel_slots: int
    schema: str = HEBREW_CODEC_SCHEMA
    epistemic_status: str = "CANDIDATE_TEST_CODEC"
    canon_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "surface": self.surface,
            "consonantal_skeleton": self.consonantal_skeleton,
            "slots": [slot.to_dict() for slot in self.slots],
            "gematria": self.gematria,
            "explicit_vowel_slots": self.explicit_vowel_slots,
            "latent_vowel_slots": self.latent_vowel_slots,
            "epistemic_status": self.epistemic_status,
            "canon_allowed": self.canon_allowed,
        }


@dataclass(frozen=True)
class HebrewRadicalBinding:
    radical: str
    surface: HebrewOrbitalSurface
    radical_positions: tuple[int, ...]
    schema: str = HEBREW_CODEC_SCHEMA
    canon_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "radical": self.radical,
            "surface": self.surface.to_dict(),
            "radical_positions": list(self.radical_positions),
            "canon_allowed": self.canon_allowed,
        }


def _slot_records(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for ch in unicodedata.normalize("NFD", text):
        base = canonical_letter(ch)
        if base in GEMATRIA:
            current = {"letter": base, "vowels": []}
            records.append(current)
        elif ch in VOWEL_INDEX and current is not None:
            current["vowels"].append(ch)
    return records


def _explicit_phase(marks: tuple[str, ...]) -> float:
    phasors = [cmath.exp(1j * vowel_phase(mark)) for mark in marks]
    mean = sum(phasors, 0j) / len(phasors)
    if abs(mean) <= 1e-12:
        raise ValueError("explicit vowel points cancel under candidate phase map")
    return math.atan2(mean.imag, mean.real)


def analyze_hebrew_surface(
    surface: str,
    *,
    lambda_coupling: float = 1.0,
) -> HebrewOrbitalSurface:
    lam = float(lambda_coupling)
    if not math.isfinite(lam) or lam < 0.0:
        raise ValueError("lambda_coupling must be finite and non-negative")
    records = _slot_records(surface)
    if not records:
        raise ValueError("surface must contain Hebrew consonants")

    slots: list[HebrewOrbitalSlot] = []
    explicit = 0
    latent = 0
    latent_receipt = latent_vowel_receipt()

    for index, record in enumerate(records):
        letter = record["letter"]
        carrier = KakuState(
            kaku_id=f"he:kaku:{index}:{letter}",
            symbol=letter,
            structural_mass=structural_mass_from_letter(letter),
            payload={
                "language": "he",
                "gematria": GEMATRIA[letter],
                "ordinal": LETTER_ORDINAL[letter],
                "physical_mass_claim": False,
            },
        )
        marks = tuple(record["vowels"])
        if marks:
            explicit += 1
            cell = OrbitalCell(
                cell_id=f"he:chi:{index}:{letter}",
                carrier=carrier,
                base_phase_rad=_explicit_phase(marks),
                branch=PhaseBranch.PLUS,
                lambda_coupling=lam,
                payload={
                    "language": "he",
                    "vowel_marks": list(marks),
                    "phase_coordinate_claim": "COMPUTATIONAL_ONLY",
                },
            )
            latent_phase = None
        else:
            latent += 1
            cell = None
            latent_phase = latent_receipt

        slots.append(HebrewOrbitalSlot(
            position=index,
            carrier=carrier,
            vowel_marks=marks,
            explicit_cell=cell,
            latent_phase=latent_phase,
            mater_lectionis_candidate=letter in MATRES_CANDIDATES,
        ))

    skeleton = "".join(record["letter"] for record in records)
    return HebrewOrbitalSurface(
        surface=surface,
        consonantal_skeleton=skeleton,
        slots=tuple(slots),
        gematria=sum(GEMATRIA[ch] for ch in skeleton),
        explicit_vowel_slots=explicit,
        latent_vowel_slots=latent,
    )


def bind_radical(
    radical: str,
    surface: str,
    *,
    lambda_coupling: float = 1.0,
) -> HebrewRadicalBinding:
    root = consonant_skeleton(radical)
    analyzed = analyze_hebrew_surface(surface, lambda_coupling=lambda_coupling)
    if not root:
        raise ValueError("radical must contain Hebrew consonants")

    positions: list[int] = []
    cursor = 0
    for letter in root:
        found = analyzed.consonantal_skeleton.find(letter, cursor)
        if found < 0:
            raise ValueError("radical is not an ordered subsequence of the surface")
        positions.append(found)
        cursor = found + 1

    return HebrewRadicalBinding(
        radical=root,
        surface=analyzed,
        radical_positions=tuple(positions),
    )


__all__ = [
    "HEBREW_CODEC_SCHEMA", "GEMATRIA", "VOWEL_MARKS", "MATRES_CANDIDATES",
    "HebrewOrbitalSlot", "HebrewOrbitalSurface", "HebrewRadicalBinding",
    "canonical_letter", "consonant_skeleton", "gematria_total",
    "structural_mass_from_letter", "vowel_phase", "latent_vowel_receipt",
    "analyze_hebrew_surface", "bind_radical",
]
