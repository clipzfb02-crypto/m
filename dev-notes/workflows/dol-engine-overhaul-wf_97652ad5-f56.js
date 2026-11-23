export const meta = {
  name: 'dol-engine-overhaul',
  description: 'Big overhaul of DOL Engine v2: 15-lens audit with exact patches, adversarial verification, synthesis, sequential integration, syntax gate, final review and fixes',
  phases: [
    { title: 'Audit', detail: '15 independent specialist lenses propose findings with exact patches' },
    { title: 'Verify', detail: 'adversarial verifier per lens' },
    { title: 'Plan', detail: 'dedupe, resolve conflicts, order the patch set' },
    { title: 'Integrate', detail: 'apply patches region by region, then syntax gate' },
    { title: 'Final review', detail: 'compile / runtime / regression / visual review of the integrated diff' },
    { title: 'Fix', detail: 'apply confirmed final-review fixes and re-check syntax' },
  ],
}

const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const FILE = '/home/user/m/indicators/dol_engine.pine'
const BASE = `${SP}/brief/baseline_v2.pine`
const PARSE = `${SP}/tools/pine_parse.sh`
const PRE = `First read ${SP}/brief/CONTEXT.md in full (the shared brief: project, constraints, docs, already-verified constructs, decision history). The code under review is ${BASE} (frozen copy; identical to ${FILE} right now). Line numbers below refer to it. Product spec: ${SP}/brief/tradeaxis_description.md. Reference look: ${SP}/brief/reference_look.png (open it with Read when visuals matter).`

const READONLY = `You are in a READ-ONLY review role: do not modify ${FILE} or the baseline. You may write scratch notes under ${SP}/runs/ if useful.`

const PATCH_RULES = `PATCH RULES. Every finding must carry exact patches.
- Each patch is {find, replace}. 'find' must be text copied EXACTLY from ${BASE}, including indentation, and must occur EXACTLY ONCE in that file. Include enough surrounding lines to make it unique. Check uniqueness with grep -c or python.
- 'replace' is the full replacement text.
- Patches must be minimal, compile-safe Pine v6, consistent with the brief's hard constraints, and must not depend on other findings' patches unless you say so in 'dependsOn'.
- New functions or globals must be placed BEFORE their first use (no forward references). Verify declaration order.
- Prefer high-impact, low-risk changes. Report at most 10 findings, ordered by severity.
- Severity: P0 = compile error, runtime error or wrong output that breaks the indicator; P1 = clearly wrong behaviour or a significant quality issue a trader would notice; P2 = polish or minor improvement.
- Do not report style nits. An empty list is a valid answer if nothing real is wrong.`

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'short unique id, prefixed with the lens key' },
          severity: { type: 'string', enum: ['P0', 'P1', 'P2'] },
          title: { type: 'string' },
          line: { type: 'integer' },
          evidence: { type: 'string', description: 'quoted code + doc quote (compile claims) or concrete scenario (behaviour claims)' },
          impact: { type: 'string', description: 'what the trader sees / what breaks' },
          patches: { type: 'array', items: { type: 'object', properties: { find: { type: 'string' }, replace: { type: 'string' } }, required: ['find', 'replace'] } },
          dependsOn: { type: 'array', items: { type: 'string' } },
        },
        required: ['id', 'severity', 'title', 'line', 'evidence', 'impact', 'patches'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['findings', 'summary'],
}

const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          real: { type: 'boolean' },
          worthIt: { type: 'boolean', description: 'true if the change is a net improvement at acceptable risk' },
          confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
          reasoning: { type: 'string' },
          finalPatches: { type: 'array', items: { type: 'object', properties: { find: { type: 'string' }, replace: { type: 'string' } }, required: ['find', 'replace'] }, description: 'patches to apply (corrected if needed; verified exact/unique against the baseline); empty if not real or not worth it' },
        },
        required: ['id', 'real', 'worthIt', 'confidence', 'reasoning', 'finalPatches'],
      },
    },
  },
  required: ['verdicts'],
}

