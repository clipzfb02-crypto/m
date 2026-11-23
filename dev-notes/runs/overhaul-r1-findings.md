# Overhaul round 1: audit findings (15 lenses) and verdicts so far

Workflow killed during Verify; resume with dev-notes/workflows/dol-engine-overhaul-*.js (see HANDOFF.md).

## P2 cs-hvalid-equal-high: f_structure marks an MTF pivot as swept on an exactly equal high/low, against the strict-through sweep rule used everywhere else
- line 780 | VERIFIED real=True worth=True (medium)
- impact: If a right-side HTF/STF bar exactly ties the pivot high or low, htfHV/stfHV comes back false. The double-top or double-bottom pivot, which is classic equal-high liquidity, is then never pushed into the external registry, so it never becomes a candidate DOL. The docs do not say how ta.pivothigh treats ties, so this may not happen at all. In that case the patch is a harmless no-op. Otherwise it brings back the strongest MTF pools on instruments with coarse ticks (futures). Effect: low. Risk: none.

## P2 cs-mtf-anchor-print-bar: HTF/STF pivot zones start at the HTF/STF candle's opening bar, not the candle that printed the high/low
- line 1223 | VERIFIED real=True worth=True (high)
- impact: When the active DOL is an STF or HTF liquidity pool (often, since their tier weights 0.45/0.65 are higher than chart pools at 0.25), the Clean-style target box and the Terminal dotted lines start at the first candle of the 4H/D bar, not at the wick that made the high or low. That is up to 3 candles early on 1H for 4H pivots, up to 23 on 1H for D pivots, and up to 47 on 5m for 4H pivots, so the zone visibly starts at a candle that never traded that price. This contradicts the reference look (a box 'anchored left at the candle that formed it') and the input's own tooltip. PDH/PWH and session pools are unaffected because they already carry exact print bars.

## P2 perf-1: Last-bar analytics (f_invalidation, 4x f_reachD, ETA scan, median) run on every realtime tick even when the Clean style displays none of them
- line 2111 | VERIFIED real=True worth=True (high)
- impact: No visual change. In the default Clean style each realtime tick no longer runs a pool scan, two f_raceH series, four survival-curve scans, a scan over up to 300 hits and two median sorts. That is roughly 1-3k primitive operations saved per tick. Terminal style, Reach Bands and Invalidation are unaffected because their conditions still compute exactly what they read.

## P1 rp-bias-done: Bias (table and engine) ignores the last completed HTF/STF/exec bar until the next bar opens, so it is stale for the whole night or weekend when the market is closed
- line 926 | not yet verified
- impact: Over a weekend or overnight, a trader sees 'D BEARISH' even though Friday's daily candle closed through the protected high. The table, the draw direction and the DOL side all lag by one full HTF candle exactly when traders prepare the next session. Without this fix the table looks wrong.

## P1 rp-partial-pwh: PWH/PWL (and PDH/PDL on short histories) come from a partial first period when chart history starts mid-week or mid-day
- line 946 | not yet verified
- impact: Scalpers on 1m and 2m charts get a 'PWH' or 'PWL' target, top-tier and labelled as such, at a price that is not the previous week's high or low. The DOL can lock onto it, and it disagrees with the trader's own PWH line, so the targets look wrong.

## P2 rp-table-below-chart: Bias rows whose timeframe is below the chart's show chart-timeframe structure under the lower timeframe's label
- line 2303 | not yet verified
- impact: A trader on a 4H chart reads '1H BULLISH' as execution-timeframe confirmation while it is really the 4H bias of the previous bar. That gives false HTF/exec alignment, which is exactly the confluence the table is meant to show.

## P2 rp-kz-above-1h: Killzones are classified by bar open time on 2H/4H charts, so selection hysteresis and session affinity flip by accident
- line 975 | not yet verified
- impact: On 4H charts the DOL becomes sticky or responsive depending on which 4H candle is open, not on the actual killzone. The HUD reports the wrong killzone.

## P1 LIQ1: Stacked-pool rule demotes key levels (PDH/PWH/session/HTF) to inducement when any weaker pool sits just beyond them
- line 1240 | not yet verified
- impact: The DOL label says 'BSL' at a random older swing above the obvious PDH or session high, or it skips the key level altogether. An ICT trader sees the textbook draw (PDH or session high) passed over for an insignificant swing. With the patch, the outermost pool is still the draw when its tier is equal or higher, which is the old behaviour for every same-tier pair. A higher-tier inner pool is no longer demoted, and both pools count as a stack.

