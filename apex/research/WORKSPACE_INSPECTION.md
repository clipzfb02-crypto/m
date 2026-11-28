# APEX ULTIMATE · Phase 1 workspace inspection (official deliverable)

Lead inspector's merge of the two Phase 1 inspection reports, with spot-checks.
- First drafted 2026-11-27. That pass was cut off by a usage limit.
- Completed and re-verified 2026-11-28 in a resume pass. Every [lead] check in §0.2 was re-run in that pass unless the row says otherwise, and the newer study material was added (§0.3).

- **I1 · DOL lineage:** `apex/research/inspection/I1_dol_lineage.md`. Covers DOL Engine v2, the early DOL Engine and Liquidity Flow Pro.
- **I2 · Signal and backtest lineage:** `apex/research/inspection/I2_signal_lineage.md`. Covers XAUUSD Fast/Balanced Pro, the Buy/Sell Indicator and the MNQ 5m ORB project.

Both reports stay in place as the detailed evidence. This file is the single Phase 1 reference for the architect (Phase 4). No source file was modified.

---

## 0. Method, spot-checks and honesty notes

### 0.1 Labels used in this report
- **Concept class.**
  - **E**: established market mechanics, exchange or platform documentation.
  - **A**: academic or statistical evidence.
  - **D**: discretionary practitioner theory.
  - **C**: contested, or unsupported by tests.
- **Evidence grade:** strong, moderate, weak or none.
- **Where a statement comes from:**
  - **[I1]** or **[I2]**: the inspector's report.
  - **[lead]**: I checked it myself in this session.
  - **[study: key §]**: a study report (`<scratchpad>/brief/study/<key>.final.md`) whose B researcher verified it.
  - **[claim]**: a legacy README says so, but the code that produced the number was never committed, so it cannot be re-run.
  - **[ran]**: executed in this session, by the inspector named or by me.
  - **[doc]**: checked against the local Pine v6 docs mirrors.
- **Scores are not probabilities.** In this report, "PoT" names the legacy readout. It is a probability only where Section 6, conflict C2, says so.

### 0.2 What I spot-checked, and what changed as a result

| # | Claim checked | How | Result |
|---|---|---|---|
| S1 | Every file in `apex/legacy/` is byte-identical to its origin commit | `git show <commit>:<path> \| cmp` for every copied file | **Confirmed**, 22 of 22. The folder holds 23 files; the 23rd is the index `README.md`, which has no origin. The first draft said "23 of 23"; corrected [lead] |
| S2 | The v2 legacy copy equals the frozen baseline `<scratchpad>/brief/baseline_v2.pine` | `diff -q` | **Confirmed**. The live `indicators/dol_engine.pine` is also byte-identical today, but the bug-fix pass may change it, so every v2 line number here refers to the frozen copy [lead] |
| S3 | About 45 v2 line references (e.g. 37, 404, 434, 447, 466, 564, 570, 597, 623, 650, 661, 691-693, 865, 917, 923-925, 1141, 1211, 1230, 1314, 1376, 1441, 1518, 1580-1582, 1891-1894, 1945-1947, 2066, 2084, 2214-2226, 2295-2307, 2390) | `sed -n` on the frozen copy | **All match** [lead] |
| S4 | Line references in the other legacy files: early engine 180-181, 353, 490, 731, 734, 886, 922, 964, 1034, 1053, 1098, 1330, 1550, 1583-1585, 1637, 2032, 2423; LFP 12-13, 55, 61, 104, 299, 336, 461, 554, 784, 885, 1045, 1300, 1320, 1324; XAUUSD 99, 131-147, 154, 212-218, 245, 360, 382, 395, 450, 458-459, 515, 681, 725, 731-746, 1162; Buy/Sell 1, 116; ORB 65, 152, 201; `bt.py` 76 | `sed -n` | **All match** [lead] |
| S5 | The 49 overhaul findings: 18 P1 and 31 P2, of which 3 are verified | Counted `dev-notes/runs/overhaul-r1-findings.md` | **Confirmed** [lead] |
| S6 | v2 has 104 inputs and never uses `display.none`. The early engine has 186 inputs and LFP 96 | `grep -c` | **Confirmed**. XAUUSD has 86 and the ORB indicator 23 [lead] |
| S7 | XAUUSD `f_killLines` (731-746) reassigns globals inside a function, which is a compile error | Read the code (globals declared at 725) and the docs | **Confirmed** [doc]: `mmmy_pine-script-doc-v6/pine-script-docs/language/user-defined-functions.md:811` says functions "*cannot modify* those variables using the reassignment or compound assignment operators". I2 cites the path without the `pine-script-docs/` segment; the text is the same |
| S8 | v6 lazy `and`/`or` corrupts `ta.*` history | Docs | **Confirmed** [doc]: `jabez4jc_pinescriptv6/migration_guides/to_pine_version_6.md:777-807` |
| S9 | `"0000-0000"` is a 24-hour, 7-day session | Docs | **Confirmed** [doc]: `concepts/sessions.md:43` (mmmy mirror) |
| S10 | I2's runs | Read I2's saved outputs | **Confirmed**: `ALL CHECKS PASSED`; random-direction share 0.0045; bootstrap CI −$0.52 to +$12.60, t = 1.87; buy/sell 3-of-3 fired 0 times [lead] |
| S11 | I1's LFP simulator run | Re-ran `python3 -I liquidity_model_sim.py` | **Confirmed**: 15/15 checks pass; EXTREME on 7.35% of bars; 14.77 flips per 1,000 bars [ran, lead] |
| S12 | About 25 study numbers that the two reports quote | `grep` in the `.final.md` files | **All found as quoted**, with one citation fix (S13). Those checked include: quant_pot +3.66% and the 2.00 ratio; ict_struct 47.4-52.7%, 65.3 vs 65.8% and MSS 49.4%; bias_dol 3.8-8.3 pp; ict_liq −2.8 ± 0.8 and +0.1 ± 0.4 pp; ict_time 76% and +0.3 ± 1.1 pp; calib_ml 0.99/0.004, 66/47/33% and 1.10-1.43 ATR; skeptic 13.5% and −0.62 to −0.97R; ux_design ΔE 6.7; amt_profile 63-86%; ict_pd 11-24% and +7.0 pp; smc_impl 12%/41%; pine_eng 59.5% and 88.1% |
| S13 | I1 cites "iFVG first retest holds 49-50%, n ≈ 25,000" to `smc_impl §0.4` | `grep` | **Citation corrected.** The number is in `ict_pd.final.md` §0 item 4 and its table (line 285): 49.1% (n 3,857), 49.5% (11,768), 50.2% (7,399), 49.7% (2,220), total n 25,244. The value is right; the source is `ict_pd` |
| S14 | The legacy README dates `00a405a` to 2026-11-23 | `git log` | **Date corrected.** Commit `00a405a` is dated 2026-10-16. The baseline was *frozen* on 2026-11-23 |
| S15 | "Every file found" | Listed every remote branch and searched the workspace for `*.pine` and images | **Three additions** that neither report lists: (a) the early engine's origin branch also holds `CLAUDE.md`, the user's own setup notes (used in §5 and §6); (b) branch `claude/peaceful-gauss-tr43jz` is an unrelated car-dealership website; (c) branch `claude/youthful-ritchie-ttryl6` is an unrelated Obsidian-vault setup. No other Pine file exists anywhere |
| S16 | The reference screenshot | Viewed `dev-notes/brief/reference_look.png` | **Confirmed** as described in §5.1. It is a screenshot of the commercial product's own page. We copy the layout only, never its name or branding |
| S17 | I1's "cost < 3% of the stop lost about 4× less" is a README claim | `grep` in the early README and engine | **Citation corrected.** The sentence is in the early engine's *input tooltip* (EE 286: "signals with cost under 3% of the stop lost about 4x less than the rest"), not in its README. It is still a [claim]: no script exists |
| S18 | The 49 audit IDs all appear in the §4.1 summary | Extracted every `## P1/P2` heading and matched it against the table | **Confirmed**, 49 of 49 (18 P1 + 31 P2). One line reference fixed: PD-5 is reported at line 942, so theme 24 now reads 785-796, 942 [lead] |
| S19 | About 30 further line references in §3 (LFP 139, 337, 432, 876, 891, 1082, 1163; XAU 413, 1085; EE 199, 265, 291, 314, 320, 432, 493, 896, 981, 1012, 1031, 1158, 1505, 1708, 1754, 1900, 1918, 1966, 1975, 1984, 2100, 2355, 2397, 2431, 2464; ORB 73, 90, 200, 250; v2 170, 220, 229, 964, 1253, 1585, 1950, 1984, 2021, 2160) | `sed -n` | **All match** [lead] |
| S20 | Session defaults and the early engine's core hours quoted in §5.4 | `grep` of every `input.session` and EE 283, 331, 1047 | **Confirmed**, with one addition: the early engine's own session pools (Asia 2000-2359, London 0200-0500, NY 0930-1130; EE 217-221) were missing and are now listed [lead] |
| S21 | Newer study material that the first draft could not use | Read `x1_behavioral.md` (§0), `x1_positioning.md` (§0), `ict_time` §0 item 2, `quant_pot` §0, `calib_ml` §0.6 | **Added** to §6 (C2), §7 and §8, each tagged with its source. The x1 reports have no combined `.final.md`, so they are marked "non-final" [lead] |