const LENSES = [
  { key: 'cmpR1', title: 'Compile safety, lines 1-620', prompt: `LENS: COMPILE SAFETY for lines 1-620 (header, inputs, theme, constants, types, pure helpers, table cell helpers). Hunt for anything that would make TradingView refuse to compile:
- wrong signatures, argument types or qualifiers (input.* must get const defaults; simple vs series);
- switch/ternary type mismatches; UDT field defaults; names that clash with built-ins or reserved words;
- v6 rules: na bools, int->bool casting, int/float division;
- duplicate declarations; anything used before it is declared.
Use the reference docs; quote them.` },
  { key: 'cmpR2', title: 'Compile safety, lines 621-1080', prompt: `LENS: COMPILE SAFETY for lines 621-1080 (methods, f_structure / f_htfFvg / f_sessOpen / f_rangeTrack / f_sessTrack, series, the request.security calls and their tuples, the 1H volume feed, state declarations). Check especially:
- functions called inside request.security: what they are allowed to contain (var, history references, tuples of mixed types, bools in tuples);
- request.security_lower_tf return types and how they are used;
- methods with 'this' typed UDT params;
- every history reference on function-local variables;
- the tuple element types.
Quote the docs.` },
  { key: 'cmpR3', title: 'Compile safety, lines 1081-1500', prompt: `LENS: COMPILE SAFETY for lines 1081-1500 (state helpers: f_newLevel, f_findLiq, f_mergeAt / f_mergeLiq, f_anchorScan, f_recOpen / tfOpenBar and the hOpenB / sOpenB block, f_barAtTime, f_pushExt, f_stackSide, f_ghost, f_bump / f_surv / f_empPoT / f_potModel / f_potBase / f_reachD, f_invalidation, f_raceAdj, f_calMult, f_profile, f_pathVol, f_openTrial, f_step, f_book). Check:
- functions modifying globals (only array/UDT contents may be mutated inside functions; := on a global inside a function is an error);
- the declaration order of globals used inside functions;
- for...in loops over arrays of UDTs, map methods, tuple destructuring;
- int/float mixing; history references like time[mid] in functions.
Quote the docs.` },
  { key: 'cmpR4', title: 'Compile safety, lines 1501-2058', prompt: `LENS: COMPILE SAFETY for lines 1501-2058 (live sweep and the big confirmed-bar ENGINE block). Check:
- local declarations inside nested ifs and loops; := vs = on globals and locals; variables declared in one branch and used in another;
- tuple destructuring inside if blocks;
- history references inside loops (e.g. low[k], coilScore[obI + 1]) and their allowed forms;
- method calls; array element types; while loops;
- every function call against its declaration (argument counts and types), e.g. f_mergeLiq with 11 params and f_mergeAt with 10.
Quote the docs.` },
  { key: 'cmpR5', title: 'Compile safety, lines 2059-2448', prompt: `LENS: COMPILE SAFETY for lines 2059-2448 (live readouts, alert() and alertcondition(), the rendering block, the LVN block, the table panel, plots). Check:
- alertcondition requirements (const strings, global scope);
- label / line / box / table built-in signatures and argument types (size.* constants, text.align_*, xloc);
- table.new / table.clear / table.cell;
- plot with display.data_window;
- local variables reused across branches;
- the tooltip and string concatenation line continuations (wrapped lines must be indented, and NOT by a multiple of 4 spaces).
Quote the docs.` },
  { key: 'perf', title: 'Runtime limits and performance', prompt: `LENS: RUNTIME LIMITS AND PERFORMANCE. Read ${SP}/docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md and profiling_and_optimization.md first. Then estimate the worst-case per-bar cost and total cost on a 20k-bar 1-minute chart with default inputs (calcBars 5000, poolMax 40, registry 60, ledger up to H+1 trials, f_raceH up to 400 terms, f_anchorScan, f_stackSide, f_profile, loops over ifvgs, fvgTrk and obTrk).
Find anything that could trigger:
- 'Calculation takes too long' or loop-time errors;
- runtime errors: index out of range, history beyond max_bars_back = 500 (check EVERY [] history reference and its maximum value), drawing limits (500 boxes / lines / labels, 500 bars into the future, 10000 bars into the past);
- request limits.
Propose concrete, behaviour-preserving optimisations with the biggest wins, e.g. gating work to inCalc or the last bars, caching, avoiding per-bar allocations such as array.from in f_book, early exits, and cheaper math.` },
  { key: 'repaint', title: 'Repainting and MTF alignment', prompt: `LENS: REPAINTING AND MTF DATA ALIGNMENT. Read the docs on other timeframes and repainting under ${SP}/docsrc/jabez4jc_pinescriptv6/concepts/. Verify:
- every request.security call (expression offsets [1], lookahead_on, f_tfSafe);
- the HTF FVG time[2] anchoring;
- tfOpenBar mapping and f_barAtTime;
- session and key-level trackers (f_rangeTrack with timeframe.change, f_sessTrack);
- killzone and session time() calls with the timezone;
- request.security_lower_tf for the 1H profile;
- that all structural logic is gated on barstate.isconfirmed;
- what happens on realtime bars versus history (e.g. f_recOpen and hOpenB / sOpenB on unconfirmed bars, var state mutated outside isconfirmed).
Report anything that repaints, leaks future data, or misaligns the bias table versus what that timeframe really shows.` },
  { key: 'ictLiq', title: 'ICT liquidity model', prompt: `LENS: ICT LIQUIDITY MODEL (as an expert ICT/SMC trader and Pine developer). Evaluate how buy-side / sell-side liquidity is found, merged and swept:
- chart pivots with pivLen 5;
- equal highs/lows tolerance; the stacked-pool outermost logic;
- PDH / PDL / PWH / PWL; Asia, London and NY sessions;
- the external registry and re-entry;
- the strict sweep rule; the liquidity zone depth (0.2 ATR beyond the swing).
Would a professional ICT trader agree with the pools and the targets? Find wrong or missing behaviour: for example, missing obvious draws (relative equal highs, untouched session highs, the previous-day high not shown), levels that should already be invalid, wrong side assignment, levels too close to be meaningful, and pools that never leave the pool. Propose concrete code patches.` },
  { key: 'ictPD', title: 'ICT PD arrays (FVG / iFVG / OB / breaker)', prompt: `LENS: ICT PD ARRAYS. Evaluate:
- FVG detection and quality gating;
- CE / partial-fill cropping; delivery rules;
- HTF FVGs;
- iFVG inversion (close through the gap); upkeep (body closes inside, failure); how the boxes look;
- order block detection (the last opposite candle of the leg after a BOS); mitigation; quality;
- breaker creation only from blocks that took liquidity.
Compare with standard ICT definitions and with the spec. Find incorrect detections, missed obvious arrays, wrong directions (e.g. which side of price a bearish FVG target sits on and how it is labelled BEFVG / BUFVG), and stale arrays that keep being targeted. Propose concrete patches.` },
  { key: 'bias', title: 'Market structure and bias table', prompt: `LENS: MARKET STRUCTURE AND BIAS TABLE. Study f_structure (swing bias with protected levels, internal bias with body closes), its [1]-shifted outputs, and how the Clean table shows bias (swing bias, internal bias as fallback).
The spec says the bias table removes lagging Neutral states by requiring true candle-body breaks of established structural nodes.
Check:
- correctness of BOS / CHoCH on each timeframe;
- whether the bias can be stuck NEUTRAL for long (e.g. at chart start or on the W/D timeframes in Swing mode);
- whether a bias flips on wicks (it should not);
- whether biasLen 3 is a sensible default;
- whether D / 4H / 1H on a 5m chart show what a trader sees when opening those timeframes;
- the dealing range premium/discount.
Propose patches that make the table trustworthy.` },
  { key: 'select', title: 'DOL scoring and target selection quality', prompt: `LENS: DOL SCORING AND TARGET SELECTION QUALITY (the core value of the product). Study evaluate(), the five pillars and weights, the mult factors (origin lockout, inner pools, counter-draw, killzone, VP path, calibration), the trimming, the two-stage selection with hysteresis and the 2-bar challenger, the draw vector D, and minScore.
Think through realistic sequences, such as:
- a trend day;
- a range day;
- after a sweep;
- a fresh FVG right next to price;
- equal highs 1 ATR above;
- PDH 6 ATR away.
Find the pathologies a trader would hate:
- targets that are too close (already being delivered) or absurdly far;
- picking an imbalance price is sitting inside;
- flicker; stuck targets; no target at all for long periods (minScore 35 too strict?);
- the label showing a target on the wrong side of price;
- the target sitting behind a closer, more obvious pool on the same side.
Propose concrete scoring and selection patches with reasoning. Keep the patches surgical.` },
  { key: 'pot', title: 'Probability of Touch and accuracy stats', prompt: `LENS: PROBABILITY OF TOUCH AND STATISTICS. Verify the maths and numerics:
- f_erfc, f_pot (reflection with drift), f_expPhi overflow guards;
- the empirical surface (f_bump / f_surv / f_empPoT with bStep, nMin, regimes); the nEff blend;
- f_race / f_raceH; f_raceAdj; the ledger stats (Wilson, cluster variance, calibration).
Check that the PoT a trader sees is sensible: not stuck at 95% or 0%, consistent with distance, and with no NaN shown as 'NaN%'. You may write small Python checks under ${SP}/runs/pot/ to test the formulas numerically. Propose patches only for real defects or clear improvements.` },
  { key: 'visual', title: 'Visual fidelity and premium polish', prompt: `LENS: VISUAL FIDELITY AND PREMIUM POLISH (Clean style is the default). Open ${SP}/brief/reference_look.png and compare in detail with the rendering code: the active DOL zone, the glow lines, the tether, the label (text, size, background, position), the iFVG boxes, the bias table (colours, sizes, header, borders, position), the Classic theme colours.
Then think about how it renders on real charts at different zoom levels and instruments:
- zone thickness when the zone is tiny: a BSL zone is only 0.2 ATR deep, so make sure the target stays visible like in the screenshot;
- label overlap with the price scale or other labels;
- drawings recreated every tick (flicker or performance);
- objects left over after the target changes;
- light-theme charts;
- what appears when there is no target.
Propose concrete patches that make it look premium and match the reference.` },
  { key: 'trader', title: "Trader's-eye holistic review", prompt: `LENS: TRADER'S EYE (holistic). Imagine loading the indicator with DEFAULT settings on:
- NQ 1-minute and 5-minute;
- Gold futures 5-minute;
- EURUSD 15-minute;
- BTCUSD 1-hour;
- a daily stock chart.
For each, walk through the code to predict exactly what appears: table rows and values, whether a target exists, its type and label, PoT values, iFVG boxes, warnings, alerts.
List the TOP problems a demanding trader would complain about ("this is bad"), for example:
- nothing shows for the first N bars;
- the target is miles away; the target flips every few bars;
- PoT always 95%;
- the table says NEUTRAL;
- the timeframe warning on common charts (e.g. a 4H chart in Day Trading mode);
- clutter; unclear labels; bad defaults.
Propose concrete patches (defaults, logic or display) for the highest-impact problems.` },
  { key: 'spec', title: 'Feature parity with the spec, inputs and alerts', prompt: `LENS: FEATURE PARITY AND UX. Compare the indicator with every feature in ${SP}/brief/tradeaxis_description.md:
- the scoring pillars;
- modes;
- iFVG behaviour;
- LVN from 1H volume;
- the ghost trail (currently off by default — should it be on but subtle?);
- the bias table;
- PoT with its minimum filter;
- alerts named exactly "New DOL Target Active", "New iFVG Formed", "DOL Target Swept";
- non-repainting.
Also review the inputs: names, groups, tooltips, sensible defaults, anything confusing or useless, and the alert message contents.
Find missing or weaker-than-spec features and propose concrete patches. Do not add the other product's branding.` },
]