## P1 LIQ2: Relative equal highs/lows between key levels (PDH ~ Asia H, London L ~ PDL, ...) are never counted
- line 1845 | not yet verified
- impact: The most obvious ICT draws, equal key highs/lows across sessions and days, score like any single level and show no EQ tag. As a side benefit, a chart pivot on the same candle as a merged key print is no longer counted again.

## P2 LIQ3: Relative equal highs/lows lose their EQ history when the second swing runs the first by less than the equal tolerance
- line 1762 | not yet verified
- impact: Double tops and bottoms that are nearly equal, among the most obvious draws, lose their equal-high/low density and EQ tag.

## P2 LIQ6: Killzone affinity boosts days-old session and PD pools as if they were today's ranges
- line 1941 | not yet verified
- impact: During London or NY the target can become an 'ASIA H' or 'LDN L' that is days old. A trader reads it as today's session range and the target looks wrong.

## P2 LIQ5: Session, day and week extremes start 'immature' on freshness exactly when they matter most
- line 671 | not yet verified
- impact: PDH, PDL, PWH, PWL and session highs/lows systematically lose a few points to ordinary swings the day after they form. With minScore 35 and hysteresis 4, that is enough to change the selected target.

## P2 LIQ7: HTF/STF liquidity pools anchor at the open of the MTF bar, not on the candle that printed the high/low
- line 1783 | not yet verified
- impact: HTF/STF targets are drawn from the wrong candle, and their bornBar (freshness and print identity) is off by up to one MTF bar.

## P2 LIQ4: A tick-exact touch of a pool counts as neither a sweep nor a test
- line 654 | not yet verified
- impact: Exact equal highs/lows on non-pivot bars, the strongest kind of test, add no density.

## P1 PD-1: HTF FVGs are dropped for good once price is more than 15 chart-ATR away, and are never added at all if they print that far away
- line 1859 | not yet verified
- impact: On the user's 5m Gold chart (screenshot) daily FVGs either never show up or disappear after one session. When price later trades into an obvious unfilled daily FVG, the engine does not know the FVG exists, so 'HTF BEFVG/BUFVG' targets are largely missing. The HTF density bonus and slow freshness clock (hlMult) built for long-lived HTF arrays never get used.

## P2 PD-2: The classic ICT breaker (old low taken, then a close above the swing high) is never created; the breaker liquidity gate checks the wrong extreme
- line 1706 | not yet verified
- impact: The most common breaker in ICT trading, the sweep followed by a market-structure shift, never appears as a BUBRK/BEBRK target. Breakers only show up from the rarer case of a failed order block that itself swept liquidity.

## P2 PD-3: An order block is thrown away instead of being moved to the higher-low (or lower-high) retest candle
- line 1695 | not yet verified
- impact: Clear BUOB/BEOB arrays at double bottoms, double tops and higher-low/lower-high retests, the most obvious order blocks on the chart, are missing from the target pool.

## P2 PD-4: The order-block quality gate almost always passes: a one-tick gap anywhere in the leg counts as 'imbalance'
- line 1688 | not yet verified
- impact: Weak order blocks with no displacement get into the pool as BUOB/BEOB targets. The user's OB quality input appears to have no effect.

## P2 PD-5: HTF FVGs skip the quality gate and the middle-candle direction check that chart FVGs get
- line 942 | not yet verified
- impact: 'HTF BEFVG/BUFVG' targets come from non-displacement daily gaps, so the HTF target looks arbitrary to an ICT trader.

## P2 PD-6: iFVG boxes left far behind are never cleaned up and keep stretching to the right edge
- line 1636 | not yet verified
- impact: Old iFVG bands crowd the Clean view and do not match the reference, where only nearby iFVGs share the DOL's right edge.

## P1 struct-F1: Swing CHoCH lags: the protected low/high is set from the previous BOS candle instead of the HL/LH that produced the break
- line 755 | not yet verified
- impact: The swing bias on D/4H/1H flips about 8 HTF bars earlier at the median after a real structure shift. On D that is more than a week of a stale BULLISH or BEARISH reading while the chart has already broken the HL. Agreement is unchanged and there is only a small rise in whipsaw. drawD and the PoT bias buckets inherit the more timely htfBias and stfBias.

