# Premium indicator UX and visual design: study for DOL Engine v2

**Domain.** What makes a TradingView overlay indicator look premium and stay readable:
- status line (legend) hygiene;
- label, table and typography design;
- contrast on dark *and* light charts;
- colour semantics and colour-vision safety;
- glow and layering;
- clutter control and label collisions;
- drawing-object lifecycle;
- input UX;
- how probability and timing are communicated.

The lens is the forecasting problem: a display should help the trader read **where** price is drawn, **when**, and **how likely**, and nothing more.

**Conventions.**
- All line numbers refer to `brief/baseline_v2.pine`, which is identical to `/home/user/m/indicators/dol_engine.pine`.
- Proposal IDs are prefixed `UX-`.
- Cross-references to `COMP-n` point to `study/competitors.md`, which overlaps this domain in places. Where the two overlap, this report adds the visual-design detail and says so, so a later merge can de-duplicate.

**Working files** (all under `study/ux_tools/`):
- `contrast.py`: WCAG contrast, alpha compositing, colour-vision simulation (Machado 2009);
- `light.py`: light-theme recipe check;
- `mock.py` → `mock_light_theme.png`: dark vs light mock;
- `ref_*.png`: zoomed crops of the reference.

**Research limits in this session.**
- The Firecrawl account ran out of credits after the first call.
- The shared WebSearch budget ran out after 5 searches.
- WebFetch could not resolve w3.org, nature.com or northwestern.edu (blocked by the session network).

What remains rests on:
1. the official Pine v6 reference and manual mirrored locally (strong, for platform mechanics);
2. pixel measurements of the reference screenshot and computed contrast and colour-vision numbers (reproducible with the scripts above);
3. five verified web searches (Bazley et al. 2021, Fernandes et al. 2018, colour-vision prevalence, WCAG 1.4.11, LuxAlgo display modes);
4. two citations already verified by the competitors study (Hoffrage et al. 2015; Jerez-Fernandez et al. 2014);
5. a few classic papers cited from memory, each marked **[unverified this session]**.

---

## 0. Executive summary

1. **The Clean style already reproduces the reference pixel-for-pixel.**
   - The fill, the 4-layer glow, the white filament core, the dashed border, the iFVG fill and border, and the label and table colours all match the screenshot within ±3 RGB units (§2.1).
   - Label size (`size.normal` = 12 pt) and table size (`size.small` = 10 pt) agree with the measured 1.2 ratio of text heights.
   - **Do not "improve" these values.** Treat them as the regression baseline for every later change.
2. **The biggest visible gap is the status line.**
   - 76 of the 104 `input.*()` calls are int, float, string, timeframe or session inputs without `display = display.none`.
   - Pine's default for those types is `display.all`, so roughly 76 values ("Day Trading 240 60 15 3 5000 14 5 0.2 0.1 …") are printed next to the script name.
   - The reference legend shows only the name.
   - 76 inputs also have no tooltip, and `active` is unused. (UX-1, same finding as COMP-1.)
3. **On a light chart the DOL is invisible.** Every element of the Clean zone composites to 1.04–1.37:1 against white (fill 1.04, glow 1.09–1.34, white core 1.07, tether 1.30). WCAG asks 3:1 for graphics.
   - The Pine manual explicitly tells authors to test light and dark themes.
   - The fix needs **two colour roles**:
     - graphics drawn on the chart background switch to dark variants;
     - text on the dark Clean label and table keeps the neon colour. A light variant on `#161616` falls to 3.1–3.3:1.
   - (UX-2 extends COMP-8, which missed the second role.)
4. **Lines always render below boxes.**
   - The z-index groups run lines (6) < boxes (7) < labels (8) < tables (9), so iFVG, LVN and ghost boxes are drawn *over* the DOL glow and tether wherever they overlap.
   - This bites exactly when the trader is watching an iFVG retest toward the target (UX-8).
5. **The display can communicate WHEN and HOW LIKELY better, in ways the ledger can grade:**
   - an ETA marker whose coverage (share of hits arriving before it) the ledger checks (UX-4);
   - a counter-draw marker with its own ledger track record (UX-3);
   - an alignment cue in the bias table with a ledger split, aligned vs against (UX-5).

   Evidence for showing uncertainty: quantile dotplots and CDFs raised decision payoff to about 97% of optimal, 5 points above a no-uncertainty control, and beat textual uncertainty (Fernandes et al., CHI 2018). Natural frequencies raise correct Bayesian inferences from 7% to 45% (Hoffrage et al. 2015).
6. **Colour is not neutral.**
   - Red-coloured financial data cut risk-taking by about 15–30% and prolonged pessimistic expectations in 8 experiments (Bazley, Cronqvist & Mormann, *Management Science* 2021). The effect was absent in colour-blind subjects.
   - About 8% of men of Northern European ancestry have red-green colour-vision deficiency.
   - Simulated deuteranopia shrinks the bias-table bull/bear distance from ΔE 130 to ΔE 17.
   - The text labels make the table readable anyway, but a CVD-safe theme is cheap (UX-6).

---

## 1. Concepts (definitions and parameters)

Each concept gives a precise definition, the parameters that matter, its role for WHERE / WHEN / HOW LIKELY, how practitioners use it, and its failure modes.

### 1.1 Status line (legend) hygiene
- **Definition.** The script's status line shows the title followed by the value of every input whose `display` includes `display.status_line`, plus plot values whose `display` includes it.
  - Inputs: "The default is `display.all` for all input types except 'bool' and 'color' inputs, which use `display.none` by default" (concepts/inputs.md:112; reference/input.md:27, 76).
  - The parameter is `const plot_display`. Values: `display.none`, `display.data_window`, `display.status_line`, `display.all`, combinable with + and −.
- **Parameters.** Per-input `display`, and per-plot `display`.
- **DOL role.** None directly. Clutter competes for attention with the one target the tool exists to show.
- **Practitioner use.** Premium scripts show only the name, at most the trading mode. The reference legend reads "TradeAxis DOL" only.
- **Failure modes.**
  - A long legend wraps over candles at the top-left.
  - It exposes tuning internals that invite meddling.
  - `display.none` also removes the value from the Data Window. That is fine for inputs.

### 1.2 Input UX: groups, inline, tooltips, `active`, ordering
- **Definitions.**
  - `group` collects inputs under a header; groups appear in order of first appearance in the code.
  - `inline` puts inputs on one row.
  - `tooltip` adds an (i) hover.
  - `active` (input bool, added July 2025): "If `false`, the input is grayed out, and users cannot change the value. Programmers can use this parameter to define inputs whose states depend on the values of other inputs" (release_notes.md:506; reference/input.md:28).
- **Parameters.** Group order; which inputs depend on which toggles; tooltip text.
- **DOL role.** Indirect. Fewer mis-set inputs means fewer silently degraded targets. Session and timezone mistakes directly mislabel PDH, Asia and killzone levels.
- **Practitioner use.**
  - Simple settings first, internals last or under "Advanced".
  - Colour presets instead of raw colour pickers. The Pine manual: "Providing a selection of color presets in your inputs … can help color-challenged users" (visuals/colors.md:400).
- **Failure modes.**
  - 100+ undifferentiated inputs.
  - Session strings without a stated timezone.
  - Inputs that do nothing in the current mode but look editable.

### 1.3 Reference-fidelity palette and layered glow
- **Definition.** A "neon" line is built from N co-linear lines with increasing width and transparency, plus a thin near-white core.
  - Composited over a dark background the outer layers act as a halo.
  - The Pine manual endorses the technique: "give it more importance by using multiple plots for the same line … modulate the successive width and transparency" (visuals/colors.md:406–410).
- **Engine parameters (Clean, lines 2216–2223).**
  - Zone: fill `color.new(c, 92)`; dashed border `color.new(c, 75)`, width 1.
  - Glow layers as (transparency, width): (90, 10), (80, 7), (60, 4), (30, 2).
  - Core: `color.new(color.white, 15)`, width 1.
  - Tether: `color.new(c, 30)`, dashed.
  - Label: `cLblBg` = `#161616`, `size.normal`, centre-aligned, `style_label_left` at `xR = bar_index + 20`.
