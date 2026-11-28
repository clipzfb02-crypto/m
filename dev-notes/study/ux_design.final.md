# Premium indicator UX and visual design: combined final study (researcher A + researcher B)

**Domain.** What makes a TradingView overlay indicator look premium and stay readable:
- status line (legend) hygiene and settings UX;
- label, table and typography design;
- contrast on dark *and* light charts;
- colour semantics, cultural conventions and colour-vision safety;
- glow, layering and z-order;
- clutter control, label collisions and right-edge layout;
- drawing-object lifecycle;
- how probability and timing are communicated, and how display stability affects trust.

The lens is the forecasting problem: the display should help the trader read **where** price is drawn, **when**, and **how likely**, and nothing more.

**Provenance markers** (this file merges A's `ux_design.md` with B's verification and extension):
- **[A]** from researcher A, not re-checked;
- **[A✓]** from A, verified by B (source re-opened, re-computed or re-grepped);
- **[B-corr]** A's claim corrected or downgraded by B (what changed is stated);
- **[B-new]** added by B.

**Conventions.**
- All line numbers refer to `brief/baseline_v2.pine`, which is byte-identical to `/home/user/m/indicators/dol_engine.pine` (checked with `diff`).
- Proposal IDs are prefixed `UX-`. Cross-references: `COMP-n` (competitors.final.md), `PENG-n` (pine_eng.md), `SMC-n` (smc_impl.final.md). Where proposals overlap, the overlap map in §4.0 says which one to implement.

**Working files.**
- A (`study/ux_tools/`): `contrast.py` (WCAG contrast, alpha compositing, Machado 2009 CVD simulation), `light.py`, `mock.py` → `mock_light_theme.png`, reference crops `ref_*.png`.
- B (`study/ux_b_tools/`):
  - `sample_ref.py`: independent pixel sampling of the reference;
  - `zorder_check.py`, `core_fit.py` → `core_compare.png`: the core-line correction (§2.1);
  - `light_check.py`: re-check of all light-theme and CVD numbers, including deuteranomaly;
  - `inputs_audit.py`: input, tooltip and inline audit;
  - `ext/`: 8 open-source Pine v6 repositories (24 indicator files), cloned read-only for the practice survey (§2.5). Concepts were learned from them; no code was copied.

**Research limits.**
- A: Firecrawl credits ran out after 1 call; the shared WebSearch budget ran out after 5 searches; WebFetch could not reach w3.org, nature.com or northwestern.edu.
- B: Firecrawl was again out of credits. About 17 WebSearch calls ran before the shared per-turn budget was exhausted. WebFetch could not resolve pubmed.ncbi.nlm.nih.gov, mucollective.northwestern.edu or csc2.ncsu.edu (blocked by the session network). B therefore relied on search-result summaries for the literature, on the local official Pine v6 docs for platform facts, on GitHub clones for practice, and on reproducible computation. Every number taken from a search summary rather than the paper is flagged as such.

---

## 0. Executive summary

1. **The Clean style reproduces the reference almost exactly. One small correction applies.** [A✓, B-corr]
   - B re-sampled the screenshot independently (vertical profile at x = 800, 900 and 1000; histograms of the label, table and iFVG). Every glow layer, the fill, the border, the iFVG fill (`#002D1E`) and border, the label background (`#161616`) and all four table colours match A's values.
   - **Correction.** A composited the box fill *under* the glow. In Pine, boxes always render *above* lines (z-index: lines 6 < boxes 7). For the four same-colour glow layers the order does not matter (same-colour compositing commutes), so A's ±1 RGB match stands. For the white core it does matter:
     - the engine's real core pixel is `#D3FACB`, ΔE 6.7 from the reference `#DDFCD8`;
     - `color.new(color.white, 10)` instead of 15 gives ΔE 0.9 (UX-10).
   - **Also confirmed: candles draw over the zones in the reference.** Pure `#FFFFFF` candle pixels appear unblended inside the iFVG box. So the reference, like the engine, uses the default `behind_chart = true`. Keep it.
2. **The biggest visible gap is the status line.** [A✓]
   - 76 of 104 inputs are int, float, string, session or timeframe inputs. Pine's default for those is `display.all` (reference/input.md:27), so about **411 characters of default values** print after "DOL Engine v2". The reference legend shows only the name.
   - Same finding as COMP-1 and PENG-1: implement it once.
   - **B-corr.**
     - The affected range is lines 60–229, not 59–216: `tz`, the 7 session/killzone inputs (219–227) and `theme` (229) are included.
     - A's `active` map had three errors: `useBRK` must not depend on `useOB`; `fvgMin` must stay active; `obLook` depends on `useOB or useBRK` (§3).
   - **B-new.** The four colour rows (230–237) put titles on both inline inputs. That misaligns them under the October 2026 alignment model and raises compiler warning CW10026.
3. **On a light chart the DOL is invisible.** [A✓]
   - Every Clean element composites to 1.04–1.37:1 against white; WCAG asks 3:1 for graphics.
   - The fix needs two colour roles: dark variants for graphics on the chart, and the neon text kept on the dark label and table. A light variant on `#161616` drops to 3.08–3.31:1.
   - **B-corr.** A's open risk, "does a background change recalculate?", is answered by the docs: scripts that use `chart.fg_color` or `chart.bg_color` reload when the user changes the chart background (execution_model.md:498). UX-2 is safe.
4. **Lines render below boxes.** [A✓] iFVG, LVN and ghost boxes therefore draw over the DOL glow and tether wherever they overlap, which happens during exactly the iFVG retests the product promotes (UX-8).
5. **Communicating WHEN and HOW LIKELY.** [A, B-corr grades]
   - Showing uncertainty improves decisions. In a bus-arrival-time task, quantile dotplots with 50 outcomes reached 97% of optimal payoff (95% CI 95–98%), 5 points above a no-uncertainty control. CDFs did nearly as well, and both beat text (Fernandes et al. CHI 2018).
   - Uncertainty forecasts improved decisions and *trust*, and softened the damage done by forecast errors (Joslyn & LeClerc 2012) [B-new]. That matters because roughly 30% of 70%-PoT targets will miss.
   - A's "natural frequencies 7% → 45%" was not verified. The competitors B-pass found a meta-analysis figure of 4% → 24%, so the grade for our use is moderate [B-corr].
   - The three ledger-graded display proposals stand: UX-3 (counter-draw state and split), UX-4 (ETA band with coverage check) and UX-5 (alignment cue and split).
6. **Colour carries meaning beyond position.** [A, B-corr, B-new]
   - Red-presented financial data lowered risk-taking by about 15–30% (a press-summary figure) across 8 experiments with 1,451 people (Bazley et al. 2021, *Management Science*). The effect was absent in colour-blind subjects and muted in China.
   - Transfer to "a sell-side target drawn in red" is indirect, so the grade for our use is weak [B-corr].
   - Red means *up* in Chinese, Japanese, Korean and Taiwanese market convention [B-new]. A one-switch "red-up" option costs almost nothing (UX-6).
   - CVD: about 8% of European men (Birch 2012). Most of them are anomalous trichromats (deuteranomaly ≈ 5%), for whom the bias pair keeps ΔE ≈ 53. Only the ≈ 2% who are dichromats see A's worst case of ΔE 17 [B-corr nuance].
7. **Premium matters beyond taste.** [B-new]
   - Perceived usability tracks perceived beauty (Kurosu & Kashimura 1995, 252 participants; replicated by Tractinsky 1997).
   - A meta-analysis found a *small* effect of aesthetics on objective performance (Thielsch et al. 2019; 25 studies, 101 effects, about 3,025 participants).
   - Clutter measurably slows visual search (Rosenholtz, Li & Nakano 2007).
   - A unique-luminance target is found pre-attentively, in under about 200–250 ms (Healey & Enns 2012).
   - Together these justify "one bright target, everything else dim, legend clean", and they make the user's "SO BAD" complaint plausibly a perception-of-quality problem as much as a logic problem.
8. **Open-source practice survey** [B-new] (24 recent Pine v6 indicator files in 8 GitHub repositories):
   - 0 hide their inputs from the legend;
   - 1 uses `active`;
   - 4 adapt to the chart theme with `chart.fg_color` / `bg_color`;
   - 22 use tooltips;
   - 10 update drawings with setters.

   Legend hygiene and theme adaptivity are rare even in modern scripts, which makes them cheap differentiators.

---

## 1. Concepts (definitions and parameters)

Each concept gives a precise definition, the parameters that matter, its role for WHERE / WHEN / HOW LIKELY, how practitioners use it, and its failure modes.

### 1.1 Status line (legend) hygiene [A✓, B-new numbers]
- **Definition.** The script's status line shows the title, followed by the value of every input whose `display` includes `display.status_line`, followed by plot values whose `display` includes it.
  - Inputs: "The default is `display.all` for all input types except 'bool' and 'color' inputs, which use `display.none` by default" (concepts/inputs.md:112).
  - The reference says the same: `display` is a `const plot_display`; "The default depends on the type of the value passed to `defval`: `display.none` for `bool` and `color` values, `display.all` for everything else" (reference/input.md:27).
  - Values: `display.none`, `display.data_window`, `display.status_line`, `display.all`.
- **Layering of settings** [B-new].
  - The chart-wide "Status line › Indicator arguments / values" settings override the script's own display settings.
  - Users *can* hide the arguments themselves, but most never change the defaults. The author's default decides what most people see.
- **Engine numbers** [B-new].
  - With defaults, the legend prints about 411 characters: "Day Trading 240 60 15 3 5000 14 5 0.20 0.10 0.75 … America/New_York 0000-0100 … Classic".
  - That is 2–4 wrapped lines at common pane widths.
- **DOL role.** None directly. Clutter competes for attention with the single target.
- **Practice.**
  - The reference legend reads "TradeAxis DOL" only.
  - TradingView's own publishing guidance: "the script's status line should show its name" (writing_scripts/publishing.md:122).
  - In the OSS survey, 0 of 24 files hide inputs (§2.5).
- **Failure modes.**
  - Wrapped legend over candles.
  - Internals exposed in the legend invite tinkering.
  - `display.none` also removes the inputs from the Data Window, which is fine.

### 1.2 Input UX: groups, inline alignment, tooltips, `active`, ordering, progressive disclosure [A, B-new]
- **Definitions.**
  - `group` collects inputs under a header; groups appear in order of first appearance.
  - `inline` puts inputs on one row.
  - `tooltip` adds an (i) hover. On an inline row, only the last tooltip shows (inputs.md:98).
  - `active` (input bool, July 2025): "If `false`, the input is grayed out, and users cannot change the value" (release_notes.md:506).
- **B-new: inline alignment model** (release notes, October 2026; errors/CW10026.md).
  - Inline inputs now align with non-inline ones only when the *first* input on the row has a title and every other input on that row has an *empty* title `""`.
  - Otherwise the compiler warns CW10026 and the row misaligns.
  - The engine's rows `c1`–`c4` (230–237) title both fields ("Custom · Buy-side" / "Sell-side"), so they trigger the warning 4 times. PENG-1 found this first.