## P1 struct-F2: Bias table is one HTF candle stale whenever the last chart bar is confirmed (weekend, after hours, period close)
- line 782 | not yet verified
- impact: Over a weekend or after hours, which is when traders do their HTF analysis, the D / 4H / 1H rows agree with what the trader sees on those charts. Today they lag one candle and can show the wrong direction right after a structure break on the last candle.

## P2 struct-F3: Table rows are labelled with the configured TF even when f_tfSafe substituted the chart TF
- line 2303 | not yet verified
- impact: No visible change in normal use. When the chart TF is too high, the table says which timeframe each row really shows instead of misreporting a 1H or 5m bias.

## P1 dol-A-taper-evicts-active: Near-distance taper takes points off the ACTIVE target as price closes in, so it gets swapped out just before it is taken
- line 666 | not yet verified
- impact: The DOL jumps to a further pool exactly as price is about to tag the obvious one. The trader then sees:
- the EQH get raided while it is no longer the target;
- no 'DOL Target Swept' alert;
- a ledger miss instead of a hit;
- a target that looks like it runs away from price.
The taper was meant to screen NEW picks ("being delivered, not drawn to"), not to evict a committed target.

## P1 dol-D-inner-demotes-bigger-pool: Stack logic demotes equal highs or a PDH (x0.70) behind any lone pivot within 0.75 ATR beyond it
- line 1240 | not yet verified
- impact: This is exactly 'the target sitting behind a closer, more obvious pool on the same side'. The label reads 'Target: BSL' on a random pivot just past the EQH or PDH that every trader is watching. When the EQH/PDH raid reverses, which is the common outcome, the displayed target is never reached. The fix keeps the 'outermost pool is the draw' rule when the outer pool is at least as big (same tier, or more equal highs/lows), so stacked chart pivots behave as before.

## P1 dol-C-trim-kills-fresh-arrays: When the pool is full, trimming by score deletes every new FVG/OB/breaker during its origin lockout, plus the whole counter-draw side
- line 1956 | not yet verified
- impact: On any busy intraday chart (pool at 40), FVG/OB/breaker targets, like the 'BEFVG' in the reference screenshot, almost never survive long enough to be chosen. When D flips, the new draw side has been emptied of its chart swing lows/highs, so the engine shows no target or a far, weak one. Using max(score, neutral pillars) keeps draw-side levels protected by their score, and keeps fresh or counter-side levels by their intrinsic quality. Old, far, weak pools are trimmed first.

## P1 dol-B-out-of-range-target: Levels beyond Max ATR Distance (proximity 0, PoT about 0%) can still be chosen as the DOL or stay stuck as it
- line 1950 | not yet verified
- impact: The trader sees 'Target: BSL / PoT: 0.4%' far off-screen. The tooltip of 'Max ATR Distance' says proximity scores 0 beyond it, and the spec says levels beyond the max distance are ejected. Zeroing the score beyond Max ATR Distance, measured with the same slow-ATR yardstick the registry re-enters with, makes such a level unpickable. An active target that drifts out of range is dropped through curOk. The level stays in the pool for re-entry and is still ejected at 1.5x as before. Quiet sessions are not affected because atrE = max(fast, slow ATR).

## P2 dol-G-htf-fvg-no-lockout: HTF FVGs are exempt from the origin lockout, so one that arrives with price sitting on it can be picked at once
- line 689 | not yet verified
- impact: This produces 'picking an imbalance price is sitting inside' and 'already being delivered' targets. The touch on the next bar fires 'swept' right after 'new target'. For HTF FVGs that arrive at a distance, the lockout costs only the first 3 bars: track() sets maxAway at 1 ATR or more on the next bar.

## P2 dol-E-hlmult-slows-maturation: The HTF timeframe factor (hlMult) also slows the 'stops accumulate' ramp, so PDH/PWH/HTF pools score as if they were brand new
- line 668 | not yet verified
- impact: The most important key liquidity is systematically 3 to 5 points behind ordinary chart swings. hlMult was meant to slow decay, not to keep HTF pools 'young'. Example: PDH at 2.5 ATR goes from 61.4 to 65.3 with the fix. Session pools and chart pools have hlMult 1, so they are unchanged.