- **DOL role.** WHERE. The glow makes the single target the brightest object on the chart.
- **Failure modes.**
  - An additive glow has no meaning on a light background (§1.5).
  - A 10-px glow on a 2-px-tall liquidity zone overflows the dashed box. This is acceptable: it still reads as "the level".

### 1.4 Visual hierarchy and single focal point
- **Definition.** Visual weight (luminance contrast × area × saturation) should rank elements by importance.
  - Pine manual: "When you make everything stand out, nothing does. Make room for some elements to stand out by toning down the visuals surrounding it" (visuals/colors.md:398).
- **Parameters.** Number of simultaneously visible objects, and their weight ranking. In the engine:
  - DOL core 18.9:1 on black;
  - glow 11.9:1;
  - tether 7.5:1;
  - iFVG border 3.4:1 and fill 1.39:1;
  - DOL fill 1.11:1;
  - dashed border 2.15:1.
- **DOL role.** WHERE. One committed target, not a menu.
- **Evidence for minimalism.** More information raises confidence faster than accuracy (Tsai, Klayman & Hastie 2008, *OBHDP*; Oskamp 1965) [unverified this session].
- **Failure modes.**
  - Secondary targets, objective, reach bands, candidate pool, LVN and ghosts all on at once. The engine defaults them off, which is correct.

### 1.5 Contrast and theme adaptivity
- **Definitions.**
  - WCAG 2.x contrast ratio = (L1 + 0.05) / (L2 + 0.05), with relative luminance L from linearised sRGB.
  - Text needs 4.5:1, or 3:1 for large text (≥ 18 pt, or ≥ 14 pt bold), under SC 1.4.3.
  - Graphical objects "required to understand the content" need 3:1 against adjacent colours under SC 1.4.11. Line charts are explicitly in scope.
- **Pine mechanics.**
  - `chart.bg_color` (input color) returns the chart background, the midpoint for gradients.
  - `chart.fg_color` returns `#dbdbdb` on dark backgrounds and `#0f0f0f` on light ones (concepts/chart_information.md:430–431).
  - The manual's own light test: `bool isLight = chart.fg_color == #0f0f0f`.
- **DOL role.** WHERE. Below 3:1 the target is not seen.
- **Failure modes.**
  - Neon on white.
  - White core on white.
  - Transparent-background labels with neon text on white.
  - Dark panels that are fine on both themes but whose text colour changes with the theme.

### 1.6 Colour semantics (side, direction, state)
- **Definition.** The engine colours by **draw side**: buy-side (above price) is lime, sell-side is red, regardless of kind.
  - That is why a *bearish* FVG target above price is green in the reference ("Target: BEFVG" in lime).
- **DOL role.** WHERE and direction at a glance.
- **Evidence that colour shifts behaviour.** Bazley, Cronqvist & Mormann (2021, *Management Science* 67(9):5616–5641):
  - in 8 experiments, red-presented financial data lowered risk-taking and return expectations;
  - SMU summary: about 15–30% less risk-taking vs black;
  - red prolonged pessimism after losses;
  - absent in colour-blind subjects, weaker in China, not produced by yellow or blue.
- **Failure modes.**
  - Kind-coloured zones (bull FVG green below price, bear FVG red above) would contradict side colouring.
  - Red sell-side targets may make users less willing to act on them. This is unmeasured for this tool.

### 1.7 Colour-vision-deficiency safety and redundant encoding
- **Definition.** Information carried by hue alone fails for about 8% of men with Northern European ancestry (about 1 in 12; women about 0.4–0.5%) who have red-green CVD (Birch 2012; MedlinePlus).
  - The remedy is (a) a CVD-safe palette (blue/orange, as in Okabe & Ito 2008 and Wong 2011 [unverified this session]) and (b) redundant cues: position, text, glyphs, line style.
- **Engine redundancy already present:**
  - side = position relative to price;
  - table text BULLISH / BEARISH;
  - iFVG direction = position.
- **Computed** (Machado 2009 simulation, CIE76 ΔE):

  | Pair | Normal ΔE | Deuteranopia ΔE |
  |---|---|---|
  | DOL buy/sell | 170 | 37 |
  | Bias bull/bear | 130 | 17 |
  | iFVG bull/bear | 120 | 31 |
  | Blue/orange `#2F9BFF` / `#FF8A1F` | 132 | 134 |

- **Failure modes.** Any future feature that encodes state by hue only, for example a "counter-draw = amber" scheme.

### 1.8 Typography
- **Definition.** Pine v6 text sizes accept `size.*` constants or int points.
  - Labels: tiny ≈ 7, small ≈ 10, normal 12, large 18, huge 24.
  - Tables and boxes: tiny 8, small 10, normal 14, large 20, huge 36 (visuals/text_and_shapes.md:488–500; reference/label.md:177).
  - `text_formatting` adds bold and italic. `text_font_family` can be default or monospace.
- **Engine.**
  - Clean label: `size.normal` (12 pt), default font.
  - Clean table: `size.small` (10 pt), default font, centred (604–610).
  - Terminal: monospace.
- **Measured reference.** Label cap height about 8–9 px and table about 7 px, a 1.2 ratio, which matches 12/10.
- **Failure modes.**
  - Monospace in Clean looks "terminal".
  - Fixed sizes are too small on 4K screens and too big on mobile. Int points allow a size input.

### 1.9 Probability communication (HOW LIKELY)
- **Definition.** A probability readout has four parts: value, precision, horizon (the "within H bars" clause) and reference class (calibration: "of N similar targets, K were hit").
- **Evidence.**
  - Natural frequencies: 7% → 45% correct Bayesian inferences (Hoffrage, Krauss, Martignon & Gigerenzer 2015, *Front. Psychol.* 6:1473).
  - More decimal digits are read as more confidence (Jerez-Fernandez, Angulo & Oppenheimer 2014, *Psych. Sci.* 25:633).
  - Uncertainty visualisations (quantile dotplots, CDFs) brought decisions to about 97% of optimal payoff, +5 pp over control, and beat textual uncertainty (Fernandes, Walls, Munson, Hullman & Kay 2018, CHI).
- **Engine.**
  - "PoT: 70.1%" with no horizon or reference class (line 2225).
  - After a live sweep it shows "PoT: 95.0%" (2067), a reached target displayed as a probability.
  - The tooltip holds the pillars but no price, horizon or calibration (2206–2209).
  - This is COMP-4's territory; UX-3 and UX-4 add to it.
- **Failure modes.** False precision; no horizon; uncalibrated numbers presented as fact.

### 1.10 Timing communication (WHEN)
- **Definition.** An expected time-to-target, conditional on reaching it. The empirical median and 80th percentile of bars-to-hit for past targets at similar distance.
  - The engine computes the median as `etaHit` (lines 2117–2126: hits within ±0.5 ATR of the current distance, n ≥ 5).
- **Practitioner use.** Time-projection boxes (session-end, "by NY close"). The competitors study reports users asking "*when* will it be reached".
- **Engine.**
  - Terminal HUD only ("ETA|hit ~Nb", line 2240).
  - Clean shows nothing.
  - The zone's right edge is a fixed 20 bars and carries no time meaning.
- **Failure modes.**
  - An ETA shown without saying it is *conditional on a hit*.
  - An ETA on bars rather than clock time across session gaps.

### 1.11 Tooltips as progressive disclosure
- **Definition.** Keep the chart minimal and put detail one hover away.
  - `label.new(..., tooltip = string)` (used, line 2226).
  - `table.cell(..., tooltip = string)` (reference/table.md:53, 69; unused).
  - Boxes and lines have no tooltip.
- **DOL role.** All three questions can be answered on hover without clutter.
- **Failure modes.**
  - Mobile has no hover. The essentials must stay in the visible text.
  - An object recreated on every tick may close an open tooltip [hypothesis, not verified].

