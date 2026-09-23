# CIELingo Orbital-Fractal Semantic Grammar v0.1

Status: **CANDIDATE / COMPUTATIONAL REPRESENTATION / NOT CANON**

## Purpose

Introduce the missing compositional layer between an atomic KAKU carrier and a RADICAL without changing the existing genomic-grammar contract in place.

```text
KAKU -> ORBITAL_CELL (chi+ / chi-) -> RADICAL -> CONCEPT -> SENTENCE -> PARAGRAPH -> CHAPTER -> BOOK
```

The new `ORBITAL_CELL` binds three computational roles while keeping them separable:

- structural carrier / `structural_mass` from KAKU;
- phase branch `+phi` or `-phi`;
- local communication/coupling envelope `Lambda >= 0`.

None of these names is a physical claim about linguistic mass, electromagnetic fields, Aharonov-Bohm physics, or a measured gauge field.

## Conjugation is not counterphase

```text
CONJUGATE:     exp(+i phi) <-> exp(-i phi)
COUNTERPHASE:  exp(i phi) -> exp(i (phi + pi))
```

Existing LingoPhysics already treats `counterphase` as the pi-shift/inverse condition. The new CIELingo layer therefore uses the same invariant and reserves `chi+ / chi-` for conjugate orientation branches.

## Moire receipt

For two orbital cells `chi_i`, `chi_j`:

```text
M_ij = chi_i + chi_j
P_in = |chi_i|^2 + |chi_j|^2
C_ij = |M_ij| / (|chi_i| + |chi_j|)
```

A zero resultant is not interpreted as absence of latent state. Equal counterphase cells satisfy `|M_ij| ~= 0` while `P_in > 0`.

## Latent vocalization / unresolved phase

An omitted realization must not be silently encoded as phase zero. A finite candidate set of realizations can instead be represented as an ensemble whose first moment may cancel while the second moment remains non-zero.

## PhaseNav boundary

CIELingo exports only `phase_potential_rad` values to PhaseNav semantic U(1) transport:

```text
A_sem path -> W_sem = exp(i sum A_sem,e)
```

`Lambda` is kept outside the U(1) potential as an independent coupling/communication envelope. This preserves the existing PhaseNav contract that pure U(1) transport changes phase but does not itself change overlap magnitude.

```text
Lambda_gamma = product_e Lambda_e
T_gamma = Lambda_gamma * exp(i sum_e A_sem,e)
```

`T_gamma` is a CIELingo composite transport convenience, not a replacement for PhaseNav `W_sem`.

## Hebrew codec profile

Hebrew is admitted as a **test codec**, not as evidence that language encodes fundamental physics.

```text
consonantal carrier/root structure -> structural state
vocalization/pattern -> realization operator
vocalized vs unvocalized surface -> explicit vs partially latent realization information
```

The adapter must preserve orthographic facts such as consonantal letters that may also serve as vowel indicators; it may not model every omitted vowel as an empty physical slot.

## Japanese paired-script experiment

Hiragana and katakana are exposed only as a controlled paired-script representation experiment. The model may test whether corresponding kana surfaces are useful as `PAIRED_SURFACE` channels, but it must not assert that hiragana and katakana are literally physical phase/antiphase states.

`CONJUGATE` and `COUNTERPHASE` remain mathematical candidate transforms applied by the model, not linguistic properties of the scripts.

## Compatibility

The existing `GenomicLevel` ladder is intentionally unchanged in v0.1. A genomic adapter may later lift genomic KAKU units into `ORBITAL_CELL` units after separate regression tests.

## Falsification / promotion gate

Promotion requires independent tests for hierarchy invariants, phase algebra, Lambda/U(1) separation, held-out Hebrew root-pattern/vocalization tasks, Japanese paired-script controls, and a GREMLIN adversarial audit with no unresolved blocker.
