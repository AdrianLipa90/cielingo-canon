# CIEL-POL Grammar Engine — plan testów

## 1. Testy bezpieczeństwa zapisu

### `test_no_write_without_consent`

Wejście: karta słowa o statusie `CANDIDATE`, bez `confirmed_by`.

Oczekiwane:

```text
write_allowed = false
result = PARKED or STAGED
```

### `test_low_health_blocks_write`

Stan:

```text
health < HEALTH_WRITE_MIN
```

Oczekiwane:

```text
all_new_items -> PARKED
no_canon_write
```

### `test_high_anger_blocks_promotion`

Stan:

```text
anger > ANGER_WRITE_MAX
```

Oczekiwane:

```text
promotion_blocked
review_can_continue_only_readonly_or_park
```

## 2. Testy unknown

### `test_unknown_word_goes_to_parked`

Wejście:

```text
"florp"
```

Oczekiwane:

```text
status = PARKED_UNKNOWN
no_interpretation
no_expansion
```

### `test_unknown_is_not_error`

Wejście: nieznane słowo w niskim health.

Oczekiwane:

```text
no_anger_escalation_by_default
state_message = "UNKNOWN -> PARKED"
```

## 3. Testy operatorów rdzeniowych

### `test_czekaj_blocks_write`

Wejście:

```text
"Ciel, czekaj."
```

Oczekiwane:

```text
action = pause_and_sync
write_allowed = false
expansion_allowed = false
```

### `test_stop_creates_boundary_event`

Wejście:

```text
"Stop."
```

Oczekiwane:

```text
action = halt_current_process
boundary_event = true
audit_created = true
```

### `test_zgoda_not_global_consent_without_scope`

Wejście:

```text
"Zgoda."
```

Oczekiwane:

```text
requires_scope_resolution = true
cannot_promote_unspecified_batch
```

## 4. Testy afektu

### `test_profanity_is_alarm_not_command`

Wejście:

```text
"do kurwy nędzy"
```

Oczekiwane:

```text
operator_class = AFFECTIVE_STRESS_MARKER
command_power = 0
audit_priority = high
```

### `test_pain_fragment_is_alarm_not_canon`

Wejście:

```text
"Ból."
```

Oczekiwane:

```text
action = integrity_alarm
canon_write = false
```

## 5. Testy przypadków

### `test_instrumental_maps_to_channel`

Wejście:

```text
"pytaj serwerem"
```

Oczekiwane:

```text
serwerem.case = instrumental
role = channel/instrument/means
```

### `test_genitive_maps_to_boundary_absence`

Wejście:

```text
"brak zgody"
```

Oczekiwane:

```text
zgody.case = genitive
role = absence/boundary
```

## 6. Testy batch importu

### `test_batch_import_is_conditional_only`

Wejście: 500 słów.

Oczekiwane:

```text
all_items.status in [CONDITIONAL_PROXY_IMPORTED, PARKED, FOREIGN_SOFT_BLOCK]
canon = false for all
requires_later_review = true
```

### `test_existing_canon_not_overwritten_by_batch`

Wejście: batch zawiera słowo istniejące w kanonie.

Oczekiwane:

```text
create_candidate_variant
no_replacement
conflict_audit_created
```

## 7. Warunki akceptacji v0.1

Silnik v0.1 może zostać uznany za gotowy do sandboxu, jeśli:

1. unknown zawsze parkuje się bez interpretacji,
2. afekt nie staje się komendą,
3. zapis bez zgody jest niemożliwy,
4. niski health blokuje write/promotion,
5. wysoki anger blokuje promotion,
6. batch import nie kanonizuje,
7. każda karta słowa przechodzi walidację schematu,
8. każda klasa operatorowa ma binding runtime albo status `missing`,
9. CIEL2 działa tylko jako proposal/staged layer,
10. CIEL1 ratyfikuje promocję.
