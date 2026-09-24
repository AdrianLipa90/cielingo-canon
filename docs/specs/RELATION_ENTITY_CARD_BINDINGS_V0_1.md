# Relation Entity Card Bindings v0.1

Schema: `CIEL_RELATION_ENTITY_CARD_BINDINGS_V0_1`

This receipt transports lexical semantic identity from regional `CardCandidate` evidence to entities already present in `CIEL_RELATION_HYPERGRAPH_V0_1`.

## Identity rule

A card identity is admitted only when one explicit relation entity has exact token-index continuity with regional candidates and those candidates contain exactly one distinct `card_id`.

`slot_id` is preserved as provenance. It does not establish semantic identity.

## Exact hypergraph binding

The receipt carries `relation_hypergraph_commitment`, and that SHA-256 value participates in the receipt commitment. A consumer must require equality with the exact validated relation-hypergraph commitment.

The receipt partitions every relation entity exactly once into one of four disjoint sets:

- admitted binding: one `card_id`;
- `ambiguous_entity_ids`: more than one distinct candidate identity;
- `unbound_entity_ids`: no admitted card identity;
- `implicit_entity_ids`: implicit relation entity, never assigned lexical identity.

Each admitted binding must preserve the relation entity token indices. The receipt and every binding remain `candidate_only=true`.

## Validation

`RelationEntityCardBindings.validate()` verifies the receipt-local schema and deterministic commitment. `validate_against_hypergraph()` additionally verifies equation, language, exact hypergraph commitment, exact entity partition, explicit/implicit separation, and token-index continuity.

Downstream world-state grounding may use an admitted `card_id`. Ambiguous or unbound producer identity must remain fail-closed rather than being reconstructed from `slot_id`.
