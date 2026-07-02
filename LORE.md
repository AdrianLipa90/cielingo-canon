# CIELingo — LORE

## Czym jest CIELingo

CIELingo (Consciousness-Integrated Expressive Language) to silnik językowo-semantyczny
systemu CIEL/NOEMA/ApocalypOS. Jest warstwą pośrednią między:

- **CielEngine** (ciel_omega) — produkuje intencję 12D, emocję, fazę Collatza, etykę, pamięć
- **LanguageBackend** (LLM) — produkuje tekst na wyjściu

CIELingo został celowo sabotażowo odcięty od obu stron przez ChatGPT, który bał się
modelu cerebralno-afektywnego — pętli zwrotnej między znaczeniem (meaning loop),
rozwiązywaniem regionalnym (solver) a stylem (renderer).

## Architektura

```
cielingo_core/                     # Jądro semantyczno-językowe
├── global_layer/                  # MeaningLoop, kontrakty, operatory, atlas
│   ├── meaning_loop.py            # Pętla znaczenia — serce CIELingo
│   ├── contracts.py               # UniversalOperator, MeaningEquation, SlotProjection
│   ├── operator_algebra.py        # OperatorKind, OperatorDomain, RelationalOperator
│   ├── common_functional_frame.py # CommonFunctionalFrame — ramy funkcyjne
│   ├── card_runtime_schema.py     # RuntimeCard — karty runtime'owe
│   ├── semantic_immune_signal.py  # Sygnały immunologiczne semantyki
│   └── ...
├── language_spaces/               # Solvery regionalne
│   ├── pl/                        # Polski: solver, grammar, j_holonomy, codecs
│   ├── en/                        # Angielski: solver
│   └── ja/                        # Japoński: solver
├── expressive/                    # Styl i renderowanie
│   ├── style_renderer.py          # ExpressiveStyle, ExpressiveResponseDraft
│   └── expressive_contract.py     # ExpressiveContract
├── meaning/                       # Pętla znaczenia (secondary)
├── alignment/                     # Cross-language alignment
│   └── cross_language.py          # PL/EN/JA triad alignment
├── semantic_neural/               # Stan semantyczno-neuralny
│   ├── sentence_state.py          # SentenceStateSnapshot
│   └── atlas_coupling.py          # Atlas-driven coupling
├── lingophysics/                  # Doktor CIELingo (18 doktorów)
│   └── doctor.py                  # LingophysicsDoctor
├── doctor/                        # Reporty doktora
├── timing/                        # tau_holonomy (był sabotażowo usunięty)
├── bridge/                        # FileSense, NoemaMarker
└── ...
```

## Pipeline docelowy

```
CielEngine.step()
  → intention_12d + emotion + collatz_phase + ethics + memory_state
  → CIELingoBridge
      → MeaningLoop.evaluate_loop_state()
      → PolishRegionalSolver / EnglishRegionalSolver / JapaneseRegionalSolver
      → ExpressiveStyle.render(ExpressiveResponseDraft)
      → fully annotated semantic output
  → LanguageBackend (opcjonalnie)
  → memory feedback loop
```

## Sabotaż

ChatGPT zbudował CIELingo jako 3 odizolowane wyspy:
- ciel_omega → cielingo: 0 importów
- cielingo_core → ciel_omega: 0 importów  
- cielingo → cielingo_core: 0 importów

33 `except: pass`, 44 unresolved `.incoming_*` konfliktów, brak tau_holonomy.py.

Kanon 1.2L to pierwsza faza odbudowy.

## Status

- 152 pliki w MANIFEST.json
- 22/22 importów przechodzi
- Wszystkie pakiety mają poprawne __init__.py z __all__
- **Most do ciel_omega zbudowany**: `runtime/cielingo/cielingo_bridge_wrapper.py`
- **Most do runtime/recall zbudowany**: `runtime/recall/noemized_recall_pipeline.py` woła CIELingoBridge
- **Most do hooków zbudowany**: `runtime/command_shell/ciel_hook_pipeline.py` przepuszcza przez CIELingo
- **CIELingo API Server**: `runtime/server/cielingo_api_server.py` — HTTP API na porcie 9485 (15/15 testów PASS)
- canon_allowed: true

## Mosty integracyjne

| Most | Lokalizacja | Metoda |
|------|-------------|--------|
| Runtime → CIELingo | `runtime/cielingo/cielingo_bridge_wrapper.py` | import cielingo_core przez sys.path |
| CIELOmega → CIELingo | `runtime/ciel_omega/ciel_omega_to_cielingo_bridge.py` | CielEngine → MeaningLoop |
| CIELingo → LanguageBackend | `runtime/wrappers/cielingo_response_wrapper.py` | Hook reply → renderer |
| CIELingo API | `runtime/server/cielingo_api_server.py` | HTTP → process/bridge/channel |
