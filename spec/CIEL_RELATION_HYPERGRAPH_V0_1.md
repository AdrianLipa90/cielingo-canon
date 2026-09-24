# CIEL Relation Hypergraph v0.1

## Model

A typed linguistic relation is represented as an n-ary event rather than forced into a set of unrelated binary edges.

```text
RelationEvent(operator, signature)
  <-[CASE:operator_role]- RelationEntity
  <-[CASE:operator_role]- RelationEntity
  ...
```

For example:

```text
GIVES
  NOM:giver              -> ja
  DAT:recipient          -> Zosi
  ACC:transferred_object -> książkę
```

## Components

### RelationEntityNode

Preserves entity label, surface form, token indices, confidence and whether the entity is implicit. An implicit first-person subject is retained as an entity with empty `token_indices`.

### RelationEventNode

Preserves operator, relation family, directionality/symmetry, source CasePortFrame, signature ID, signature commitment and confidence.

### RelationIncidence

Connects one event to one entity through:

- grammatical case;
- operator-local role;
- token indices;
- optional adposition;
- optional already-admitted UniversalRole and normalization basis.

Case and semantic role remain separate axes.

## Admission

Only CasePortFrames that pass their `OperatorSignature` are promoted into RelationEvents. An invalid or unknown signature does not create an event.

Optional UniversalRole annotations originate only from the signature-validated normalization path already carried by `MeaningRoleMultimap`.

## Commitment

`CIEL_RELATION_HYPERGRAPH_V0_1` is bound by deterministic SHA-256 over:

- schema;
- equation ID;
- language ID;
- ordered entity nodes;
- ordered event nodes;
- ordered incidences;
- candidate-only boundary.

Validation checks unique identities, incidence endpoints, event/frame continuity, entity token-index continuity, symmetry/directionality consistency and commitment integrity.

## Transport

The hypergraph is serialized additively as:

```text
SentenceEquation.relation_hypergraph
```

It does not replace CasePort ROLE terms or MeaningRoleMultimap; those remain independent auditable layers.

## Authority

The relation hypergraph remains candidate-only and carries no SOURCE, canon, runtime execution, memory-write, NOEMA-writeback or CURRENT authority.
