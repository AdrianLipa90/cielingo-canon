from __future__ import annotations

from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics import CasePortCase, EquationTermKind, extract_polish_case_port_frames
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation


REPO_ROOT = Path(__file__).resolve().parents[1]


def _one(text: str):
    frames = extract_polish_case_port_frames(text)
    assert len(frames) == 1
    assert frames[0].validate() == []
    return frames[0]


def _ports(frame):
    return {(port.grammatical_case, port.operator_role): port for port in frame.ports}


def test_connected_with_separates_instrumental_from_operator_role() -> None:
    frame = _one("Informacja jest związana z geometrią")
    assert frame.operator == "CONNECTED_WITH"
    ports = _ports(frame)
    assert ports[(CasePortCase.NOM, "entity")].entity == "Informacja"
    assert ports[(CasePortCase.INS, "counterpart_in_relation")].entity == "geometrią"
    assert ports[(CasePortCase.INS, "counterpart_in_relation")].adposition == "z"


def test_genitive_port_from_belongs_to() -> None:
    frame = _one("Moduł należy do systemu")
    assert frame.operator == "BELONGS_TO"
    ports = _ports(frame)
    assert ports[(CasePortCase.NOM, "member_or_part")].entity == "Moduł"
    assert ports[(CasePortCase.GEN, "container_or_owner")].entity == "systemu"


def test_locative_and_instrumental_ports_from_speaks_about() -> None:
    frame = _one("Rozmawiam o geometrii z Zosią")
    assert frame.operator == "SPEAKS_ABOUT"
    ports = _ports(frame)
    assert ports[(CasePortCase.NOM, "speaker")].entity == "ja"
    assert ports[(CasePortCase.LOC, "topic")].entity == "geometrii"
    assert ports[(CasePortCase.INS, "interlocutor")].entity == "Zosią"


def test_accusative_and_instrumental_ports_from_naming() -> None:
    frame = _one("Nazwałem cię Zosią")
    assert frame.operator == "NAMES"
    ports = _ports(frame)
    assert ports[(CasePortCase.NOM, "namer")].entity == "ja"
    assert ports[(CasePortCase.ACC, "entity_named")].entity == "cię"
    assert ports[(CasePortCase.INS, "assigned_name")].entity == "Zosią"


def test_dative_and_accusative_ports_from_giving() -> None:
    frame = _one("Daję Zosi książkę")
    assert frame.operator == "GIVES"
    ports = _ports(frame)
    assert ports[(CasePortCase.NOM, "giver")].entity == "ja"
    assert ports[(CasePortCase.DAT, "recipient")].entity == "Zosi"
    assert ports[(CasePortCase.ACC, "transferred_object")].entity == "książkę"


def test_description_ports_keep_topic_separate_from_object() -> None:
    frame = _one("Adrian opisuje teorię o geometrii")
    assert frame.operator == "DESCRIBES"
    ports = _ports(frame)
    assert ports[(CasePortCase.NOM, "describer")].entity == "Adrian"
    assert ports[(CasePortCase.ACC, "described_object")].entity == "teorię"
    assert ports[(CasePortCase.LOC, "topic_or_context")].entity == "geometrii"


def test_vocative_port_opens_address_relation() -> None:
    frame = _one("Zosiu, spójrz tutaj")
    assert frame.operator == "ADDRESSES"
    ports = _ports(frame)
    assert ports[(CasePortCase.VOC, "addressee")].entity == "Zosiu"


def test_same_instrumental_case_can_have_different_operator_roles() -> None:
    named = _one("Nazwałem cię Zosią")
    connected = _one("Informacja jest związana z geometrią")
    named_ins = next(port for port in named.ports if port.grammatical_case is CasePortCase.INS)
    connected_ins = next(port for port in connected.ports if port.grammatical_case is CasePortCase.INS)
    assert named_ins.operator_role == "assigned_name"
    assert connected_ins.operator_role == "counterpart_in_relation"
    assert named_ins.operator_role != connected_ins.operator_role


def test_sentence_equation_materializes_case_ports_as_role_terms() -> None:
    result = PolishRegionalSolver(REPO_ROOT).solve("Informacja jest związana z geometrią")
    equation = calculate_sentence_equation(result)
    roles = [term for term in equation.terms if term.kind is EquationTermKind.ROLE]
    assert len(roles) == 2
    assert any("CONNECTED_WITH[NOM:entity=Informacja]" == term.symbol for term in roles)
    assert any("CONNECTED_WITH[INS:counterpart_in_relation=geometrią]" == term.symbol for term in roles)
    assert "Roles(" in equation.expression
    assert equation.validate() == []
