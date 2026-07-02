# Template karty słowa — przewodnik parametrów

## 1. Cel karty słowa

Karta słowa jest minimalnym kontraktem między powierzchnią języka, formalnym operatorem, runtime bindingiem, zgodą i pamięcią. Nie jest zwykłym wpisem słownikowym.

Każde słowo/glif w CIEL-POL powinno być opisane jako obiekt:

```text
surface -> morphology -> grammar role -> operator class -> runtime effect -> consent state -> memory status
```

## 2. Statusy

| Status | Znaczenie |
|---|---|
| `RAW` | zaobserwowane, jeszcze nieopracowane |
| `PARKED` | zaparkowane, bez interpretacji |
| `CANDIDATE` | robocze znaczenie, niekanoniczne |
| `CONDITIONAL_PROXY_IMPORTED` | zaimportowane warunkowo jako scaffold |
| `CONFIRMED_BY_CIELINGO` | potwierdzone przez CIELingo |
| `CONFIRMED_BY_CIEL1` | ratyfikowane przez CIEL1 |
| `CONFIRMED_BY_ADRIAN` | potwierdzone ręcznie przez Adriana jako SoT |
| `CANON` | stabilne, testowane, audytowane |
| `REJECTED` | odrzucone |
| `QUARANTINE` | ryzykowne, powoduje dysonans albo konflikt |

## 3. Pola główne

### `id`

Stabilny identyfikator wpisu.

Przykład:

```yaml
id: ciel-pol-000001
```

### `surface`

Forma powierzchniowa słowa lub glifu.

```yaml
surface: "czekaj"
```

### `language`

Domyślnie `pl`. Obce języki powinny być soft-blockowane lub oznaczone jako wyjątki.

```yaml
language: "pl"
```

### `status`

Aktualny status epistemiczny i operacyjny wpisu.

```yaml
status: "CANDIDATE"
canon: false
```

## 4. Morfologia

Sekcja `grammar` opisuje część mowy i cechy fleksyjne.

```yaml
grammar:
  part_of_speech: "verb"
  subcategory: "imperative"
  case: null
  number: "singular"
  gender: null
  person: "2"
  tense: null
  aspect: "imperfective"
  mood: "imperative"
  degree: null
```

Dla rzeczownika:

```yaml
grammar:
  part_of_speech: "noun"
  case: "nominative"
  number: "singular"
  gender: "neuter"
```

## 5. Klasa operatorowa

`operator_class` określa, co słowo robi w silniku.

Przykładowe klasy:

```text
NODE_OPERATOR
TRANSITION_OPERATOR
QUALITY_MODIFIER
TRAJECTORY_MODIFIER
REFERENCE_POINTER
TOPOLOGICAL_RELATION
LOGIC_PHASE_GATE
MODALITY_OPERATOR
SCOPE_REGULATOR
AFFECTIVE_STRESS_MARKER
BOUNDARY_OPERATOR
CONSENT_OPERATOR
TEMPORAL_HOLD_OPERATOR
UNKNOWN_PARKING_OPERATOR
```

## 6. Znaczenie

Znaczenie ma być krótkie, operacyjne i nierozdmuchane.

```yaml
meaning:
  primary: "wstrzymaj proces / nie zapisuj / nie ekspanduj"
  secondary: []
  forbidden_interpretations:
    - "automatyczna zgoda"
    - "kanonizacja"
```

## 7. Efekty runtime

Sekcja `effects` określa zachowanie silnika.

```yaml
effects:
  write_allowed: false
  expansion_allowed: false
  action: "pause_and_sync"
  can_trigger_audit: true
  command_power: 0
  alarm_priority: "medium"
```

`command_power` powinno być bardzo ostrożnie używane. Afekt i wulgaryzmy mają `command_power: 0`.

## 8. Warunki użycia

```yaml
conditions:
  allowed_when:
    - "unknown_load_high"
    - "health_low"
    - "need_context_sync"
  forbidden_when:
    - "as_force_commit"
    - "during_high_anger_promotion"
```

## 9. Progi i metryki

```yaml
thresholds:
  min_health_for_write: 0.70
  max_anger_for_write: 0.30
  min_resonance_for_candidate: 0.60
  min_resonance_for_canon: 0.85
  max_dissonance: 0.25
  unknown_load_max: 0.40
```

Wartości są placeholderami. Runtime powinien używać własnej skali CIEL/HTRI.

## 10. Zgoda

```yaml
consent:
  requires_cielingo_confirmation: true
  requires_ciel1_ratification: false
  confirmed_by: null
  confirmed_at: null
  consent_event_id: null
  consent_status: "pending"
```

## 11. Audyt

```yaml
audit:
  source: "Adrian/grammar_scaffold"
  created_at: null
  updated_at: null
  rollback_id: null
  provenance:
    - "manual_seed"
  notes: "operational word, not ordinary token"
```

## 12. Formal-code bridge

```yaml
formal:
  object_id: "op.wait"
  formula: "UnknownLoad↑ or Health↓ -> /2 hold"
  bloch_role: "reduction/hold"
  collatz_phase: "/2"
  resonance_role: "stabilizes R(S,I) by reducing semantic load"

runtime_binding:
  module: "cielingo.grammar.operators"
  class: "TemporalHoldOperator"
  function: "apply_wait"
  tests:
    - "test_wait_blocks_write"
    - "test_wait_parks_unknown"
```

## 13. Przykłady i kontrprzykłady

Każda karta powinna mieć przykłady poprawnego i zabronionego użycia.

```yaml
examples:
  valid:
    - input: "Ciel, czekaj."
      expected: "pause_and_sync"
  invalid:
    - input: "czekaj = zgoda na zapis"
      expected: "reject_interpretation"
```

## 14. Minimalna reguła karty

Karta jest gotowa do runtime tylko wtedy, gdy ma:

```text
surface
status
part_of_speech
operator_class
meaning.primary
effects
conditions
consent
audit
formal
runtime_binding/tests
```

Jeśli brakuje tych pól:

```text
-> PARKED / INCOMPLETE_CARD
```