### 1.12 Z-order and layering
- **Definition.** Pine groups visuals by type, in ascending z: background colours < fills < plots < hlines < linefills < **lines < boxes < labels < tables**. "Within the same group, elements created last … appear on top" (visuals/overview.md:230–246). Only plots, hlines and fills can be re-ordered (`explicit_plot_zorder`).
- **Consequences for the engine.**
  - The DOL glow and tether (lines) sit under the DOL's own box fill (a 92-transparency tint, intended) and also under every iFVG box (fill t75), LVN box (t91) and ghost box (t94).
  - The DOL box itself is created last, so it is on top of iFVG boxes.
  - Labels sit above all boxes; the table above everything.
- **Failure mode.** An iFVG retest, with price inside or under an iFVG and the tether passing through it, dims and tints the tether start by 25%. An iFVG overlapping the target zone tints the glow.

### 1.13 Right-edge layout and label collisions
- **Definition.** Labels anchored at `xR` with `style_label_left` stack vertically by price. Two labels collide when the gap between their prices is smaller than the label height expressed in price units.
- **Label height.** About 36 px for a 2-line `size.normal` label, measured on the reference. At a typical 500–900 px pane showing 150 bars, that is about 4–7% of the visible price range.
- **Engine.**
  - Clean default has one label, so there is no collision.
  - These optional elements all anchor at `xR` and can overlap each other or the DOL label: secondary targets (2188), objective (2166), invalidation (2212), LVN box text (2278) and ghost labels (1256, anchored at the sweep bar).
- **Failure mode.** Unreadable overprinted labels when the user enables the extras.

### 1.14 Drawing-object lifecycle
- **Definitions.**
  - Limits: 500 lines, 500 boxes and 500 labels with garbage collection of the oldest (visuals/lines_and_boxes.md:22); x up to `bar_index + 500` (limitations.md:381).
  - Setters versus recreation: "Utilizing these setters is typically less computationally expensive than creating a new drawing object"; in the manual's profile, `box.new()` cost "close to double the combined time" of two setters (profiling_and_optimization.md:1074–1112).
- **Engine.**
  - iFVG boxes are long-lived and updated with `box.set_right` (good, lines 1638–1641, 2145–2149).
  - The active zone, glow, tether and label (8 objects in Clean) are **deleted and recreated on every realtime tick** (2132–2141 and onward).
  - Ghosts are FIFO-capped. `f_x` clamps x to the 5000-bar time buffer (404).
- **Failure modes.**
  - CPU per tick.
  - Hover and selection state lost on recreation [hypothesis].
  - Hitting the 500 cap would garbage-collect historic ghosts. Not reached with current caps.

### 1.15 Data Window and plot formatting
- **Definition.** `plot(..., format, precision)` controls the digits shown in the Data Window, status line and scale (reference/plot.md:244–245).
- **Engine.** Five `display.data_window` plots (2444–2448) inherit the symbol's price precision. On EURUSD "DOL Score" and "PoT %" would print with 5 decimals; on futures with tick precision.
- **Failure mode.** Noisy readouts.

### 1.16 Bias table design
- **Definition.** A compact two-column table: Timeframe | Bias with three rows (HTF, STF, Execution).
- **Measured reference colours.** Header `#25272C` with text `#D5D5D6`; body `#1B1F24`; grid `#3A3C43`; frame `#303136`; BULLISH `#00C864`; BEARISH `#E63C3C`; TF text `#FFFFFF`; row pitch 20 px.
- **Engine.** Matches exactly (lines 294–299, 2291–2307).
- **Contrast.**
  - BEARISH `#E63C3C` on `#1B1F24` is 4.00:1, below AA 4.5:1 for 10-pt text. It is faithful to the reference, so leave it.
  - NEUTRAL `cGhost` is 4.57:1.
- **DOL role.** Bias. The reference text says to act when "Execution TF bias aligns with the HTF bias", but the table never states alignment or ties it to the target.
- **Failure modes.**
  - No hover detail (why bullish? which level would flip it?).
  - No alignment cue.

### 1.17 Autoscale compression
- **Definition.** Drawings far from price widen the auto-scaled range and squash the candles. The user-side fix is "Scale price chart only" (TradingView help 43000762934, via competitors.md).
- **Engine.** Proximity and eject limits bound pool levels. LVN zones (whole 1H profile), the objective and the reach bands are not distance-limited (COMP-7).

### 1.18 State communication
- **Definition.** A target is in one of these states:
  - active and draw-side;
  - active but counter-draw;
  - reached (swept intrabar);
  - stale (older than the PoT horizon without a hit);
  - filtered (below Min PoT);
  - none.
- **Engine.**
  - Terminal shows "⚠ COUNTER-DRAW" and "✕ SWEPT" (2237).
  - Clean shows none of these. Counter-draw appears only in the tooltip (2206). "Reached" shows as 95% (2067). A filtered or absent target simply disappears.
- **Failure modes.** Silent state changes read as "the target jumped".

### 1.19 Confidence encoded as visual weight
- **Definition.** Map the forecast confidence (PoT or score) to opacity, blur or glow intensity.
  - In user studies, fuzziness, transparency and value were judged the most intuitive uncertainty encodings (MacEachren et al. 2012, IEEE TVCG) [unverified this session].
- **Engine.** Terminal maps score to zone opacity (`zA = 92 − 0.12·score`, line 2228). Clean uses fixed weights.
- **Failure mode.** Too strong a mapping hides low-PoT targets that may still be correct. Keep it bounded.

---

## 2. Evidence (numbers and sources)

### 2.1 Pixel audit: reference screenshot vs engine Clean renderer (measured and computed)

**Method.**
- Sampled pixels of `brief/reference_look.png`: a vertical profile through the zone at x = 900, plus colour histograms of the label, tether, iFVG and table.
- Composited the engine's transparencies over black with `contrast.py`.

| Element | Reference pixel | Engine composite | Match |
|---|---|---|---|
| Zone fill (`c` t92) | `#041402` | `#051402` | ✓ |
| Glow t90 w10 | `#0A2B04` | `#0A2C03` | ✓ |
| Glow t80 w7 | `#135508` | `#135607` | ✓ |
| Glow t60 w4 | `#229A0D` | `#229A0C` | ✓ |
| Glow t30 w2 | `#32E113` | `#32E112` | ✓ |
| Core (white t15, 1 px) | `#DDFCD8` | `#E0FADB` | ✓ (±3) |
| Dashed border (t75) | `#18560E` / `#114F06` (anti-aliased) | `#124F06` | ✓ |
| Tether (t30, diagonal, anti-aliased) | brightest `#22980C` | `#28B20E` (unaliased) | ✓ |
| Label background | `#161616` | `cLblBg` = gradient 0.086 → `#161616` | ✓ exact |
| Label text | `#33D115` (anti-aliased `#39FF14`) | `c` | ✓ |
| iFVG fill (`#00B478` t75) | `#002D1E` | `#002D1E` | ✓ exact |
| iFVG border (t50 over fill) | `#00704B` | `#00704B` | ✓ exact |
| Table body / header / grid / frame | `#1B1F24` / `#25272C` / `#3A3C43` / `#303136` | same constants (294–298) | ✓ exact |
| BULLISH / BEARISH / TF / header text | `#00C864` / `#E63C3C` / `#FFFFFF` / `#D5D5D6` | `cIBull` / `cIBear` / `cText` / `cHdrTx` | ✓ |

**Geometry.**
- **Zone.** Right edge about 19–20 bars after the last candle (`extBars = 20`). Left edge on the origin candle.
- **Glow.** About 10 px total thickness; the core is 1 px.
- **Label.** The pointer tip touches the zone's right edge, so `style_label_left` at `xR` is correct. Body 91 × 36 px, two centred lines.
- **Tether.** It runs from the last candle at (972, 675) to the box's bottom-right corner (1049, 525). Extrapolated to `xR` (x = 1057) it lands at y ≈ 509, which is the core line. So the tether targets the **centre** at `xR`, as Clean does (2224). Terminal deliberately targets the near edge (2232).
- **Text sizes.** Label cap height 8–9 px vs table 7 px, a 1.2 ratio, consistent with `size.normal` (12) and `size.small` (10).

