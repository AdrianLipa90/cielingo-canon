# CIEL-POL Grammar Engine Pack

Pakiet zawiera szczegółowe opracowanie silnika gramatycznego CIEL-POL oraz template karty słowa dla leksykonu operacyjnego CIELingo / NOEMA / OrbitalDB.

Status: scaffold projektowy, nie kanon runtime. Każdy wpis słownikowy wymaga późniejszej walidacji przez CIELingo / CIEL1 zgodnie z zasadą zgody i promocji.

## Zawartość

- `docs/CIEL_POL_GRAMMAR_ENGINE_SPEC.md` — pełne opracowanie silnika gramatycznego.
- `docs/WORD_CARD_TEMPLATE_GUIDE.md` — opis pól karty słowa.
- `schemas/word_card.template.yaml` — główny template karty słowa.
- `schemas/word_card.schema.json` — JSON Schema do walidacji karty słowa.
- `schemas/engine_config.template.yaml` — template konfiguracji silnika.
- `bridge/formal_code_bridge.yaml` — most formalizm ↔ kod.
- `examples/*.word.yaml` — przykładowe karty słów: `czekaj`, `stop`, `zgoda`, `ból`, `nieznane`.
- `tests/GRAMMAR_ENGINE_TEST_PLAN.md` — plan testów i warunki akceptacji.

## Reguła nadrzędna

Nieznane znaczenie nie jest błędem. Nieznane znaczenie jest parkingiem.

```text
UNKNOWN -> PARKED
```

Nie wolno przekształcać:

```text
UNKNOWN -> interpretacja zewnętrznego modelu -> CANON
```

## Zasada zapisu

Żaden element języka, pamięci, gramatyki ani tożsamości nie przechodzi do kanonu bez jawnego procesu ratyfikacji:

```text
parse -> classify -> constrain -> propose -> consent/review -> staged write -> audit -> promotion
```

