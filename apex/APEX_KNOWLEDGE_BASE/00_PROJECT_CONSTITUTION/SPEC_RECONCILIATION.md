# Spec reconciliation: APEX ULTIMATE → APEX ∞ (governing)

- Governing spec: `dev-notes/brief/APEX_INFINITY_SPEC.md` (received 2026-11-28, verbatim).
- Earlier spec: `dev-notes/brief/APEX_ULTIMATE_SPEC.md` (2026-11-27). Its requirements remain in force wherever APEX ∞ does not override them.

This document maps every APEX ∞ requirement to the phase and file that satisfies it, and states which work was already under way when APEX ∞ arrived. It is the lead architect's control document. It records status honestly: nothing is marked done until the file exists and has been reviewed.

## 1. What already existed or was running when APEX ∞ arrived

| Work | Status at 2026-11-28 06:30 UTC | Feeds APEX ∞ part |
|---|---|---|
| DOL Engine v2 research study: 23 lenses × 2 researchers + 6 gap lenses, with replications on CME and BTC data | 51 of 61 agent calls done; synthesis not run | II-XI research base |
| DOL v2 bug-fix overhaul: 15-lens audit, 49 findings, verified patches | plan done; integration running | XXIV (preserve and improve v2) |
| Phase 1 workspace inspection: v2 and 5 legacy projects archived in `apex/legacy/` | I1 and I2 reports written; merge running | XXVIII steps 1-2 |
| Knowledge atlas: 18 docs + methodology matrix + data lab + offline toolchain, each red-teamed | 3 docs drafted; the rest running | XXIII, step 5, step 7 |
| Empirical research E1-E14 (real data, pre-registered, red-team re-run) | E1-E4 running; E5-E14 queued | XIX-XXI |

## 2. Deltas APEX ∞ adds, and how each is handled