const auditPrompt = (L) => `${PRE}
${READONLY}

${L.prompt}

${PATCH_RULES}`

const verifyPrompt = (L, rep) => `${PRE}
${READONLY}

You are an ADVERSARIAL VERIFIER for the lens "${L.title}". For EACH finding below:
1. Re-read the cited code in ${BASE}.
2. Try hard to REFUTE the finding. Use the docs for compile claims; walk through a concrete scenario for behaviour claims.
3. Decide 'real' (the defect or improvement is genuine) and 'worthIt' (applying it is a net improvement at acceptable risk for a production indicator).
4. Check every patch mechanically:
   - the 'find' text occurs EXACTLY ONCE in ${BASE} (check with python or grep -F -c);
   - the replacement is valid Pine v6 (types, qualifiers, declaration order, no forward references, names exist);
   - it does not break other code that uses the changed names (grep all usages);
   - it respects the brief's hard constraints.
5. If a patch is fixable, return corrected 'finalPatches'. If it is not real or not worth it, return finalPatches = [].
Be strict: wrong compile claims and risky rewrites have appeared before.

FINDINGS:
${JSON.stringify(rep.findings, null, 1)}`

phase('Audit')
const lensResults = await pipeline(
  LENSES,
  (L) => agent(auditPrompt(L), { label: `audit:${L.key}`, phase: 'Audit', schema: FINDINGS }),
  (rep, L) => {
    if (!rep || !rep.findings || rep.findings.length === 0) return { key: L.key, title: L.title, findings: [], verdicts: [], summary: rep ? rep.summary : 'no result' }
    return agent(verifyPrompt(L, rep), { label: `verify:${L.key}`, phase: 'Verify', schema: VERDICTS })
      .then(v => ({ key: L.key, title: L.title, findings: rep.findings, verdicts: v ? v.verdicts : [], summary: rep.summary }))
  },
)