**Conclusion.** Clean fidelity is complete. These constants are the regression baseline.

### 2.2 Contrast of the current palette (computed, WCAG 2.x formula)

| Colour | on black | on TV dark `#131722` | on `#0F0F0F` | on white |
|---|---|---|---|---|
| buy-side `#39FF14` | 15.49 | 13.20 | 14.14 | **1.36** |
| sell-side `#FF1744` | 5.46 | 4.65 | 4.98 | 3.85 |
| bias green `#00C864` | 9.45 | 8.05 | 8.62 | **2.22** |
| bias red `#E63C3C` | 5.08 | 4.33 | 4.63 | 4.14 |
| iFVG teal `#00B478` | 7.80 | 6.65 | 7.12 | **2.69** |
| LVN `#FFC400` | 13.15 | 11.21 | 12.00 | **1.60** |
| ghost `#7D8799` | 5.80 | 4.94 | 5.29 | 3.62 |

**Rendered Clean zone on white.**

| Element | Contrast vs white |
|---|---|
| Fill | 1.04 |
| Glow layers | 1.09, 1.16, 1.27, 1.34 |
| White core | 1.07 |
| Border | 1.15 |
| Tether | 1.30 |
| iFVG fill / border | 1.29 / 1.89 |

**Every element is below the 3:1 graphics threshold: the DOL is effectively invisible.**

**Text on dark panels.**

| Text | Contrast |
|---|---|
| Label buy text | 13.35 |
| Label sell text | 4.70 |
| Table BULLISH | 7.45 |
| Table BEARISH | 4.00 (< 4.5, reference-faithful) |
| Table TF | 16.56 |
| Table header | 10.19 |
| NEUTRAL | 4.57 |

**Light-variant candidates on white.**

| Colour | on white | on TV light `#F8F9FD` | on dark label `#161616` |
|---|---|---|---|
| `#0B7A2E` | 5.47 | 5.20 | **3.31** |
| `#C8102E` | 5.88 | 5.59 | **3.08** |
| `#00875A` | 4.55 | 4.33 | n/a |
| `#9A6B00` | 4.69 | 4.46 | n/a |
| `#5F6B7A` | 5.43 | 5.16 | n/a |

- The `#161616` column is why the **text role must stay neon** on dark panels.
- Light glow recipe (UX-2): core t0 w2 = 5.47; halo t70 w4 = 2.04 and t85 w8 = 1.41 (decorative); fill t90 = 1.15 (tint); border t45 ≈ 2.6; tether t20 = 3.75.
- A generic fallback for any theme colour, `color.from_gradient(0.55, 0, 1, c, #000000)`, gives at least 5.08:1 on white across all 17 theme colours (worst: Mono above `#6E6E6E`).

### 2.3 Colour-vision deficiency simulation (Machado et al. 2009, severity 1.0; CIE76 ΔE)

| Pair | Normal | Deuteranopia | Protanopia | Luminance ratio |
|---|---|---|---|---|
| DOL buy/sell `#39FF14` / `#FF1744` | 170.5 | 37.0 (`#F0D83F` vs `#A2923C`) | 85.6 | 2.84 |
| Bias bull/bear `#00C864` / `#E63C3C` | 129.5 | **17.1** | 38.1 | 1.86 |
| iFVG bull/bear `#00B478` / `#E63C3C` | 119.8 | 30.6 | 25.0 | 1.54 |
| Okabe-Ito `#0072B2` / `#E69F00` | 120.2 | 121.7 | 109.5 | 2.30 |
| Proposed dark CVD `#2F9BFF` / `#FF8A1F` | 132.1 | 133.7 | 119.2 | 1.23 |
| Proposed light CVD `#0072B2` / `#C25400` (on white 5.19 / 4.60) | n/a | 103.5 | n/a | n/a |

- Dark CVD pair contrast: on black 7.25 and 8.91; on `#161616` 6.25 and 7.68; on the table 5.72 and 7.02.

### 2.4 Literature and platform evidence

| Claim | Numbers | Grade | Source |
|---|---|---|---|
| Red presentation changes financial risk-taking and expectations | 8 experiments; about 15–30% lower risk-taking vs black; red prolongs pessimism; absent in colour-blind subjects; weaker in China; yellow and blue no effect | **strong** (peer-reviewed, multi-study) | Bazley, Cronqvist & Mormann 2021, *Management Science* 67(9):5616–5641, https://papers.ssrn.com/abstract=2992812 ; summaries https://www.smu.edu/cox/coxtoday-magazine/2020-12-09-visual-finance-101 , https://news.ku.edu/news/article/2021/03/29/red-color-impacts-investor-behavior-financial-research-reveals |
| Showing uncertainty (quantile dotplot or CDF) improves decisions | Payoff about 97% of optimal, +5 pp vs no-uncertainty control; more consistent; beats textual uncertainty | **strong** (incentivised controlled experiment, CHI Best Paper HM) | Fernandes, Walls, Munson, Hullman & Kay 2018, CHI, doi:10.1145/3173574.3173718, https://idl.uw.edu/papers/uncertainty-bus |
| Natural frequencies beat probabilities | 7% → 45% correct Bayesian inferences | **strong** | Hoffrage et al. 2015, *Front. Psychol.* 6:1473, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604268/ (verified in competitors.md) |
| Precision is read as confidence | More digits → judged more confident; precise advisors preferred | **moderate** | Jerez-Fernandez, Angulo & Oppenheimer 2014, *Psych. Sci.* 25(2):633–635 (verified in competitors.md) |
| Red-green CVD prevalence | About 8% of men (1 in 12) and about 0.4–0.5% of women of Northern European ancestry; 4–6.5% in Chinese and Japanese men | **strong** | Birch 2012, PubMed 22472762, https://pubmed.ncbi.nlm.nih.gov/22472762/ ; MedlinePlus https://medlineplus.gov/genetics/condition/color-vision-deficiency |
| Contrast thresholds | Text 4.5:1 (large ≥ 18 pt or 14 pt bold: 3:1); graphics needed for understanding 3:1; line charts explicitly in scope | **strong** (standard) | WCAG 2.1 SC 1.4.3, 1.4.11, https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast (via search summary; host blocked for fetch) |
| More information raises confidence more than accuracy | Football-outcome forecasts: confidence rose with cues while accuracy plateaued | **moderate** | Tsai, Klayman & Hastie 2008, *OBHDP* 107:97–105 [unverified this session] |
| Transparency and fuzziness are intuitive uncertainty encodings | Ranked most intuitive among visual variables | **moderate** | MacEachren et al. 2012, IEEE TVCG 18(12) [unverified this session] |
| Colour-blind-safe palette | 8-colour Okabe-Ito set (`#0072B2`, `#E69F00`, `#56B4E9`, `#D55E00`, `#009E73`, `#F0E442`, `#CC79A7`, black) | **moderate** (design standard) | Okabe & Ito 2008; Wong 2011, *Nat. Methods* 8:441 [unverified this session] |
| Premium SMC tools offer declutter modes | LuxAlgo SMC: "Historical (default) or Present, which displays only recent data"; "Monochrome" style for FVG and premium/discount | **weak** (practitioner convention) | https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-LuxAlgo/ (via search summary) |
| Setters are cheaper than recreating drawings | `box.new()` cost ≈ 2× the two setter calls | **strong** (official profiler example) | local docs writing_scripts/profiling_and_optimization.md:1074–1112 |
| Test colours on light *and* dark themes; layered-width glow technique | Manual guidance | **strong** (official), benefit **weak** | local docs visuals/colors.md:394–410 |
| Input `display` defaults; `active` | `display.all` default for non-bool/colour inputs; `active` greys out | **strong** (official) | reference/input.md:27–28, 76; concepts/inputs.md:112; release_notes.md:506, 844 |
| Z-index groups | lines < boxes < labels < tables | **strong** (official) | visuals/overview.md:230–246 |
| Text sizes in points | Label normal = 12, small ≈ 10; table small = 10, normal = 14 | **strong** (official) | visuals/text_and_shapes.md:488–500; reference/label.md:177; reference/table.md:67 |
| Light / dark detection | `chart.fg_color` `#0f0f0f` = light, `#dbdbdb` = dark | **strong** (official) | concepts/chart_information.md:430–452; reference/chart.md:7–21 |