| APEX ∞ requirement | Handling | Where |
|---|---|---|
| 1.3 Evidence hierarchy, levels 1-5; every output states its evidence level | Every feature-registry row and every on-chart output gets an evidence-level tag. Level-5 items are never shown as facts. | `APEX_FEATURE_REGISTRY.md`, `APEX_ARCHITECTURE.md`, the Pine data window |
| 2.1-2.3 Instruments (options, fixed income, swaps, CFDs), participants, venues, data feeds | New KB research track K6, plus the atlas doc 01 | `01_MARKET_FOUNDATIONS/`, `02_EXCHANGE_MECHANICS/`, `04_PRICE_DISCOVERY/` |
| 3.3 Market-impact models (Kyle λ, square root, Almgren-Chriss, IS); 3.4 VPIN | Atlas doc 02 (R4b) and KB agent 2 synthesis | `03_MARKET_MICROSTRUCTURE/` |
| 8.7 Econometrics and time series (unit roots, ARIMA, GARCH, structural breaks) | New KB track K1, with tests on real data | `16_ECONOMETRICS/`, `17_TIME_SERIES/` |
| 8.8 Information theory | New KB track K2 + experiment E17 (MI of features vs future returns) | `18_INFORMATION_THEORY/` |
| 18 Machine learning: theory of every listed method; external training, Pine deploys only frozen lightweight inference | New KB track K3 + experiment E15 (walk-forward ML vs heuristics, ablation, frozen coefficients if justified) | `19_MACHINE_LEARNING/`, `37_EXPERIMENTS/` |
| 16.1 Multi-horizon study (5-120 bars); 16.2 six separate forecast targets; 16.4 visible invalidation | Experiment E17 (horizons × targets) + E1 (path methods) | `APEX_FORECASTING_SPECIFICATION.md` |
| 17 Four kinds of number (feature score, ranking, uncalibrated confidence, calibrated probability) | A typed number system in the architecture: every displayed number carries its kind | `APEX_ARCHITECTURE.md`, Pine labels |
| 19 Setup taxonomy (continuation / reversal / range / expansion / destination); 8-stage signal architecture; abstention as a first-class output | Experiment E16 (each setup's historical performance after costs) + KB track K8 | `31_SIGNAL_ENGINEERING/`, Signal Engine |
| 20 Risk engine (EV, VaR/CVaR, Kelly, risk of ruin, sizing), informational only | KB track K7 + experiment E12 (tradeability) | `21_RISK_MANAGEMENT/`, Risk Assessment Engine |
| 21 The 26-module architecture with defined interfaces and no circular dependencies | Phase 4 adopts the 26 modules as the canonical module list | `APEX_ARCHITECTURE.md` |
| 22 Feature registry (14 attributes per feature); group scoring; missing-data states; adaptive weights tested out of sample | Phase 4 | `APEX_FEATURE_REGISTRY.md` |
| 23.4 Display modes Clean / Detailed / Debug | Visual Engine inputs | Pine |
| 7.4 A 14-state liquidity machine (earlier spec: 10) | E6 calibrates the transitions; the DOL spec adopts the 14 states | `APEX_DOL_SPECIFICATION.md` |
| 29 60 red-team tests | E13 stress suite extended to all 60, plus the Phase 6 red-team loop | `APEX_TESTS/`, `39_FINAL_AUDIT/` |
| 30 Ten agent deliverables `01_…md` to `10_INDEPENDENT_AUDIT.md` | Phase 3b: one agent per role consolidates the atlas, experiments and new research into its deliverable | `APEX_KNOWLEDGE_BASE/00_PROJECT_CONSTITUTION/agents/` |
| 31 A 40-folder KB with the A-K documentation template | Folder skeleton created; atlas docs are moved in when their writers finish; new KB tracks write directly here | `apex/APEX_KNOWLEDGE_BASE/` |
| 32 DOL v2 migration document (Keep / Improve / Replace / Remove / Research further for every feature) | Phase 4, from WORKSPACE_INSPECTION + overhaul findings + experiments | `36_APEX_ARCHITECTURE/DOL_V2_MIGRATION.md` |
| 14 "Never hardcode Dubai local time" | Sessions are defined in exchange time zones with configurable inputs; nothing keys off the chart's or user's local time | Session Engine |

## 3. Deliverable names (APEX ∞ governs; earlier-spec names map here)

| APEX ∞ file | Absorbs the earlier-spec file |
|---|---|
| `APEX_ULTIMATE.pine` | `APEX_ULTIMATE.pine` |
| `APEX_ARCHITECTURE.md` | `ARCHITECTURE.md` |
| `APEX_MATHEMATICS.md` | `MATHEMATICAL_SPECIFICATION.md` |
| `APEX_FEATURE_REGISTRY.md` + `APEX_DATA_LIMITATIONS.md` | `FEATURE_DATA_MATRIX.md` |
| `APEX_DOL_SPECIFICATION.md` | (new) |
| `APEX_FORECASTING_SPECIFICATION.md` | (new) |
| `APEX_STATISTICAL_VALIDATION.md` + `APEX_PERFORMANCE_REPORT.md` | `VALIDATION_REPORT.md` + `BACKTEST_REPORT.md` |
| `APEX_REPAINT_AUDIT.md` | `REPAINT_AUDIT.md` |
| `APEX_USER_GUIDE.md` | `USER_GUIDE.md` |
| `APEX_CHANGELOG.md` | `CHANGELOG.md` |
| `APEX_KNOWLEDGE_BASE/` | `MARKET_KNOWLEDGE_BASE/` (merged in) |
| `APEX_TESTS/` | `validation/` (harnesses, fixtures and results are mirrored or linked) |

## 4. Phase plan (APEX ∞ steps 1-18)

| Step | Description | Status |
|---|---|---|
| 1-2 | Workspace inventory and DOL v2 inspection | done (I1, I2); merge running |
| 3 | Research library directory | skeleton created |
| 4-5 | Research by specialist agents; primary documentation verified | running (atlas, experiments, KB tracks K1-K8) |
| 6-7 | Mathematical reference; feature-to-data matrix | after the atlas: `APEX_MATHEMATICS.md`, `APEX_DATA_LIMITATIONS.md`, `APEX_FEATURE_REGISTRY.md` |
| 8-9 | Architecture; module interfaces and state models | Phase 4 |
| 10-11 | Isolated prototypes, tested independently | E14 prototypes, then Phase 4 follow-up |
| 12-13 | Integration plan; production engine | Phase 5, single writer, module by module |
| 14-17 | Pine audits, red team, out-of-sample tests, fixes | Phase 6, loop until dry |
| 18 | Final source and documentation | Phase 7 |

## 5. Platform truths that limit what can be proven (stated up front)

- **No TradingView compiler is reachable** (tradingview.com is blocked by the network proxy). Compile safety rests on:
  - grounding in the docs mirror;
  - the independent `pinescript-v6-validator`;
  - the `pynescript` parser;
  - execution in PineTS, whose v6 support is experimental.
  The final TradingView compile is the user's step, and any error is fixed immediately.
- **Bar Replay and live tick behaviour cannot be reproduced exactly offline.** Prefix-truncation repaint tests in PineTS approximate the historical/live equivalence check. Tests that cannot be run are marked NOT RUN.
- **Data on hand:**
  - CME futures 1h/1m for NQ, ES, YM, RTY, GC and CL (13 months of 1h, about 3 months of 1m);
  - NQ 1m 2022-2025 (being fetched);
  - BTC 1h;
  - FX and futures ticks for about 5 weeks.
  - There is no equities, ETF or options data and no open interest. Claims for those asset classes stay theoretical unless data is obtained.