const confirmed = []
const lensSummaries = []
for (const r of lensResults.filter(Boolean)) {
  lensSummaries.push({ lens: r.key, summary: r.summary, found: r.findings.length })
  for (const f of r.findings) {
    const v = (r.verdicts || []).find(x => x.id === f.id)
    if (v && v.real && v.worthIt && v.finalPatches && v.finalPatches.length) {
      confirmed.push({ id: f.id, lens: r.key, severity: f.severity, title: f.title, line: f.line, impact: f.impact, verifier: v.reasoning.slice(0, 600), confidence: v.confidence, patches: v.finalPatches, dependsOn: f.dependsOn || [] })
    }
  }
}
log(`Audit+verify done: ${lensResults.filter(Boolean).reduce((s, r) => s + r.findings.length, 0)} findings, ${confirmed.length} confirmed with patches`)
if (confirmed.length === 0) return { confirmed, lensSummaries, note: 'nothing to apply' }

phase('Plan')
const PLAN = {
  type: 'object',
  properties: {
    regions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          region: { type: 'string', enum: ['R1', 'R2', 'R3', 'R4', 'R5'] },
          items: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                title: { type: 'string' },
                severity: { type: 'string' },
                patches: { type: 'array', items: { type: 'object', properties: { find: { type: 'string' }, replace: { type: 'string' } }, required: ['find', 'replace'] } },
                notes: { type: 'string' },
              },
              required: ['id', 'title', 'severity', 'patches', 'notes'],
            },
          },
        },
        required: ['region', 'items'],
      },
    },
    dropped: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, reason: { type: 'string' } }, required: ['id', 'reason'] } },
    crossRegionNotes: { type: 'string' },
  },
  required: ['regions', 'dropped', 'crossRegionNotes'],
}
const plan = await agent(`${PRE}
${READONLY}

You are the LEAD ENGINEER who merges the verified findings of 15 specialist reviewers into ONE coherent, conflict-free patch set for ${BASE}.

Your job:
1. Deduplicate findings that fix the same thing. Keep the best patch.
2. Resolve conflicts. Where two patches touch overlapping text, merge them into one combined patch, or drop the weaker one. Merged patches must still use 'find' text copied exactly from ${BASE}, occurring exactly once.
3. Drop anything risky, speculative, low-value, or that contradicts the brief's hard constraints and decision history. Record each drop with its reason.
4. Check cross-region dependencies, e.g. a new input in R1 used in R4, or a new helper in R3 used in R5. Make sure every new name is declared before use and that every dependency is included.
5. Assign each kept item to the region where its patches live (if an item spans regions, split it into per-region items with the same id plus a suffix):
   - R1 = lines 1-620;
   - R2 = 621-1080;
   - R3 = 1081-1500;
   - R4 = 1501-2058;
   - R5 = 2059-2448.
6. Order the items within each region so that later patches still find their text after earlier ones are applied. Prefer non-overlapping finds.
7. Verify every final 'find' string mechanically with python: it must occur exactly once in ${BASE}.

Priorities: all P0, then the highest-impact P1s; P2 only when cheap and safe. Prefer quality over quantity: a smaller set of correct changes beats a large risky one.

VERIFIED FINDINGS (JSON):
${JSON.stringify(confirmed)}`, { label: 'plan:merge', phase: 'Plan', schema: PLAN })