### 0.3 What is missing or unverified
- **TradingView compile status of every legacy script: unverified.** No offline compiler exists. Two scripts are known *not* to compile (XAUUSD, Buy/Sell; §4.6-4.7).
- **The early engine's research scripts and data are not in any branch.** Every early-engine statistic is a [claim]. The later study reproduced its conclusions independently (§7).
- **Project C (ORB) rejected-idea scripts and its 0.5R-era bootstrap were never committed** [claim].
- **Still not available on 2026-11-28:**
  - `STUDY.md` and `ROADMAP.md` (the study's synthesis has not run);
  - the gap-lens report `x1_retail_schools`.
- **Gap lenses that do exist,** as single `.md` files without a combined `.final.md`: `x1_positioning`, `x1_internals`, `x1_tv_validation`, `x1_implied_vol` and, new since the first draft, `x1_behavioral`. Numbers from them are tagged "non-final".
- **Phase 2 experiments are still running.**
  - `apex/research/experiments/` holds pre-registrations for E1, E2, E3, E4, E6, E7, E9, E10 and E12. There is no file for E5, E8, E11, E13 or E14; HANDOFF lists E8, E11, E13 and E14 as on hold.
  - Some experiment folders under `apex/validation/python/experiments/` already contain run outputs (for example E1 and E4), but no experiment file has a written results section. E3's "Part B · Results" is still empty.
  - None of their results is used here.

---

## 1. Inventory of every file found

Sizes are bytes and lines at inspection time.

### 1.1 Legacy sources (`apex/legacy/`, read-only copies)

| File | What it is | Origin branch | Commit (date) | Bytes | Lines |
|---|---|---|---|---:|---:|
| `dol_engine_v2_00a405a.pine` | DOL Engine v2, Pine v6 indicator. The current product | `claude/determined-lovelace-erktyz` (`indicators/dol_engine.pine`) | `00a405a` (2026-10-16; frozen 2026-11-23) | 127,223 | 2,448 |
| `DOL_Engine_early.pine` | Early DOL engine, titled "DOL Engine v6 · Draw on Liquidity". Pine v6 indicator with a trade assistant | `claude/quirky-volta-vgbrq5` (`DOL_Engine.pine`) | `32e460f` (2026-10-05) | 155,335 | 2,548 |
| `DOL_Engine_early.README.md` | Its README, with research results | same (`README.md`) | `32e460f` | 10,771 | 157 |
| `liquidity-flow-pro.pine` | Liquidity Flow Pro [Non-Repaint], Pine v6 indicator | `claude/liquidity-flow-pro-indicator-z310f3` | `a2e3c06` (2026-10-03) | 91,647 | 1,615 |
| `liquidity-flow-pro.README.md` | Its README | same | `a2e3c06` | 7,521 | 91 |
| `liquidity_model_sim.py` | Python behavioural simulator for LFP | same (`tools/liquidity_model_sim.py`) | `a2e3c06` | 29,804 | 645 |
| `XAUUSD_Fast_Balanced_Pro.pine` | XAUUSD Fast/Balanced Pro [3m], Pine v6 **strategy** | `arena/01a08150-m` | `b2741c2` (2026-09-08) | 60,731 | 1,248 |
| `XAUUSD_Fast_Balanced_Pro.README.md` | README, contents `# m` only | same | `b2741c2` | 4 | 1 |
| `buy_sell_indicator.pine` | Buy/Sell Indicator, Pine **v5** | `claude/tradingview-buy-sell-indicator-u0m9ke` | `0f261a2` (2026-09-30) | 4,956 | 117 |
| `buy_sell_indicator.README.md` | Its README | same | `0f261a2` | 3,710 | 100 |
| `mnq_orb/MNQ_5m_ORB_Signals.pine` | MNQ 5m ORB Signals, Pine v6 indicator | `claude/jolly-cerf-5bmcgk` (`pine/`) | `99f7390` (2026-10-01) | 21,159 | 306 |
| `mnq_orb/MNQ_5m_ORB_Strategy.pine` | MNQ 5m ORB Strategy, Pine v6 strategy twin | same (`pine/`) | `99f7390` | 9,756 | 149 |
| `mnq_orb/README.md` | Plain-language README with results | same | `99f7390` | 12,236 | 159 |
| `mnq_orb/backtest.py` | Produces every README table | same (`research/`) | `99f7390` | 5,337 | 104 |
| `mnq_orb/bt.py` | Broker emulator `simulate` and TradingView-equivalent helpers | same (`research/`) | `99f7390` | 6,975 | 151 |
| `mnq_orb/final_ref.py` | Python reference of the final rules and liquidity levels | same (`research/`) | `99f7390` | 4,391 | 79 |
| `mnq_orb/ind_ref.py` | Python reference of the indicator's semantics | same (`research/`) | `99f7390` | 2,493 | 39 |
| `mnq_orb/prepare_data.py` | Resamples the public NQ/MNQ data | same (`research/`) | `99f7390` | 1,611 | 33 |
| `mnq_orb/fetch_data.sh` | Downloads the public dataset | same (`research/`) | `99f7390` | 525 | 11 |
| `mnq_orb/verify.py` | PineTS equivalence harness (orchestration) | same (`research/verify_pinets/`) | `99f7390` | 5,146 | 87 |
| `mnq_orb/run_pinets.mjs` | PineTS runtime driver | same | `99f7390` | 1,615 | 23 |
| `mnq_orb/validate.cjs` | Static validator driver | same | `99f7390` | 627 | 9 |
| `README.md` | The legacy index | (this branch) | | 1,124 | 12 |

### 1.2 Files on origin branches that were *not* copied

| File | Branch / commit | What it is | Matters for APEX? |
|---|---|---|---|
| `CLAUDE.md` (1,435 B) | `quirky-volta-vgbrq5` / `32e460f` | **The user's own setup notes for the early engine:** instruments, timeframes, colour-only reading on mobile, "always show where price is going", compile with 0 errors and 0 warnings, paste the full script and send the file | **Yes:** preferences in §5, conflicts C4 and C5 in §6. Neither inspector reported it [lead] |
| `research/verify_pinets/package.json` | `jolly-cerf-5bmcgk` / `99f7390` | Pins `pinescript-v6-validator 0.4.3` and `pinets 0.10.0` | Yes, for reproducing the harness [I2] |
| `research/.gitignore`, `research/verify_pinets/.gitignore` | `99f7390` | Ignore rules (data, node_modules, work) | No |
| `.gitignore` | `a2e3c06` | Python cache | No |
| `.agents/skills/composio/*`, `skills-lock.json` | `32e460f` | Agent tooling | No |

### 1.3 Other branches

| Branch | Head | Content | Relevance |
|---|---|---|---|
| `main` | `1ca46a6` (2026-09-08) | `README.md` with the text "# m" | None |
| `claude/peaceful-gauss-tr43jz` | `56bf085` (2026-10-21) | A car-dealership website (HTML, CSS, JS, images) | None; not trading [lead] |
| `claude/youthful-ritchie-ttryl6` | `36f98d4` (2026-11-23) | An Obsidian-vault setup | None; not trading [lead] |

### 1.4 The working branch (`claude/determined-lovelace-erktyz`)

| Path | Bytes | What it is |
|---|---:|---|
| `indicators/dol_engine.pine` | 127,223 | Live v2. Byte-identical to `00a405a` at inspection time; the bug-fix overhaul may edit it |
| `README.md` | 9,148 | User-facing v2 design: sources, scoring, Clean and Terminal styles |
| `CLAUDE.md` | 541 | Project pointer to `HANDOFF.md` |
| `dev-notes/HANDOFF.md` | 13,594 | Goal, constraints, status log (grows as sessions log progress) |
| `dev-notes/brief/APEX_ULTIMATE_SPEC.md` | 32,063 | The governing specification |
| `dev-notes/brief/CONTEXT.md` | 5,288 | Agent brief, hard constraints, decision history |
| `dev-notes/brief/reference_look.png` | 81,701 | **The only visual design reference** (§5.1) |
| `dev-notes/brief/tradeaxis_description.md` | 4,529 | Feature description of the commercial product that inspired v2 (features only; never its branding) |
| `dev-notes/runs/overhaul-r1-findings.md` | 22,886 | The 49 audited v2 findings (§4.1) |
| `dev-notes/runs/overhaul-r1-journal.jsonl` | 262,596 | Raw audit results with exact patches. Not read by either inspector |
| `dev-notes/runs/wf_*-journal.jsonl` | 9 files, 554 B to 1.59 MB | Workflow run journals (study, overhaul, APEX phases) |
| `dev-notes/study/` | 3.6 MB, 51 files | Synced copies of the study reports: 23 `.final.md`, 23 first-pass `.md`, 5 x1 gap lenses |
| `dev-notes/tools/pine_parse.sh`, `parse_one.py`, `split.py` | 1,182 / 233 / 763 | Syntax checker based on pynescript (syntax only) |
| `dev-notes/workflows/*.js` | 9 files | Workflow scripts (study, overhaul, APEX phases) |
| `apex/.gitignore` | 166 | Keeps data, `out/` folders and caches out of git |
| `apex/research/inspection/I1_dol_lineage.md`, `I2_signal_lineage.md` | 99,852 / 72,220 | The two inspector reports merged here |
| `apex/research/experiments/E1, E2, E3, E4, E6, E7, E9, E10, E12 *.md` | 9.7-13.7 KB each | Phase 2 pre-registrations; no written results yet |
| `apex/research/team/` | empty | Reserved |
| `apex/MARKET_KNOWLEDGE_BASE/09_volatility.md`, `10_momentum.md`, `11_statistical_mathematics.md` | 96,929 / 69,250 / 134,891 | Phase 3 atlas documents, in progress (sizes at 2026-11-28) |
| `apex/validation/python/experiments/` | (data and `out/` git-ignored) | Phase 2 experiment code and run outputs |
| `apex/validation/pine/` | empty | Reserved for Pine-side validation |

### 1.5 Scratchpad resources the team uses (not in git)
- `<scratchpad>/brief/baseline_v2.pine`: the frozen v2, identical to `00a405a`.
- `<scratchpad>/brief/study/*.final.md` and `*_tools/`: the study reports and their replication scripts.
- `<scratchpad>/docsrc/`: two Pine v6 docs mirrors.
- `<scratchpad>/pine_harness`: `pinets 0.13.1` and `pinescript-v6-validator 0.4.3`.
- `<scratchpad>/i2/`: I2's ORB reproduction, with Appendix A of I2 as the rebuild recipe.

---

## 2. What each project does

| Project | Type | One-line purpose | Signals? | Evidence |
|---|---|---|---|---|
| **DOL Engine v2** | v6 indicator, 2,448 lines | Pools liquidity targets, scores each 0-100 on confirmed bars, tracks the best as the Draw on Liquidity; shows a PoT readout, a bias table, iFVGs and a self-grading ledger | None (target, flip, iFVG and sweep events only) | Study replications of its parts (§7); never run on TradingView data in any recorded test |
| **Early DOL Engine** ("v6") | v6 indicator, 2,548 lines | DOL queue + "self-learning" PoT + News Guard + filters + three trade modes + virtual-trade tracker + BUY/SELL banner, tuned for MNQ/ES 1m/5m | Yes: DOL Direction (default), Sweep Reversal, Confirmed | README research on 26 datasets and 3.7 years of NQ/S&P [claim]. All tested setups lost after costs |
| **Liquidity Flow Pro** | v6 indicator, 1,615 lines | Turns a pool map into a BUY-SIDE/SELL-SIDE liquidity share; Video style shows "▲ UP xx% / ▼ DOWN yy%" zones | Optional (off by default) | 15/15 behavioural checks on synthetic paths [ran]; no real-data outcome test |
| **XAUUSD Fast/Balanced Pro** | v6 **strategy**, 1,248 lines | Ten setup engines joined by OR → additive score → FAST/BALANCED thresholds → filters → 3-target bracket orders | Yes, forced by design | None. **Does not compile** (§4.6) |
| **Buy/Sell Indicator** | **v5** indicator, 117 lines | Counts RSI-state, MA-cross and MACD-cross votes; signals at `min_signals` | Yes | None. **Does not compile** (§4.7). 3-of-3 never fires [ran] |
| **MNQ 5m ORB** | v6 indicator + strategy twin + Python backtest + PineTS harness | 15-minute opening-range breakout with a strong-close filter, 0.2R target, one trade a day; PDH/PDL/ONH/ONL liquidity tags | Yes | The only reproduced backtest: 729 trades, 85.7% win, PF 1.24 [ran]. The win rate is mostly geometry (§7) |

### 2.1 DOL Engine v2 (the base)
- **Sources:** chart, STF and HTF swings; PDH/PDL and PWH/PWL; Asia, London and NY-AM highs and lows; chart and HTF FVGs; order blocks and breakers.
- **Registry:** external levels live in a registry with eviction and re-entry.
- **Score:** five pillars (proximity 25, freshness 10, confluence 15, density 20, draw 30) times multipliers (lockout, inner stack, counter-draw, killzone, calibration, volume-profile path).
- **Selection:** draw side first, a 2-bar challenger and hysteresis.
- **PoT:** an analytic first-passage probability with drift, blended with an empirical excursion surface, capped at 95%.
- **Ledger:** grades each pick against a distance-matched random baseline.
- **Styles:** Clean (default; matches the reference) and Terminal (full HUD).
- **Section map:** I1 §2.2. **Calculation inventory:** I1 §2.4.

### 2.2 Early DOL Engine
- **Target queue and score:** one unified queue (`Zn`) with a 6-pillar score, blended with a logistic PoT into a priority.
- **PoT:** an empirical surface blended with an analytic first passage, plus a seasonality factor and a logistic layer with hard-coded weights.
- **Extras:** Brier SKILL readout, FIRST race readout, Auto mode with a timeframe ladder, News Guard with a pre-filled FOMC calendar, a 1-minute volume-delta proxy, cost-aware stops, $-risk sizing, a daily loss limit, flat at 15:55 NY.
- **Defaults:** Simple View; trade mode DOL Direction; Lock DOL Until Hit.
- **README:** reports that nothing tested is reliably profitable after costs [claim]. I1 §3.

### 2.3 Liquidity Flow Pro
- **Pools:** from confirmed swings, external swings (3× length), bounded equal-level clusters, HTF swings, D/W/M and session levels.
- **Commit outcome:** sweep, taken or test.
- **Output:** strength × freshness × distance weight is summed per side and turned into a percentage share with smoothing, a stability prior and a LOW-DATA shrink.
- **Header:** says "NOT a probability". The Video tooltip and README nevertheless say the larger side is "the more likely direction" (LFP 55, 61; README 24) [lead]. I1 §4.

### 2.4 XAUUSD Fast/Balanced Pro
- **Pipeline:** regime → features → engines A-J (trend continuation, pullback, VWAP reclaim, breakout, break-and-retest, BOS, sweep reversal, CHoCH reversal, momentum shift, compression expansion), joined by OR.
- **Score:** additive, 0-100, with grades A+/A/B/C.
- **Modes:** FAST/BALANCED are threshold presets on the same engine (§5.3).
- **Trade manager:** 1R/2R/3R partial exits, break-even after TP1, ATR trail.
- **Dashboard:** shows live Strategy Tester stats and a "why blocked" debug table. I2 §2.

### 2.5 Buy/Sell Indicator
- **Logic:** RSI < 30 / > 70 (a state) plus MA and MACD crosses (events). Signals when at least `min_signals` of three agree.
- **Display:** background fills on signal bars and a debug label. I2 §3.

### 2.6 MNQ 5m ORB
- **Rules:**
  - opening range 09:30-09:44 NY;
  - first close beyond it from 09:45 to 12:00 with close location ≥ 0.8;
  - stop at the opposite OR side, target 0.2R, flat at 15:50;
  - one signal per day.
- **Instrument lock:** MNQ/NQ 5m only (`syminfo.root` check, ORB 65).
- **Python:** reproduces every README table.
- **PineTS harness:** proves per-bar parity between the Pine scripts and the Python references. I2 §4-5.

---

## 3. PRESERVE / REWORK / DROP (consolidated across projects)

Source abbreviations:
- **v2** = `dol_engine_v2_00a405a.pine` (equal to the frozen baseline);
- **EE** = `DOL_Engine_early.pine`;
- **LFP** = `liquidity-flow-pro.pine`;
- **XAU** = `XAUUSD_Fast_Balanced_Pro.pine`;
- **BS** = `buy_sell_indicator.pine`;
- **ORB** = `mnq_orb/*`.

The "I-ID" column traces each row back to I1 (P-v2-*, R-e-*, X-l-* …) or I2 (§ number).

### 3.1 PRESERVE: carry into APEX with the logic essentially unchanged (re-wrapping into modules allowed)

| ID | APEX module (spec §) | Component | Source: lines | Class / grade | Reason | I-ID |
|---|---|---|---|---|---|---|
| P01 | Platform (§11, §19.1) | Non-repaint MTF pattern: `[1]` inside the requested function + `lookahead_on`; never request below the chart (`f_tfSafe`) | v2 564, 782, 796, 923-925, 939, 981; the same pattern in EE 779/923 and LFP 660 | E strong | Correct per docs. The `pine_eng` measurement shows the cost of getting it wrong: a leaking daily read lifts a no-skill 1-ATR/10-bar win rate from 49.6% to 59.5% (6 CME futures, 1H, about 33k signals) [study: pine_eng §0] | P-v2-4 |
| P02 | Platform (§19.1) | Confirmed-bar engine gate; confirm-on-close signals; written non-repaint statement | v2 1518; EE 1179, 1687, 1712, 1827; XAU 32-48, 86, 681; ORB 152, 201 | E strong | The spec's default contract | P-v2-5, I2 §2.15 |
| P03 | Platform (§19) | Last-bar rendering with bounded object arrays; time-anchored drawings with an object budget; pool-owned drawings that fade on a sweep | v2 2098-2149; EE 2032-2060; LFP 239-265, 397-455 | E | Object lifecycle hygiene within platform limits | P-v2-5, P-e-1, P-l-9 |
| P04 | Statistics (§10, §15) | `f_erfcLog`, `f_erfc`, `f_phi`, `f_expPhi`, `f_pot`: one-barrier first passage | v2 408-444 | A strong | Matches Monte Carlo. P(touch within H) = 2.00 × P(finish beyond) on CME 5m (H 30) and 1H (H 12) bars [study: quant_pot §0.4]. **Call it with zero drift** | P-v2-1 |
| P05 | Statistics (§4.7, §14) | `f_race`, `f_raceH`: two-barrier, finite-horizon race | v2 447-482 | A strong | Which side is taken first follows geometry: 65.3% observed vs 65.8% predicted, n 12,148, 8 markets [study: ict_struct §0]. Feed it σ_eff | P-v2-2 |
| P06 | Statistics (§10) | `f_clamp`, `f_wilson`, `f_logit`, `f_sigm` | v2 400-503 | E | Standard helpers | P-v2-3 |
| P07 | Calibration (§15) | Empirical excursion surface (survival counts of H-bar excursions) | v2 1061-1062, 1265-1300, 1527-1532 | A strong | Calibrated: slope 0.99, ECE 0.004 on 1.2M 5-min rows [study: calib_ml §0.1]. Extend the keys to volatility state and time of day; add an overflow guard in `f_bump` (1268) | P-v2-6 |
| P08 | Calibration (§15, §20) | Distance-matched baseline `f_potBase`; ledger records `f_openTrial`/`f_step`, including the candle-colour intrabar order | v2 1314, 1426-1459 (colour rule 1441) | A strong | Leak-free [study: skeptic §0.3]. The colour rule orders the high and low correctly 88.1% of the time vs 80.6% for TradingView's rule, about 140k CME bars [study: pine_eng §0.4] | P-v2-7 |
| P09 | Calibration (§15) | Brier SKILL scorecard with overlap-weighted sampling | EE 684-688, 1637-1646, 2375-2386 | A strong (proper scoring) | The per-chart grading that v2 lacks | P-e-4 |
| P10 | Liquidity (§4.1-4.2) | Exact anchoring: `f_anchorScan`, the `tfOpenBar` map + `f_barAtTime`, `f_x` + `max_bars_back(time, 5000)` | v2 37, 404, 1141, 1165-1209 | E | Anchors each zone on its printing candle, as the reference shows. Extend it to the exact MTF wick bar | P-v2-8 |
| P11 | Liquidity (§4) | External registry with eviction and re-entry | v2 365, 1211, 1591-1596, 1813-1852 | E | Far HTF and key pools come back into range without bloating the pool | P-v2-9 |
| P12 | Lifecycle (§4.5) | Sweep rule: strict trade-through for pools, touch for arrays | v2 623 (`touched`) | E/D definition | Matches open-source conventions [study: smc_impl §0.1]. Add "exact touch = test" (LIQ4) | P-v2-10 |
| P13 | Lifecycle (§4.5-4.6) | Three-way commit outcome: **sweep** (beyond the band, close back inside), **taken** (close beyond), **test** (approach); Strict/Balanced/Aggressive modes | LFP 139-140, 784-837 | D definition; wick-depth statistics A moderate | The clearest lifecycle primitive. Set the band from measured wick depths (median 0.23-0.28 ATR, p80 0.51-0.64 ATR) [study: ict_liq §0.6] | P-l-1 |
| P14 | Clustering (§4.4) | Bounded-span clustering with members, hi/lo and same-point dedupe | LFP 461-503 | D/E | Identifiable constituents, no chain drift | P-l-2 |
| P15 | Liquidity (§4.1-4.2) | First-partial-period discard; chart-TF gating of D/W/M levels; PMH/PML | LFP 554-623, 674-676; EE 886-888, 1330-1334 | E | Fixes v2's rp-partial-pwh and TE5; adds the missing PM levels | P-l-3, P-l-4, P-e-3 |
| P16 | Data quality (§13.2) | Volume-quality detection (`volOK`) and the LOW DATA shrink to neutral | LFP 299-302, 337, 891, 1045-1051 | E / principle | "When data is missing, reduce confidence" (spec §25). v2 silently fails on zero volume | P-l-5, P-l-6 |
| P17 | Platform (§19.1) | Freeze-live option; display-only live "RAIDING / BREAKING" status; live sweep check | LFP 104-105, 876-878, 994-1004; v2 1504-1509 | E | Provisional states, labelled as such and kept out of confirmed alerts | P-l-7, P-l-8, P-v2-16 |
| P18 | ICT zones (§5) | FVG detection; CE/full delivery with partial crop | v2 907-908, 1566-1577 | E/D definition | Objective formation and mitigation rules. The quality score is a clutter control only (§7) | P-v2-14 |
| P19 | ICT zones (§5) | iFVG inversion on a full close through; body-close upkeep | v2 1598-1644 | D (display) | Display and alerts only. The first retest holds 49.1-50.2% (n 25,244) [study: ict_pd §0, item 4] | P-v2-15 |
| P20 | Structure (§3) | HH/HL/LH/LL typing; protected swing → structural | LFP 694-695, 723, 733, 853-868 | D definition | Spec §3 vocabulary | P-l-10 |
| P21 | Selection stability (§4.7) | 2-bar challenger + hysteresis (×2 to flip sides); optional lock-until-hit with N-bar confirmation | v2 2011-2020; EE 180-181, 1586-1618 | D weak (stability) | Stops "targets jump around". Drop the killzone multiplier on the hysteresis | P-v2-12, P-e-5 |
| P22 | Ranking (§4.7) | Origin lockout: an array is not a target until price has left it | v2 650, 689-690 | D weak | Sound guard. Extend it to HTF FVGs (dol-G) and to every array | P-v2-13 |
| P23 | MTF (§11) | Auto mode; timeframe ladder that never goes below the chart | EE 731-735, 852-873 | E | Fixes v2's TE2 (4H/D charts in Day mode) | P-e-2 |
| P24 | Display (§17) | Clean look: DOL render, Classic palette, Clean bias table, Clean iFVG box | v2 2214-2226, 240-299, 2295-2307, 1607-1615 | Design (user preference) | Matches the reference within ±1 RGB, except the white core: transparency 10 instead of 15 brings ΔE from 6.7 to about 0.9 [study: ux_design §0.1] | P-v2-11 |
| P25 | Normalisation (§13.1) | ATR-normalised thresholds throughout | XAU (throughout) | E principle | Instrument-agnostic | I2 §2.15 |
| P26 | Explainability (§4.7, §17) | "Why didn't it fire" debug table, as a concept | XAU 1162-1248 | Design | Becomes APEX's reason codes and debug dashboard, OFF by default | I2 §2.15 |
| P27 | Calibration (§14) | FIRST race readout, as a concept | EE 2355-2374 | A strong (geometry) | Re-implement with the zero-drift `f_raceH` | P-e-6 |
| P28 | Honesty (§15, §25) | Honest self-reporting: "This chart" track record after costs; "not a probability" header; stats labelled in-sample; "nothing is fabricated" | EE 2397, 2431; LFP 12-17; ORB stats table; XAU 1083 | Process | Matches the spec's honesty rules, and the user accepted negative results | P-e-7, P-l-11, I2 §4.13 |
| P29 | Validation (§20) | Offline broker emulator `bt.simulate`: decide on the close, fill at the next open, SL/TP from the fill, stop first on same-bar ambiguity, gap fills at the open, EOD exit | ORB `bt.py` 76-140 | E | Reproduced exactly [ran: I2 T1]. The core of the APEX evaluator | I2 §4.14 |
| P30 | Validation (§20) | TradingView-equivalent reference helpers (`ema/rma/rsi/atr/dmi`, `htf_ema` emulating `[1]` + `lookahead_on`) | ORB `bt.py` 7-72 | E | Pine ↔ Python parity library | I2 §4.14 |
| P31 | Validation (§20) | Backtest protocol: design / validation / holdout splits, neighbour grid, per-year and monthly tables, cost stress | ORB `backtest.py` | A | Extend it with baselines, confidence intervals and a holdout that is never retuned (§7.3) | I2 §4.14 |
| P32 | Display (§17) | Status-line UX ("Watching for breakout", "Done for today"), as a concept | ORB 250-306 | Design | A minimal state readout | I2 §4.14 |

### 3.2 REWORK: keep the idea, change the logic

| ID | APEX module (spec §) | Component | Source: lines | Class / grade | What to change | I-ID |
|---|---|---|---|---|---|---|
| R01 | Structure (§3) | `f_structure` (swing and internal bias, dealing range, protected levels) | v2 708-782; superseded alternatives XAU 267-314, LFP 741-752 | D definition; C as a predictor | Fix the swing CHoCH lag (struct-F1), staleness at the HTF close (struct-F2) and the equal-pivot `hValid` (780). Use `protH/protL` for the dealing range. Emit BOS/CHoCH/MSS events, each stamped with the bar on which it becomes knowable. Add internal/external structure without a score bonus. Handle pivot ties (12% of pivots on ES 5m, 41% on 6E 1m) [study: smc_impl §0.5] | R-v2-1, R-l-1 |
| R02 | Ranking (§4.7) | `evaluate` → **Draw Score** | v2 661-696 | C (most pillars unsupported) | Neutralise the draw, density, tier and confluence levers. Taper only *new* picks (TE4). Score zero beyond max distance (TE3). Remove self-confluence (676-680). Remove drift from reach (665). Add the opposing-FVG path cost (A moderate: −2.8 ± 0.8 pp at 1H, n 4,757 [study: ict_liq §0.4]). Use expected reach d·PoT(d) as the objective: it delivered 1.10-1.43 ATR per target vs 0.86-1.09 for the hand score (13 sets) [study: calib_ml §0.8]. Add reason codes | R-v2-2 |
| R03 | Ranking (§4.7) | Selection | v2 1964-2035 | D | Output **both** the best buy-side and the best sell-side target, each with price, ticks, ATR distance, Draw Score, reason codes and state. Pick the side with a zero-drift finite-horizon race, then with a gated calibrated side model. Neutral is allowed | R-v2-3 |
| R04 | Destination vs reversal (§4.6, §4.8) | Draw vector D and raid events `liqEvt` | v2 1535, 1580-1582, 1891-1898 | C (no skill; wrong sign) | Model destination and post-target reaction as **separate** processes. Treat REJECT as neutral (the data show a small continuation lean: 1H +1.5 ± 0.7 pp, n 12,550 [study: ict_liq §0.2]). Record hold/reject as features for the ledger, not as a static lean | R-v2-4 |
| R05 | Clustering (§4.4) | Stacks: inner ×0.70 and "outermost is the draw" | v2 684-685, 1230-1251, 1912-1927 | C (heterogeneous) | Keep the stack count as an attribute only (LIQ1, dol-D) | R-v2-5 |
| R06 | Clustering (§4.4) | EQ merging | v2 1090-1131 | D; EQ A weak | Make it two-sided (the outer branch 1116-1126 is effectively dead). Add relative EQ across key levels (LIQ2, LIQ3) and pivot-tie handling. Adopt LFP's bounded cluster (P14). Touches never add strength by themselves (spec §4.4) | R-v2-6 |
| R07 | Liquidity (§4.1-4.2) | Calendar trackers | v2 807-832, 945-961 | E | Partial-period guard, chart-TF gating and PMH/PML (P15) | R-v2-7 |
| R08 | Liquidity, time (§4.1-4.2) | Sessions and killzones | v2 798, 835-863, 971-976; LFP 132-135; EE 283, 1046-1048 | E definition | Use time-interval membership, not the bar open (the NY AM range is wrong on 76% of 1H days [study: ict_time §0.7]). Show killzones only ≤ 1H. Configurable sessions with exchange-timezone defaults. Add NY PM and opening-range pools | R-v2-8, R-l-5, R-e-7 |
| R09 | Calibration (§15) | Displayed PoT `f_potModel`; drift `potMu` | v2 917, 1303, 2063-2068; duplicate blend in 1314 | A strong (model class); ungraded per chart | Zero drift: +3.66% log-loss, CI +2.99 to +4.32, 326 symbol-days [study: quant_pot §0.2]. Key by volatility state and clock. Grade it per chart (P09). Gated online Platt. Merge `f_potModel`/`f_potBase`. Label policy: §6, conflict C2 | R-v2-9 |
| R10 | Risk (§16) | `f_invalidation`, `f_raceAdj` | v2 1343-1371 | A (race); C (EV) | Zero drift; σ_eff; structural invalidation; gate `f_raceAdj` | R-v2-10 |
| R11 | Calibration (§15) | Ledger verdict and variance | v2 1077, 1461-1499, 2374-2430 | A strong (method); C (verdict) | A mirror-controlled, anytime-valid three-way verdict; centred open-keyed blocks; a candidate shadow ledger [study: skeptic §0.5] | R-v2-11 |
| R12 | Calibration (§13.2) | `f_calMult` | v2 1376-1382 | C (noise) | Neutral by default, evidence-gated. Under a true null it sits ≥ 10% off 1 for 66%, 47% and 33% of families at n = 10, 40 and 80 [study: calib_ml §0.4] | R-v2-12 |
| R13 | ICT zones (§5) | Order blocks; breakers; HTF FVG | v2 785-796, 938-942, 1646-1661, 1663-1748, 1854-1865; EE 1432-1455 | D definition; C as targets | OB: retest candle (PD-3), a real quality gate (PD-4), neutral target weight. Breaker: the template definition (11-24% reproduced today; 57-77% without the `tookL` gate [study: ict_pd §0.3]); EE's "any close through" is closer. HTF FVG: keep far ones in the registry (PD-1), add quality and direction checks (PD-5) and the lockout (dol-G) | R-v2-13/14/15, R-e-12 |
| R14 | Volume (§7) | 1H volume profile, `f_pathVol`, LVN | v2 978-1015, 1384-1424, 2251-2286 | A weak (LVN); C (path cost) | Path multiplier neutral. Detect zero or na volume and flag data quality. POC/VA only as labelled *estimates*. LVN display only | R-v2-16 |
| R15 | Time (§9, §14) | Intraday volatility seasonality (`sfNow`) | EE 937-969 | A strong (the clock is real) | Use the real future-bar calendar (964 ignores session gaps). Compute once per bar, not per tick. Gate it per chart (it fails on GC 1H) [study: ict_time §0.3] | R-e-1 |
| R16 | Regime (§9) | Volatility regime `atrPct`; chop and chase scores; ATR-ratio volatility state | EE 1022-1025; XAU 382-410, 413-415 | A moderate (volatility state); D (point tables) | Percentile-based measures with hysteresis and compression/expansion states. Volatility state persists across windows; trend labels do not (§7.1) | R-e-2, I2 §2.15 |
| R17 | Momentum (§8) | Momentum composite averaging RSI, MACD and DMI; LFP pressure EMA and bounded tilts | XAU 212-218; LFP 876-919 | A (redundancy principle) | One documented, normalised momentum feature with redundancy control. Keep LFP's ≤ 1.25× cap principle; tilts stay neutral until measured | I2 §2.15, R-l-2 |
| R18 | Risk (§16) | Cost model, max-cost-%-of-stop filter, minimum cost stop, sizing | EE 286, 1051-1065, 1693-1695, 1954-1964, 2408-2412 | A weak (input tooltip at EE 286: cost < 3% of the stop "lost about 4x less") [claim] | Instrument-agnostic: the user enters cost in ticks; tick size and point value come from `syminfo`; mark the estimate "incomplete" when the cost is unknown. No hard-coded roots (1053) | R-e-3 |
| R19 | Intermarket/events (§12) | Event calendar and release windows | EE 291-306, 981-1011 | E (manual windows) | Manual windows only. No unverified pre-filled FOMC dates. Never call it news detection | R-e-4 |
| R20 | Regime (§9) | Spike detector (range ≥ 2.5 ATR and volume ≥ 3×) | EE 1012-1019 | D weak | Rename it the "abnormal move" regime flag | R-e-5 |
| R21 | Volume (§7) | Order-flow proxy: sign(close − open) × 1-minute volume | EE 1031-1042 (lower-TF request 1034) | D proxy; A weak (≈ 0.05R, not significant) [claim] | Optional, labelled "volume-delta proxy (no bid/ask)", data-quality weighted, never on by default. It requests *below* the chart TF inside an `if` | R-e-6 |
| R22 | Lifecycle (§4.6) | Sweep queue | EE 1708-1740 | D definition | A sweep *event* detector that feeds the lifecycle, not a reversal entry | R-e-8 |
| R23 | Signals (§13.3) | FAST/BALANCED presets | XAU 131-159, 654-694 | D (design); none (untested) | Keep the user's model: one engine, two presets. BALANCED asks for a higher threshold, more *de-correlated* evidence groups, longer persistence and wider spacing. Add STRONG states. Fix the dual-use input (136) and the "opposite" spacing that really uses `barsSinceAny` (141-142, 898). Thresholds come from pre-registered tests (E2), never as win rates | I2 §2.15, §7 |
| R24 | Liquidity (§4.1-4.2), volatility unit | Opening range | ORB 73-84 | D concept; A moderate as a *unit* [study: session_stats §2.10] | Only as OR high/low pools and as a volatility unit, not as a signal. Configurable session, no NY constants | I2 §4.14 |
| R25 | Liquidity (§4.1-4.2) | PDH/PDL/ONH/ONL as known at the bar close | ORB 90-130; `final_ref.py` 6-32 | E | Generalise away from NY/CME constants and the 0.25 tick. Decide whether "swept" includes the current bar | I2 §4.14 |
| R26 | Validation (§20, §21) | PineTS equivalence harness | ORB `verify.py`, `run_pinets.mjs`, `validate.cjs` | E (tool) | Adopt I2's layered template L0-L8 (I2 §5.5): custom lints (global reassignment in functions; `ta.*` in `and`/`or`, ternaries and `if`; the HTF pattern), a runtime-parity register, start-point invariance, stream/update repaint tests, asserted metrics, pinned versions, data hashes | I2 §5.5 |
| R27 | Calibration display (§15) | On-chart stats tables | ORB 250-306; XAU 1085-1157 | Process | An indicator cannot read `strategy.*`. Show a ledger with the geometric break-even and a baseline beside every win rate | I2 §2.15, §4.14 |
| R28 | Platform (§19) | Inputs | v2 60-237 | E | `display = display.none` on every non-plot input (0 uses today); `active =` dependencies; fix the colour rows (CW10026); auto-fit timeframes to the chart | R-v2-17 |
| R29 | Display (§17) | Ghost trail | v2 1253, 1585, 2021-2023 | A (survivorship bias) | Ghost every outcome, including replaced targets, with time-to-hit; faint by default; optional | R-v2-18 |
| R30 | Display (§17) | Clean label states | v2 2225, 2305 | Design | "Swept ✓" after a sweep; timeframe in the code ("D BSL"); a "no target" state | R-v2-19 |
| R31 | Ranking (§4.7) | Pool trim at capacity | v2 1950-1962 | D | Protect fresh arrays and the counter side by intrinsic quality (dol-C) | R-v2-20 |
| R32 | Display (§17) | Terminal HUD and panel; early-engine ALIGN/NEWS/VOL rows | v2 2227-2248, 2309-2433; EE 2316-2421 | Design | Become the optional debug dashboard, OFF by default, without the dropped readouts | R-v2-21, R-e-11 |
| R33 | Alerts (§18) | Alerts | v2 2079-2093; EE 2504-2548; LFP 1573-1615 | E | The spec §18 set, with content (target, price, side, state). No sweep alert for unannounced targets. The live sweep alert becomes a labelled provisional option | R-v2-22 |
| R34 | Display (§17) | Themes | v2 229-291 | Design | Keep Classic + Custom + automatic light/dark ink; the others optional at best | R-v2-23 |
| R35 | Decision (§13 F) | LFP model confidence | LFP 1082-1091 | D, no validation | Rework into a documented data-quality and forecast-quality input. Never shown as % certainty | R-l-3 |
| R36 | Lifecycle (§4.5) | Faded swept pools with depth | LFP 432-455 | E | Add time-to-sweep; feeds the honest ghost trail | R-l-4 |
| R37 | Volatility (§9) | Garman-Klass + close-to-close σ; drift `mu` | EE 896-911 | A weak (+0.28% LL, n.s.) | Optional σ estimator; drift set to 0 | R-e-9 |
| R38 | Calibration (§15) | Empirical store with decay | EE 432-452, 1158-1174 | A | Merge the forgetting-factor idea into v2's surface, with an overlap-aware n | R-e-10 |
| R39 | Forecast uncertainty (§14.3) | Reach bands (`f_reachD`) and the reach bisection | v2 1325-1338; EE 2100-2123 | A (empirical quantiles) | A seed for the forecast's uncertainty band only | I1 §7 |

### 3.3 DROP: do not carry into APEX

| ID | Component | Source: lines | Class / grade | Reason | I-ID |
|---|---|---|---|---|---|
| X01 | Dead code | v2 `f_changed` 865-866 and the unused tuple outputs at 923-925 (`htfProtH/L`, `stfProtH/L`, `exePv*`, `exeHV/LV`, `exeProtH/L`); EE `f_flagW` 490, `xSH..xSLW` 922, `rH/rD` 1187; LFP `adxVal` 885; XAU array `tSL0` 701/871/1003; BS `show_ma`/`show_macd` 28-29 | — | Unused. Wire `protH/L` into R01 instead of dropping that information | X-v2-1/2, X-e-10, X-l-6, I2 D11, B3 |
| X02 | Biased readouts: ETA\|hit, "heat" (p80 MAE over hits only), EV, L50 | v2 2116-2127, 2240; 2404-2408; 2245-2246, 2359-2363; 2395-2396 | C | Biased by construction. EV shows −0.62R to −0.97R where the martingale truth is 0 [study: skeptic §0.4] | X-v2-3..6 |
| X03 | "✕ NO EDGE" / "✓ EDGE" verdict wording | v2 2390 | C | Peeking: false "✓" at some point on 13.5% of 288 real no-skill paths [study: skeptic §0.5] | X-v2-11 |
| X04 | Fixed draw levers: `wDraw` 30, counter-draw ×0.5, `dGate` | v2 145, 155-162, 691-693, 1975 | C, strong null | D called the first side right 47.4-52.7% on 8 markets [study: ict_struct §0.1]. D-first selection loses 3.8-8.3 pp of first-touch accuracy on 7 datasets [study: bias_dol §0.4] | X-v2-8 |
| X05 | Killzone affinity `f_kzAff`; off-killzone hysteresis | v2 163, 597-602, 976, 1941 | C | Macro windows +0.6 ± 0.5 pp (61k windows) [study: ict_time §0.6] | X-v2-7 |
| X06 | Volume-profile path multipliers ×1.10/×0.85 | v2 1945-1947 | C | Wrong-signed or null; 63-86% of the "thin" class are clamped beyond-range targets [study: amt_profile §0.2] | X-v2-9 |
| X07 | HTF Objective (ranked without proximity) | v2 170-171, 1984-1992, 2160-2168 | C (no test) | The best buy-side and sell-side outputs (R03) cover spec §4.7 | X-v2-10 |
| X08 | Midnight open as a special anchor | v2 220, 964 | C | +0.3 ± 1.1 pp, 1,412 instrument-days [study: ict_time §0.8]. Keep it as a plain level at most | X-v2-12 |
| X09 | Logistic PoT layer with hard-coded weights `lrW0` and ungated online SGD | EE 478, 672-697, 1098-1103, 1549 | C | The fit cannot be reproduced (scripts absent); ungated learners lose to the baseline [study: calib_ml] | X-e-1 |
| X10 | Priority = 0.65·score + 0.35·PoT | EE 185, 1550 | C | Mixes a heuristic score with a probability | X-e-2 |
| X11 | "Never leave the chart without a DOL" fallback | EE 1583-1585 | C | Neutral is legitimate (spec §13.3, §25) | X-e-3 |
| X12 | Target Win Rate mode | EE 314-316, 1900-1901, 1984-1987 | A (the controller works) / no edge | A high win rate from tiny targets; about 0R before costs [claim] | X-e-4 |
| X13 | Edge Gate with a 10-size in-sample replay | EE 320-322, 1754-1799, 1966-1999 | C | Picks the best of 10 sizes in-sample. Reported: 10 trades −2R (NQ), 70 trades −8R (S&P) [claim] | X-e-5 |
| X14 | Trade modes as signals: DOL Direction, Sweep Reversal; LFP sweep+shift+flow signals; ORB rule and its sweep-first filter / LIQ tag | EE 265-266, 1918-1945, 1975-1983; LFP 1163-1182; ORB 200-223 | C (tested, negative) | −0.02R (n 1,235) and −0.06R (n 1,350) [claim]; MSS analogue 49.4%, n 4,032 [study: ict_struct]; ORB holdout spent and the sweep filter failed out of sample (§7) | X-e-6, X-l-4, I2 §4.14 |
| X15 | "BUY NOW / SELL NOW" banner with contract counts | EE 2423-2464 | Design / C | Encourages trading on signals that tested negative (spec §16). At most an optional tradeability panel | X-e-7 |
| X16 | Confluence counted from source names; 0.85^touches and mitigation penalties; LFP's tests bonus and fixed cluster multiplier | EE 199, 493-520, 1505, 1527-1531, 1541; LFP 335-336 | C | Double-counts one price region (spec §5). Touches show about 0 effect (spec §4.4) | X-e-8, X-e-9, X-l-3 |
| X17 | Magenta DOL colour as the default | EE 353 | Preference conflict | Superseded by the neon green/red reference (§6, C6) | X-e-11 |
| X18 | LFP side-share % as a direction forecast; Video "▲ UP / ▼ DOWN" zones; "Sellers / Buyers" wording; the "pull is used up and price often turns" tooltip | LFP 54-65, 1300-1341, 1320-1321, 1324 | C, none | No predictive test. On driftless random walks it flips side about every 68 bars and is EXTREME on 7.35% of bars [ran]. Large background fills (spec §17). The sweep claim is contradicted by the data | X-l-1, X-l-2, X-l-5 |
| X19 | XAUUSD: 10-engine OR trigger set; additive point score; 3-target trade manager and sizing; session VWAP; HTF block | XAU 450-479; 515-634; 768-1057; 245-259; 360-371 | C / D | A forced-signal design. 38-46 of 96 points come from correlated trend features. Exits cannot create expectancy [study: trade_mgmt §1.4]. The VWAP never resets. The HTF block is superseded by P01 | I2 §2.15 |
| X20 | The whole Buy/Sell Indicator | BS 1-117 | C | v5; compile error; contradictory vote; untested marketing claims | I2 §3.7 |

---

## 4. Broken or duplicated functions and known defects

### 4.1 DOL Engine v2: the 49 audited findings, in summary form
- **Source:** `dev-notes/runs/overhaul-r1-findings.md`.
- **Counts:** 49 findings, 18 P1 and 31 P2 [lead: counted]. Only **3** are VERIFIED (cs-hvalid-equal-high, cs-mtf-anchor-print-bar, perf-1); 46 are "not yet verified". The exact patches are in `overhaul-r1-journal.jsonl`.
- **Grouping:** below they form 32 themes, about 35 distinct defects.
- **The "APEX" column** says where each fix lands (IDs from §3).

| # | Theme | Finding IDs (priority) | v2 lines | APEX |
|---|---|---|---|---|
| 1 | 76 input values printed in the chart legend | VIS-statusline-inputs, TE1, ux-statusline-inputs (P1 ×3) | 60-237 | R28 |
| 2 | Bias one HTF candle stale when the last bar is confirmed (weekends, after hours) | rp-bias-done, struct-F2 (P1 ×2) | 782, 926 | R01 |
| 3 | Swing CHoCH lag: protected level set from the BOS candle | struct-F1 (P1) | 755-774 | R01 |
| 4 | Table rows below the chart TF mislabelled; 4H/D charts in Day mode warn | TE2 (P1); rp-table-below-chart, struct-F3 (P2) | 68-82, 2303 | P23, R01 |
| 5 | Near-distance taper evicts the committed target just before the hit | dol-A, TE4 (P1 ×2) | 666-667 | R02 |
| 6 | Out-of-range targets (PoT about 0%) chosen or kept | dol-B, TE3 (P1 ×2) | 664-667, 1950-2020 | R02, R03 |
| 7 | Stack demotes key levels behind weaker pools | LIQ1, dol-D (P1 ×2) | 684-685, 1230-1251 | R05 |
| 8 | Pool trim deletes fresh arrays and the counter side | dol-C (P1) | 1950-1962 | R31 |
| 9 | No relative EQ between key levels | LIQ2 (P1) | 1824-1852 | R06 |
| 10 | PWH/PWL from a partial first period | rp-partial-pwh (P1) | 945-946 | P15, R07 |
| 11 | Daily chart: every candle becomes a PDH/PDL pool | TE5 (P1) | 945, 1790-1794 | P15, R07 |
| 12 | HTF FVGs dropped beyond 15 ATR | PD-1 (P1) | 1859 | R13 |
| 13 | MTF pools anchored at the HTF bar open, not the wick | cs-mtf-anchor-print-bar (**verified**), LIQ7 (P2) | 1223, 1783 | P10 |
| 14 | Exactly equal MTF pivot marked swept | cs-hvalid-equal-high (**verified**, P2) | 780 | R01 |
| 15 | Last-bar analytics run on every tick, even in Clean | perf-1 (**verified**, P2) | 2111 | P02, P03 |
| 16 | Killzones by bar open on 2H/4H charts | rp-kz-above-1h (P2) | 975 | R08 |
| 17 | EQ history lost on a slightly higher second swing | LIQ3 (P2) | 1762 | R06 |
| 18 | Killzone affinity boosts days-old session pools | LIQ6 (P2) | 1941 | X05 |
| 19 | Key extremes start "immature"; `hlMult` slows maturation | LIQ5, dol-E (P2) | 668-671 | R02 |
| 20 | Exact touch counts as neither test nor sweep | LIQ4 (P2) | 654 | P12 |
| 21 | Classic breaker never created; liquidity gate checks the wrong extreme | PD-2 (P2) | 1691, 1706 | R13 |
| 22 | OB not moved to the HL/LH retest candle | PD-3 (P2) | 1695 | R13 |
| 23 | OB quality gate almost always passes | PD-4 (P2) | 1688 | R13 |
| 24 | HTF FVG has no quality or direction check | PD-5 (P2) | 785-796, 942 | R13 |
| 25 | HTF FVG exempt from the origin lockout | dol-G (P2) | 689 | P22, R13 |
| 26 | iFVGs far behind never cleaned; 8 bands clutter; overlaps stack | PD-6, TE7, ux-ifvg-overlap-merge (P2 ×3) | 198, 1609, 1636 | P19 |
| 27 | Label shows "PoT 95%" after a live sweep; no TF in the code; no "no target" state | dol-F, VIS-swept-label, ux-clean-swept-label, TE6, VIS-no-target-state (P2 ×5) | 2225, 2305 | R30 |
| 28 | Displayed PoT never checked against outcomes | pot-ledger-calibration (P2) | 2067 | R09, P09 |
| 29 | `f_bump` can overflow `int` | pot-bump-floor-guard (P2) | 1268 | P07 |
| 30 | Light chart theme nearly invisible | VIS-light-theme-ink (P2) | 2219 | R34 |
| 31 | Ghost trail off by default, loud when on | ux-ghost-default (P2) | 210 | R29 |
| 32 | Alert text lacks direction, price and event names | TE8, ux-alert-content (P2 ×2) | 2083, 2090 | R33 |

### 4.2 DOL Engine v2: defects the study found and the audit missed
Each one is from I1 §2.9, with its study source.
1. **The raid → D mapping is wrong-signed** (1581). REJECT is scored as reversal, but the data lean slightly the other way (continuation) [study: ict_liq §0.2].
2. **The volume-profile path cost is wrong** (570, 1945-1947): 63-86% of the "thin" class are clamped beyond-range targets [study: amt_profile §0.2].
3. **With zero or na volume the profile features silently switch off** (997, 1007). This hits cash indices and many CFDs.
4. **Self-confluence** (676-680): PDH/PDL/PWH/PWL are their own anchors, worth about +5 points [study: calib_ml §0.10].
5. **The EQ merge is one-sided;** the outer branch (1116-1126) is effectively dead for chart pivots [study: ict_liq §0.8a].
6. **The breaker definition reproduces only 11-24% of template breakers** [study: ict_pd §0.3].
7. **The NY AM session range is wrong on 76% of 1H days,** because membership is tested at the bar open [study: ict_time §0.7].
8. **ETA, heat, EV and L50 are biased by construction** [study: skeptic §0.4].
9. **The EDGE verdict peeks:** 13.5% of 288 no-skill paths showed a false "✓" [study: skeptic §0.5].
10. **`f_calMult` is noise** [study: calib_ml §0.4].
11. **The ghost trail is survivorship-biased:** out-scored targets vanish without a ghost [study: skeptic §0.11].
12. **`ta.pivothigh` ties:** the newest equal bar wins, so tight double tops lose their EQ count and first-print anchor [study: smc_impl §0.5].
13. **Wyckoff lens:** registry re-entries (1848) and HTF FVGs (1862) take the *current* bar's coil and inducement, not the values at birth. The inducement score is ≥ 2/3 on 91-98% of bars, which makes it effectively a constant [study: wyckoff_sd §0, item 3]. Neither inspector listed this; I add it [lead: read in the study].

### 4.3 DOL Engine v2: duplication, non-repaint and performance
- **Duplicated logic:**
  - `f_potModel` (1303) and `f_potBase` (1314) repeat the empirical/analytic blend;
  - the iFVG right edge is updated twice (1641-1644 and 2145-2149);
  - `f_levelName` and `f_shortName` overlap [I1].
- **Non-repaint:**
  - PASS for `request.security`, pivots and the confirmed-bar gate.
  - Deliberately live: the PoT readout (2066), the sweep alert (2084, `alert.freq_once_per_bar`) and the Clean label after a sweep.
  - **Parity risk (PENG-10).** Cumulative learned state (`f_calMult`, `f_raceAdj`, the ledger) depends on where history starts. A reloaded chart, a server-side alert and Bar Replay can therefore pick different targets from the same prices [I1; study: pine_eng].
- **Performance:**
  - 6 request calls, three of them 12-tuples with 9 unused values;
  - levels tracked on every historical bar;
  - `f_raceH` up to 400 terms;
  - all drawings rebuilt on every tick.
  - Runtime on TradingView is **unmeasured** [I1].

### 4.4 Early DOL Engine
- **Dead:** `f_flagW` (490), `xSH..xSLW` (922), `rH/rD` (1187).
- **Duplicated:** `f_kindTxt`/`f_kindTxtK` (484-488); `f_tpPick`/`f_sqPick` (704, 1743); `f_potAll`/`f_potLive` (456, 2109).
- **Defects:**
  - `request.security_lower_tf(…, "1")` sits *below* the chart TF, inside an `if` (1034). It is not a repaint, but it breaks the no-lower-TF rule.
  - The seasonality loop runs on every bar *and every tick* (945-969).
  - The O(n²) scoring pair loop (1516-1527).
  - 186 inputs.
  - NQ/MNQ/ES/MES costs hard-coded by root (1053).
  - Unverified pre-filled FOMC dates.
  - The future calendar ignores session gaps (964).
  - STF/HTF pools anchored at the HTF bar open (1339).
  - No partial-period guard (810).
  - Confluence counts source names.
  - The "never without a DOL" fallback.
  - Score mixed with PoT [I1 §3.8].

### 4.5 Liquidity Flow Pro
- **Dead:** `adxVal` (885).
- **Duplicated:** `f_intrinsic` and the inline strength formula (952-953).
- **Defects:**
  - The directional claim in the Video tooltip and README (55, 61; README 24) contradicts its own "not a probability" header (12-17) [lead: read].
  - HTF pools are anchored at the HTF bar time, with `b = bar_index` (758).
  - Tests add strength (336).
  - "Sellers/Buyers" wording (1320).
  - The reversal tooltip (1324) [I1 §4.8].

### 4.6 XAUUSD Fast/Balanced Pro (I2 §2.11)
- **D1 BLOCKER, 731-746.** `f_killLines` reassigns the global line variables (declared at 725) inside a function, which is a compile error [doc, lead-verified]. Neither the static validator nor PineTS caught it.
- **D2 HIGH, 458-459, 475-476 (also 297-298).** `ta.crossover`/`ta.crossunder` are called inside lazy `and`/`or`, which corrupts their history [doc].
- **D3 HIGH, 99, 245.** The `"0000-0000"` VWAP session is a 24-hour, 7-day session, so the VWAP never resets [doc-reasoned]. PineTS instead returned VWAP = hlc3 on every bar.
- **D4 MEDIUM, 345-346, 395-396.** `ta.highest`/`ta.lowest` are called inside `if` blocks and ternaries.
- **D5 MEDIUM, 360-364.** `expr[1]` with `lookahead_off` times historical bars differently from realtime.
- **D6 MEDIUM, 801-856.** "AVG R (model)" is optimistic on same-bar TP1/SL.
- **D7-D10 LOW.**
  - A dual-use input (136).
  - "Opposite" spacing that really uses `barsSinceAny` (141-142).
  - Signals depend on trade state and equity (909-939).
  - Lines finalised for the wrong trade (862).
  - Cooldowns counted on `barstate.isnew` (665-668); unverified in a close-only strategy.
- **D11 dead:** `tSL0`.
- **D12:** buy and sell code duplicated as mirrors.
- **D13:** the "optimised for XAUUSD 3m" claim has no evidence.

### 4.7 Buy/Sell Indicator (I2 §3.4)
- **Compile error:** `label.style_label_lower` (116) does not exist [ran: validator; doc].
- **v5** (line 1).
- **`show_rsi` hides every signal** (81, 85).
- **Dead inputs** `show_ma`/`show_macd` (28-29).
- **A new label every realtime bar** (113-117).
- **No confirmation gate:** `alertcondition` fires intrabar.
- **Background fills.**

### 4.8 MNQ 5m ORB (I2 §4.5, §4.12)
- **Hard-coded to MNQ/NQ, 5m and NY constants** (`syminfo.root` check at 65; 09:30/16:00/18:00; a 0.25 tick in Python).
- **Early-close holidays not handled.**
- **`sslSwept`/`bslSwept` include the signal bar,** which contradicts the README's "earlier that morning".
- **The strategy's `canSignal` has no `barstate.isconfirmed` guard** if a user turns on every-tick recalculation.
- **Research code:**
  - the rejected-idea scripts and the bootstrap were never committed;
  - `verify.py` paths assume the original layout;
  - `package.json` is missing from the copy;
  - strategy metrics are printed, not asserted;
  - per-year slicing causes boundary effects (90 vs 91 sweep-ON trades in 2025).

### 4.9 Cross-cutting
- **No legacy file has a recorded TradingView compile.** Two are known not to compile (XAU, BS).
- **The early engine's CLAUDE.md demanded "0 errors and 0 warnings on TradingView's compiler before it is handed over".** That can only be met by the user pasting the script into TradingView. APEX must report compile status as **NOT RUN** offline and ask the user for the exact error and line, as I2 notes the user already does.
- **Static tools have blind spots** [ran: I2 T3, T6]:
  - the validator 0.4.3 and PineTS 0.10.0 miss global reassignment and lazy-evaluation hazards;
  - PineTS ran a script TradingView would reject;
  - PineTS diverges on session `time()` history.

---

## 5. Settings and user preferences

### 5.1 The visual reference (the user's target look)
Sources: `dev-notes/brief/reference_look.png` [lead: viewed], `CONTEXT.md`, and the v2 Clean code that reproduces it (v2 2214-2226, 2295-2307, 1607-1615).

| Element | What the reference shows | How v2 draws it (Classic theme) |
|---|---|---|
| Chart | Dark background; Gold futures 5m (COMEX) | — |
| **"Timeframe \| Bias" table** | Top right, compact, small text. Rows **D / 4H / 1H**; values **BULLISH** (green) / **BEARISH** (red). The screenshot reads D BULLISH, 4H BULLISH, 1H BEARISH | `f_cellC` cells; header background #25272C; bias green **#00C864**, bias red **#E63C3C**; NEUTRAL possible; a "⚠ CHART TF > EXEC TF" warning row (2295-2307) |
| **ONE target zone** | One translucent box with a **dashed** border, anchored **left at the origin candle**, extending right past the last candle | `box.new(aX, top, xR, bottom, border_color = color.new(c, 75), border_style = line.style_dashed, bgcolor = color.new(c, 92))`; right extension input default **20 bars** (176) |
| **Neon glow core** | A bright neon centre line with a glow | Five co-linear lines: widths 10/7/4/2 at transparency 90/80/60/30 in the side colour, plus a **white core** of width 1 at transparency **15**. Use **10** to match the reference (ΔE 6.7 → about 0.9) [study: ux_design §0.1] |
| **Tether** | A dashed line from the last candle to the label | `line.new(bar_index, close, xR, price, color.new(c, 30), line.style_dashed)` |
| **Label** | A dark box, two lines: **"Target: BEFVG"** / **"PoT: 70.1%"**, in the side colour | `label.style_label_left`, background `cLblBg` (dark), text colour = side colour, `size.normal`, centred, tooltip with the pillar breakdown |
| **iFVG boxes** | Two **dark-green** filled boxes below price, ending on the same right edge | Clean + Classic bullish iFVG: **#00B478**, border transparency 50, fill 75 (1607-1612); bearish uses #E63C3C |
| Side colours | The target above price is neon green | Buy-side (above) **#39FF14**; sell-side (below) **#FF1744**; panel **#000000** |
| Absent from the reference | No BUY/SELL markers, no forward path, no EMA lines, no oscillator panes, no background fills, a minimal legend (name only) | — |

The screenshot is of the commercial product's own page. APEX reproduces the *layout and style*, never its name, branding or code.

### 5.2 Colour preferences across the lineage

| Source | BUY / bullish | SELL / bearish | DOL target | Other |
|---|---|---|---|---|
| v2 Classic (latest, matches the reference) | #39FF14 buy-side; #00C864 bias | #FF1744 sell-side; #E63C3C bias | Side colour (green above, red below) | Black panels; iFVG #00B478 |
| Early engine (`CLAUDE.md` and inputs) | **Solid blue #2962FF, only on real trades** | **#FF4D6D red, only on real trades** | **Magenta #E040FB** (EE 353) | "Everything else stays white / grey / amber" |
| XAUUSD | #00c853 / #00e676 | #ff3d00 | — | Dashboard #101418 / #1b2027; cyan header #00e5ff |
| ORB | #089981 | #f23645 | — | OR #2962ff; prior day #ff9800; overnight #ab47bc |
| Buy/Sell | green triangles | red triangles | — | Background fills |
| APEX spec §14 | **Bullish path: green** | **Bearish path: red** | — | — |

### 5.3 Modes and timeframes
- **Trading modes:** Scalping, **Day Trading (default)**, Swing and Custom (v2, matching spec §11 and §23).
  - v2 maps them to HTF/STF/EXE: Swing W/D/4H; Day D/4H/1H; Scalping 1H/15m/5m; Custom 240/60/15. The chart must be ≤ the execution TF.
  - Spec §11 instead lists *three context TFs plus the chart as the execution TF*: Day = D, 4H, 1H + chart. That is consistent with the screenshot (5m chart, D/4H/1H table). See §6, C9.
- **Auto mode** from the chart TF (EE: ≤ 5m Scalping, ≤ 1H Day, else Swing), with auto-tuned distance, horizon and stop lookback.
- **FAST and BALANCED** (XAU): pure threshold presets on one engine.

| Setting | FAST | BALANCED | XAU lines |
|---|---|---|---|
| Minimum score | 42 | 58 | 131-132 |
| Minimum alignment groups (of 5) | 1 | 2 | 133-135 |
| Same-direction cooldown | 3 bars | 6 bars | 139-140 |
| Bars since any signal | 2 | 4 | 141-142 |
| Chop veto | ≥ 85 | ≥ 68 | 144-145 |
| Chase veto | ≥ 85 | ≥ 62 | 146-147 |
| Extreme-volatility veto | off | on (ATR ratio 2.8) | 154 |

None of these thresholds was ever tested [I2].

- **Strictness knob:** BS's "how many must agree" (`min_signals`) is the same intuition.
- **HTF role:** supporting evidence, not a veto, by default (XAU "strict HTF" off).

### 5.4 Instruments and sessions
- **Instruments:**
  - Gold futures 5m (the screenshot);
  - **MNQ1! and ES1!/MES1! on 1m and 5m, New York session, traded with real money on a prop account** (EE `CLAUDE.md`);
  - XAUUSD 3m (XAU header, unsupported by evidence);
  - MNQ/NQ 5m (ORB).
- **Sessions in use:**
  - v2: Asia 2000-0000, London 0200-0500, NY AM 0930-1200, America/New_York; killzones Asia 2000-0000, London 0200-0500, NY AM 0700-1000, NY PM 1330-1600;
  - EE: session pools Asia 2000-2359, London 0200-0500, NY 0930-1130 (EE 217-221); signal hours "Auto" = core 09:30-11:30 + 13:30-15:45 NY on futures, indices and stocks, any time on crypto and forex (EE 283, 1047); flat at 15:55 (EE 331);
  - LFP: Asia 1800-0300, London 0300-0830, NY 0830-1600;
  - ORB: OR 09:30-09:44, last entry 12:00, flat 15:50.

### 5.5 Wording
- **Plain trader terms:** Target, PoT, BSL/SSL, BUY-SIDE/SELL-SIDE, BULLISH/BEARISH, and short codes (PDH, PWL, ASIA H, HTF BSL, BEFVG, BUFVG, BUOB, BEOB, BUBRK, BEBRK).
- **Tooltips carry the detail.**
- **Status phrases:** "Watching for breakout", "Done for today".
- **Plain-language READMEs** with a "Read this first" risk box, install steps and tables.

### 5.6 Workflow and delivery
- **From the user's own notes** (EE `CLAUDE.md`):
  - reads the chart **on a phone and acts on colour alone**;
  - **"wants to always see where price is going"**: the banner always showed "DOL SAYS ▲ HIGHER / ▼ LOWER", "never just WAIT";
  - wanted to trade toward the DOL without waiting (trade mode DOL Direction was the default);
  - "Keep it fast; no long-running loops."
- **Delivery:** paste the **full script in ONE code block** in chat and send the file (EE `CLAUDE.md`, HANDOFF). The user is often on a phone.
- **Trade workflow** (EE, XAU, ORB):
  - BUY/SELL with entry, stop and target on the label and in alerts;
  - $-risk sizing; a daily loss limit; one trade at a time;
  - an alert when a trade closes.
- **Dashboard and debug:** a grade (A+/A/B/C), a regime readout, a compact dark dashboard, and a "why didn't it fire" debug view.
- **Verification:** asks for scripts to be verified several independent ways, and to be sent the exact error and line if TradingView rejects a script.
- **Communication:** a trader, not a programmer. Writes informally; wants short plain replies.

### 5.7 Honesty and non-repaint
- **Every product stresses non-repainting.** Titles say "[Non-Repaint]"; the engines are confirmed-bar.
- **The READMEs report losing results plainly** ("Nothing tested here is reliably profitable on its own"; "not a blind test any more") and say "not a probability" and "not a guarantee".
- **One counter-signal:** the user values a high win rate. The ORB target was retuned from 0.5R to 0.2R "for an ~86% win rate" (commit `9e0b0ce` title [I2]), and EE has a Target Win Rate mode.

### 5.8 v2 defaults worth carrying (I1 §2.5)
- Pivot length 5; EQ tolerance 0.10 ATR; zone depth 0.20 ATR; test proximity 0.30 ATR; min target distance 0.5 ATR; max distance 10 ATR; origin lockout 3 bars / must leave by 1.0 ATR.
- PoT horizon 30, volatility lookback 50; ledger warm-up 300; calculation depth 5000.
- Right extension 20; iFVG max closes inside 2; Clean style; Classic theme.
- **To change:** drift weight 0.5 → **0**; draw weight 30 → **neutral**; killzone hysteresis ×2 → **off**.

---

## 6. Conflicts between earlier preferences and the APEX spec, with recommended resolutions

The spec governs (HANDOFF: "supersedes"). Where a resolution changes something the user visibly asked for, the last column flags it for a one-line confirmation at delivery.

| # | Earlier preference (source) | APEX spec rule | Recommended resolution | Confirm with user? |
|---|---|---|---|---|
| **C1** | The reference look: "Timeframe \| Bias" table on, iFVG boxes on, no markers, no path (screenshot; v2 Clean default) | §17/§23 default display: **BUY/SELL markers + one forward path + minimal essential DOL information**; "unnecessary tables" off; FVGs and diagnostics optional and OFF | Make the default **APEX Clean**: BUY/SELL markers, one forward path, and the reference DOL element (ONE dashed neon zone with the glow core, tether and two-line label). That DOL element *is* the spec's "minimal essential DOL information", and it keeps the user's signature look. Offer a single **Display preset** input: "Clean" (default, spec) and "Clean + Bias table" (the exact reference layout: 3-row table + at most 2 merged iFVG boxes). The table shows confirmed structure state per TF, can read NEUTRAL, and its tooltip says "structure state, not a forecast". It is **off by default** per spec §17 | **Yes**: the table off by default is a visible change |
| **C2** | Label "Target: BEFVG / **PoT: 70.1%**", live tick-by-tick, capped at 95% (screenshot; v2 2225; reference product notes) | §4.7: call it a **Draw Score until statistically calibrated**; §15: a probability only for an empirically calibrated outcome frequency with a defined target, sample and horizon; §19.1: confirmed by default | Keep the two-line label slot. **Line 2 reads "Draw Score: 72"** (confirmed-bar value) until a **per-chart calibration gate** passes. The gate: prequential Brier skill > 0 against the distance-matched baseline (P08/P09), an anytime-valid test (R11), a reliability slope within a pre-set band, and a minimum n of resolved targets for *this* horizon. Only after it passes does line 2 read **"PoT 30b: 64%"**, with the event (touch of the near edge within H bars), H, n and Brier skill in the tooltip. It reverts to the Draw Score if the gate later fails. No 95% cap display; after a sweep it reads "Swept ✓". While the gate has not passed, the tooltip says "calibrating" or "no measured edge" instead of showing nothing. Evidence: the PoT *model class* is well calibrated in aggregate (slope 0.93-1.04 on 13 clean sets, 76,181 probes [study: calib_ml §0.1]), but it is ungraded per chart, carries the drift bias (+3.66% LL when removed) and is hour-biased by up to about ±17 pp on 5m [study: ict_time §0.1]. That is exactly what the gate is for. A live readout is also unstable: on NQ 1-minute paths the live PoT moves a median 10.9 pp inside one 1H bar (90th percentile 26.4 pp) and crosses 70% inside 27% of bars, so the label uses the bar-close value [study: x1_behavioral §0 items 5-6, non-final] | Yes: the user will see "Draw Score" until their chart earns "PoT" |
| **C3** | Terminal HUD with R:R, WIN≤H, EV, ETA, EDGE verdict; EE BUY NOW banner; XAU stats dashboard | §17: debug dashboard optional and OFF; §15: no fake confidence; §16: do not encourage trading because a signal exists | One optional debug dashboard, OFF by default, with reason codes and the honest ledger (win rate beside break-even and baseline, n and horizon). Drop the biased readouts (X02, X03) and the banner (X15) | No |
| **C4** | "Always see where price is going"; banner "DOL SAYS HIGHER/LOWER", never just WAIT; "never leave the chart without a DOL"; D-first selection (EE `CLAUDE.md`, EE 1583-1585, v2 1964-2035) | §13.3/§25: NEUTRAL is a legitimate output; "do not force BUY and SELL signals"; "when evidence is weak, remain neutral"; §4.7: output the best buy-side **and** sell-side targets | Always *compute* the best buy-side and best sell-side targets, so the user can always see where price could go. Show the selected DOL zone when one qualifies. The **signal state and the path direction may be NEUTRAL**. In NEUTRAL the path is drawn in neutral grey with its uncertainty band, and the label reads "No clear draw" instead of inventing a side. No fallback target that ignores the minimum score | **Yes**: this reverses an explicit earlier wish |
| **C5** | Colour-only reading on a phone: **blue = BUY, red = SELL**, colours only on trades; magenta DOL (EE `CLAUDE.md`, EE 353) | §14/§23: **green bullish path, red bearish path**; clear bullish/bearish colours | Default to green/red, in the Classic neon family (the later choice, consistent with the reference). Colour is the **direction of travel**: a buy-side target and an up path are green; a sell-side target and a down path are red; NEUTRAL is grey. Offer a "Blue/Red" marker palette for colour-only phone reading. Magenta is an optional theme only (X17) | Yes: ask whether they still want blue for BUY |
| **C6** | DOL colour = side of the target (v2), even when a signal points the other way | §4.8: destination ≠ reversal; §25: do not confuse a likely destination with an entry | Markers and path come from the decision engine (§13); the DOL zone colour comes from the target's side. If they disagree (e.g. a SELL signal while the nearest draw is buy-side), show both, and the tooltip explains "target above, bearish bias: price may sweep it first or reverse". No colour override | No |
| **C7** | FAST/BALANCED thresholds hand-set (42/58, cooldowns 3/6 …); 10 OR'd engines force signals (XAU) | §13.3: FAST favours responsiveness; BALANCED stronger confluence and confirmation; configurable thresholds, confirmation and persistence; **no invented probability percentages for modes** | Keep the names and the mental model (R23). One evidence engine; presets differ in threshold, persistence and spacing; values come from the pre-registered E2 experiment. Never show a win rate or probability per mode. No OR'd trigger set | No |
| **C8** | Entry/SL/TP1-3 on labels and in alerts; $-risk sizing; daily loss limit; one trade at a time (EE, XAU, ORB) | §16: tradeability assessment; label estimates incomplete when inputs are missing; do not encourage trading because a signal exists. §23 lists tradeability, not trade management | The signal tooltip and alert carry the **invalidation level, the selected target, R:R and a tradeability flag** (expected move vs user-entered costs in ticks). Position sizing, daily loss limit and partial-exit management are **not** in the indicator; at most an optional risk panel, OFF. A strategy twin (validation only) handles trade simulation | Yes: sizing and daily limits move out of the default |
| **C9** | Mode tables as HTF/STF/**Execution** with "chart ≤ Exec TF" and a red warning (v2) | §11: execution = **chart** TF; Day = D / 4H / 1H as context; "starting templates, not universal laws" | Rename the rows to HTF structure / Primary context / Confirmation, with the chart as execution. Auto-fit with EE's ladder (P23) so a 4H/D chart in Day mode moves the stack up instead of warning (TE2). Rows stay D/4H/1H in the default Day mode, as in the screenshot | No |
| **C10** | Hard-coded instruments, hours and costs: MNQ/NQ root lock, NY constants, 15:55 flat, NQ/ES cost table, "tuned for 1m/5m", "XAUUSD 3m" (ORB 65; EE 1053; XAU header) | §2.1: universal; never hard-code calculations for XAUUSD or NQ; account for tick size, sessions and volume quality | Everything instrument-specific comes from `syminfo` plus inputs. Sessions are configurable, with exchange-timezone defaults. Costs are a user input in ticks (default "unknown" → tradeability marked "incomplete"). Asset-class presets at most, never per-symbol constants | No |
| **C11** | LFP "▲ UP xx% / ▼ DOWN yy%" as a likely direction; large background zones | §17: no large background fills; §15/§25: scores are not probabilities | Drop (X18). Side balance may appear as a feature in the debug dashboard only | No |
| **C12** | A high win rate as a goal (ORB 0.2R retune, Target Win Rate mode) | §15/§20: baselines, calibration, sample sizes; never imply edge from a win rate | Every win rate is shown **with its geometric break-even and a baseline**, n and horizon (§7.1). No Target Win Rate mode (X12) | No |
| **C13** | Live PoT and an intrabar sweep alert (v2 2066, 2084; reference product notes) | §18/§19.1: alerts on confirmed conditions; live features labelled and kept out of confirmed alerts by default | Confirmed alerts by default. The live sweep becomes an opt-in "provisional" alert, labelled as such. Live readouts carry a "live" marker (P17) and are never the default label value (see the intrabar instability in C2) | No |
| **C14** | Reference product: the bias table "removes lagging Neutral states" | §11: if timeframes disagree, reduce confidence or stay neutral | The table may read NEUTRAL. Disagreement between rows lowers the Forecast Quality score (§13 F) | No |
| **C15** | "Compile with 0 errors and 0 warnings on TradingView before hand-over" (EE `CLAUDE.md`) | §19.2: no compile errors; §24: if a test cannot be run, mark it as not run | Doc-grounded engineering with the layered offline checks (R26). The compile is marked **NOT RUN** in VALIDATION_REPORT. The user is asked to paste any TradingView error and line | No (process) |

---

## 7. Lessons learned from earlier tests

### 7.1 What the data supported

| Lesson | Evidence (sample, dataset) | Source type | Class / grade |
|---|---|---|---|
| **Distance and volatility drive whether, and which, liquidity is touched** | Early: Brier skill analytic ≈ 0.14, empirical + analytic 0.192, v6 learning 0.201 (26 datasets: 13 markets × 5m/1h, about 1.1M bars, about 519k resolved targets, 70/30 time split) [claim]. Study: pools beyond distance +0.1 ± 0.4 pp (1H, 7 datasets, n 52,762) [study: ict_liq §0.1]; geometric race 65.3% vs 65.8% predicted (n 12,148) [study: ict_struct] | claim + study | A strong |
| **The analytic first passage is correct; drift hurts** | Reflection identity 2.00 on CME 5m and 1H [study: quant_pot §0.4]; drift removal +3.66% LL (CI +2.99 to +4.32, 326 symbol-days) [study: quant_pot §0.2] | study | A strong |
| **The empirical excursion surface is calibrated** | Slope 0.99, ECE 0.004 (1.2M 5-min rows) [study: calib_ml §0.1] | study | A strong |
| **Expected reach d·PoT(d) is the better ranking objective** | 1.10-1.43 ATR per target vs 0.86-1.09 (hand score) and 0.66-0.93 (nearest), 13 intraday/1h sets [study: calib_ml §0.8] | study | A moderate |
| **The intraday volatility clock is real** | Hour bias in v2's PoT up to −17 pp at 08:00 NY and +11 pp at 21:00 (about 1.2M level-windows) [study: ict_time §0.1] | study | A strong |
| **One time-of-day effect exists beyond volatility: the US cash-open drive in index futures** | 20-minute windows starting 09:20-09:59 ET take the prior 60-minute high or low +10 to +15 pp more often than a variance clock predicts (observed 90-93% vs model 79%; 1-min ES/NQ/YM/RTY, 60 days, day-clustered SE 1.6-3.2 pp). Absent at 08:30, after 10:00 and in CL/GC [study: ict_time §0 item 2] | study | A moderate. An empirical time-of-day surface learns it; a pure volatility clock cannot |
| **Keying the PoT surface by volatility state helps** | Partial pooling by volatility tercile: +1.79% log-loss (CI +1.45 to +2.13), all 6 symbols, 5-min [study: quant_pot §0] | study | A strong |
| **Volatility state persists; trend labels do not** | Volatility correlation 0.49-0.80 between consecutive windows; ER/CHOP/Hurst about 0 [study: quant_regime §0] | study | A strong |
| **Equal highs/lows at 1H are the only pool attribute that survives a multiple-testing correction** | EQ +0.29 logit (t +3.6), Holm p 0.007, 1-hour group; null at 5-min. Distance-matched reach of EQ is +0.3 ± 1.8 pp (1H) [study: calib_ml §0.6; ict_liq] | study | A weak. A candidate feature for the gated shadow ledger, not a default weight |
| **Dealer gamma and its Pine proxies are a volatility-state input, not a direction input** | SPX daily 2011-2026 (n 2,665 days): range/ATR20 falls from 1.154 (low-gamma quintile) to 0.803 (high), t −10.8 beyond VIX-implied σ. VIX/VIX3M term structure + VIX-implied σ recover about 75% of that gain [study: x1_positioning §0 item 1, non-final] | study (non-final) | A moderate; candidate σ/regime input on index charts |
| **Crypto perpetual funding tilts which side is run first** | BTC 1h 2019-09 to 2025-01 (7,444 decided races): negative funding → BSL first +5.2 ± 2.1 pp above calibrated geometry; sign holds in both halves [study: x1_positioning §0 item 5, non-final] | study (non-final) | A weak; crypto only, gated per chart |
| **Opposing untouched FVGs in the path reduce reach** | −2.8 ± 0.8 pp at 1H (n 4,757); −2.1 ± 1.0 at 5m (n 3,387); negative in 11 of 12 datasets [study: ict_liq §0.4] | study | A moderate (the only supported ICT path claim) |
| **Win rate is set by target/stop geometry** | ORB at 0.2R: observed 85.7%, driftless random walk 83.3%, cost-adjusted break-even 84.6% (729 trades, NQ 5m 2023-2025) [ran: I2 T4]; BE = 1/(1+RR) [study: trade_mgmt §1.2] | ran + study | E strong |
| **Costs dominate short-horizon futures signals** | ORB PF 1.24 → 1.16 → 1.08 as round-trip cost goes 1.5 → 2.5 → 3.5 pts (729 trades) [ran: I2 T1]. MNQ/MES 1m: −0.08R (NQ) and −0.17R (S&P) per trade from costs; filters cut NQ from 20,031 trades (−1,655R) to 2,460 (−75R) (about 3.7 years, about 420 NY sessions per market) [claim] | ran + claim | E strong |
| **ORB breakout direction carries a little in-sample information** | Beat 99.55% of 2,000 random-direction draws with the same geometry (random median PF 0.98); bootstrap 95% CI for mean P&L/trade −$0.52 to +$12.60 (t = 1.87) [ran: I2 T4]. The 2026 MNQ file has PF 0.74 (41 trades). Study: Mesfin 2026, 947 MNQ RTH days, year-unstable [study: session_stats §2.10] | ran + study | C weak |
| **Next-open fills, stop-first same-bar resolution and the candle-colour intrabar order are honest defaults** | `bt.simulate` reproduced every README number [ran]; colour rule 88.1% vs 80.6% (about 140k CME bars vs 1-minute truth) [study: pine_eng §0.4] | ran + study | E strong |
| **The Target Win Rate controller works, but has no edge** | Targets 85/90/95% realised 84.9/89.6/93.7% on 12 markets; about 0R per trade before costs [claim] | claim | A (mechanics) / no edge |
| **A small persistent cross-asset effect exists** | Sister-swept state: pool hit lift 1.035-1.042 (about +1.5 to +1.9 pp), placebo 1.006 [study: smt_inter §0, item 3] | study | A weak; a candidate feature, gated |
| **Implied volatility is a second-order σ input** | Geometric blend over the clock + fast realised level: +0.3 to +1.6% LL on 1H sets; IV alone is worse [study: x1_implied_vol §0, non-final] | study (non-final) | A weak |

### 7.2 What the data rejected

| Idea | Evidence (sample, dataset) | Source type | Class / grade |
|---|---|---|---|
| **Liquidity type, HTF bias, sweeps, premium/discount, confluence and the DOL score as predictors** | No out-of-sample value for touch or side (26 datasets) [claim]. The DOL side was taken first 59.3% of the time, equal to distance alone (59.3%) [claim]. Study replicates: tests/tier/confluence/prominence Holm p 0.07-0.23 [study: calib_ml §0.6] | claim + study | C, strong null |
| **The draw vector D as a side predictor** | D right 47.4-52.7% on 8 markets; matched random walks 48.4-52.1% [study: ict_struct §0.1]. D-first selection −3.8 to −8.3 pp on 7 datasets [study: bias_dol §0.4] | study | C, strong null |
| **Sweep → reversal** | Sweep Reversal: 1,350 trades, 38% win, −0.06R/trade (MNQ/NQ and S&P 1m/5m; 4 weeks 1m + 10 weeks 5m CME + 6 weeks 1m index, Mar-Apr 2025) [claim]. With the order-flow filter: 357 trades, +0.09R, positive only in Mar-Apr 2025 [claim]. Study: REJECT → continuation +1.5 ± 0.7 pp at 1H (n 12,550) [study: ict_liq §0.2]; Turtle Soup ≤ geometry on 9 datasets [study: bias_dol]; MSS 49.4% (n 4,032) [study: ict_struct] | claim + study | C, moderate-strong |
| **DOL Direction trading** | 1,235 trades, 53% win, −0.02R/trade [claim]. HTF-aligned break setups won 48.7% *with* the signal vs 49.8% against it (1-ATR symmetric) [claim] | claim | C |
| **Order-flow proxy filter** | A 10-20 minute window lost about 0.05R less per trade with about half the trades; not significant; still negative after costs (19 days 1m + 49 days 5m CME + 42 days 1m index) [claim] | claim | C weak |
| **FVG, OB and breakers as targets** | FVG +0.4 pp (n 1,756) CME 1H; −0.6 pp (n 4,950) 5m. Breakers −4.9 to −8.3 pp (CME 1H) [study: ict_pd §0.1, §0.3]. The engine's FVG quality is not a target signal: rejected FVGs +7.0 pp (z 3.3, CME 1H) [study: ict_pd §0.2] | study | C |
| **iFVG retest as a continuation signal** | First retest holds 49.1-50.2% (n 25,244) [study: ict_pd §0, item 4] | study | C |
| **Killzone and macro windows beyond the volatility clock** | Macro +0.6 ± 0.5 pp (61k windows); Silver Bullet +0.2 ± 0.6 [study: ict_time §0.6] | study | C |
| **Midnight open as a magnet** | +0.3 ± 1.1 pp (1,412 instrument-days) [study: ict_time §0.8] | study | C |
| **Volume-profile levels and the thin-path bonus** | POC/VAH/VAL reached at random-level rates; the thin-path bonus is wrong-signed or null [study: amt_profile §0.1-0.2] | study | C |
| **Wyckoff spring/UTAD → the opposite side** | Spring excess +0.007 ± 0.032 (n 209) and +0.018 ± 0.027 (n 301) [study: wyckoff_sd §0] | study | C |
| **Compression → expansion breakouts continue** | NR7 first-break ±1 ATR race 0.482-0.515 vs null 0.479-0.517 [study: quant_regime] | study | C |
| **SMT as a reversal signal** | 50.5% vs 50.8%, n 16,258 / 16,187 [study: smt_inter §0, item 1] | study | C |
| **Market internals (TICK, ADD, VOLD, TRIN) for which pool is taken first** | No incremental value on 35-37 sessions (1,571 race events); a fake t = 14.3 appeared before time alignment [study: x1_internals §0, non-final] | study (non-final) | C |
| **LFP side share as a direction** | Never tested on outcomes. On driftless random walks it flips about every 68 bars and is EXTREME on 7.35% of bars (6 seeds × 3,000 bars) [ran] | ran | C, none |
| **Sweep-first filter (ORB)** | In-sample PF 1.24 → 1.62 (729 → 290 trades, 2023-25); out of sample PF 0.83 (23 NQ trades) and 0.51 (18 MNQ trades) in 2026 [ran: I2 T1] | ran | C weak |
| **Targets below 0.2R** | 0.1R: PF 1.14 in-sample, 0.58 on 2026 NQ [ran: I2] | ran | C |
| **ORB-lineage filters and alternatives** | EMA 9/21/50 pullback + VWAP (PF about 0.9); RSI(2) mean reversion (about 65% win, PF 0.87-0.97); 30-minute OR; HTF, VWAP, ADX, volume, gap and OR-size filters; extra trades per day; limit retest entries; profit-lock stops: all did not help or lost [claim; scripts not committed] | claim | C weak |
| **ICT sweep reversals, ORB, noise-boundary momentum and first-half-hour momentum on MNQ/MES 1m; linear and GBM walk-forward models on about 20 features** | None reliably profitable after costs (about 3.7 years Dukascopy, about 420 NY sessions per market) [claim] | claim | C |
| **High-capacity online learners** | All 20 ICT features: Brier skill 0.192, below 0.201 (over-fits) [claim]; ungated learners lose to the baseline [study: calib_ml] | claim + study | C |
| **Voting that ANDs a state with events** | Buy/Sell 3-of-3 fired 0 times in 3 years on NQ 1H (17,396 bars) and 4H (4,718 bars); RSI + MA never co-occurred [ran: I2 T5] | ran | E (combinatorics) strong |
| **Cost-basis levels (swing-anchored VWAP) as magnets** | Reached exactly as often as distance implies: NQ 15m −0.5 / −0.6 ± 0.5 pp (n about 11,500 per side), NQ 1h +0.7 / −0.4 ± 1.0 pp; a time-weighted placebo gives the same numbers [study: x1_behavioral §0 item 2, non-final] | study (non-final) | C. VWAP belongs in §7 as context, not as a target family |
| **"The SMC/ICT crowd changed how levels behave"** | Same-instrument pre-2019 vs post-2021 (BTC 1h, EURUSD 1h, SPX daily): reach beyond distance unchanged (e.g. EURUSD −0.1 ± 2.3 pp; SPX −2.9 ± 4.0 pp vs a placebo of −2.1 ± 3.6); sweep depth unchanged [study: x1_behavioral §0 item 1, non-final] | study (non-final) | C. No era-aware priors |
| **COT positioning, max pain and OPEX-week flows** | COT (E-mini S&P 2008-2026, 723 weeks) does not predict which side of the prior week's range is taken first (t −0.3 and +1.4). Max pain adds nothing over "close near the prior close" on SPX 2004-2026 [study: x1_positioning §0 items 3-5, non-final] | study (non-final) | C |

### 7.3 Method lessons
1. **A spent holdout is no longer evidence.** The 0.5R ORB rule lost on both 2026 files (−$224 NQ on 50 trades, −$1,674 MNQ on 41). Then 0.2R was chosen after seeing them [ran: I2]. APEX needs a pre-registered holdout that is never retuned (Phase 6).
2. **Selection at the edge of a fragile grid means over-fitting.** The selected ORB cell is the best 0.2R cell, and 5 of its 8 neighbours have PF < 1 in at least one period [ran: I2].
3. **Commit every script that produces a reported number.** The early engine and the ORB rejected ideas are unreproducible.
4. **PineTS parity holds per construct; PineTS is not a compiler.** It ran a script TradingView rejects, and it diverged on a session VWAP. APEX needs custom lints and a runtime-parity register (R26).
5. **Look-ahead and time misalignment manufacture edges.** A leaking daily read: 49.6% → 59.5% [study: pine_eng]. Internals misaligned by 585-930 s: t = 14.3 → −0.4 [study: x1_internals].
6. **Peeking at a running z-score produces false "EDGE".** 13.5% of 288 null paths showed one [study: skeptic]. Use anytime-valid tests.
7. **Ungated adaptive weights are noise at per-chart sample sizes** (`f_calMult`; per-chart MDE 5.5-9.5 pp per 5,000 bars [study: x1_tv_validation, citing skeptic §0.7]).
8. **Net lesson.** Geometry (distance, volatility, the clock) is the backbone. ICT labels, sweep reversals, fixed bias votes and named levels failed every test. Costs dominate. Features start neutral and earn weight per chart behind prequential gates. Default to neutral when evidence is weak.

---

## 8. What APEX must build new (spec §3-18)

Status of the best legacy material: **EXISTS** (meets the spec in substance), **PARTIAL** or **MISSING**. The constraint column states what the evidence allows.

| Spec § | Requirement | Best legacy material | Status | Must be built new | Evidence constraint |
|---|---|---|---|---|---|
| 3 | Structure: swings, internal/external, HH-LL, BOS/CHoCH/MSS, displacement, failed breaks, compression/expansion, P/D, dealing ranges, "knowable-at" | v2 708-782, 898-904, 888-891; LFP typing 694-733, 853-868; EE `SEvt` 144, 1201-1216 | PARTIAL | An explicit event stream with knowable-at bars; failed breakout/breakdown; dealing range from `protH/protL`; P/D on the chart (optional); compression/expansion states | Structure events carry no side skill (MSS 49.4%). They are descriptive features and context, not votes |
| 4.1-4.3 | BSL/SSL sources: PD/PW/**PM**, sessions incl. NY PM, swings, EQ/relative EQ, clusters, range, **opening range**, historical extremes, internal liquidity | v2 945-961, 1752-1865; EE PMH/PML; ORB OR and ONH/ONL | PARTIAL | PMH/PML; opening-range pools; NY PM; relative EQ across key levels; major historical extremes; retracement liquidity | Pools are not magnets beyond distance; sources are a *map*, not weights |
| 4.4 | Clustering with tick/ATR tolerance, constituents, touches, age, time between touches, sweeps, reactions, acceptance | LFP 461-503; v2 1090-1131 | PARTIAL | A cluster record holding the member list, a touch history with time between touches, and reactions and acceptance as attributes | Touches add no strength |
| 4.5 | 10-state lifecycle (Candidate → Expired) with exact transitions | LFP sweep/taken/test 784-837; v2 delivery and registry; EE ghost reasons | PARTIAL (implicit) | **New:** an explicit state machine (Candidate, Confirmed, Active, Approaching, Swept, Reclaimed, Rejected, Accepted beyond, Mitigated, Expired) with formal transition rules and no double counting | Band from wick depths (median 0.23-0.28 ATR) |
| 4.6 | Sweep intelligence: probe vs reclaim vs acceptance vs failed break; follow-through | LFP 784-837; v2 1504, 1580-1582 (wrong use) | PARTIAL | Event classes with close location, wick/body, displacement and follow-through measurement | No reversal edge; REJECT leans to continuation |
| 4.7 | Best buy-side AND sell-side targets with price, ticks, ATR, Draw Score, reason codes, state | v2 661-696, 1964-2035 | PARTIAL | **New:** two-sided output; distance in ticks; reason codes; the Draw Score name; path-barrier cost | d·PoT(d) objective; opposing-FVG cost the only supported path term |
| 4.8 | Destination vs post-target reversal as separate processes | none | **MISSING** | **New:** a destination model (reach/race) and a separate post-touch reaction model, with its own ledger | Post-sweep reaction ≈ coin flip at 1 ATR; stay neutral unless the per-chart ledger shows otherwise |
| 5 | FVG, iFVG, OB, breaker, mitigation block, BPR, void, displacement, OTE, CE; formation, invalidation, mitigation, age, size, freshness, reaction; no double counting | v2 907-912, 1566-1748, 785-796; EE in-place transitions | PARTIAL | Mitigation blocks, BPR, liquidity voids, OTE zones; the corrected breaker; overlap-merging so one region is counted once | Zones are context and display; target weight neutral |
| 6 | Wyckoff and AMT proxies (balance, acceptance, value migration, IB, opening auction, trend day) | v2 VP 1384-1424 | **MISSING** | Labelled *proxies* only: balance/imbalance from the range and volatility state; IB; value migration from the session VWAP/VA estimate; acceptance as time beyond a level | Wyckoff events and VP levels are null beyond geometry; never claim accumulation or distribution |
| 7 | RVOL, volume percentiles, session/anchored/rolling VWAP, VWAP deviation, VAP, POC/VA estimates, volume around breakouts and sweeps; source and feed limits | LFP `volOK`, RVOL; EE RVOL, volume-delta proxy; v2 VP | **MISSING** (VAP partial) | **New:** a VWAP family with a correct reset (`ta.vwap` with an anchor or `timeframe.change`, not the broken XAU code); RVOL and percentiles; a data-quality flag for zero or na volume; proxy labels | No bid/ask in Pine; never manufacture order flow; the volume-delta proxy is optional |
| 8 | EMA 20/50/100/200, slope, separation, RSI, MACD, ROC, DMI/ADX, VWAP, regression slope, acceleration, divergence, persistence; redundancy control | XAU momentum composite 212-218; LFP pressure | **MISSING** | **New:** a feature block grouped into de-correlated families (trend, momentum, mean reversion), each normalised, counted once per family | Trend regime adds nothing to the side choice beyond geometry [study: quant_regime] |
| 9 | ATR percentile, realised vol, range percentile, expansion/contraction, clustering, vol-of-vol, gaps, abnormal moves, trend/range/transition regimes with hysteresis | EE `atrPct` 1022-1025, spike 1012-1019; XAU chop/chase | PARTIAL (weak) | **New:** a regime classifier with percentile thresholds and hysteresis; compression vs expansion; abnormal-move flag; gap handling | Volatility state persists and is the useful regime; trend labels are noisy (ER20 ≥ 0.40 on 15.7% of random-walk bars) |
| 10 | Statistics toolbox, defined target/sample/horizon/validation | v2 400-503, 1265-1336, 1461-1499; EE Brier | EXISTS (core) | Robust stats (MAD, percentiles), calibration curve data, log-loss, a Brier scorecard on the chart | — |
| 11 | MTF hierarchy, modes, provisional vs confirmed HTF, disagreement → lower confidence | v2 60-82, 564, 923-936; EE ladder 731-735 | PARTIAL (strong core) | Auto-fit; an explicit provisional HTF state (display only); a disagreement penalty in Forecast Quality | Use `[1]` + `lookahead_on` only (P01) |
| 12 | Intermarket (DXY, yields, metals, oil, indices, BTC), rolling correlation and its stability; manual event windows; fail soft | EE manual event windows 291-306, 981-1011 | **MISSING** | **New:** a configurable reference-symbol module with rolling correlation and stability; graceful `na`; manual event windows | SMT reversal is null; a small persistent sister-swept effect (+1.5-1.9 pp) is a candidate gated feature; internals add nothing |
| 13 | Scores A-F (regime, directional bias, buy-side draw, sell-side draw, setup quality, forecast quality); normalisation; data-quality weights; STRONG BUY … STRONG SELL; FAST/BALANCED | XAU FAST/BALANCED, debug gates; LFP LOW DATA | **MISSING** | **New:** the whole decision engine. Six separate scores, a signal state machine with thresholds, confirmation and persistence, NEUTRAL, and explicit data-quality weights | No tested directional edge exists yet (§7.2). Thresholds must come from E2 and be validated after costs; default to NEUTRAL |
| 14 | One conditional forward path (20-120 bars, default 60), green/red, components, uncertainty from out-of-sample residuals | v2/EE reach bands (uncertainty seed only) | **MISSING** | **New:** a volatility-scaled conditional scenario path with a target-aware shape and an empirical prediction interval by horizon and regime | No method has beaten a random walk in the lineage. Pending E1. The path must be honest about uncertainty and stay neutral when evidence is weak |
| 15 | Heuristic vs ranking vs confidence vs calibrated probability; Brier, log-loss, calibration, precision/recall, baselines | v2 ledger + baseline; EE SKILL | PARTIAL | The per-chart calibration gate and label policy (C2); outcome definitions; baseline comparisons on the chart | — |
| 16 | Spread, slippage, tick size, contract specs, session liquidity, stop distance, R:R, gaps, event risk; "incomplete" labels | EE cost/stop/sizing (NQ-specific); v2 `f_invalidation` | PARTIAL | **New:** an instrument-agnostic tradeability module (expected move vs costs, poor-location flag) | Costs dominate short horizons (§7.1) |
| 17 | Clean default (markers + one path + minimal DOL); diagnostics optional and OFF | v2 Clean 2214-2226, 2295-2307 | PARTIAL | BUY/SELL markers; the forward path; Display presets (C1); `display.none`; one-click toggles for the liquidity map, sessions, HTF levels, FVGs, OBs, structure labels, debug dashboard, target scoring, uncertainty | — |
| 18 | Alerts: BUY, SELL, STRONG BUY/SELL, neutral transition, new target, target reached, sweep, confirmed reclaim, forecast changed, forecast invalidated; no duplicates | v2 2079-2093; EE 13 alertconditions; LFP one rich `alert()` per bar | PARTIAL | **New:** the full set on confirmed conditions, with de-duplication and rich content | — |

**Build order this implies for Phase 4/5** (lead recommendation; the architect decides):
1. **Platform core:** P01-P03, R28. No behaviour change.
2. **Liquidity map, lifecycle and clustering:** §4.1-4.6, built from P10-P17, R05-R08, R22.
3. **Probability core with zero drift, the clock and per-chart grading:** P04-P09, R09-R12, R15, R38.
4. **Two-sided ranking:** R02-R04 with the destination/reaction split (§4.8).
5. **Feature blocks:** regime, volume/VWAP, momentum, structure events (§3, §7-§9) as neutral features with data-quality flags.
6. **Decision engine and signals:** §13, after E2 results.
7. **Forward path and uncertainty:** §14, after E1 results.
8. **Tradeability:** §16.
9. **Display presets, alerts and the debug dashboard:** §17-18.

---

## 9. Open questions and unverified items for the architect
1. **TradingView compile status** of every legacy file is unverified. Two are known not to compile.
2. **46 of the 49 audit findings are unverified.** Their patches sit in `overhaul-r1-journal.jsonl`. The overhaul workflow may be applying them to the live file now. APEX should cite the frozen baseline and re-check after the overhaul lands.
3. **Early-engine statistics are README claims;** the scripts are absent. They agree with the later study, which raises confidence but does not make them reproducible.
4. **The 24 pre-filled FOMC dates** in the early engine are unverified. Do not ship them unverified.
5. **Runtime on large 1-minute histories** is unmeasured for every engine.
6. **The user's current view of three earlier wishes** is unknown: "always show a direction" (C4), blue/red colour-only reading (C5) and in-indicator sizing (C8). The spec overrides them; confirm at delivery.
7. **Spec §13 and §14 have no tested foundation in the lineage.** E1 (forecast paths) and E2 (signals) are pre-registered but have no results yet.
8. **Data caveats** [I2]:
   - the public NQ 1m file is cut at 1,048,576 rows (it ends 2025-12-11);
   - its contract-roll construction is unknown.

---

## 10. Sources

**Opened in this session (lead):**
- `apex/research/inspection/I1_dol_lineage.md` and `I2_signal_lineage.md` (read in full).
- `dev-notes/brief/APEX_ULTIMATE_SPEC.md` (in full), `HANDOFF.md`, `CONTEXT.md`, `tradeaxis_description.md`, `reference_look.png`, `README.md` (first 80 lines), `apex/legacy/README.md`, `dev-notes/runs/overhaul-r1-findings.md`.
- All legacy files: byte comparison with their origin commits, plus the line spot-checks in §0.2. Origin-branch file lists for all 10 remote branches; `32e460f:CLAUDE.md`; `99f7390:research/verify_pinets/package.json`.
- Pine v6 docs mirrors:
  - `mmmy_pine-script-doc-v6/pine-script-docs/language/user-defined-functions.md:32, 811`;
  - `…/concepts/sessions.md:39-47`;
  - `jabez4jc_pinescriptv6/migration_guides/to_pine_version_6.md:777-809`.
- Study reports, grepped for the quoted numbers: `quant_pot`, `ict_struct`, `bias_dol`, `ict_liq`, `ict_time`, `calib_ml`, `skeptic`, `ux_design`, `amt_profile`, `ict_pd`, `smc_impl`, `pine_eng`, `session_stats`, `trade_mgmt`, `quant_regime`, `wyckoff_sd`, `smt_inter`, `orderflow_micro` (`.final.md`), and the non-final `x1_positioning`, `x1_internals`, `x1_implied_vol`, `x1_tv_validation`.
- I2's saved outputs: `<scratchpad>/i2/baselines_output.txt`, `verify_output.txt` (tail), `buysell_output.txt`.

**Executed (lead):**
- `python3 -I apex/legacy/liquidity_model_sim.py`: 15/15 pass.

**Relied on from the inspectors without re-running:**
- I2's ORB backtest reproduction (T1) and PineTS harness run (T2). I read their outputs only.
- I1's unused-identifier scan.

No web sources were used.
