# CIEL MeaningRoleMultimap v0.1

## Purpose

`MeaningRoleMultimap` is the lossless GLOBAL carrier for zero-or-more normalized semantic-role bindings produced from signature-validated CasePortFrames.

It complements the legacy `MeaningEquation.roles` mapping without replacing it. Multiple entities may therefore occupy the same `UniversalRole` without overwriting one another.

## Binding shape

```text
MeaningRoleBinding(
  universal_role,
  entity,
  operator,
  operator_role,
  grammatical_case,
  token_indices,
  source_frame_id,
  signature_id,
  signature_commitment,
  normalization_basis,
  confidence
)
```

Each binding remains candidate-only and preserves both the language-local grammatical evidence and the operator-local normalization basis.

## Multimap shape

```text
CIEL_MEANING_ROLE_MULTIMAP_V0_1 {
  equation_id,
  bindings[],
  candidate_only: true,
  commitment: SHA256(canonical body)
}
```

The commitment is computed over the schema, equation ID, ordered binding list and candidate boundary using UTF-8 JSON with sorted keys and compact separators.

## Admission chain

A GLOBAL role binding is emitted only through the chain:

```text
CasePortFrame
-> valid OperatorSignature typing
-> explicit UniversalRole normalization rule
-> MeaningRoleBinding
-> MeaningRoleMultimap commitment
```

A grammatical case by itself does not admit a `UniversalRole`.

## Consumer verification

The Semantic Model independently recomputes the multimap commitment. `UniversalRole` is retained in ASIR only when a ROLE term matches a binding in a valid committed multimap on:

- source frame ID;
- operator;
- grammatical case;
- operator-local role;
- entity;
- token indices;
- signature ID;
- signature commitment;
- universal role;
- normalization basis.

The underlying CasePort relation may remain available when normalization is absent or uncorroborated; the stronger GLOBAL normalization is then withheld.

## Authority

The multimap is candidate-only. It does not grant SOURCE, canon, runtime execution, memory write authority, NOEMA writeback, or CURRENT mutation.