if (!plan) return { confirmed, lensSummaries, note: 'plan agent failed' }

phase('Integrate')
const INTEG = {
  type: 'object',
  properties: {
    applied: { type: 'array', items: { type: 'string' } },
    skipped: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, reason: { type: 'string' } }, required: ['id', 'reason'] } },
    notes: { type: 'string' },
  },
  required: ['applied', 'skipped', 'notes'],
}
const integResults = []
for (const reg of ['R5', 'R4', 'R3', 'R2', 'R1']) {
  const items = (plan.regions.find(r => r.region === reg) || { items: [] }).items
  if (!items.length) continue
  const res = await agent(`${PRE}

You are an INTEGRATOR for region ${reg}. Apply the patch items below to the LIVE file ${FILE}, in order, using the Edit tool. You are the only agent editing the file right now.

For each patch:
1. Confirm its 'find' text occurs exactly once in the CURRENT ${FILE}. Earlier items may have changed nearby text; if so, adapt the find minimally while keeping the intended change.
2. Apply it.
3. Re-read the edited area and check that indentation, continuation lines and declaration order are correct.

If a patch can no longer be applied safely, skip it and say why. Do not make any other changes and do not reformat unrelated code. Do NOT run the syntax checker (a later step does that). Cross-region notes from the planner: ${plan.crossRegionNotes}

ITEMS (JSON):
${JSON.stringify(items)}`, { label: `integrate:${reg}`, phase: 'Integrate', schema: INTEG })
  integResults.push({ region: reg, result: res })
}