---

## 3. Engine gap analysis (line refs in `baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Status-line hygiene | **wrong** | 59–226 | 104 input calls (9 string, 3 timeframe, 23 int, 31 float, 10 session, 20 bool, 8 color). The 76 non-bool/colour inputs default to `display.all`, so about 76 values print in the legend. Data-window plots are fine (2444–2448). |
| Input tooltips / `active` / ordering | **partial** | 59–226 | 16 groups (42–57), good. 76 inputs have no tooltip, including all 10 sessions and the timezone. `active` is unused. Internals (Scoring, Order Flow) come before display groups. |
| Reference-fidelity palette and glow | **present** | 294–299, 1610–1615, 2214–2226 | Pixel-exact (§2.1). |
| Visual hierarchy / single focal point | **present** | 162–171 (extras off by default), 2214–2226 | One target, extras off, iFVG subordinate. |
| Contrast / light theme | **wrong** on light charts | 228–292, 2216–2226, 1256, 2166, 2189, 2212, 2278 | Dark-only palettes. On white every Clean element is ≤ 1.37:1. No use of `chart.bg_color` / `chart.fg_color`. |
| Colour semantics by side | **present** | 2203, 2154, 2164, 2183 | Side-coded, as in the reference. |
| CVD safety | **partial** | 228–284 | Redundant position and text cues exist. No CVD-safe theme; bias pair ΔE 17 under deuteranopia. |
| Typography | **present** | 604–610, 2226, 2143 | Matches the reference. No size input (int points possible). |
| Probability communication | **partial** | 2067, 2206–2209, 2225 | No horizon, no reference class; 95% shown on a reached target (COMP-4). |
| Timing communication | **partial** | 2117–2126, 2240 | `etaHit` is computed but shown only in Terminal; no p80; no calibration of ETA. |
| Tooltips | **partial** | 2206, 2226, 2248 (label); 604–610 (table) | Label tooltip present but lacks price, horizon and calibration. Table cells have none. |
| Z-order and layering | **partial** | 1613, 2216–2224, 2276–2286, 1254 | Glow and tether are lines, so iFVG, LVN and ghost boxes draw over them. No overlap fading. |
| Right-edge collisions | **missing** | 2166, 2188, 2212, 2278 | All at `xR`; no de-overlap. Clean default unaffected. |
| Drawing lifecycle | **partial** | 2132–2141, 2214–2248; 1638–1641 | 8 Clean objects deleted and recreated on every tick; iFVG uses setters; object caps are safe. |
| Data Window formatting | **partial** | 2444–2448 | No `precision`; score, PoT, D and hit % inherit symbol precision. |
| Bias table | **present** (look) / **missing** (alignment, tooltips) | 2294–2307 | Exact reference look; no alignment cue, no cell tooltips, no size option. |
| Autoscale | **partial** | 2250–2287, 2160–2168, 2193–2199 | LVN, objective and reach bands are not distance-capped (COMP-7). |
| State communication in Clean | **partial** | 2067, 2214–2226, 2237 | Counter-draw only in the tooltip; reached shown as 95%; stale and filtered silent. |
| Confidence as visual weight | **partial** | 2228 (Terminal only) | Clean has fixed weights. |

---

## 4. Proposals (best first; maximum 10)

All keep the Clean default visually identical to the reference on a dark chart unless stated.

### UX-1 (P1, S) · Legend and settings hygiene
Same core finding as COMP-1; this version adds the dependency map, ordering and Data Window precision.

**Problem.** About 76 input values print in the status line; 76 inputs have no tooltip; inputs irrelevant to the current mode look editable; internals precede display settings.

**Spec.**
1. **`display = display.none`** on every `input.int`, `input.float`, `input.string`, `input.timeframe` and `input.session` call (76 calls, lines 59–216).
   - Write the literal in each call. The parameter is `const plot_display`; do not store it in a variable.
   - Optional: keep `modeIn` as `display.status_line` so the legend reads "DOL Engine v2 Day Trading".
2. **`active` dependency map.** Usages were checked by grep.

   | Inputs | `active =` |
   |---|---|
   | `cHTF`, `cSTF`, `cEXE` | `modeIn == "Custom"` |
   | `sessAs`, `sessLo`, `sessNA` | `useSess` |
   | `fvgMin`, `fvgQMin` | `useFVG` |
   | `obLook`, `obQMin`, `useBRK` | `useOB` |
   | `lvnHours`, `lvnRows` | `showLVN or usePathVP` (both feed `needVP`, lines 979, 1009, 1902) |
   | `lvnThr`, `lvnN` | `showLVN` (used only at 2261, 2275, 2282) |
   | `ghostMax` | `showGhost` |
   | `hudSize` | `uiStyle == "Terminal"` |
   | `priorM` | `potModel == "Empirical"` (1310, 1321) |
   | `tablePosIn` | `showTable` |
   | `uAbove` … `uText` | `theme == "Custom"` |

   - Leave `dispMult` (used by displacement in D, 902–939), `ifvgMaxIn` and `ifvgMax` (the iFVG alert works even when boxes are hidden) always active.
   - The `active` argument must reference inputs declared *above* it. All of these already are.
3. **Group order.** Pine lists groups in order of first appearance. Move input blocks to this order (inputs have no dependencies except `active` and the derived `tfH`/`tfS`/`tfE` and theme colours, which move with them):
   1. Trading Mode
   2. DOL Display
   3. Probability of Touch
   4. Theme
   5. Panel
   6. iFVG
   7. Ghost Trail
   8. Volume Profile
   9. Liquidity Sources
   10. Key Liquidity
   11. Imbalances & Blocks
   12. Sessions & Killzones
   13. "Advanced · Scoring"
   14. "Advanced · Order Flow"
   15. "Advanced · Engine"
   16. "Advanced · Accuracy"

   Rename the const group strings (42–57) accordingly.
4. **Tooltips** for the 76 inputs without one. Priority set:
   - **Sessions and killzones:** "HHMM-HHMM in the Session Timezone below (default America/New_York). Asia 20:00–00:00 NY = 01:00–05:00 London."
   - `tz`: "IANA name, e.g. Europe/London. All session and killzone inputs use it."
   - **Weights:** "Relative importance; they are normalised, so only ratios matter."
   - `wS`/`wM`/`wL`: "Components of the draw vector D; normalised."
   - `potH`: "PoT is the chance of touch within this many bars of the chart TF."
   - `extBars`: "How far right of the last bar the target zone, label and iFVGs extend (reference look: 20)."
   - `minScore`, `hyst`: what changes visibly.
5. **Text-size inputs** (int points, v6):
   - `int lblPt = input.int(12, "Label Text (pt)", minval = 6, maxval = 24, group = G_DOL, display = display.none)`. Use `size = lblPt` in the Clean label (2226). `size` is "series int/string" (reference/label.md:177). The default 12 equals `size.normal`, which keeps fidelity.
   - `int tblPt = input.int(10, "Panel Text (pt)", minval = 6, maxval = 20, group = G_TABLE, display = display.none)`. Used in `f_cellC` / `f_cell` (604–610) as `text_size = tblPt`. The default 10 equals `size.small`.
   - Functions may read globals declared earlier; the inputs are declared at 40–226, before 604.
