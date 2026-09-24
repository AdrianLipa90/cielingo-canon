# CIEL Operator Signatures v0.1

## Core typing rule

CIELingo treats grammatical case and semantic role as independent axes.

```text
CasePort = (grammatical_case, operator_role, entity, adposition?, provenance)
OperatorSignature = operator -> allowed CasePort specifications
```

A grammatical case never maps directly to a universal semantic role. Universal normalization is optional and is admitted only after the complete operator-local `(operator, case, operator_role, adposition)` signature matches.

## Reference signatures

```text
CONNECTED_WITH[NOM:entity, INS+z:counterpart_in_relation]
BELONGS_TO[NOM:member_or_part, GEN+do:container_or_owner]
SPEAKS_ABOUT[NOM:speaker, LOC+o:topic, INS+z:interlocutor]
NAMES[NOM:namer, ACC:entity_named, INS:assigned_name]
GIVES[NOM:giver, DAT:recipient, ACC:transferred_object]
DESCRIBES[NOM:describer, ACC:described_object, LOC+o:topic_or_context]
ADDRESSES[VOC:addressee]
```

`CONNECTED_WITH` is explicitly symmetric. The remaining reference signatures are directional.

## Universal-role normalization

Reference v0.1 admits only operator-local normalizations that are explicitly encoded in the signature registry. Examples:

```text
GIVES/NOM:giver -> AGENT
GIVES/DAT:recipient -> RECIPIENT
GIVES/ACC:transferred_object -> THEME
NAMES/NOM:namer -> AGENT
NAMES/ACC:entity_named -> THEME
```

No normalization exists for `NAMES/INS:assigned_name`, `CONNECTED_WITH/INS:counterpart_in_relation`, or `SPEAKS_ABOUT/INS:interlocutor`. In particular, `INS` alone never implies `UniversalRole.INSTRUMENT`.

## Fail-closed behavior

Typing reports are invalid when:

- the operator has no registered signature;
- a required `(case, operator_role)` port is missing;
- an unexpected port is present;
- an operator-local adposition constraint is violated.

An invalid typing report emits no `UniversalRoleBinding` entries.

## Receipts

Every signature has a deterministic SHA-256 `signature_commitment` over its normalized structure. `SentenceEquation` ROLE terms carry:

- `signature_known`;
- `signature_valid`;
- `signature_id`;
- `signature_commitment`;
- optional `universal_role`;
- optional `normalization_basis`.

This keeps the original CasePort evidence intact while making semantic normalization auditable.

## Authority

Operator signatures and typing reports remain candidate-only. They do not grant SOURCE promotion, canon promotion, runtime execution, NOEMA writeback, or CURRENT mutation.