const SYNTAX = {
  type: 'object',
  properties: {
    clean: { type: 'boolean' },
    fixes: { type: 'array', items: { type: 'string' } },
    report: { type: 'string' },
  },
  required: ['clean', 'fixes', 'report'],
}
const syntax1 = await agent(`${PRE}

You are the SYNTAX GATE.
1. Run: bash ${PARSE} ${FILE} ${BASE}. It parses only the changed top-level statements; this can take up to about 15 minutes, so give the command a long timeout, e.g. 1500000 ms.
2. For every FAIL line, inspect the corresponding code in ${FILE}, fix the syntax with minimal Edit changes that keep the intended behaviour, and re-run the parser on the file again (with the baseline argument) until there are no FAIL lines.
3. Also do a quick manual review of 'git -C /home/user/m diff -- indicators/dol_engine.pine'. Look for obvious problems a parser would not catch: duplicated declarations, a name used before it is declared, a removed variable that is still used. Fix those too.
Report what you fixed.`, { label: 'integrate:syntax-gate', phase: 'Integrate', schema: SYNTAX })

phase('Final review')
const FR = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          severity: { type: 'string', enum: ['P0', 'P1', 'P2'] },
          title: { type: 'string' },
          evidence: { type: 'string' },
          fix: { type: 'string', description: 'exact Edit instructions: find text in the CURRENT live file (exactly once) and its replacement' },
        },
        required: ['id', 'severity', 'title', 'evidence', 'fix'],
      },
    },
    checkedOk: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'checkedOk'],
}
const DIFF = `Get the integrated change with: git -C /home/user/m diff -- indicators/dol_engine.pine (the baseline is the last commit). The current live file is ${FILE}.`
const FINAL = [
  { key: 'cmpA', prompt: `FINAL COMPILE REVIEW, first half: every changed or added line in the diff that lies in lines 1 to 1300 of the CURRENT file. ${DIFF}
Check each changed construct against the docs (signatures, qualifiers, types, declaration order, forward references, v6 rules, := on globals inside functions). Also check that every call site of a changed function matches its new signature anywhere in the file. Report only real compile errors, each with a doc quote and an exact fix.` },
  { key: 'cmpB', prompt: `FINAL COMPILE REVIEW, second half: every changed or added line in the diff that lies after line 1300 of the CURRENT file. ${DIFF}
Check each changed construct against the docs: signatures, qualifiers, types, declaration order, local scoping in if/for blocks, alertcondition const args, drawing and table functions, and line-continuation indentation. Report only real compile errors, each with a doc quote and an exact fix.` },
  { key: 'rt', prompt: `FINAL RUNTIME AND REGRESSION REVIEW of the integrated diff. ${DIFF}
For every change, check:
- runtime errors: index out of range, history references beyond 500, loop time, drawing limits, na propagation into int() or array indices;
- logic regressions against the decision history in the brief (strict sweeps, draw-first selection, the non-repainting rules);
- whether the change does what its intent says.
Report only real problems with concrete scenarios and exact fixes.` },
  { key: 'vis', prompt: `FINAL VISUAL AND TRADER REVIEW. Open ${SP}/brief/reference_look.png. ${DIFF}
Read the current rendering code (DOL zone, label, tether, iFVG boxes, Clean table) and predict what a trader sees with default settings on Gold futures 5-minute. Report remaining mismatches with the reference, and anything the changes made worse (clutter, unreadable text, missing target). Give exact fixes. Do not re-propose changes that were deliberately decided in the brief.` },
]
const finalResults = await pipeline(
  FINAL,
  (F) => agent(`${PRE}
READ-ONLY review of the INTEGRATED file (do not edit). ${F.prompt}`, { label: `final:${F.key}`, phase: 'Final review', schema: FR }),
  (rep, F) => {
    if (!rep || !rep.findings || rep.findings.length === 0) return { key: F.key, findings: [], verdicts: [], checkedOk: rep ? rep.checkedOk : [] }
    return agent(`${PRE}
READ-ONLY. You are an ADVERSARIAL VERIFIER of final-review findings on the integrated file ${FILE}. ${DIFF}
For each finding, re-check it against the current code and the docs, and try to refute it. Return verdicts. 'finalPatches' must use find text copied exactly from the CURRENT ${FILE} that occurs exactly once there. Return empty patches if the finding is not real or not worth it.

FINDINGS:
${JSON.stringify(rep.findings, null, 1)}`, { label: `final-verify:${F.key}`, phase: 'Final review', schema: VERDICTS })
      .then(v => ({ key: F.key, findings: rep.findings, verdicts: v ? v.verdicts : [], checkedOk: rep.checkedOk }))
  },
)