- **B-new: progressive disclosure.**
  - Show the few settings a trader needs first. Put tuning internals behind an "Advanced" header, optionally greyed out by an "Unlock advanced tuning" toggle.
  - This is a long-standing HCI convention (Nielsen's "aesthetic and minimalist design" and "recognition rather than recall" heuristics) [weak; convention, not measured here].
- **DOL role.** Indirect. Mis-set sessions or timezone silently mislabel PDH, Asia and killzone levels, which corrupts scoring and target selection.
- **Practice.**
  - Simple settings first, internals last.
  - Colour presets instead of raw pickers: "Providing a selection of color presets … can help color-challenged users" (visuals/colors.md:400).
  - Publishing guidance: use `minval`, `maxval` and `options` (publishing.md:109).
- **Failure modes.**
  - 104 inputs in a flat list.
  - Session strings without a stated timezone.
  - Inputs that do nothing in the current mode but look editable.
  - Wrong `active` dependencies that grey out inputs which still matter (A made three such mistakes; §3).

### 1.3 Reference-fidelity palette and layered glow [A✓, B-corr]
- **Definition.** A "neon" line is N co-linear lines of increasing width and transparency plus a near-white core.
  - The Pine manual endorses "multiple plots for the same line … modulate the successive width and transparency" (visuals/colors.md:406–410).
  - It also advises "zero transparency … to keep [important lines] crisp" (colors.md:404).
- **Engine parameters (Clean, 2214–2226).**
  - Zone box: fill `color.new(c, 92)`; dashed border `color.new(c, 75)`, width 1.
  - Glow lines as (transparency, width): (90, 10), (80, 7), (60, 4), (30, 2).
  - Core: `color.new(color.white, 15)`, width 1.
  - Tether: `color.new(c, 30)`, dashed, from (`bar_index`, `close`) to (`xR`, `price`).
  - Label: background `cLblBg` = `#161616` (Classic), `size.normal`, centred, `style_label_left` at `xR = bar_index + extBars` (20).
- **Measured geometry** [A✓ by B's independent profile at x = 800/900/1000, rows 497–522].

  | Rows | Colour | Element |
  |---|---|---|
  | 497 | `#18560E` | border (anti-aliased) |
  | 498–503 | `#041402` | fill |
  | 504–505 | `#0A2B04` | t90 glow |
  | 506 | `#135508` | t80 glow |
  | 507 | `#229A0D` | t60 glow |
  | 508 | `#32E113` | t30 glow |
  | 509 | `#DDFCD8` | core |
  | 510–513 | — | mirror of the glow |
  | 514–521 | — | fill |
  | 522 | — | border |

  - Total glow is 10 px with a 1 px core, so the widths 10/7/4/2/1 are confirmed.
- **B-corr: z-order and the core colour.**
  - Boxes are always above lines (visuals/overview.md:240–246), so the engine's own fill (t92) is composited *over* the glow and the core.
  - Same-colour layers commute, so the glow matches either way. The white core does not: under the box fill, t15 renders `#D3FACB` (ΔE 6.7 from the reference), while t9–t10 renders `#DEFCD9` / `#DCFCD6` (ΔE 0.4–0.9).
  - A ΔE of about 2.3 is one just-noticeable difference, so 6.7 is visible side by side but not alone.
- **DOL role.** WHERE. The glow makes the single target the brightest object on the chart.
- **Failure modes.**
  - An additive glow has no meaning on a light background (§1.6).
  - For a 2-px-tall liquidity zone the 10-px glow overflows the box; it still reads as "the level".
  - **B-new.** For far-anchored targets (PWH/PWL or HTF levels thousands of bars back), the 10-px band spans the whole visible chart. Candles stay on top (§1.4), but the band dominates the pane. This is faithful to "anchored left to the origin candle".

### 1.4 Layering, z-order and drawing behind price [A✓, B-new]
- **Definitions.**
  - Ascending z groups: background colours < fills < plots < hlines < linefills < **lines < boxes < labels < tables**.
  - "Within the same group, elements created last … appear on top" (visuals/overview.md:230–246).
  - Only plots, hlines and fills can be re-ordered (`explicit_plot_zorder`).
  - **B-new.** `indicator(behind_chart = true)` is the default: "visuals overlayed in the main pane appear behind the chart bars" (overview.md:36–38). The user can override it with "Visual Order / Bring to front".
- **Evidence from the reference** [B-new]. Inside the reference iFVG box, candle pixels are pure `#FFFFFF` and `#808080`. If the box (t75 teal) were above them they would read about `#BFECDD`. So the reference draws zones behind candles, and the engine, which leaves the default, does too.
- **Consequences.**
  - The DOL glow and tether (lines) sit under every iFVG box (fill t75), LVN box (t91) and ghost box (t94) where they overlap. They also sit under the DOL's own fill, which is intended.
  - The DOL box is created last, so it is above the iFVG boxes.
  - Labels sit above all boxes; the table is above everything, including the DOL label if they overlap.
- **Failure modes.**
  - During an iFVG retest, the tether start and the glow are tinted and dimmed by the t75 iFVG fill.
  - A top-right table can hide a DOL label near the top of the pane (§1.13).
  - Never set `behind_chart = false`: zones would tint the candles inside them.

### 1.5 Visual hierarchy, pre-attentive pop-out and clutter [A, B-new evidence]
- **Definition.** Visual weight (luminance contrast × area × saturation) should rank elements by importance.
  - Pine manual: "When you make everything stand out, nothing does" (colors.md:398).
  - Engine on black: core 18.9:1 > glow 11.9 > tether 7.5 > iFVG border 3.4 > DOL border 2.15 > fills 1.1–1.4 [A✓ recomputed].
- **B-new evidence.**
  - **Pop-out.** A target that differs from its neighbours in one pre-attentive feature (hue or luminance) is found in under about 200–250 ms, independent of the number of distractors (Healey & Enns 2012, IEEE TVCG 18(7):1170–1188; via search summary).
    - The neon core is the only near-white, high-luminance horizontal object, so it pops out.
    - Anything else at similar luminance competes: LVN `#FFC400` at 13:1, the Terminal HUD text, or secondary lines if they were bright.
  - **Clutter.** Feature-congestion and edge-density clutter measures predict visual-search performance in complex displays (Rosenholtz, Li & Nakano 2007, *J. Vision* 7(2):17; replicated with eye movements by Henderson et al. 2009). Colour variability adds clutter.
  - **More information, more confidence, not more accuracy.** Tsai, Klayman & Hastie (2008, *OBHDP* 107(2):97–105): 3 studies; confidence rose with information while accuracy plateaued. The 63%-accuracy and 68%-confidence football figures come only from a blog summary.
- **DOL role.** WHERE. One committed target, not a menu.
- **Engine.** The extras (secondary targets, objective, invalidation, reach bands, candidate pool, LVN, ghosts) are off by default (162–171, 203, 210). That is correct.
- **Failure modes.** The user turns on all the extras. Several bright, saturated colours (LVN amber, ghost labels) then break the hierarchy.

### 1.6 Contrast and theme adaptivity [A✓, B-corr, B-new]
- **WCAG 2.x.**
  - Contrast ratio = (L1 + 0.05) / (L2 + 0.05), with L the relative luminance from linearised sRGB.
  - Text: 4.5:1, or 3:1 for large text (≥ 18 pt, or ≥ 14 pt bold), SC 1.4.3.
  - Graphics: graphical objects "required to understand the content" need 3:1 against adjacent colours, SC 1.4.11.
  - **B-corr.** A wrote that line charts are "explicitly in scope". The normative text is the "required for understanding" qualifier. "All lines must pass" is a conservative testing practice from secondary sources. For the DOL the distinction does not matter: price *location* is conveyed only graphically, so the zone and core are required for understanding.
- **Pine mechanics.**
  - `chart.bg_color` and `chart.fg_color` are `input color`.
  - fg = `#dbdbdb` on dark backgrounds and `#0f0f0f` on light ones.
  - The manual's light test: `bool isLight = chart.fg_color == #0f0f0f` (concepts/chart_information.md:430–449).
  - Gradient backgrounds return the midpoint for `bg_color`.
- **B-corr (resolves A's open risk).** "The script uses the `chart.fg_color` or `chart.bg_color` variable, and the user changes the chart's background color" is listed among the events that reload the script (language/execution_model.md:498). A theme switch therefore re-renders the DOL in the right palette.
- **Manual guidance.** "At a minimum, test your visuals … with both the light and dark TradingView themes; they are the most commonly used. Colors such as black and white, for example, should be avoided" (colors.md:394).
  - The engine's Clean core is white, and the Classic panel is pure black (`#000000`), though the label and table are dark grey blends.
- **B-new practice.** 4 of 24 OSS files use `chart.fg_color` for neutral text and `chart.bg_color` for table backgrounds.
- **B-new technique.** `label.style_text_outline` (since August 2022, release_notes.md:933) draws text without a box. Presumably the `color` argument becomes the outline (halo) colour; verify in the editor.
  - A `chart.bg_color` halo around side-coloured text keeps transparent-background labels legible over candles and zones on either theme.
  - This is the cartographic "text halo" technique [weak; convention].
- **DOL role.** WHERE. Below 3:1 the target is not perceived.
- **Failure modes.** Neon on white; white core on white; transparent-background labels with neon text on white; changing the text colour of dark panels with the theme (dark panels already work on both themes).

### 1.7 Colour semantics: side, affect, culture [A, B-corr, B-new]
- **Definition.** The engine colours by **draw side**: buy-side (above price) is lime, sell-side is red, regardless of kind. That is why a bearish FVG above price reads "Target: BEFVG" in lime in the reference [A✓; engine line 2203].
- **Affect** [B-corr].
  - Bazley, Cronqvist & Mormann (2021, *Management Science* 67(9):5616–5641): 8 experiments, 1,451 participants (KU news release). Red-presented financial data lowered risk-taking and return expectations and prolonged pessimism.
  - The SMU press summary gives "15% to 30% depending on the context", and about a 25% higher required risk premium when losses are shown in red.
  - The effect was absent in colour-blind subjects, muted in China, and not produced by other colours.
  - **Grade.** Strong as a laboratory finding. **Weak** for our use: their red marked losses or declines, while ours marks a level below price.
- **Culture** [B-new].
  - In mainland China, Japan, South Korea and Taiwan the market convention is red = up, green = down (Benzinga explainer; widely documented, but the explainer is a weak source).
  - A green sell-side target there reads "bullish", the opposite of the intended side cue. Bazley's "muted in China" result fits this.
- **Failure modes.**
  - Kind-coloured zones would contradict side colouring.
  - A hue-only state cue (for example "counter-draw = amber").
  - Red sell-side targets may lower willingness to act (unmeasured here).

### 1.8 Colour-vision-deficiency safety and redundant encoding [A✓, B-corr nuance]
- **Prevalence.**
  - Red-green CVD affects about 8% of European men and about 0.4% of women, and 4–6.5% of Chinese and Japanese men (Birch 2012, *JOSA A* 29:313–320; abstract via search). "Northern European" is not the abstract's wording.
  - **B-new breakdown** for Caucasian men: deuteranomaly about 5%; protanopia, deuteranopia and protanomaly about 1% each (University of Arizona ophthalmology resource; Memorial University gives 1.2–1.3% each).
- **Simulation (CIE76 ΔE).**

  | Pair | Normal | Deuteranomaly ≈ 0.6 [B-new, approx.] | Deuteranopia (Machado 2009, severity 1.0) [A✓] | Protanopia |
  |---|---|---|---|---|
  | DOL buy/sell `#39FF14`/`#FF1744` | 170.5 | 78.6 | 37.0 | 85.6 |
  | Bias bull/bear `#00C864`/`#E63C3C` | 129.5 | 53.0 | **17.1** | 38.1 |
  | iFVG/bear `#00B478`/`#E63C3C` | 119.8 | 53.0 | 30.6 | 25.0 |
  | Okabe-Ito `#0072B2`/`#E69F00` | 120.2 | n/a | 121.7 | 109.5 |
  | Proposed `#2F9BFF`/`#FF8A1F` | 132.1 | n/a | 133.7 | 119.2 |

  - The ≈ 0.6 column linearly blends the identity with the Machado dichromat matrix. That is an approximation, not Machado's published severity matrices.
- **Remedies.**
  - A CVD-safe palette (blue/orange; Okabe & Ito 2008, Wong 2011 [unverified this session]).
  - Redundant cues: position, text, glyph, line style.
- **Engine redundancy already present.** Side follows position relative to price; the table says BULLISH / BEARISH in words; iFVG direction follows position.
- **Failure modes.** Any future hue-only state cue.

### 1.9 Typography [A✓]
- **Definition.** v6 text sizes accept `size.*` or int points.
  - Labels: tiny ≈ 7, small ≈ 10, normal 12, large 18, huge 24.
  - Tables and boxes: tiny 8, small 10, **normal 14**, large 20, huge 36 (visuals/text_and_shapes.md:488–500; reference/label.md:177; reference/table.md:67).
  - Note that `size.normal` differs between labels (12) and tables (14).
  - `text_formatting` sets bold or italic; `text_font_family` is default or monospace.
- **Engine.**
  - Clean label: `size.normal` (12 pt), default font.
  - Clean table: `size.small` (10 pt), default font, centred (604–610).
  - Terminal: monospace.
- **Measured reference.** Label to table text height ratio ≈ 1.2, consistent with 12/10 [A].
- **Failure modes.**
  - Monospace in Clean looks "terminal".
  - Fixed sizes are small on 4K screens and large on phones. Int points allow a size input (UX-1).

### 1.10 Probability communication (HOW LIKELY) [A, B-corr, B-new]
- **Definition.** A probability readout has four parts:
  - the value;
  - its precision;
  - the horizon ("within H bars");
  - the reference class ("of N similar targets, K were hit").
- **Evidence.**
  - Natural frequencies help Bayesian reasoning.
    - **B-corr.** A's "7% → 45%" was not verified. A meta-analysis gives about 4% → 24% (McDowell & Jacobs 2017, *Psych. Bull.*, via the competitors B-pass).
    - Hoffrage, Krauss, Martignon & Gigerenzer 2015 (*Front. Psychol.* 6:1473) reports large gains in complex tasks.
    - Grade **moderate for our use**: showing k-of-n is not a Bayesian inference task.
  - More decimal digits are read as more confidence (Jerez-Fernandez, Angulo & Oppenheimer 2014, *Psych. Sci.* 25(2):633–635) [A✓ via competitors].
  - **B-new: dual verbal + numeric.** Lay readers in 24 countries (25 samples) read verbal probability terms as nearer 50% than intended. Adding numbers to the words improved consistency: about 40% vs 26% correspondence (Budescu, Por, Broomell & Smithson 2014, *Nature Climate Change* 4:508–512; the numbers come from Budescu's 2016 IPCC slides, a secondary source).
    - The Terminal HUD's "70.1% · CORE" already is a dual format. Clean is numeric-only, which is fine.
- **Engine.**
  - "PoT: 70.1%" shows no horizon or reference class (2225).
  - After a live sweep it shows "PoT: 95.0%" (2067), which presents a reached target as a probability.
  - The tooltip holds the pillars but not the price, horizon or calibration (2206–2209). COMP-4 owns the tooltip and the "✓ Reached" text.
- **Failure modes.** False precision; no horizon; uncalibrated numbers shown as fact.

### 1.11 Uncertainty display, trust and display stability [B-new]
- **Definition.** Displaying forecast uncertainty, and keeping the display stable, protects user trust when a forecast misses.
- **Evidence.**
  - **Showing uncertainty improves decisions** (Fernandes, Walls, Munson, Hullman & Kay, CHI 2018, Best Paper Honourable Mention; incentivised).
    - Quantile dotplot with 50 outcomes: 97% of optimal payoff, 95% CI 95–98%, +5 pp vs a no-uncertainty control.
    - CDFs did nearly as well; textual intervals were worse and sensitive to the interval communicated [B-corr precision; A had attributed the 97% to both].
  - **Uncertainty forecasts help decisions and trust.** Joslyn & LeClerc 2012 (*J. Exp. Psychol.: Applied* 18(1):126–140; road-salting task, 3 experiments): uncertainty forecasts improved decisions, increased trust, and attenuated the reluctance to act that grows with forecast error.
  - **Cry wolf.** LeClerc & Joslyn 2015 (*Risk Analysis*): false alarms reduce compliance, and adding a probability improved both compliance and decision quality.
- **DOL role.** HOW LIKELY and trust.
  - A target that flickers (the PoT filter oscillating at `minPoT`; G21 in PENG-4) or silently jumps reads as a false alarm.
  - A miss shown alongside its stated PoT ("expected 30% of the time") does not erode trust the way an unexplained miss does (COMP-5).
- **Failure modes.** Unstable visibility; silent replacement; no record of past calibration.

### 1.12 Timing communication (WHEN) [A]
- **Definition.** Expected time-to-target, conditional on reaching it: the empirical median and 80th percentile of bars-to-hit for past targets at a similar distance.
  - The engine computes the median as `etaHit` (2117–2126): hits within ±0.5 ATR of the current distance, n ≥ 5.
- **Evidence.** Fernandes et al. is literally a *when-will-it-arrive* task, so showing time uncertainty as a band is directly supported (moderate). Whether this tool's ETA is valid is unknown; UX-4 measures it.
- **Engine.**
  - Terminal HUD only ("ETA|hit ~Nb", 2240).
  - Clean shows nothing.
  - The 20-bar right extension carries no time meaning.
- **Failure modes.** An ETA read as a promise (it is conditional on a hit); bars mistaken for clock time across session gaps.

### 1.13 Right-edge layout, label collisions, clipping and table overlap [A, B-new]
- **Definition.** Labels anchored at `xR` with `style_label_left` stack vertically by price. Two collide when their price gap is smaller than the label height expressed in price units.
- **Label height.** About 36 px for a 2-line `size.normal` label (measured). At typical zoom that is about 4–7% of the visible price range.
- **Engine.**
  - Clean default has one label, so no collision.
  - These anchor at `xR` without de-overlap: secondary targets (2188), objective (2166), invalidation (2212) and LVN box text (2278).
- **B-new: clipping.**
  - The label body extends right of `xR`: about 91 px, roughly 20 bars at the reference's 4.25 px/bar.
  - In the reference, the last candle sits about 180 bars left of the price scale, which is a user-scrolled view.
  - With a small chart right margin, the label at `bar_index + 20` is clipped by the price scale until the user scrolls. TradingView's default right margin is believed to be about 10 bars [unverified this session].
  - Pine cannot read the visible range without reloading on every scroll (`chart.right_visible_bar_time`; execution_model.md:497). So the only remedies are tooltips and documentation (UX-1).
- **B-new: table overlap.** The table (z 9) is above labels. A DOL label near the top of the pane can sit under a top-right table when the right margin is small. Remedies: the existing Position input, and UX-8's guard.
- **B-new practice.** OSS scripts de-overlap by priority-ordered placement against a list of used prices, with a minimum gap. One profile script uses 6 profile rows and drops the clashing label. A liquidity map merges labels within 1 × ATR.
- **Failure modes.** Overprinted labels when extras are on; clipped labels on narrow or mobile screens.

### 1.14 Drawing-object lifecycle [A✓, B-new pattern]
- **Limits.**
  - 500 lines, 500 boxes and 500 labels, with the oldest garbage-collected (visuals/lines_and_boxes.md:22).
  - x up to `bar_index + 500` (limitations.md:381).
- **Setters vs recreation.** "Utilizing these setters is typically less computationally expensive than creating a new drawing object"; `box.new()` costs about twice two setter calls in the manual's profile (profiling_and_optimization.md:1074–1112).
- **Rollback.** On realtime bars, an object created on an unconfirmed update is deleted on the next update (text_and_shapes.md:478). A recreated label is therefore a *new object every tick*.
  - That is a plausible reason a hover tooltip closes on fast symbols [hypothesis; PENG-5 reaches the same inference].
- **B-new: OSS hide pattern** (seen in 10 of 24 files that use setters).
  - Pre-create objects as `label.new(na, na, "", style = label.style_none)` and `box.new` with `na` colours.
  - Show and hide them with `set_xy`, `set_text("")`, `set_style(label.style_none)` and `set_bgcolor(na)`.
  - This also answers PENG-5's "verify that `na` coordinates are accepted": a published v6 script uses exactly that constructor.
- **Engine.**
  - iFVG boxes use `box.set_right` (1638–1641, 2145–2149).
  - The Clean zone, 5 glow lines, tether and label (8 objects) are deleted and recreated on every tick (2132–2141, 2214–2226).
  - Ghosts are FIFO-capped. `f_x` clamps x to the 5000-bar time buffer (404).
- **Failure modes.** CPU per tick; tooltip and selection lost [hypothesis]; stale-object bugs in setter code.

### 1.15 Data Window and plot formatting [A✓]
- **Definition.** `plot(format, precision)` sets the digits in the Data Window, status line and scale; precision 0–16 (visuals/plots.md:164–170; reference/plot.md:244–245).
- **Engine.** The five `display.data_window` plots (2444–2448) inherit symbol precision: 5 decimals on FX.
- **Related.** COMP-7 turns "DOL Price" into a price-scale tag (`display.data_window + display.price_scale`; `display` on `plot` is `input plot_display`, so an input can switch it).

### 1.16 Bias table design and alignment cue [A✓]
- **Definition.** A two-column table, Timeframe | Bias, with three rows (HTF, STF, Execution).
- **Measured reference colours** [A✓ by B's histogram]: header `#25272C` with text `#D5D5D6`; body `#1B1F24`; grid `#3A3C43`; frame `#303136`; BULLISH `#00C864`; BEARISH `#E63C3C`; TF `#FFFFFF`; rows 20 px.
- **Engine.** Exact (294–299, 2294–2307).
- **Contrast.** BEARISH is 4.00:1 (below 4.5 for 10 pt), which is faithful to the reference. NEUTRAL `cGhost` is 4.57:1.
- **Usage doctrine.** The spec says "look for execution signals when the Execution TF bias aligns with the HTF bias". The table never states alignment or ties it to the target.
- **Failure modes.** No hover detail (why bullish? what would flip it?); no alignment cue.

### 1.17 Autoscale compression [A✓ via competitors]
- **Definition.** Drawings far from price widen the auto-scale range and squash the candles. The user-side fix is "Scale price chart only" (TradingView help 43000762934).
- **Engine.** Proximity and eject limits bound the pool levels. LVN zones, the objective and the reach bands are not distance-capped (COMP-7 owns the fix).

### 1.18 Target state communication [A, B-new evidence]
- **States:**
  - active, draw-side;
  - active, counter-draw;
  - reached (intrabar);
  - stale (older than H without a hit);
  - filtered (PoT below the minimum);
  - none.

  Each should be visible without relying on hue.
- **Engine.**
  - Terminal shows "⚠ COUNTER-DRAW" and "✕ SWEPT" (2237).
  - Clean shows counter-draw only in the tooltip (2206).
  - "Reached" shows as 95% (2067).
  - Stale and filtered targets vanish silently.
- **Evidence.**
  - State visibility is a heuristic (weak).
  - The trust results in §1.11 (Joslyn & LeClerc) make silent changes costly (moderate, indirect).

### 1.19 Confidence encoded as visual weight [A, B-corr]
- **Definition.** Map the forecast confidence (PoT or score) to opacity or blur.
- **B-corr evidence.** MacEachren et al. 2012 (IEEE TVCG 18(12):2496–2505) rated *fuzziness* and *location* most intuitive for uncertainty, *transparency* moderate, and *saturation* low, with direction mattering (more blur or more transparency = more uncertain). The tests used discrete point symbols, not lines.
  - A had listed "fuzziness, transparency and value" as the most intuitive; transparency was only moderate.
  - Grade **weak** for a line glow.
  - **Design consequence.** A wider halo *is* fuzziness, so "more glow for higher PoT" points the wrong way. Map low PoT to *more transparency* at fixed widths, and keep the core crisp.
- **Engine.** Terminal maps score to zone opacity (2228). Clean uses fixed weights.

### 1.20 Tooltips as progressive disclosure [A, B-new caveat]
- **Definition.** Keep the chart minimal and put detail one hover away.
  - `label.new(..., tooltip)` is used (2226).
  - `table.cell(..., tooltip)` (table.md:53, 69) is unused.
  - Boxes and lines have no tooltips.
- **B-new.** Whether TradingView mobile shows Pine label tooltips on tap is undocumented (searched; nothing found). Assume no. Essentials ("Target", "PoT") must stay in visible text.
- **Failure modes.** Detail visible only on desktop; tooltip closes on tick-by-tick recreation [hypothesis].

### 1.21 Aesthetic-usability and premium perception [B-new]
- **Definition.** Users rate interfaces they find attractive as easier to use. This is a halo effect.
- **Evidence.**
  - Kurosu & Kashimura (1995): 26 ATM layouts, 252 participants. Apparent usability correlated with aesthetics more than with inherent usability.
  - Tractinsky (CHI 1997): 3 experiments in Israel replicated it across cultures.
  - Thielsch et al. (2019) meta-analysis: 25 studies, 101 effects, about 3,025 participants, found a *small* positive effect of aesthetics on objective performance. The effect on perceived usability is larger but fades with longer use (all via search summaries).
  - Grade **moderate**.
- **DOL role.** Adoption and trust, not forecasting accuracy. A clean, faithful look buys the patience needed for the ledger to show whether the engine has an edge.
- **Failure mode.** Polish without calibration means misplaced trust (COMP-11 wording honesty).

### 1.22 Settings defaults as product decisions [B-new]
- **Definition.** Most users keep the defaults. The defaults therefore *are* the product: Clean style, extras off, Classic theme, PoT filter 0, `extBars` 20.
- **Evidence.**
  - TradingView's publishing guidance: "Show the script's *default* behavior so that users know what to expect" (publishing.md:124).
  - The default effect in choice architecture is well established in other domains [not re-verified here; weak for this domain].
- **Engine.** The defaults are sensible. The exceptions are that legend clutter is default-on (§1.1), and the light-theme failure applies to every light-chart user (§1.6).

---

## 2. Evidence (numbers and sources)

### 2.1 Pixel audit: reference vs engine Clean renderer [A✓, B-corr]

| Element | Reference pixel (A; B re-sampled) | Engine composite (Pine z-order) | Match |
|---|---|---|---|
| Zone fill (`c` t92) | `#041402` | `#051402` | ✓ |
| Glow t90 w10 | `#0A2B04` | `#0A2C03` | ✓ |
| Glow t80 w7 | `#135508` | `#135607` | ✓ |
| Glow t60 w4 | `#229A0D` | `#229A0C` | ✓ |
| Glow t30 w2 | `#32E113` | `#32E112` | ✓ |
| **Core (white t15, under the box fill)** | `#DDFCD8` | **`#D3FACB` (ΔE 6.7)** [B-corr; A had `#E0FADB` by compositing in the wrong order] | ≈ |
| Core with white **t10** | `#DDFCD8` | `#DCFCD6` (ΔE 0.9) [B-new] | ✓ |
| Dashed border (t75) | `#18560E` / `#114F06` (anti-aliased) | `#124F06` | ✓ |
| Tether (t30) | brightest `#22980C` (anti-aliased diagonal) | `#28B20E` | ✓ |
| Label background | `#161616` (2,530 px mode) | `cLblBg` = `#161616` | ✓ exact |
| Label text | `#32D014` … (anti-aliased `#39FF14`) | `c` | ✓ |
| iFVG fill (`#00B478` t75) | `#002D1E` (5,794 px mode) | `#002D1E` | ✓ exact |
| iFVG border | `#00704B` | `#00704B` | ✓ |
| Table body / header / grid / frame | `#1B1F24` / `#25272C` / `#3A3C43` / `#303136` | constants 294–298 | ✓ exact |
| BULLISH / BEARISH / TF / header text | `#00C864` / `#E63C3C` / `#FFFFFF` / `#D5D5D6` | `cIBull` / `cIBear` / `cText` / `cHdrTx` | ✓ |
| Candles inside the iFVG | pure `#FFFFFF`, `#808080` [B-new] | `behind_chart` default true | ✓ |

**Geometry** [A✓].
- The zone's right edge is about 20 bars after the last candle; its left edge is on the origin candle.
- The glow is 10 px with a 1 px core.
- The label's pointer touches the zone's right edge; the body is 91 × 36 px, with two centred lines.
- The tether, extrapolated, reaches the core at `xR`.
- Bar spacing in the screenshot is about 4.25 px per bar [B-new].

`study/ux_b_tools/core_compare.png` shows the 12× magnified cross-sections.

### 2.2 Contrast of the current palette (WCAG 2.x, computed) [A✓, re-run by B]

| Colour | on black | on TV dark `#131722` | on `#0F0F0F` | on white |
|---|---|---|---|---|
| buy-side `#39FF14` | 15.49 | 13.20 | 14.14 | **1.36** |
| sell-side `#FF1744` | 5.46 | 4.65 | 4.98 | 3.85 |
| bias green `#00C864` | 9.45 | 8.05 | 8.62 | **2.22** |
| bias red `#E63C3C` | 5.08 | 4.33 | 4.63 | 4.14 |
| iFVG teal `#00B478` | 7.80 | 6.65 | 7.12 | **2.69** |
| LVN `#FFC400` | 13.15 | 11.21 | 12.00 | **1.60** |
| ghost `#7D8799` | 5.80 | 4.94 | 5.29 | 3.62 |

**Rendered Clean zone on white.** Every element is below the 3:1 graphics threshold.

| Element | Contrast vs white |
|---|---|
| Fill | 1.04 |
| Glow layers | 1.09, 1.16, 1.27, 1.34 |
| White core | 1.07 |
| Border | 1.15 |
| Tether | 1.30 |
| iFVG fill / border | 1.29 / 1.89 |

**Text on dark panels.**

| Text | Contrast |
|---|---|
| Label buy text | 13.35 |
| Label sell text | 4.70 |
| Table BULLISH | 7.45 |
| Table BEARISH | 4.00 |
| Table TF | 16.56 |
| Table header | 10.19 |
| NEUTRAL | 4.57 |

**Light-variant candidates** [A✓; B added the table column and extra candidates].

| Colour | on white | on label `#161616` | on table `#1B1F24` |
|---|---|---|---|
| `#0B7A2E` | 5.47 | 3.31 | 3.03 |
| `#C8102E` | 5.88 | 3.08 | 2.81 |
| `#00875A` | 4.55 | 3.98 | 3.64 |
| `#9A6B00` | 4.69 | 3.86 | 3.53 |
| `#5F6B7A` | 5.43 | 3.34 | 3.05 |
| `#0072B2` | 5.19 | 3.49 | 3.19 |
| `#C25400` | 4.60 | 3.93 | 3.60 |

- None of them reaches 4.5:1 on the dark panels. **Text on dark panels must keep the neon colours.**

**Light glow recipe** [A✓, recomputed with the Pine z-order; same-colour layers make the order irrelevant].

| Element | Contrast on white | Role |
|---|---|---|
| Core `g` t0 w2 | 5.47 | |
| Halo t70 w4 | 2.04 | decorative |
| Halo t85 w8 | 1.41 | decorative |
| Fill t90 | 1.15 | tint |
| Border t45 | 2.57 | |
| Tether t20 | 3.75 | |

**Generic darkening** `color.from_gradient(0.55, 0, 1, x, #000000)` [A✓]:
- worst case across the 25 theme colour values tested (Classic, Neon, Matrix, Ice, Mono) is 5.08:1 on white (Mono `#F5F5F5` → `#6E6E6E`);
- the Mono buy/sell pair after darkening is ΔE 16.3 with a luminance ratio of 1.83, which is distinguishable but weak.
- This assumes `from_gradient` interpolates linearly in sRGB.

### 2.3 Colour-vision simulation
See the table in §1.8.
- Dark CVD pair `#2F9BFF` / `#FF8A1F`: on black 7.25 / 8.91; on the `#161616` label 6.25 / 7.68; on the table 5.72 / 7.02 [A].
- Light CVD pair `#0072B2` / `#C25400`: 5.19 / 4.60 on white [A✓].

### 2.4 Literature and platform evidence (graded)

| Claim | Numbers | Grade | Source | Status |
|---|---|---|---|---|
| Red presentation lowers financial risk-taking | 8 experiments, n = 1,451; about 15–30% less risk-taking vs black (press figure); about 25% higher risk premium for losses in red; absent in colour-blind; muted in China | **strong** (lab), **weak** (transfer to target colour) | Bazley, Cronqvist & Mormann 2021, *Mgmt Sci* 67(9):5616–5641; SSRN 2992812; SMU Cox and KU summaries | [B-corr grade] |
| Uncertainty displays improve decisions | Dotplot-50: 97% of optimal (95–98), +5 pp vs control; CDF nearly as well; text worse | **strong** | Fernandes et al. 2018, CHI, doi:10.1145/3173574.3173718 | [B-corr precision] |
| Uncertainty forecasts raise trust and soften error effects | 3 experiments; better decisions, higher trust, less reluctance after forecast errors | **strong** (domain), **moderate** (transfer) | Joslyn & LeClerc 2012, *JEP: Applied* 18(1):126–140; LeClerc & Joslyn 2015, *Risk Analysis* | [B-new] |
| Natural frequencies help Bayesian reasoning | Meta-analysis about 4% → 24% | **moderate** for our use | McDowell & Jacobs 2017; Hoffrage et al. 2015 *Front. Psychol.* 6:1473 | [B-corr: 7% → 45% unverified] |
| Precision is read as confidence | More digits → judged more confident | **moderate** | Jerez-Fernandez et al. 2014, *Psych Sci* 25(2):633–635 | [A✓ via competitors] |
| Dual verbal + numeric probability | 24 countries; about 40% vs 26% consistency (secondary) | **moderate** | Budescu, Por, Broomell & Smithson 2014, *Nat. Clim. Change* 4:508–512 | [B-new] |
| More information raises confidence more than accuracy | 3 studies; confidence up, accuracy flat | **moderate** | Tsai, Klayman & Hastie 2008, *OBHDP* 107(2):97–105 | [A✓ bibliographic; numbers via blog] |
| Transparency as an uncertainty cue | Fuzziness and location most intuitive; transparency moderate; saturation low | **weak** for lines | MacEachren et al. 2012, IEEE TVCG 18(12):2496–2505 | [B-corr] |
| Pre-attentive pop-out | Unique-feature target found in < 200–250 ms regardless of distractors | **strong** (mechanism) | Healey & Enns 2012, IEEE TVCG 18(7):1170–1188 | [B-new] |
| Clutter slows search | Feature congestion and edge density predict search time; colour variability adds clutter | **strong** (mechanism), **moderate** (transfer) | Rosenholtz, Li & Nakano 2007, *J. Vision* 7(2):17; Henderson et al. 2009 | [B-new] |
| Aesthetic-usability effect | 252 participants, 26 layouts; replicated in Israel; meta-analysis 25 studies / 3,025 people: small effect on performance | **moderate** | Kurosu & Kashimura 1995; Tractinsky 1997 (CHI); Thielsch et al. 2019 | [B-new] |
| Red-green CVD prevalence | European men about 8%, women about 0.4%; Chinese and Japanese men 4–6.5%; deuteranomaly about 5%, dichromats about 2% | **strong** | Birch 2012 *JOSA A* 29:313–320; U. Arizona ophthalmology; MUN | [A✓, B-corr nuance] |
| East Asian red-up convention | CN / JP / KR / TW: red = rising | **moderate** (widely known; weak source) | Benzinga explainer 2021 | [B-new] |
| WCAG thresholds | Text 4.5:1 (large 3:1); graphics required for understanding 3:1 | **strong** (standard) | WCAG 2.1 SC 1.4.3, 1.4.11 (Understanding pages via summaries) | [B-corr scope] |
| Colour-blind-safe palette | Okabe-Ito 8 colours | **moderate** | Okabe & Ito 2008; Wong 2011 *Nat. Methods* 8:441 | [A, unverified] |
| Premium SMC tools offer declutter modes and label size | LuxAlgo SMC: Historical / Present, Colored / Monochrome, "Label Size" (tiny / small / normal) | **weak** | tradingview.com/script/CnB3fSph (search summaries) | [A✓, B-new label size] |
| Setters are cheaper than recreation | `box.new()` ≈ 2× two setters | **strong** | profiling_and_optimization.md:1074–1112 | [A✓] |
| Light / dark detection, reload on theme change | fg `#0f0f0f` / `#dbdbdb`; reload on background change | **strong** | chart_information.md:430–449; execution_model.md:498 | [A✓, B-new reload] |
| Inline alignment rules | Only the first input titled; else CW10026 | **strong** | release_notes.md (Oct 2026); errors/CW10026.md | [B-new] |
| Visuals behind bars by default | `behind_chart = true` default | **strong** | visuals/overview.md:36–38; reference pixels | [B-new] |
| Text sizes in points | Label normal 12; table normal 14, small 10 | **strong** | text_and_shapes.md:488–500; label.md:177; table.md:67 | [A✓] |
| Z-index groups | lines < boxes < labels < tables | **strong** | overview.md:230–246 | [A✓] |

### 2.5 Open-source practice survey [B-new]
Method: 8 recent public Pine v6 repositories from a GitHub search for liquidity, SMC and ICT indicators, cloned read-only to `study/ux_b_tools/ext/` (24 indicator files after excluding helper files), then grepped.

| Practice | Files (of 24) | Note |
|---|---|---|
| `display = display.none` on inputs | **0** | Legend clutter is the norm even in v6 OSS. The reference product is the exception. |
| `display = display.data_window` on plots | 11 | Common for "machine" outputs. |
| `active =` dependencies | 1 | Used for "Custom" colour pickers and a custom symbol. |
| `chart.fg_color` / `chart.bg_color` | 4 | Neutral text = `chart.fg_color`; table background = `color.new(chart.bg_color, 10–30)`. |
| Input tooltips | 22 | Universal. Good scripts explain sessions and timezones in tooltips. |
| Setter-updated drawings | 10 | Pre-created `label.new(na, na, "", style = label.style_none)` pools, hidden via `style_none` / `set_text("")` / `na` colours. |
| Label de-overlap | 2 | (a) Priority placement against used prices with a minimum gap, drop on clash. (b) Merge labels within 1 × ATR. |
| "Glow" lines | 1 | Two stacked lines for a POC. |

**Takeaway.** The engine's Clean look already exceeds typical OSS polish. Legend hygiene, theme adaptivity, `active` and collision handling are where premium scripts differ.

### 2.6 Platform facts used by the proposals [verified in the local docs]
- `input.*(display)` is `const plot_display` (input.md:27).
- `plot(display)` is `input plot_display` (plot.md:243).
- `active` is `input bool` (input.md:28).
- `label.new(size)` takes "series int/string" (label.md:177).
- `table.cell(text_size, tooltip, text_formatting)` (table.md:53–71).
- `color.new(transp)` accepts series int/float (color.md:116).
- `array.median` / `array.percentile_linear_interpolation` return float or int (array.md:626–627, 1090–1091).
- These setters all exist: `box.set_border_style`, `box.set_lefttop`, `box.set_rightbottom`, `box.set_bgcolor`, `label.set_size`, `label.set_tooltip`, `label.set_text_formatting`, `line.set_style`, `line.set_width`, `table.cell_set_tooltip`.
- `label.style_text_outline` exists (constants.md:190; release_notes.md:933).
- A visible-range change reloads the script when `chart.left_visible_bar_time` or `chart.right_visible_bar_time` is used (execution_model.md:497). Do not use them for layout.

---

## 3. Engine gap analysis (line refs in `baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Status-line hygiene | **wrong** | 60–229 [B-corr range] | 104 input calls: 9 string, 3 timeframe, 23 int, 31 float, 10 session, 20 bool, 8 color. The 76 legend-type inputs default to `display.all`, printing about 411 characters. The 5 plots are correctly `display.data_window` (2444–2448). |
| Input tooltips | **partial** | 60–237 | 76 of 104 inputs have no tooltip, 54 of them legend-type; this includes all 10 sessions and `tz`. 16 groups (42–57). |
| `active` | **missing** | — | Unused. The correct dependency map is in UX-1 [B-corr]. |
| Inline alignment | **wrong** [B-new] | 230–237 | 4 rows title both inline inputs → CW10026 ×4 and misalignment under the October 2026 model. |
| Group order | **partial** | 42–237 | Internals (Engine, Liquidity, Scoring, Order Flow) precede DOL Display, PoT, Theme. |
| Reference-fidelity palette and glow | **present** (one deviation) [B-corr] | 2214–2226, 293–299, 1609–1615 | All layers exact except the core: t15 under the box fill gives ΔE 6.7; t10 gives ΔE 0.9. |
| Layering / `behind_chart` | **present** [B-new] | 31 | Default `behind_chart = true`, as in the reference. Never set it false. |
| Z-order overlaps | **partial** | 1613, 2216–2224, 2276–2286, 1254 | Glow and tether (lines) sit under iFVG (t75), LVN (t91) and ghost (t94) boxes where they overlap. No overlap fade. |
| Visual hierarchy | **present** | 162–171, 203, 210 | One target; extras off; iFVG subordinate. |
| Light-theme contrast | **wrong** | 240–299, 2216–2226, 1256, 2166, 2189, 2212, 2278 | Dark-only palettes; no `chart.fg_color` / `bg_color`. On white every Clean element is ≤ 1.37:1. |
| Colour semantics by side | **present** | 2203, 2154, 2164, 2183 | Side-coded. No red-up option for East Asian users [B-new]. |
| CVD safety | **partial** | 240–292 | Redundant position and text cues; no CVD theme; bias pair ΔE 17 for dichromats (≈ 53 for anomalous trichromats). |
| Typography | **present** | 604–610, 2226, 2143 | Matches the reference; no size input. |
| Probability communication | **partial** | 2067, 2206–2209, 2225 | No horizon or reference class; 95% on a reached target (COMP-4). |
| Uncertainty, trust, stability [B-new] | **partial** | 2068, 2202 | Live `dolShown` flickers at the `minPoT` threshold (PENG-4). No visible record of past calibration in Clean (COMP-4 / COMP-5). |
| Timing communication | **partial** | 2117–2126, 2240 | `etaHit` only in Terminal; no p80; ETA calibration unchecked. |
| Tooltips | **partial** | 2206, 2226, 2248; 604–610 | Label tooltip lacks price, horizon and calibration. Table cells have none. Mobile: assume no tooltips. |
| Right-edge collisions | **missing** | 2166, 2188, 2212, 2278 | All at `xR`, no de-overlap. Clean default is unaffected. |
| Label clipping / table overlap [B-new] | **missing** | 2142, 2225, 2291 | `xR = bar_index + 20` plus a 91-px body can clip at small right margins. The top-right table (z 9) can cover the label. No tooltip tells the user. |
| Drawing lifecycle | **partial** | 2132–2141, 2214–2248; 1638–1641 | 8 Clean objects recreated per tick. iFVG uses setters. Caps are safe. |
| Data Window formatting | **partial** | 2444–2448 | No `precision`. "DOL Price" leaks filtered targets (COMP-2). |
| Bias table | **present** (look) / **missing** (alignment, tooltips) | 2294–2307 | Exact look; no alignment cue, no cell tooltips, no size option. |
| Autoscale | **partial** | 2251–2287, 2160–2168, 2193–2199 | LVN, objective and reach bands are not distance-capped (COMP-7). |
| State communication in Clean | **partial** | 2067, 2214–2226, 2237 | Counter-draw only in the tooltip; reached shown as 95%; stale and filtered silent. |
| Confidence as visual weight | **partial** | 2228 (Terminal) | Clean fixed. If added, use transparency, not width [B-corr]. |
| Far-anchor glow band [B-new] | **edge case** | 2216–2223 | A target anchored thousands of bars back draws a 10-px band across the whole pane. Faithful to the spec; candles stay on top. |

**Corrections to A's `active` map** [B-corr, verified by grep of every usage]:
- **`useBRK` must not depend on `useOB`.** Breakers are tracked whenever `useBRK` is true. The OB leg scan runs under `useOB or useBRK` (1668, 1711), and `obTrk` pushes need only `useBRK and tookL` (1706, 1747).
- **`obLook`: `active = useOB or useBRK`** (1669, 1712 are inside that branch).
- **`obQMin`: `active = useOB`** (1701, 1742 only). A was right on this one.
- **`fvgMin` must stay active.** It feeds the iFVG tracker for every chart FVG regardless of `useFVG` (907–908, 1877, 1887) and the HTF FVG request (939).
- **`fvgQMin`: `active = useFVG`** (1872, 1882). Correct in A.
- **`ifvgMaxIn`, `ifvgMax`: `active = showIFVG`.** They only cap and clean the drawn and stored iFVGs (1620, 1637). The "New iFVG Formed" alert is raised before the cap, so it does not depend on them. A kept them always active; PENG-1 is right.
- **`trackAge` stays active.** It drives the inversion tracker behind the iFVG alert and the breaker tracker (1626, 1660). PENG-1's `showIFVG or useBRK` would grey it out while the alert still uses it.
- **`warmup`: `active = accView != "Off" or useCal`** (2038).
- **`accView` stays active.** With `useCal` off it switches the ledger itself off (2038), which also changes the "Ledger Hit %" plot.
- **`lvnHours`, `lvnRows`: `showLVN or usePathVP`** (needVP, 979). **`lvnThr`, `lvnN`: `showLVN`.** **`priorM`: `potModel == "Empirical"`.** **`hudSize`: `uiStyle == "Terminal"`.** **`tablePosIn`: `showTable`.** **`ghostMax`: `showGhost`.** **`cHTF`/`cSTF`/`cEXE`: `modeIn == "Custom"`.** **`sessAs`/`sessLo`/`sessNA`: `useSess`.** **`uAbove`…`uText`: `theme == "Custom"`.** All confirmed by B.

---

## 4. Proposals (best first; maximum 12)

### 4.0 Overlap map (implement each fix once)

| UX proposal | Same as / coordinates with | Owner |
|---|---|---|
| UX-1 | COMP-1 = PENG-1 | UX-1, which has the corrected `active` map |
| UX-2 | supersedes COMP-8 | UX-2 |
| UX-3 | COMP-4 ("✓ Reached", tooltip) and PENG-4 (visibility hysteresis) | UX-3 for the state grammar; COMP-4 for the tooltip body |
| UX-5 | COMP-4 item 5 (cell tooltips) | UX-5 |
| UX-7 | PENG-5 = part of SMC-4 | PENG-5, with UX-7's hide pattern |
| Price-scale tag, distance units, autoscale caps | COMP-7 | COMP-7 (not repeated here) |

All proposals keep the Clean default visually identical to the reference on a dark chart unless stated.

### UX-1 (P1, S) · Legend and settings hygiene, with the corrected dependency map [A, B-corr, B-new]
**Problem.**
- About 411 characters of input values print in the status line.
- 76 inputs have no tooltip.
- Inputs irrelevant to the current mode look editable.
- Four inline rows misalign (CW10026).
- Internals come before display settings.

**Spec.**
1. **Legend** (the P1 core of this proposal; zero risk). Add the literal `display = display.none` to all 76 `input.int`, `input.float`, `input.string`, `input.session` and `input.timeframe` calls on lines 60–229, including `tz`, the sessions and `theme`. It is a `const plot_display`, so write the literal in each call.
2. **Inline alignment** [B-new]. Rows `c1`–`c4` (230–237): the first input keeps a title covering both fields, and the second gets `""`. Example:

   ```
   input.color(#00E5FF, "Custom · Buy / Sell-side", group = G_COL, inline = "c1", active = theme == "Custom")
   input.color(#FF2BD6, "", group = G_COL, inline = "c1", active = theme == "Custom")
   ```

   Likewise "Custom · Bull / Bear", "Custom · LVN / Ghost" and "Custom · Panel / Text". Put one tooltip on the second input of each row: only the last tooltip on a row shows.
3. **`active` map.** Use the corrected table in §3. Every dependency is declared above its dependants, so there are no forward references.
4. **Group order without moving derived code** [B-new simplification]. Group order follows the *first input* of each group. So move only the `input.*` lines of DOL Display, Probability of Touch, Theme and Panel up, right after Trading Mode.
   - Derived variables (`tfH`/`tfS`/`tfE`, the `cAbove`… switches, `cLblBg`…) stay where they are, because the inputs they read are still declared earlier.
   - Rename the internals' groups "Advanced · Engine", "Advanced · Scoring", "Advanced · Order Flow" and "Advanced · Accuracy", and place them last.
   - Optional progressive disclosure: `bool advOn = input.bool(false, "Unlock advanced tuning", group = G_ENG)`, used as `active = advOn` on about 40 scoring, flow and engine inputs. Their defaults keep working; they are just greyed out.
5. **Tooltips**, priority set:
   - **Sessions and killzones:** "HHMM-HHMM, read in Session Timezone (default America/New_York). Asia crosses midnight."
   - **`tz`:** "IANA name, e.g. Europe/London; all session and killzone inputs use it."
   - **Weights:** "Relative; normalised, so only ratios matter."
   - **`potH`:** "PoT = chance of a touch within this many chart bars (30 bars on 5m ≈ 2.5 h)."
   - **`extBars`:** "How far right of the last bar the zone, label and iFVGs extend (reference look: 20). If the label is cut off at the price scale, scroll left or increase the chart's right margin." [B-new]
   - **`tablePosIn`:** "Move the panel if it covers the target label."
6. **Text sizes** (int points):
   - `int lblPt = input.int(12, "Label Text (pt)", minval = 6, maxval = 24, group = G_DOL, display = display.none)`, used as `size = lblPt` at 2226;
   - `int tblPt = input.int(10, "Panel Text (pt)", minval = 6, maxval = 20, group = G_TABLE, display = display.none)`, used in `f_cell` / `f_cellC` (604–610) as `text_size = tblPt`.
   - The defaults 12 and 10 equal `size.normal` (label) and `size.small` (table), so fidelity is kept.
   - These globals are declared before line 604, so the functions can read them.
7. **Data Window precision** (2444–2448): `precision = 1` for Score, PoT % and Hit %; `precision = 2` for D. Coordinate with COMP-7 on the "DOL Price" display.

**Value.** Removes the single most visible deviation from the reference and stops silent session and timezone misconfiguration. The OSS survey shows this is rare: 0 of 24 files hide their inputs.
**Evidence.** Mechanism **strong** (official docs); benefit **weak** (convention, reference look).
**Risk.**
- Users lose inputs in the legend.
- Moving input lines risks a forward reference if an `active` argument names a later input; every argument in the map refers to an earlier one. Run `pine_parse.sh`.
**Effort.** S. **Ledger.** Not measurable.

### UX-2 (P1, M) · Theme-aware rendering for light charts: two colour roles plus a light glow recipe [A, B-corr, B-new]
**Problem.**
- On white every Clean DOL element is 1.04–1.37:1.
- iFVG is 1.29 / 1.89; LVN 1.60; transparent-background label text ≤ 1.6.
- A single colour swap (COMP-8's first version) breaks the dark Clean label and table: light variants reach only 2.8–3.98:1 there.

**Spec.**
1. **Detection** (global, after line 299):
   ```
   string bgMode  = input.string("Auto", "Chart Background", options = ["Auto", "Dark", "Light"], group = G_COL, display = display.none,
     tooltip = "Auto follows the chart's background colour.")
   bool   lightBg = bgMode == "Light" or (bgMode == "Auto" and chart.fg_color == #0f0f0f)
   ```
   - `chart.fg_color` is `input color`, so `lightBg` is input-qualified.
   - The script reloads when the user changes the background (execution_model.md:498) [B-corr: A's open risk resolved].
2. **Roles.**
   - **Text-on-panel roles** stay as they are: `cAbove`, `cBelow`, `cIBull`, `cIBear` for the Clean label text (2225), the table (2294–2307) and the Terminal HUD panel.
   - **Graphics roles** (new; after the theme switch, about line 300):
     ```
     f_onLight(color x) => color.from_gradient(0.55, 0.0, 1.0, x, #000000)
     color gAbove = lightBg ? (classic ? #0B7A2E : f_onLight(cAbove)) : cAbove
     color gBelow = lightBg ? (classic ? #C8102E : f_onLight(cBelow)) : cBelow
     color gIBull = lightBg ? (classic ? #00875A : f_onLight(cIBull)) : cIBull
     color gIBear = lightBg ? f_onLight(cIBear) : cIBear
     color gLVN   = lightBg ? #9A6B00 : cLVN
     color gGhost = lightBg ? #5F6B7A : cGhost
     ```
     - `f_onLight` must be declared above its first use at about line 300, so immediately before these lines and *not* in PURE HELPERS (398+), which comes later. Pine has no forward references. Alternatively, inline the gradient in each line. [B-corr: A placed the helper without noting this.]
     - `color.from_gradient` at global scope is verified compiling (CONTEXT.md).
   - Use the g* colours for:
     - the box, glow, tether and the Clean iFVG colour `ic` (1612–1613, replacing the hard-coded `#00B478` when `lightBg`);
     - ghosts (1253–1257);
     - LVN (2276–2286);
     - the pool, objective, secondary and invalidation lines.
   - **Neutral text on the chart background** [B-new]: transparent-background labels (objective 2166, secondary 2189, invalidation 2212, ghost 1256) use `textcolor = lightBg ? g : c`. Optionally use `label.style_text_outline` with `color = chart.bg_color` for a halo; it is centred on x, so shift x by +3 bars; verify the outline semantics in the editor.
3. **Light glow recipe** (replaces 2219–2223 when `lightBg`):
   - halo `color.new(g, 85)` width 8, then `color.new(g, 70)` width 4, then the core `g` t0 width 2; **no white filament**;
   - fill `color.new(g, 90)`; dashed border `color.new(g, 45)`; tether `color.new(g, 20)`;
   - computed on white: core 5.47, tether 3.75, border 2.57, fill 1.15 (tint);
   - iFVG on light: fill t80, border t40.
4. **Unchanged.** `cLblBg` and the table colours: dark panels read well on both themes and keep the reference look. Optional `panelMode = "Reference dark" / "Match chart"`, where "Match chart" uses `color.new(chart.bg_color, 10)` backgrounds and `chart.fg_color` text, as 4 OSS scripts do [B-new].

- **Mock.** `study/ux_tools/mock_light_theme.png`.

**Value.** Makes the indicator usable on light charts. The manual names light and dark as "the most commonly used" themes and asks authors to test both.
**Evidence.** **Strong** (WCAG plus computed ratios; official guidance). The share of light-theme users is unknown.
**Risk.**
- Gradient backgrounds: `bg_color` returns the midpoint, and the override covers edge cases.
- About 8 more colour variables.
- The glow layer count differs (5 dark vs 3 light), which matters for UX-7.
**Effort.** M (about 40 changed lines). **Ledger.** Not measurable.

### UX-3 (P2, S) · Clean label state grammar, with a counter-draw ledger split [A; coordinates with COMP-4 and PENG-4]
**Problem.** Clean hides states a trader must know:
- a counter-draw target looks identical to a draw-side one;
- a reached target reads "PoT: 95.0%";
- a target older than H looks like a fresh forecast.

Silent state changes also cost trust (§1.11).

**Spec** (Clean branch 2214–2226; no layout change):

| State | Line 1 | Line 2 | Visual |
|---|---|---|---|
| draw-side | `Target: BSL` | `PoT: 70.1%` | as now |
| counter-draw (`activeCtr`, 2029) | `Target: BSL ⚠` | `PoT: 70.1%` | tether `line.style_dotted`; tooltip first line "Counter-draw: order flow D = −0.42 points the other way" |
| reached (`sweptNow`) | `Target: BSL` | `✓ Reached` | core solid `c` t0 (text from COMP-4) |
| stale (`bar_index − activeSince > H`, no hit) | `Target: BSL` | `PoT: 41.0% · late` | `textcolor = color.new(c, 35)` |

- **"⚠" is the redundant non-hue cue.** It is already used at 2237 and 2306, so it renders.
- **Visibility.** Adopt PENG-4: confirmed-bar visibility with a 2-pp hysteresis band, so the zone does not flicker at the `minPoT` threshold. The label text stays live.
- **Ledger split.**
  - Add `bool ctr = false` to `Trial` (375–396).
  - Set it in `f_openTrial` (1426) as `ctr = activeCtr`. The global is declared at 1038, before the function, and assigned at 2029, before the call at 2045. Alternatively pass it as an argument.
  - In `f_book` (1461) accumulate `var array<float> ctrSt = array.new<float>(6, 0.0)`: [n, k, ΣpBase] for draw-side, then for counter-draw.
  - Tooltip line: "Counter-draw targets here: 18 of 47 hit (38%) · edge −2.1 pp vs random". Terminal Full gets a row "CTR / DRAW".

**Value.** The trader sees when the target fights order flow and how such targets have fared. The split also tests the decision-history rule "draw-side first, counter-draw fallback".
**Evidence.** State visibility **weak**; trust mechanism **moderate** (§1.11); the measurement uses the engine's distance-matched baseline.
**Risk.** "⚠" changes the reference text in the counter-draw state only. The stale threshold equal to H is a choice.
**Effort.** S.

### UX-5 (P2, S) · Bias table: alignment cue, cell tooltips, optional accuracy row, and a ledger split by MTF alignment [A]
**Problem.** The spec says to act when the Execution bias aligns with the HTF bias. The table never says whether they align, nor whether the target agrees, and nobody knows whether aligned targets do better on this symbol.

**Spec.**
- **Alignment.** `int bH = htfBias != 0 ? htfBias : htfIB`, likewise `bE`. Then:
  ```
  algn = na(activeLv) ? 0 : (bH == side and bE == side) ? 1 : bH == -side ? -1 : 0
  ```
  - Compute it at commit (step 19, right after 2029) and pass it to `f_openTrial(activeLv, algn)`. Add `int algn` to `Trial`.
- **Ledger.** `var array<float> alSt = array.new<float>(9, 0.0)`: [n, k, ΣpBase] for aligned, neutral and against. Terminal Full: "ALIGN +9.2pp (n 88) · AGAINST −1.0pp (n 41)".
- **Table extras.** `tblExtra = input.string("None", "Clean Table Extras", options = ["None", "Target row", "Target + Accuracy"], group = G_TABLE, display = display.none)`. The default "None" keeps the 3-row reference look.
  - **Target row:** "DOL" | "✓ ▲ BEFVG" in the side colour; ✓ when aligned, ⚠ when against.
  - **Accuracy row:** "Hit 62% · Edge +8pp" from `stK`, `stN`, `stPE`; "calibrating" under 20 trials.
- **Cell tooltips.** Give `f_cellC` a `string tip = ""` argument passed as `table.cell(..., tooltip = tip)`.
  - TF rows: "Swing BULL (body break of 5,112.0) · internal BEAR · price at 62% of the dealing range (premium)", from `htfRH` / `htfRL` / `htfIB` and the other TFs.
  - Header: "Swing bias from confirmed pivots; internal bias while the swing is undecided."
  - Build the strings only at `barstate.islast`.

**Value.** Turns the spec's usage advice into a visible, testable cue.
**Evidence.** **Weak** (practitioner doctrine); the split makes it measurable.
**Risk.** Extra rows deviate from the reference, hence off by default. Each class needs enough trials, so show n.
**Effort.** S.

### UX-4 (P2, M) · Time projection (WHEN): ETA band in the tooltip or as markers, plus an ETA coverage check [A]
**Problem.** `etaHit` (2117–2126) is computed but Clean never shows it, the right extension carries no time meaning, and no one checks whether the ETA is calibrated.

**Spec.**
- **Helper** after `dHit` (1075) and before `f_openTrial` (1426):
  ```
  f_eta(float dNow) =>
      array<int> sim = array.new<int>()
      for [i, dd] in dHit
          if math.abs(dd - dNow) <= 0.5
              sim.push(ttHit.get(i))
      float p50 = na
      float p80 = na
      if sim.size() >= 5
          p50 := sim.median()
          p80 := sim.percentile_linear_interpolation(80)
      [p50, p80]
  ```
  - Use an `if` block, not a ternary on tuples.
  - It replaces the inline loop at 2120–2126.
- **Display.** `etaMode = "Off" / "Tooltip" (default) / "Marker"`.
  - **Tooltip:** "Typically reached in 6–14 bars (≈ 30–70 min) when reached · n 37".
  - **Marker:** dotted vertical lines at `bar_index + math.min(500, int(p50))` (`color.new(c, 40)`) and at p80 (`color.new(c, 70)`), spanning the zone's height. Extend the zone's right edge to the p80 marker when it is beyond `extBars`.
- **Ledger.** `Trial` gets `eta50` and `eta80`, set in `f_openTrial` via `f_eta(d0)`: one loop of ≤ 300 at commit only.
  - In `f_book` on a hit: `etaSt += [1, bars <= eta50, bars <= eta80]`.
  - Terminal Accuracy row "ETA cover 48% / 79% (n 63)". About 50 / 80 means calibrated.

**Value.** Answers WHEN with a band whose reliability the ledger reports. Fernandes et al. is the closest experimental analogue: the arrival time of a bus.
**Evidence.** **Moderate**.
**Risk.**
- The ETA is conditional on a hit and must say "when reached".
- It needs n ≥ 5.
- Bars are not clock time (use COMP-4's `f_dur`, with "≈").
- Marker mode changes the look, so it is off by default.
**Effort.** M.

### UX-10 (P2, S) · Reference-fidelity regression baseline and the core-line correction [B-new]
**Problem.**
- The user's hard requirement is that Clean LOOKS like the screenshot. One element deviates by ΔE 6.7: the core is `#D3FACB` instead of `#DDFCD8`, because the box fill sits above the lines.
- Nothing protects the measured constants from later "improvements".

**Spec.**
1. Line 2223: `color.new(color.white, 15)` → `color.new(color.white, 10)` (ΔE 0.9).
2. Add a comment block above the Clean branch (2214) listing the regression constants and their measured reference pixels:
   - fill t92 `#041402`;
   - glow (t, w) = (90, 10) `#0A2B04`, (80, 7) `#135508`, (60, 4) `#229A0D`, (30, 2) `#32E113`;
   - core white t10, 1 px, `#DDFCD8`;
   - border t75 dashed;
   - tether t30 dashed to the centre at `xR`;
   - label `#161616`, 12 pt, centred, `style_label_left` at `bar_index + 20`;
   - iFVG `#00B478` t75 / t50 → `#002D1E` / `#00704B`;
   - table `#1B1F24` / `#25272C` / `#3A3C43` / `#303136`, text 10 pt.
3. Keep `indicator(...)` without `behind_chart` (default true), and add a comment saying why: the candles must stay above the zones, as in the reference.
4. Regression check for later rounds: take a TradingView screenshot of the engine on a black background, then run `study/ux_b_tools/sample_ref.py` on both images and compare the zone profile. Any row off by more than ΔE 3 is a regression.

**Value.** Locks in the one thing the user explicitly asked for, at zero functional risk.
**Evidence.** **Strong** (measured pixels; official z-order).
**Risk.** None. The core becomes about 2% brighter.
**Effort.** S.

### UX-7 (P3, M) · Persistent DOL drawing objects updated with setters [A; implement as PENG-5; B adds the hide pattern]
**Problem.** Clean deletes and recreates 8 objects on every realtime tick (2132–2141, 2214–2226). Because of rollback, the label is a new object on every update, which plausibly closes a hover tooltip [hypothesis]. Setters cost about half of creation.

**Spec.**
- **Construction.**
  ```
  type DolGfx
      box zone
      line teth
      label lbl
      array<line> glow
  ```
  - Create it once with `var`: `label.new(na, na, "", style = label.style_none)` (OSS v6 precedent), `box.new(na, na, na, na, bgcolor = na, border_color = na)`, and 5 `line.new(na, na, na, na)`.
- **Show** on `barstate.islast`:
  - `box.set_lefttop` / `set_rightbottom` / `set_bgcolor` / `set_border_color` / `set_border_style`;
  - `line.set_xy1` / `set_xy2` / `set_color` / `set_width` / `set_style`;
  - `label.set_xy` / `set_text` / `set_textcolor` / `set_color` / `set_style(label.style_label_left)` / `set_tooltip` / `set_size`.
- **Hide.**
  - `label.set_text(lbl, "")` plus `label.set_style(lbl, label.style_none)`;
  - `box.set_bgcolor(zone, na)` plus `box.set_border_color(zone, na)`;
  - `line.set_color(l, na)`.
- **Light mode** (UX-2) uses 3 of the 5 glow lines; set the unused 2 to `na` colour.
- Keep `dB` / `dLn` / `dLb` for the variable-count extras.
- Validate with the Pine Profiler.

**Evidence.** Cost **strong**; tooltip benefit **weak**.
**Risk.** Stale objects if a hide path is missed. Keep one `f_hideDol()` called from every non-show branch.
**Effort.** M.

### UX-8 (P3, M) · Layering and right-edge management: fade overlapping iFVG fills, de-overlap or merge labels, table-overlap guard [A, B-new refinements]
**Problem.**
- iFVG (t75), LVN and ghost boxes dim the DOL glow and tether where they overlap.
- Optional right-edge labels overprint each other and the DOL label.
- The top-right table can cover a DOL label near the top of the pane.

**Spec.**
- **Overlap fade.**
  - Add `color col` to `Zone` (351–362), set to `ic` at creation (1609–1621).
  - In the `barstate.islast` loop (2145–2149):
    ```
    dolVis = showDOL and not na(activeLv) and dolShown
    ov     = dolVis and z.top >= activeLv.bottom and z.bottom <= activeLv.top
    onTeth = dolVis and z.top >= math.min(close, activeLv.price) and z.bottom <= math.max(close, activeLv.price)
    box.set_bgcolor(z.bx, color.new(z.col, ov ? 92 : onTeth ? 85 : base))
    ```
    with `base` = 75 for Classic Clean, else 85 (mirrors 1614). v6 `and` is lazy, so `activeLv` is never read when it is `na`.
  - Skip LVN zones that overlap the active zone (2276–2286).
- **Label de-overlap** (only when extras are on).
  - Collect (y, priority, text) for DOL > invalidation > objective > secondaries.
  - `minSep = 0.05 * (ta.highest(high, 150) - ta.lowest(low, 150))`, a global computed every bar. 5% of the 150-bar range approximates one 2-line label at default zoom.
  - Place labels in priority order. A label within `minSep` of a placed one is **merged** into the DOL tooltip ("Also near: PDH 5,131.5 · SSL 5,108.0"), not staggered.
  - **B-new reason.** The OSS survey drops or merges rather than staggers, and staggering pushes labels further into the clip zone (§1.13). Its line is still drawn, so the level remains visible.
- **Table-overlap guard** [B-new].
  - When `tablePosIn` is a top position and the DOL price is within `minSep` × 2 of `ta.highest(high, 150)`, append to the DOL label tooltip and the `tablePosIn` tooltip: "Panel may cover the label: move it to Bottom Right."
  - Pine cannot know pixel positions, and reading the visible range would reload the script on every scroll (execution_model.md:497).

**Evidence.** Z-order **strong**; benefit **weak**.
**Risk.** `minSep` is zoom-dependent. The fade alters the look only while an iFVG overlaps the target.
**Effort.** M.

### UX-6 (P3, S) · Colour conventions: colour-blind theme, direction glyph, and an East-Asian red-up option [A, B-new]
**Problem.**
- About 2% of men (dichromats) see the bias pair at ΔE 17; about 5% (anomalous trichromats) at ΔE ≈ 53.
- Red carries an affect effect (Bazley et al.).
- In CN / JP / KR / TW markets red means up, so a red sell-side target reads backwards there.

**Spec.**
- **Theme "Colorblind"** (add to the options at 229 and to each switch, 240–292): above / bull `#2F9BFF`, below / bear `#FF8A1F`, LVN `#F0E442`, ghost `#7D8799`, panel `#0B0F14`, text `#E6EDF3`.
  - Computed: deutan ΔE 134, protan ΔE 119; 6.25 / 7.68 on the label; 5.72 / 7.02 on the table.
  - Light variants with UX-2: `#0072B2` / `#C25400` (5.19 / 4.60 on white).
- **Glyph.** `glyph = input.bool(false, "Direction Glyph in Label", group = G_DOL)` prefixes "▲ " or "▼ " to Clean line 1. Force it on when the theme is Colorblind.
- **Red-up** [B-new]. `redUp = input.bool(false, "Red = up (East Asian convention)", group = G_COL)`. After the theme switches: `cAbove`/`cBelow` swap, and `cIBull`/`cIBear` swap. Declare them with plain `color` (not `const`) so they can be reassigned, or compute swapped copies.
  - Side semantics stay intact: above price uses the "up" colour of the user's convention.
  - Off by default.

**Evidence.** Prevalence **strong**; affect **strong** (lab) / **weak** (transfer); convention **moderate**.
**Risk.** None to the default.
**Effort.** S.

### UX-9 (P3, S) · Confidence-weighted glow (bounded; transparency only) [A, B-corr]
**Problem.** Clean renders a 35%-PoT target as brightly as an 85% one.

**Spec** (revised by B).
- `confGlow = input.bool(false, "Confidence-Weighted Glow", group = G_DOL)`.
- `g = na(activePoT) ? 1.0 : f_clamp((activePoT - 0.40) / 0.30, 0.0, 1.0)`. PoT ≥ 70% gives g = 1, the reference look.
- Raise **transparency only**, at fixed widths:
  - t90 → `90 + 6 * (1 - g)`;
  - t80 → `80 + 10 * (1 - g)`;
  - t60 → `60 + 15 * (1 - g)`.
- The t30 layer and the core stay as they are, so the line remains crisp and above 3:1.
- Never widen the halo for high PoT: blur reads as *more* uncertainty (MacEachren 2012). Never use saturation: it is a weak cue.
- `color.new` accepts a float `transp` (color.md:116).

**Evidence.** **Weak** [B-corr from moderate]: transparency was only moderately intuitive, and it was tested on point symbols.
**Risk.** Dimmer low-PoT targets, but bounded, so they never vanish. Off by default.
**Effort.** S.

---

## 5. Sources

**Official Pine Script v6 documentation** (local mirror `scratchpad/docsrc/jabez4jc_pinescriptv6/`):
- reference/input.md:12–28, 65–77, 99–111, 147, 206, 248 (`display` defaults, `active`);
- concepts/inputs.md:96–114;
- release_notes.md: October 2026 (input alignment), 506 (`active`), 617–618 (int sizes, `text_formatting`), 933 (`label.style_text_outline`);
- errors/CW10026.md, errors/overview.md:28;
- reference/chart.md:7–21; concepts/chart_information.md:430–452;
- language/execution_model.md:486–502 (reload triggers: background colour, visible range);
- visuals/colors.md:392–410; visuals/overview.md:20–46, 230–246 (`behind_chart`, z-index);
- visuals/text_and_shapes.md:478–500; reference/label.md:164–182; reference/table.md:53–71;
- reference/color.md:105–118; reference/array.md:621–627, 1085–1091; reference/plot.md:227–247; visuals/plots.md:149–170;
- writing_scripts/profiling_and_optimization.md:1074–1112; visuals/lines_and_boxes.md:22; writing_scripts/limitations.md:381;
- writing_scripts/publishing.md:100–125.

**Web** (A: 5 searches; B: about 17 searches; summaries, with the paper hosts blocked for fetch):
- Bazley, Cronqvist & Mormann (2021). Visual Finance: The Pervasive Effects of Red on Investor Behavior. *Management Science* 67(9):5616–5641.
  - https://papers.ssrn.com/abstract=2992812
  - https://econpapers.repec.org/RePEc:inm:ormnsc:v:67:y:2021:i:9:p:5616-5641
  - https://www.smu.edu/cox/coxtoday-magazine/2020-12-09-visual-finance-101
  - https://news.ku.edu/news/article/2021/03/29/red-color-impacts-investor-behavior-financial-research-reveals
- Fernandes, Walls, Munson, Hullman & Kay (2018). Uncertainty Displays Using Quantile Dotplots or CDFs Improve Transit Decision-Making. CHI. doi:10.1145/3173574.3173718.
  - https://idl.uw.edu/papers/uncertainty-bus
  - https://mucollective.northwestern.edu/project/uncertainty-bus
- Joslyn & LeClerc (2012). Uncertainty forecasts improve weather-related decisions and attenuate the effects of forecast error. *JEP: Applied* 18(1):126–140.
  - https://www.sci.utah.edu/~kpotter/Library/Papers/joslyn:2012:UFID/index.html
  - https://www.stat.berkeley.edu/~aldous/157/Papers/leclerk.pdf
- LeClerc & Joslyn (2015). The Cry Wolf Effect and Weather-Related Decision Making. *Risk Analysis*. https://zendy.io/title/10.1111/risa.12336
- Budescu, Por, Broomell & Smithson (2014). The interpretation of IPCC probabilistic statements around the world. *Nature Climate Change* 4:508–512.
  - https://ideas.repec.org/a/nat/natcli/v4y2014i6d10.1038_nclimate2194.html
  - https://www.cmu.edu/news/stories/archives/2014/april/april30_climatebroomell.html
  - https://www.ipcc.ch/site/assets/uploads/2016/02/Budescu_IPCC_Communication_Meeting_OSLO_February_2016.pdf
- MacEachren et al. (2012). Visual Semiotics & Uncertainty Visualization: An Empirical Study. IEEE TVCG 18(12):2496–2505.
  - https://geography.wisc.edu/cartography/projects/publications/MacEachrenEtAl_2012_TVCG.pdf
  - https://ieeevis.org/year/2012/paper/infovis/visual-semiotics-uncertainty-visualization-empirical-study
- Tsai, Klayman & Hastie (2008). Effects of amount of information on judgment accuracy and confidence. *OBHDP* 107(2):97–105.
  - https://ideas.repec.org/a/eee/jobhdp/v107y2008i2p97-105.html
  - https://alphaarchitect.com/2013/04/more-informationmore-confidencemore-problems/
- Healey & Enns (2012). Attention and Visual Memory in Visualization and Computer Graphics. IEEE TVCG 18(7):1170–1188.
  - https://healey.csc.ncsu.edu/publications/15783
  - https://www.csc2.ncsu.edu/faculty/healey/download/tvcg.12a.pdf
- Rosenholtz, Li & Nakano (2007). Measuring visual clutter. *J. Vision* 7(2):17.
  - https://pubmed.ncbi.nlm.nih.gov/18217832
  - https://dspace.mit.edu/handle/1721.1/37593
- Kurosu & Kashimura (1995); Tractinsky (1997), CHI; Thielsch et al. (2019).
  - https://chi1997.acm.org/proceedings/paper/nt.html
  - https://www.uni-muenster.de/imperia/md/content/owms/2019_thielsch_et_al.pdf
  - https://en.wikipedia.org/wiki/Aesthetic%E2%80%93usability_effect
- Birch (2012). Worldwide prevalence of red-green color deficiency. *JOSA A* 29:313–320.
  - https://pubmed.ncbi.nlm.nih.gov/22472762/
  - MedlinePlus: https://medlineplus.gov/genetics/condition/color-vision-deficiency
  - Types breakdown: https://disorders.eyes.arizona.edu/print/1377 ; https://mun.ca/biology/scarr/Colour_deficiency_test.html
- WCAG 2.1 Understanding SC 1.4.11 Non-text Contrast.
  - https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast
  - https://dequeuniversity.com/resources/wcag2.1/1.4.11-non-text-contrast
- East Asian colour convention: https://www.benzinga.com/general/education/21/10/23258001/did-you-know-you-dont-want-to-be-in-the-green-if-youre-trading-in-china-japan-or-taiwan
- TradingView status-line settings (chart-wide "Indicator Arguments"; per-indicator values in the status line):
  - https://www.tradingview.com/blog/en/hide-individual-indicator-values-29316
  - https://ru.tradingview.com/support/solutions/43000659666/
- LuxAlgo Smart Money Concepts (Historical / Present, Colored / Monochrome, Label Size):
  - https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-LuxAlgo/
  - https://www.luxalgo.com/library/indicator/smart-money-concepts-smc
- Hoffrage, Krauss, Martignon & Gigerenzer (2015), *Front. Psychol.* 6:1473, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604268/ ; McDowell & Jacobs (2017) via competitors.final.md.
- Jerez-Fernandez, Angulo & Oppenheimer (2014), *Psych. Sci.* 25(2):633–635 (via competitors.final.md).
- TradingView Help 43000762934, "My chart looks compressed" (via competitors.final.md).

**Open-source practice survey** (cloned read-only to `study/ux_b_tools/ext/`; concepts only, no code copied):
- github.com/VolodymyrFilias/feels-indicators
- github.com/Matswm86/tradingview-indicators
- github.com/kxngHADES/SMC-Marking
- github.com/DeolinNaidoo/TradingView-Larper-Indicator
- github.com/CedInvest/sm-radar-pine
- github.com/TradingSignalBot/tradingview-strategies
- github.com/mehmeterenyasar/tradingview-key-levels-indicator
- github.com/quantumalgo-official/smart-money-concepts-indicator

**Cited from memory and still unverified:** Okabe & Ito (2008); Wong (2011), *Nature Methods* 8:441; Machado, Oliveira & Fernandes (2009), IEEE TVCG (the simulation matrices in `contrast.py`); Oskamp (1965); Nielsen's usability heuristics; TradingView's default right margin of about 10 bars.

**Computed** (reproducible):
- `study/ux_tools/contrast.py`, `light.py`, `mock.py` (A);
- `study/ux_b_tools/sample_ref.py`, `zorder_check.py`, `core_fit.py`, `mock_core.py` → `core_compare.png`, `light_check.py`, `inputs_audit.py` (B).