6. **Data Window precision** (2444–2448):
   - `precision = 1` on "DOL Score", "DOL PoT %" and "Ledger Hit %";
   - `precision = 2` on "Draw Direction D";
   - leave "DOL Price" at the symbol default.
   - The `precision` parameter is "input int" (reference/plot.md:245).

**Value.** The single most visible difference from the reference disappears. Settings become navigable, and session mistakes (which silently mislabel PDH, Asia and killzones) drop.

**Evidence.** Mechanism **strong** (official docs). Benefit **weak** (convention, reference look).

**Risk.**
- Users who liked inputs in the legend lose them.
- Re-ordering a 170-line block risks a forward reference. Keep each derived variable (tfH/tfS/tfE, theme colours) immediately after its inputs, and run `pine_parse.sh`.

**Effort.** S. **Ledger.** Not measurable; zero risk to selection.

### UX-2 (P1, S/M) · Theme-aware rendering: light-chart palette with two colour roles and a light glow recipe
Extends COMP-8 with the text/graphics split and the layer recipe.

**Problem.**
- On a white chart every Clean DOL element is between 1.04 and 1.37:1, so the target is invisible.
- iFVG is 1.29 / 1.89; LVN 1.60; transparent-background label text ≤ 1.6.
- COMP-8 would switch `c` to the light variant everywhere. But the Clean label and table are **dark-backed**: `#0B7A2E` on `#161616` is 3.31:1 and `#C8102E` is 3.08:1, which fail 4.5:1. The neon text (13.35:1) must stay.

**Spec.**
- **Detection** (global, after the theme switch, about line 292):
  ```
  bool lightBg = chart.fg_color == #0f0f0f   // doc: #0f0f0f for light backgrounds (chart_information.md:431, 449)
  ```
  - `chart.fg_color` is "input color", so `lightBg` is input-qualified and usable anywhere.
  - Add `string bgMode = input.string("Auto", "Chart Background", options = ["Auto", "Dark", "Light"], group = G_COL, display = display.none)` as an override.
- **Two roles.**
  - **Text roles** (`cAbove`, `cBelow`, `cIBull`, `cIBear`) stay as they are, for the Clean label (2225), the table (2294–2307) and the Terminal HUD panel (`cPanel` t8).
  - **Graphics roles**, new:
    ```
    gAbove = lightBg ? (classic ? #0B7A2E : f_onLight(cAbove)) : cAbove
    gBelow = lightBg ? (classic ? #C8102E : f_onLight(cBelow)) : cBelow
    gIBull = lightBg ? (classic ? #00875A : f_onLight(cIBull)) : cIBull   // iFVG
    gIBear = lightBg ? f_onLight(cIBear) : cIBear
    gLVN   = lightBg ? #9A6B00 : cLVN
    gGhost = lightBg ? #5F6B7A : cGhost
    ```
    with `f_onLight(color x) => color.from_gradient(0.55, 0.0, 1.0, x, #000000)` (≥ 5.08:1 on white for all 17 theme colours; `color.from_gradient` at global scope is verified compiling).
  - Use the g* colours for the box, glow, tether, iFVG boxes (1612), ghosts (1253–1257), LVN (2276–2286), and the secondary, objective and invalidation lines and their transparent-background labels.
- **Light glow recipe** (replaces 2219–2223 when `lightBg`): a "highlighter" halo plus a solid core; no white filament.
  ```
  // dark (unchanged): (90,10) (80,7) (60,4) (30,2) + white t15 w1
  // light:            (85,8)  (70,4) + core gC t0 w2
  ```
  - Computed on white: core 5.47:1; halo 1.41 and 2.04 (decorative); fill `color.new(g, 90)` = 1.15 (tint); dashed border `color.new(g, 45)` ≈ 2.6; tether `color.new(g, 20)` = 3.75 (≥ 3:1).
  - iFVG on light: fill t80, border t40.
- **Unchanged.** `cLblBg` (`#161616`) and the table colours: dark panels read well on both themes, and they keep the reference look.
- **Mock.** `study/ux_tools/mock_light_theme.png`: current dark, current on white (invisible), proposed on white.

**Value.** The indicator becomes usable on light charts. The Pine manual asks for this explicitly, and competitor users have complained about the same failure.

**Evidence.** **Strong** (WCAG thresholds plus computed ratios; official guidance). Size of the light-theme user share: **weak/unknown**.

**Risk.**
- Gradient backgrounds: `chart.bg_color` returns the midpoint; `fg_color` should follow it. The `bgMode` override covers edge cases.
- Assumption: a change of chart background triggers recalculation, as inputs do. Verify in TradingView.
- Doubles the colour variables (about 8 lines).

**Effort.** S/M (about 40 changed lines). **Ledger.** Not measurable.

### UX-3 (P2, S) · Clean label state grammar, with a counter-draw ledger split
Builds on COMP-4's "✓ REACHED"; adds counter-draw and stale states and measures counter-draw targets.

**Problem.** Clean hides states a trader must know:
- a counter-draw target (order flow points the other way) looks identical to a draw-side one;
- a reached target reads "PoT: 95.0%";
- a target older than the PoT horizon still reads like a fresh forecast.

**Spec** (Clean branch, 2214–2226; no layout change):

| State | Line 1 | Line 2 | Visual |
|---|---|---|---|
| draw-side (default) | `Target: BSL` | `PoT: 70.1%` | as now |
| counter-draw (`activeCtr`, 2029) | `Target: BSL ⚠` | `PoT: 70.1%` | tether `line.style_dotted` instead of dashed; tooltip first line "Counter-draw: order flow D = −0.42 points the other way" |
| reached (`sweptNow`) | `Target: BSL` | `✓ Reached` | core line solid `c` t0; no PoT (COMP-4) |
| stale (`bar_index − activeSince > H`, no hit) | `Target: BSL` | `PoT: 41.0% · late` | label `textcolor = color.new(c, 35)` |

- The "⚠" glyph is a redundant cue beyond colour (CVD-safe).
- **Ledger split.**
  - Add `bool ctr = false` to `Trial` (375–396) and set it in `f_openTrial` (1426).
    - `var bool activeCtr` is declared at 1038, before `f_openTrial`, so the function may read the global directly.
    - It is assigned at 2029, before the call at 2045, so the value is current.
    - Passing it explicitly as `f_openTrial(Level lv, bool ctr)` is equally valid and clearer.
  - In `f_book` (1461) accumulate `var array<float> ctrSt = array.new<float>(6, 0.0)`: n, k and ΣpBase for draw-side (index 0–2) and counter-draw (3–5).
  - Tooltip line: "Counter-draw targets here: 18 of 47 hit (38%) · edge −2.1 pp vs random". Terminal Full gets a row "CTR / DRAW".

**Value.**
- The trader sees at once when the target fights order flow, and how such targets have actually fared on this symbol.
- The split also validates the selection rule "draw-side first, counter-draw fallback" (decision history) with data.