## P2 dol-F-clean-label-after-live-sweep: After an intrabar sweep, the Clean label keeps saying 'Target: … PoT: 95.0%' on the wrong side of price until the bar closes
- line 2225 | not yet verified
- impact: The trader sees a target label on the wrong side of price with a misleading PoT. The fix shows 'Swept: BSL / Delivered ✓' until the confirmed bar promotes the next target. The live behaviour is otherwise unchanged.

## P2 pot-ledger-calibration: The DOL's PoT is never checked against how often this engine's DOLs actually get touched
- line 2067 | not yet verified
- impact: The Clean label's 'PoT: xx.x%', the Minimum-PoT filter and the alert all show a random-level probability. If the scoring has an edge (a ledger 'EDGE +pp'), the PoT understates how often the shown target is hit. If it has none, the PoT overstates it. After the patch, a 70% PoT means about 70% for DOLs on this chart. The shift is shrunk by 30 pseudo-observations. It is a no-op until the ledger has graded DOLs, and when accView is Off and useCal is false. Secondary targets stay on the raw model because the ledger learns only from DOLs. pPot records the raw model PoT, so there is no feedback loop.

## P2 pot-bump-floor-guard: f_bump floors an unbounded ratio before clamping it, which can overflow int and crash with a negative loop bound
- line 1268 | not yet verified
- impact: Removes a possible runtime crash of the whole indicator on symbols where ATR collapses. Normal behaviour is unchanged.

## P1 VIS-statusline-inputs: Status line prints all 76 input values over the chart; the reference shows only the name
- line 60 | not yet verified
- impact: With TradingView's default status-line setting (indicator arguments on), the top-left of the chart shows a very long string: "DOL Engine v2 Day Trading 240 60 15 3 5000 14 5 0.2 0.1 0.75 ... 2000-0000 0200-0500 ... America/New_York 0000-0100 ... Classic". It wraps over the candles and makes the indicator look cluttered and amateur next to the reference. The Data Window is flooded the same way.

