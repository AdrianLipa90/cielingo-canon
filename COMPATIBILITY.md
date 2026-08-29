# Runtime Compatibility Contract

This file pins the cross-repository runtime pair. The listed SHAs identify the executable code baselines; later documentation-only commits do not change this ABI contract.

## Supported pair

| Component | Release identity | Runtime code SHA |
|---|---:|---|
| `AdrianLipa90/cielingo-canon` | `v0.6` baseline | `ab097f99d46eb446836833ac90b2bc3cf9d219e1` |
| `AdrianLipa90/Ciel-Semantic-Model-` | `0.8.1` | `0a4a1b57217fc876ed0535829686cfed8ccd0d8f` |

Supported Python matrix for the semantic runtime: `3.11`, `3.12`, `3.13`.

## Machine-readable cross-repository link

`CROSS_REPO_LINK.json` exposes this supported pair to tooling. It records repository roles, integration paths, protocol identities, ownership boundaries and candidate interface extension points. The same `link_id` is mirrored by `AdrianLipa90/Ciel-Semantic-Model-` with local and partner roles reversed.

The language-side ownership path is:

```text
language_spaces -> Lingophysics -> MeaningEquation/native semantics
```

The paired semantic-runtime consumption path is:

```text
native semantics -> ASIR -> PhaseNav/MemoryFabric integration
```

## Required protocol and schema identities

| Contract | Required identity |
|---|---|
| AUX compile request | `CIEL_AUX_PHASE_MEMORY_REQUEST_V2` |
| AUX compile packet | `CIEL_AUX_PHASE_MEMORY_PACKET_V3` |
| native semantic state | `CIEL_NATIVE_SEMANTIC_STATE_V1` |
| MemoryFabric read set | `CIEL_MEMORY_READ_SET_V1` |
| MemoryFabric delta bundle | `CIEL_MEMORY_DELTA_BUNDLE_V1` |
| response-plan request | `CIEL_AUX_RESPONSE_PLAN_REQUEST_V1` |
| response-plan result | `CIEL_AUX_RESPONSE_PLAN_RESULT_V1` |
| response semantic plan | `CIEL_RESPONSE_SEMANTIC_PLAN_V1` |
| dual-native SurfacePlan | `CIEL_NATIVE_SURFACE_PLAN_V2` |
| text-generation request | `CIEL_AUX_TEXT_GENERATION_REQUEST_V1` |
| text-generation result | `CIEL_AUX_TEXT_GENERATION_RESULT_V1` |
| generation operation | `cielingo.lingophysics.generate_surface` |

## Required semantic-generation invariants

- source-native and response-native payloads are complete and independently rehashed;
- the response plan binds the source native state and the source MemoryReadSet;
- the response-native state binds the response MemoryReadSet;
- response tokens, SentenceEquation and invariant match the response plan;
- the final text equals the validated expressive draft;
- semantic round-trip meets the configured equivalence threshold;
- any language backend candidate remains advisory-only;
- authority-bearing payloads are rejected.

## Phase and memory invariants expected from the consumer

- phase dimension: exactly `36`;
- executable phase convention: native spinor `4π`;
- spinor map: `exp(iφ/2)`;
- MemoryFabric manifest: exactly `12` lanes, IDs `0..11`;
- source and response PhaseNav receipts remain distinct;
- response projection is never the authoritative memory store;
- writes target the full authoritative source read set and require admission.

## Authority boundary

Neither repository may infer or grant any of the following from local computation, generated text, fixture success or a schema-valid packet:

- SOURCE promotion;
- canon promotion;
- NOEMA `CURRENT` mutation;
- runtime or code-update authority;
- a physical quantum, biological or physical time-crystal claim.

## Compatibility-change rule

Any change to a schema identity, response-plan representation, hashing body, receipt binding, generation operation, invariant comparison or authority boundary requires:

1. a new compatibility entry;
2. synchronized tests in both repositories;
3. a new release identity for the component whose ABI changed;
4. an explicit migration rule or an explicit rejection of older payloads.