**Evidence.** State visibility **weak** (convention). The measurement itself is **moderate** (it uses the engine's own distance-matched baseline).

**Risk.**
- "⚠" changes the reference text only when counter-draw.
- Glyph rendering in the default font: "⚠" is already used in the code (2237, 2306), so it is safe.

**Effort.** S.

### UX-4 (P2, S/M) · Time projection (WHEN): ETA marker plus ETA coverage calibration in the ledger
**Problem.**
- The engine computes the median bars-to-hit of similar past targets (`etaHit`, 2117–2126) but Clean never shows it.
- The 20-bar right extension carries no time meaning.
- Users ask "when?".
- No one checks whether the ETA is calibrated.

**Spec.**
- **Helper** in STATE HELPERS, after `ttHit` and `dHit` are declared (STATE 1020–1080):
  ```
  f_eta(float dNow) =>    // [p50, p80] bars-to-hit of hits from a similar distance, conditional on a hit
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
  - Do not return the tuple from a ternary: tuples cannot be ternary operands. Use the `if` block as above.
  - Place `f_eta` after line 1075 (`dHit`) and before `f_openTrial` (1426), which will call it.
  Use it to replace the inline loop at 2120–2126.
- **Display.** Input `etaMode = input.string("Tooltip", "Time Projection", options = ["Off", "Tooltip", "Marker"], group = G_DOL, display = display.none)`.
  - **Tooltip** (default; keeps the look): "Typically reached in 6–14 bars (≈ 30–70 min) when reached · n 37".
  - **Marker:** a short dotted vertical line at `x = bar_index + math.min(500, int(p50))`, spanning the zone's height (top to bottom), in `color.new(c, 40)`. Add a second one at p80 in `color.new(c, 70)`.
    - If p80 > `extBars`, extend the zone's right edge to `bar_index + p80` (capped at 500) so the marks sit on the zone.
    - Only one or two extra lines, created with the zone.
- **Ledger calibration.**
  - Add `float eta50 = na` and `float eta80 = na` to `Trial`. Set them in `f_openTrial` via `f_eta(d0)`. This costs one loop of ≤ 300 at commit time only.
  - In `f_book` on a hit with non-`na` `eta50`: `etaSt` += [1, `t.bars <= t.eta50`, `t.bars <= t.eta80`].
  - Terminal Accuracy row: "ETA cover 48% / 79% (n 63)". A well-calibrated ETA reads about 50% / 80%. Far below means the engine is too optimistic about speed; far above means too pessimistic.

**Value.**
- Answers WHEN with a number, the time-horizon dimension that Fernandes et al. showed improves decisions when uncertainty is shown (here as a 50–80% band).
- The ledger tells the user whether to trust the band.

**Evidence.** **Moderate** for showing time uncertainty (Fernandes 2018: about 97% of optimal, +5 pp). ETA validity is unknown, but the proposal measures it.

**Risk.**
- The ETA is conditional on a hit. Label it "when reached", or a trader will read it as a promise.
- With too few similar hits (n < 5) show nothing.
- Bars are not clock time across session gaps; COMP-4's `f_dur` gives a "≈" clock string.

**Effort.** S/M.

### UX-5 (P2, S) · Bias table: alignment cue, cell tooltips, optional accuracy row, and a ledger split by alignment
COMP-4 already lists cell tooltips; this adds the alignment logic and the measurement.

**Problem.** The reference's usage note is "act when the Execution TF bias aligns with the HTF bias", but the table never says whether they align or whether the active target agrees. Nobody knows whether aligned targets do better on this symbol.

**Spec.**
- **Alignment state** at `barstate.islast`:
  - `int bH = htfBias != 0 ? htfBias : htfIB`, and likewise `bE` for the Execution TF.
  - `int algn = na(activeLv) ? 0 : (bH == activeLv.side and bE == activeLv.side) ? 1 : (bH == -activeLv.side) ? -1 : 0`.
- **Table** (Clean; 2294–2307). New input `tblExtra = input.string("None", "Clean Table Extras", options = ["None", "Target row", "Target + Accuracy"], group = G_TABLE, display = display.none)`. The default "None" keeps the 3-row reference look.
  - **Target row:** `f_cellC(dash, 0, 4, "DOL", cText, na)` and `f_cellC(dash, 1, 4, (activeLv.side == 1 ? "▲ " : "▼ ") + f_shortName(...), side colour, na)`. Prefix "✓" when `algn == 1`, "⚠" when `algn == -1`.
  - **Accuracy row:** "Hit 62% · Edge +8pp" from the existing `stK`, `stN` and `stPE` (2382–2400 logic). Show "calibrating" below 20 trials.
  - **Cell tooltips** (`table.cell(..., tooltip = tip)`): give `f_cellC` an optional `string tip = ""` parameter (604–610).
    - Per TF row: "Swing BULL (body break of 5,112.0) · internal BEAR · price at 62% of dealing range (premium)", from `htfRH`, `htfRL`, `htfIB` and the other TFs' equivalents.
    - Header: "Swing bias from confirmed pivots; internal bias while the swing is undecided."
- **Ledger split.**
  - Add `int algn` to `Trial`, set in `f_openTrial` through a new argument.
    - Compute `algn` on confirmed bars at commit (step 19, right after `activeCtr` at 2029), not only at `barstate.islast`.
    - If it is kept as a global instead, declare `var int activeAlgn = 0` in STATE (1020–1080) so that it precedes `f_openTrial`. Pine has no forward references.
  - Accumulate n, k and ΣpBase for aligned / neutral / against, `var array<float> alSt = array.new<float>(9, 0.0)`.
  - Terminal Full row "ALIGN +9.2pp (n 88) · AGAINST −1.0pp (n 41)". Accuracy-row tooltip in Clean likewise.

**Value.** Turns the reference's usage advice into a visible cue, and gives the user per-symbol evidence of whether to filter for alignment.

**Evidence.** **Weak** for MTF alignment as practitioner doctrine. The split makes it measurable.

**Risk.**
- An extra row deviates from the reference, hence off by default.
- Tooltip strings are built only at `barstate.islast`, so the cost is negligible.

**Effort.** S.

### UX-6 (P3, S) · Colour-vision-safe theme and an optional direction glyph
**Problem.**
- Red-green hue is the only cue distinguishing bias bull from bear: deuteranopia ΔE is 17, and only the words differ.
- Red carries a documented pessimism and risk-aversion effect (Bazley et al. 2021).
- About 8% of male traders have red-green CVD.

**Spec.**
- Add theme option "Colorblind" to `theme` (line 228) and each colour `switch` (240–292):
  - above / bull `#2F9BFF`;
  - below / bear `#FF8A1F`;
  - LVN `#F0E442`;
  - ghost `#7D8799`;
  - panel `#0B0F14`;
  - text `#E6EDF3`.
- Computed: deuteranopia ΔE 134 and protanopia ΔE 119 between the pair; 6.25 and 7.68 on the label; 5.72 and 7.02 on the table.
- With UX-2, the light variants are `#0072B2` / `#C25400` (5.19 / 4.60 on white).
- **Glyph input.** `bool glyph = input.bool(false, "Direction Glyph in Label", group = G_DOL)` prefixes "▲ " or "▼ " to the Clean label's first line. Default off for reference fidelity; on when theme is Colorblind.

**Value.** Usable by about 1 in 12 male traders without relying on the table words. It also offers a hue-neutral option to users who want to avoid the red effect.

**Evidence.** Prevalence **strong**; red effect **strong** (peer-reviewed, 8 experiments); palette **moderate**.

**Risk.** None to the default.

**Effort.** S.

### UX-7 (P3, M) · Persistent drawing objects updated with setters
**Problem.**
- On every realtime tick the renderer deletes and recreates the Clean zone, 5 glow lines, the tether and the label: 8 objects (2132–2141, 2214–2226). Terminal and the extras add more.
- The Pine manual measures `box.new` at about twice the cost of two setters.
- Recreation may also reset hover tooltips or user selection on fast symbols [hypothesis].

**Spec.**
```
type DolGfx
    box   zone
    line  teth
    label lbl
    array<line> glow
var DolGfx gx = DolGfx.new(na, na, na, array.new<line>())
```
- On `barstate.islast`:
  - **If the DOL is shown:** when `na(gx.zone)`, create all 8 objects once. Otherwise update them:
    - `box.set_lefttop`, `box.set_rightbottom`, `box.set_bgcolor`, `box.set_border_color`, `box.set_border_style`;
    - `line.set_xy1`, `line.set_xy2`, `line.set_color`, `line.set_width`, `line.set_style` for the glow and tether;
    - `label.set_xy`, `label.set_text`, `label.set_textcolor`, `label.set_color`, `label.set_tooltip`, `label.set_size`.
  - **If not shown:** delete all and reset to `na`.
- Keep the existing `dB`/`dLn`/`dLb` arrays for the optional extras (secondary, objective, reach, LVN), or move them to the same pattern later.

**Value.** Lower per-tick CPU; possibly stable tooltips; cleaner code paths.

**Evidence.** Cost difference **strong** (official profiler example). UX benefit **weak** (hypothesis).

**Risk.**
- Stale-object bugs: a hidden state where objects remain must be handled by the delete branch.
- Different glow layer counts in dark (5) and light (3) modes mean deleting and recreating on a theme change; theme changes are rare.

**Effort.** M (refactor of about 60 lines). Validate with the Pine Profiler.

### UX-8 (P3, S/M) · Layering and right-edge collision management
**Problem.**
1. Lines are always below boxes. iFVG fills (t75), LVN boxes (t91) and ghost boxes (t94) draw over the DOL glow and tether where they overlap, which is typical during an iFVG retest.
2. The optional right-edge labels (secondary, objective, invalidation, LVN text) can overprint the DOL label and each other.

**Spec.**
- **Overlap fade.** In the `barstate.islast` block (2145–2149, where iFVG right edges are already set):
  ```
  bool dolVis = showDOL and not na(activeLv) and dolShown
  for z in ifvgs
      if not na(z.bx)
          // v6 `and` is lazy (migration guide "Lazy evaluation of conditions"), so activeLv is never read when na
          bool ov     = dolVis and z.top >= activeLv.bottom and z.bottom <= activeLv.top
          bool onTeth = dolVis and z.top >= math.min(close, activeLv.price) and z.bottom <= math.max(close, activeLv.price)
          box.set_bgcolor(z.bx, color.new(z.col, ov ? 92 : onTeth ? 85 : (clean and classic) ? 75 : 85))
  ```
  - Add `color col` to `Zone` (348–359) and set it at creation (1609–1621) to `ic`.
  - The base transparencies of 75 (Classic Clean) and 85 (other) mirror line 1614.
  - LVN: skip drawing LVN zones overlapping the active zone (2276–2286).
- **Collision manager** (Terminal or extras on):
  - Collect right-edge labels as (y, priority, text).
  - `minSep = 0.05 * (ta.highest(high, 150) - ta.lowest(low, 150))`. The global series is computed every bar; 5% of the 150-bar range approximates one 2-line label height at default zoom.
  - Place them in priority order: DOL → invalidation → objective → secondaries.
  - A label within `minSep` of an already placed one is **staggered right**: `x = xR + 14 * k` bars, k = 1..3, each ≤ `bar_index + 500`. Its line is extended to the new x, so the pointer still sits on its own price.
  - After 3 staggers, drop the label and append its text to the DOL label tooltip ("Also near: PDH 5,131.5 · 2 secondary").

**Value.** The target stays the brightest object even inside iFVG retests, and the optional extras stay legible.

**Evidence.** Z-order **strong** (official). Benefit **weak**.

**Risk.**
- `minSep` is a heuristic; pixel height is unknown to Pine, and `chart.left_visible_bar_time` would force a recalculation on every scroll. Do not use it.
- Fading an iFVG while it overlaps the target slightly changes the reference look in that case only.

**Effort.** S/M.

### UX-9 (P3, S) · Confidence-weighted glow (bounded)
**Problem.** Clean renders a 35% PoT target with the same brightness as an 85% one, so visual weight does not track the forecast.

**Spec.**
- `float g = na(activePoT) ? 1.0 : f_clamp((activePoT - 0.40) / 0.30, 0.0, 1.0)`, so 70% PoT gives `g = 1` and the reference look. `color.new` accepts a float `transp` ("series int/float", reference/color.md:116), so no rounding is needed.
- Outer layer transparencies become `90 + 6 * (1 - g)`, `80 + 8 * (1 - g)` and `60 + 10 * (1 - g)`. The 30-transparency layer and the core are unchanged, so the line stays crisp and above 3:1.
- Input `confGlow = input.bool(false, "Confidence-Weighted Glow", group = G_DOL)`. Default off for exact fidelity; recommended on.

**Value.** Pre-attentive cue for how likely the touch is.

**Evidence.** **Moderate** (MacEachren et al. 2012, transparency as an intuitive uncertainty cue) [unverified this session].

**Risk.** Low PoT dims the target. Bounded so it never disappears.

**Effort.** S.

---

## 5. Sources

**Official Pine Script v6 documentation** (local mirror `scratchpad/docsrc/jabez4jc_pinescriptv6/`):
- reference/input.md:12–28, 65–77, 99–111, 147 (`display` defaults, `active`);
- concepts/inputs.md:112;
- release_notes.md:506 (`active`, July 2025), 617–618 (int text sizes, `text_formatting`), 844 (input `display`), 746 (plot `format`/`precision`);
- reference/chart.md:7–21 and concepts/chart_information.md:430–452 (`chart.bg_color`, `chart.fg_color`, light detection);
- visuals/colors.md:392–410 (light/dark testing, hierarchy, presets, layered-width glow);
- visuals/overview.md:230–246 (z-index groups);
- visuals/text_and_shapes.md:482–500 and reference/label.md:177 (sizes in points);
- reference/table.md:53, 67, 69 (cell `tooltip`, `text_size`);
- writing_scripts/profiling_and_optimization.md:1074–1112 (setters vs recreation);
- visuals/lines_and_boxes.md:22 (object limits and GC);
- writing_scripts/limitations.md:381 (500 future bars);
- reference/plot.md:227–245 (plot `precision`);
- writing_scripts/publishing.md:116–123 (clean chart, status line).

**Web, verified this session** (WebSearch summaries):
- Bazley, Cronqvist, Mormann (2021). Visual Finance: The Pervasive Effects of Red on Investor Behavior. *Management Science* 67(9):5616–5641. https://papers.ssrn.com/abstract=2992812 ; https://econpapers.repec.org/RePEc:inm:ormnsc:v:67:y:2021:i:9:p:5616-5641 ; https://www.smu.edu/cox/coxtoday-magazine/2020-12-09-visual-finance-101 ; https://news.ku.edu/news/article/2021/03/29/red-color-impacts-investor-behavior-financial-research-reveals
- Fernandes, Walls, Munson, Hullman, Kay (2018). Uncertainty Displays Using Quantile Dotplots or CDFs Improve Transit Decision-Making. CHI. doi:10.1145/3173574.3173718. https://idl.uw.edu/papers/uncertainty-bus ; https://www.hullmanlab.northwestern.edu/paper%20discrete-outcome/2018/01/01/uncertainty-bus.html
- Birch (2012). Worldwide prevalence of red-green color deficiency. https://pubmed.ncbi.nlm.nih.gov/22472762/ ; MedlinePlus: https://medlineplus.gov/genetics/condition/color-vision-deficiency
- W3C WCAG 2.1 Understanding SC 1.4.11 Non-text Contrast: https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast ; WebAIM contrast: https://webaim.org/articles/contrast/
- LuxAlgo Smart Money Concepts (open source; Historical/Present mode, Monochrome style): https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-LuxAlgo/

**Verified by the competitors study** (`study/competitors.md`):
- Hoffrage, Krauss, Martignon, Gigerenzer (2015), *Front. Psychol.* 6:1473, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604268/
- Jerez-Fernandez, Angulo, Oppenheimer (2014), *Psychological Science* 25(2):633–635
- TradingView Help "My chart looks compressed" (43000762934)

**Cited from memory [unverified this session]:**
- Tsai, Klayman & Hastie (2008), *OBHDP* 107:97–105;
- Oskamp (1965), *J. Consulting Psychology*;
- MacEachren et al. (2012), IEEE TVCG 18(12);
- Okabe & Ito (2008), Color Universal Design;
- Wong (2011), *Nature Methods* 8:441;
- Machado, Oliveira & Fernandes (2009), IEEE TVCG (the simulation matrices used in `contrast.py`).

**Measured and computed in this session:**
- `study/ux_tools/contrast.py`, `light.py`, `mock.py`;
- `ref_target.png`, `ref_table.png`, `ref_table_zoom.png`, `ref_ifvg.png`, `mock_light_theme.png`.
