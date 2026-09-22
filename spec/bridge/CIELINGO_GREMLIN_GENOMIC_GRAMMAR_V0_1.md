# CIELingo × GREMLIN Genomic Grammar v0.1

Status: EXPERIMENTAL / TESTABLE MODEL. This document does not claim that linguistic hierarchy and biological regulatory hierarchy are identical, nor that a genomic phase code has been demonstrated.

## Purpose

Use CIELingo as the typed hierarchical representation layer and the complete GREMLIN MCP surface as an evidence-first orchestration backend for testing whether regulatory function is better explained by sequence plus relational geometry than by sequence symbols alone.

Pinned baselines for this first integration slice:

- CIELingo canonical repository: `AdrianLipa90/cielingo-canon`, parent `c80fa0227d6b6b41dcb10b16b1527b7d40692d63`.
- GREMLIN repository: `AdrianLipa90/GREMLIN`, observed baseline `86059ead6177fbb5bf33211f674781883a149a57`.
- GREMLIN reference core contract: 33 MCP tools plus dynamically discovered extensions from `server_with_hive`.

## CIELingo hierarchy

The computational vocabulary is:

`KAKU -> RADYKAŁ -> KONCEPT -> ZDANIE -> AKAPIT -> ROZDZIAŁ -> KSIĄŻKA`

The hierarchy is deliberately abstract. A concrete biological mapping is a hypothesis carried with an evidence class, not a canonical identity. Candidate interpretations include primitive symbol/relation, motif, motif-composition concept, local regulatory module, locus-scale regulatory context, larger chromatin domain, and chromosome/genome-scale context.

## Relational phase

For a spacing `d` in base pairs and a local helical period `h`, the model exposes

`phi(d;h) = 2*pi*d/h mod 2*pi`.

The v0.1 default `h = 10.5 bp` is a modelling default, not a universal biological constant. Callers may supply a different measured/local period. Phase is therefore an explicit derived feature that can be ablated or falsified.

## Evidence discipline

Every node/relation is tagged `OBSERVED`, `DERIVED`, or `HYPOTHESIS`. The task envelope asks GREMLIN to:

1. build the relation graph;
2. separate observation, derivation, and hypothesis;
3. search for counterexamples;
4. derive falsifiable phase predictions;
5. design an ablation against a sequence-only baseline.

No successful local fit promotes the model to biological fact.

## Full GREMLIN bridge

The bridge dynamically discovers the MCP registry instead of hard-coding the complete evolving Bestiary/Hive surface. It requires the known 33-tool GREMLIN reference core, verifies that `canon_allowed` remains false, verifies RAPHAEL in the governance topology, and retains every additional discovered tool as an extension.

The default bridge mode is `ADVISORY`. Read-only/advisory operations may be dispatched. Mutating, governance, FERRET, Hive-write, worker-write, or future unknown tools require both:

- bridge mode `AUTHORIZED_ACTUATION`; and
- a narrow `ActuationGrant` naming the exact tool.

CIELingo retains language-semantic ownership. GREMLIN does not gain CIELingo canon, NOEMA `CURRENT`, memory-write, code-promotion, or external-actuation authority from this bridge.

## Initial Bestiary route

The genomic project envelope recommends:

`OCTOPUS, SPIDER, BAT, HOUND, MOLE, OWL, FOX, BEAVER, BELZEBUB, GREMLIN, RAPHAEL`.

The first advisory phase uses routing, guarded/relational research and PhaseNav analog-invariant analysis. FERRET and Hive mutation are disabled by default.

## First falsifiable benchmark

Given experimentally measured regulatory constructs that preserve motif content while varying spacer length, compare at minimum:

- sequence-only baseline;
- sequence + absolute spacing;
- sequence + orientation;
- sequence + helical phase;
- full relational graph.

A phase contribution is supported only if it improves held-out prediction robustly and its fitted period/phase survives controls, alternative local helical periods and multiple-testing correction. Failure to improve out-of-sample prediction counts against the phase-layer hypothesis.
