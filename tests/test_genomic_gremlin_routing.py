from __future__ import annotations

from cielingo_core.bridge.gremlin_surface import GremlinConsequence, classify_consequence
from cielingo_core.genomic import (
    GenomicLevel,
    SequenceFeature,
    build_octopus_request,
    concept_from_features,
    routing_manifest,
)


def test_genomic_request_delegates_species_choice_to_octopus() -> None:
    node = concept_from_features(
        "concept-1",
        [
            SequenceFeature("a", "ACGT", 100),
            SequenceFeature("b", "TATA", 112),
        ],
    )
    request = build_octopus_request(node).to_dict()

    assert request["tool"] == "gremlin_route"
    assert classify_consequence(request["tool"]) is GremlinConsequence.READ_ONLY
    assert request["authority"]["force_species_route"] is False
    assert "species" not in request["arguments"]["payload"]
    assert request["arguments"]["payload"]["cielingo_level"] == "KONCEPT"
    assert request["arguments"]["payload"]["epistemic_boundary"]["sequence_only_baseline_required"] is True


def test_routing_manifest_covers_every_genomic_level() -> None:
    manifest = routing_manifest()
    assert set(manifest["levels"]) == {level.value for level in GenomicLevel}
    assert manifest["route_policy"] == "DYNAMIC_AUDITABLE_NO_FORCED_SPECIES"
