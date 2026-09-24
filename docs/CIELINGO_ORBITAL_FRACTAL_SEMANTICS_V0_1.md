# CIELingo Orbital–Fractal Semantic Grammar v0.1

Status: **CANDIDATE_ONLY**  
Date: 2026-09-24  
Canon: **not allowed**

## Purpose

Introduce an explicit layer between atomic surface units and radical/root states:

\[
\mathrm{KAKU}\rightarrow \chi \rightarrow \mathrm{RADICAL}\rightarrow \mathrm{CONCEPT}\rightarrow \mathrm{SENTENCE}.
\]

The missing \(\chi\) layer is an orbital cell carrying three independent computational coordinates:

\[
\chi_i =
m^{surface}_i\,\Lambda_i\,e^{i\theta_i}.
\]

- \(m^{surface}\): **surface structural mass**, not the existing LingoPhysics semantic mass \(m_s\);
- \(\Lambda\): communication/coupling coefficient on the local semantic surface;
- \(\theta\): phase coordinate used for transport/interference;
- channel metadata distinguishes phase duals.

No physical mass, electromagnetic field, Aharonov–Bohm field, or cosmological \(\Lambda\) is claimed.

## Dual channel correction

Two transformations are kept distinct:

\[
\text{conjugate: }\theta\mapsto-\theta,
\]

\[
\text{antiphase: }\theta\mapsto\theta+\pi.
\]

They are not equivalent in general. The earlier hiragana/katakana analogy is therefore treated only as inspiration for a dual carrier representation, not evidence that those scripts are physically phase/antiphase channels.

## Radical

A radical is an **ordered** bound sequence of orbital cells. Order is preserved explicitly through an ordered phase moment; the complex resultant alone is not treated as sufficient.

## Concept

A concept is a radical plus a morphology/realization operator:

\[
C = \Lambda_C R\,e^{i\phi_M}.
\]

This does not replace CIELingo concept cards. It provides a lower-level construction that may feed them.

## Sentence

A sentence is a graph of concept states and typed relation edges. Each relation may emit a scalar edge potential \(A_e^{sem}\). The packet

\[
(A_{e_1}^{sem},\ldots,A_{e_n}^{sem})
\]

is directly compatible with the existing PhaseNav semantic U(1) interface:

\[
W_{sem}[\gamma] = \exp\left(i\sum_{e\in\gamma}A_e^{sem}\right).
\]

CIELingo does **not** reimplement PhaseNav holonomy; it only emits candidate edge potentials.

## Hebrew codec

Hebrew is added as a **candidate structural codec**, not as a validated semantic oracle.

Consonant KAKU units use ordinary gematria values as raw scalar coordinates. A bounded monotone transform becomes `surface_structural_mass`. Niqqud marks are mapped to candidate computational phase coordinates. Missing written vowels are marked `latent` and represented by an unresolved phase ensemble rather than forced to numerical zero.

This preserves the distinction:

\[
0_{\text{explicit vowel mark}}\neq 0_{\text{latent potential}}.
\]

The mapping of niqqud to phase coordinates is computational and falsifiable; it is not claimed to be traditional Hebrew numerology or physical phase.

## Moiré

Moiré is represented as normalized interference between two equal-length complex lattices:

\[
M_k=\frac{|a_k+b_k|}{|a_k|+|b_k|}.
\]

It is a representation operator, not a claim that language literally forms a condensed-matter moiré material.

## Epistemic boundary

The module is designed to test whether:
1. lower-level structural states improve semantic invariance,
2. phase/antiphase channels carry reproducible grammatical information,
3. Hebrew root/vocalization structure gives a useful codec,
4. emitted edge potentials align with PhaseNav U(1) semantic holonomy,
5. any signal survives shuffled/null encodings.

Promotion requires independent corpus-scale validation and null-model controls.