## P2 VIS-light-theme-ink: On light chart backgrounds the neon glow, white core and tether almost disappear
- line 2219 | not yet verified
- impact: On a light-theme chart (TradingView's default for many accounts) the DOL target line and tether are barely visible: the trader sees a faint lime smear with a white stripe. With the patch, the dark-chart look is unchanged and light charts get a readable dark-green (or dark-red) line with a soft halo. The label (dark background, neon text) and the iFVG boxes already read fine on white.

## P2 VIS-swept-label: Clean label still reads 'PoT: 95.0%' after price has already traded through the target
- line 2225 | not yet verified
- impact: A trader watches price take the level, and the label still says there is a 95% chance price will touch it, until the bar closes. With the patch the second line reads "Swept ✓", which matches the 'DOL Target Swept' alert that fires at the same moment.

## P2 VIS-no-target-state: Clean style shows nothing when there is no DOL or the PoT filter hides it
- line 2305 | not yet verified
- impact: During those periods the chart has no zone, label or tether, only the bias table, and a trader cannot tell whether the indicator found no target or is broken. That is a plausible cause of the user's 'SO BAD' reaction. The patch adds one muted footer row, "Target | NONE" or "Target | FILTERED", which appears only when no zone is on the chart.

## P1 TE1: Chart legend shows ~76 raw input values next to the title on every chart
- line 60 | not yet verified
- impact: Before the trader sees any zone, the top-left of every chart has a run-on string of numbers and session codes that reaches across the pane. It looks amateur next to the reference.

## P1 TE2: 4H and daily charts in the default Day Trading mode show a red warning and mislabelled bias rows
- line 68 | not yet verified
- impact: On two very common charts (4H, daily stocks), the first thing the trader sees is a red error row and a table that misreports bias: 4H data is labelled 1H. Auto-fit uses W / D / 4H on 4H and 2H charts and M / W / D on daily, so every row is a real, non-repainting timeframe and the warning disappears. Charts at or below 1H (NQ 1m/5m, Gold 5m, EURUSD 15m, BTC 1H) keep D / 4H / 1H unchanged.

## P1 TE3: Levels beyond Max ATR Distance (proximity 0) can still become the target, labelled 'PoT: 0.0%'
- line 1975 | not yet verified
- impact: The trader sees the glowing target and tether 100+ points away, captioned with a near-zero probability. Spec: "levels beyond a maximum distance are ejected". With the patch, such pools stay in the pool for later re-entry but are never chosen as a NEW target. An active target that drifts out of range is still kept until it is ejected, so this adds no flicker.

## P1 TE4: The target switches away just before price reaches it (near-distance taper also hits the committed DOL)
- line 666 | not yet verified
- impact: This is the classic 'target jumped right before it got hit' complaint, and it erodes trust in every target. The taper now screens only NEW candidates (its documented purpose). The committed DOL keeps full proximity until it is swept.

## P1 TE5: Daily chart: every candle registers as a tier-0.80 'PDH/PDL' pool, so the targets are mislabelled and real HTF pools are evicted
- line 945 | not yet verified
- impact: On a daily stock chart the label reads 'Target: PDH' for a high printed weeks ago. Target choice is biased toward the last candle's high and low, and the real weekly and monthly pools are pushed out of the registry. Intraday charts are unchanged.

## P2 TE6: Clean label says 'HTF BSL' / 'STF SSL' (which timeframe?) and still shows 'PoT: 95.0%' after the target is swept live
- line 2225 | not yet verified
- impact: The trader cannot tell whether 'HTF BSL' is a daily or a 4H pool, and sees a 95% PoT on a level that was just swept. After the patch the label reads 'Target: D BSL', '4H SSL' or 'D BEFVG', and 'Swept ✓' when hit live. This matches the table rows.

## P2 TE7: Up to 8 iFVG bands stretched to the right edge clutter the Clean view (reference shows 2)
- line 198 | not yet verified
- impact: The chart looks busy and the single DOL zone no longer stands out. Three is enough for the nearest support and resistance flips and keeps the reference's sparse look. Users can still raise it.

## P2 TE8: 'New iFVG Formed' alert carries no direction or price
- line 2083 | not yet verified
- impact: Today the trader receives a stream of identical, unactionable pings. After the patch each alert reads e.g. 'DOL Engine ▸ new bullish iFVG 5081.2 – 5084.0 · GC1!'.

## P1 ux-statusline-inputs: 76 input values are printed in the chart legend. The reference legend shows only the script name. Unused inputs are never greyed out.
- line 60 | not yet verified
- impact: With defaults the trader sees a long string of numbers across the top-left of the chart, the opposite of the clean premium look in the reference. In the Inputs tab, the Custom timeframes, custom theme colours, HUD size, LVN parameters, session ranges and the Analytic prior look editable even when they have no effect. This is one of the 'looks cluttered or ugly' complaints.

## P2 ux-ghost-default: Ghost trail (a spec feature) is off by default. Turned on, it would be loud, would cover post-sweep candles, and would mark targets that are still live as 'INVALIDATED'.
- line 210 | not yet verified
- impact: By default the trader gets no trail, although the spec sells it as a core module. If the trader turns it on, they get up to 12 bright captions over price action and contradictory 'INVALIDATED' tags on zones that later become the active DOL. With this patch the default is on but faint: 5 ghosts, a 96%-transparent fill, a dotted border, a 40%-transparent caption on the zone's untraded side, and swept/ejected targets only. The Clean look stays close to the reference.

## P2 ux-alert-content: Alert texts lack the spec event names and target details, '@ {{close}}' looks like the target price, and the sweep alert fires for targets that were never announced.
- line 2090 | not yet verified
- impact: A phone notification now reads, for example, 'New DOL Target Active ▸ BEAR FVG ▲ 5122.8 (zone 5121.0 – 5124.5) · PoT 70.1% · score 62 · GC1! 5'. Before, it read 'new ... target active ... @ 5096.9' (the close). The other alerts carry the iFVG range and the swept level, and every alert() message begins with the spec name ('New DOL Target Active' / 'New iFVG Formed' / 'DOL Target Swept'). The trader is no longer alerted about a sweep of a target the filter hid and never announced.

## P2 ux-clean-swept-label: After an intrabar sweep, the Clean label still shows 'PoT: 95.0%' for a target that has already been hit.
- line 2225 | not yet verified
- impact: In the default Clean view the trader sees a 95% probability on a level that was already swept, and may act on it as if it were still the open target. The patch shows 'Swept ✓' in place of the PoT line until the bar closes.

## P2 ux-ifvg-overlap-merge: Overlapping same-direction iFVGs are drawn as stacked translucent boxes and use up the Max Active iFVGs slots.
- line 1609 | not yet verified
- impact: Fewer, cleaner iFVG zones: one box per price area rather than a layered stack, which is closer to the reference look. The Max Active iFVGs budget is spent on distinct zones.
