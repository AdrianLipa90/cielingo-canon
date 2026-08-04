# CIELingo Canon

Private canonical repository for CIELingo language solving, Lingophysics-bound response planning and validated surface realization.

## Current baseline

The current integrated baseline is:

```text
cielingo-canon v0.6
runtime code SHA: ab097f99d46eb446836833ac90b2bc3cf9d219e1
```

Documentation-only commits may follow this SHA without changing the runtime ABI. The supported cross-repository pair is defined in [COMPATIBILITY.md](COMPATIBILITY.md).

## Responsibilities

This repository owns the canonical language-side stages of the response pipeline:

- regional CIELingo surface solving;
- response-semantic planning from native semantics and explicit evidence;
- typed Lingophysics bindings used by the planner and round-trip validator;
- deterministic or advisory candidate realization;
- regional and expressive response contracts;
- independent recomputation of source-native and response-native bindings;
- rejection of authority-bearing or hash-inconsistent generation payloads.

It does not own PhaseNav evolution, MemoryFabric persistence, NOEMA authority or code promotion.

## Dual-native generation contract

The canonical endpoint accepts:

```text
operation: cielingo.lingophysics.generate_surface
request:   CIEL_AUX_TEXT_GENERATION_REQUEST_V1
plan:      CIEL_NATIVE_SURFACE_PLAN_V2
native:    CIEL_NATIVE_SEMANTIC_STATE_V1
result:    CIEL_AUX_TEXT_GENERATION_RESULT_V1
```

The endpoint validates and recomputes both complete native payloads:

```text
source-native semantics
  -> response semantic plan
  -> response-native semantics
  -> surface candidate
  -> regional realization
  -> expressive realization
  -> CIELingo × Lingophysics round-trip
  -> ACK or NACK
```

A language backend or GGUF may propose a surface candidate only in advisory mode. It may not alter the response invariant, operator arguments, polarity, TAM-E, deictic anchors or authority boundaries.

## Authority boundary

This repository never grants SOURCE, canon, NOEMA `CURRENT`, memory-write, runtime-execution or code-update authority from generated text or from successful local validation. It also makes no physical quantum, biological-equivalence or physical time-crystal claim.

## Integration

The currently supported consumer is:

```text
AdrianLipa90/Ciel-Semantic-Model-
ciel-semantic-model 0.8.1
runtime code SHA 0a4a1b57217fc876ed0535829686cfed8ccd0d8f
```

See [COMPATIBILITY.md](COMPATIBILITY.md) before changing any schema, receipt body, hashing rule or generation operation.