const finalConfirmed = []
for (const r of finalResults.filter(Boolean)) for (const f of r.findings) {
  const v = (r.verdicts || []).find(x => x.id === f.id)
  if (v && v.real && v.worthIt && v.finalPatches && v.finalPatches.length) finalConfirmed.push({ id: f.id, review: r.key, severity: f.severity, title: f.title, patches: v.finalPatches, reasoning: v.reasoning.slice(0, 500) })
}
log(`Final review: ${finalConfirmed.length} confirmed issues`)

let fixRes = null
if (finalConfirmed.length) {
  phase('Fix')
  fixRes = await agent(`${PRE}

You are the FINAL FIXER. Apply these verified fixes to ${FILE} with the Edit tool. Each 'find' must occur exactly once in the current file; adapt minimally if needed. Then run: bash ${PARSE} ${FILE} ${BASE}. This can take up to about 15 minutes, so use a long timeout. Fix any FAIL lines until it is clean. Report what you applied.

FIXES (JSON):
${JSON.stringify(finalConfirmed)}`, { label: 'fix:final', phase: 'Fix', schema: SYNTAX })
}

return {
  lensSummaries,
  confirmedCount: confirmed.length,
  plan: { regions: plan.regions.map(r => ({ region: r.region, items: r.items.map(i => ({ id: i.id, title: i.title, severity: i.severity })) })), dropped: plan.dropped, crossRegionNotes: plan.crossRegionNotes },
  integration: integResults.map(x => ({ region: x.region, applied: x.result ? x.result.applied : null, skipped: x.result ? x.result.skipped : null, notes: x.result ? x.result.notes : 'failed' })),
  syntaxGate: syntax1,
  finalReview: finalResults.filter(Boolean).map(r => ({ key: r.key, found: r.findings.length, checkedOk: (r.checkedOk || []).slice(0, 12) })),
  finalConfirmed: finalConfirmed.map(f => ({ id: f.id, review: f.review, severity: f.severity, title: f.title })),
  fix: fixRes,
}
