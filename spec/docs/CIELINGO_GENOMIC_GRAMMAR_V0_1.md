# CIELingo Genomic Grammar v0.1

Status: **computational research hypothesis / falsifiable prototype**.

## Purpose

This module tests whether sequence-local regulatory information is represented
more usefully when symbolic motif content is augmented with explicit relational
geometry: spacing, orientation and helical phase.

It does **not** claim that DNA is literally a natural language, that the
canonical genetic code is replaced by a phase code, or that a biological
mechanism has been established.

## Representation ladder

```text
KAKU -> RADICAL -> CONCEPT -> SENTENCE -> PARAGRAPH -> CHAPTER -> BOOK
```

The current v0.1 implementation operationalizes KAKU through SENTENCE:

- KAKU: one sequence symbol at a coordinate;
- RADICAL: one matched motif occurrence;
- CONCEPT: one connected component of motif occurrences under the configured
  relation-distance bound;
- SENTENCE: the record-level candidate regulatory representation.

Higher levels remain reserved for later locus/domain/genome composition.

## Relational edge

For motif centers `x_i` and `x_j`:

```text
d_ij = x_j - x_i
Delta_phi_ij = 2*pi*d_ij/h mod 2*pi
```

where `h` is configurable. Orientation and optional context travel with the
edge. v0.1 uses a constant-repeat baseline and makes no claim that local DNA
twist is constant in vivo.

## Required ablation

Every labeled experiment exposes three nested feature sets:

```text
M0 = sequence_only
M1 = sequence_plus_geometry
M2 = sequence_plus_phase
```

The phase-specific test is **M2 versus M1**, not merely M2 versus M0. This
separates phase from motif vocabulary, distance and orientation.

## Independent periodicity test

Observed spacer/readout pairs may be scanned with

```text
y(d) = beta0 + A*cos(2*pi*d/P) + B*sin(2*pi*d/P)
```

over a caller-specified period grid. The period is not fixed to a helical repeat
during the scan. Synthetic recovery tests are validation of the fitting code
only, not evidence for a biological phase channel.

## GREMLIN integration

CIELingo can expose the compiled SENTENCE object to the connected GREMLIN MCP
surface. The full-audit path uses the specialist contract implemented by
GREMLIN:

```text
SPIDER, RAVEN, HOUND, MOLE, OWL, ANT, MANTIS
```

followed by BELZEBUB synthesis only after specialist completion.

GREMLIN outputs remain advisory. No bridge result grants CIELingo canon,
NOEMA writeback or production-runtime authority.

## Falsification criteria

The phase channel is not supported if, on held-out biological data and after
controlling for sequence, motif vocabulary, distance, orientation and relevant
context, phase-aware features do not reproducibly improve predictive
performance or periodic spacer readouts do not reproduce out of sample.

A positive synthetic test is never sufficient.

## Next empirical gate

Use independently sourced enhancer/promoter datasets with measured activity.
Pre-register motif definitions, train/test partitioning, nuisance controls and
the period search range before evaluating the phase increment.
