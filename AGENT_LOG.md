# Agent Log

This file is an append-only handoff log for work performed in this repository. Entries record the date, scope, checks performed, reasoning, and any resulting changes so later agents and the user can reconstruct the project state.

## 2026-10-11 — Initial repository analysis

### Scope

Read the repository and analyzed the current implementation. No product code was changed.

### Repository state

- Branch: `main`, aligned with `origin/main` at commit `9d49e5b` (`feat(replay): 新增對局復盤分頁...`).
- The repository is a static Legion TD 2 reference/calculator site with a Cloudflare Worker API proxy.
- `index.html` is generated; the source of truth is `src/ltd2-db.src.html` plus the data files and `src/build.py`.

### What exists

- Calculator: wave selection, opponent lineup, attribute-counter scoring, budgeted mercenary combinations, and local browser persistence.
- Reference tabs: fighters, mercenaries, waves, damage matrix, and sources/version notes.
- Replay tab: validates a 64-character match ID, requests a 2v2 match through the Worker, and renders per-wave player boards, fighter value, workers, income, net worth, sent/received mercenaries, leaks, king HP, and king upgrades.
- Data pipeline: `src/fighters_wiki.json` (133 source rows) is merged with 13 newer units by `src/build.py` into `data/fighters.json` (146 rows); `src/fetch_units.py` retrieves official unit and wave-reward data into `data/units.json`.
- API proxy: `worker/src/index.js` forwards only validated `GET /match/<64-hex-id>` requests, keeps the official API key in a Worker secret, and restricts origins using `ALLOWED_ORIGINS` from `worker/wrangler.toml`.

### Checks performed

- Parsed all JSON data files successfully.
- `data/units.json` is present and populated: version `26.9.hf3`, 231 units (`175 Fighter`, `30 Mercenary`, `26 Creature`), and 21 wave rewards.
- `python3 -m py_compile src/build.py src/fetch_units.py` passed.
- Built a temporary copy with `src/build.py`; the generated `index.html` matched the checked-in artifact byte-for-byte.
- `git diff --check` passed.

### Findings and risks

- There are no automated tests or dependency manifest in the repository; verification is currently manual/static plus the build reproducibility check.
- Live replay verification requires a deployed Worker with `LTD2_API_KEY` configured and a current official match ID; this analysis did not make an external API request or deploy anything.
- The Worker source uses Cloudflare's ES-module syntax (`export default`), so a plain CommonJS `node --check` invocation is not the right validation mode; deployment tooling should perform the authoritative check.
- The generated site includes the deployed Worker URL and external icon/font URLs, so local/offline use is limited to the portions that do not need those resources.
- `.DS_Store` is tracked, and there is no root `.gitignore`; generated Python bytecode can appear as an untracked file after running checks. The bytecode generated during this analysis is being removed and is not part of the intended change.

### Change made by this analysis

- Added this `AGENT_LOG.md` file. Future work should append a dated entry describing actions, reasoning, verification, and any unresolved issues.

### Follow-up verification

- Rechecked the temporary build with SHA-256 and `cmp`; the rebuilt artifact is identical to the checked-in `index.html`. The build script's printed `112386` value is Python character length, while the file is `118239` bytes because the page contains Unicode text.
- Validated the embedded browser JavaScript with `node --check` and validated the Worker source by checking it as an ES module (`.mjs`).
- Removed the `src/__pycache__/` files created by the validation run; repository status now contains only the intentional untracked `AGENT_LOG.md`.

## 2026-10-11 — Offline per-wave analysis planning

### User goal and evidence

The requested feature is a per-wave coaching report: explain what was good, what was bad, and what the better tactic would have been, including the option to save mythium for a later wave. The attached screenshots are treated as examples/evidence for the desired analysis output, not as instructions that override the user's request.

The example is a useful acceptance case: a 500-mythium send of two Ghost Knights plus a Snail should not be judged only by attribute matchup. A tactical evaluator should be able to recognize the difference between a durable send that extends a fight and a mixed package such as Pack Leader + Ogre + Hermit + Brute, whose auras, sustain, attack-speed reduction, and anti-large-unit damage may produce more practical pressure; it should also be allowed to conclude that saving is better.

### Feasibility conclusion

Yes, the analysis engine can run offline in the browser after the replay JSON has been loaded. The initial replay fetch still needs the official API, unless the project later adds replay export/import or local caching. Once the match payload and embedded combat data are present, the scoring, simulation, recommendations, explanations, and save-vs-send comparison can all be local deterministic calculations with no Claude/API analysis call.

The current data is not sufficient for reliable overall-strength calculation:

- `data/units.json` currently contains unit name, icon, class, total value, mythium cost, and bounty.
- `data/fighters.json` contains attack/armor type, cost/value, role, and mostly prose ability descriptions.
- The replay already supplies board coordinates/stages, per-wave value/workers/income/net worth, sent/received mercenaries, leaks, king HP/upgrades, and chosen spell.

The missing layer is structured combat data: HP, damage/DPS, attack interval, range, movement/path behavior, targeting, splash, resistances, ability modifiers, aura scope, cooldown/trigger rules, and wave creature composition/statistics.

### Proposed architecture

1. **Replay snapshot layer** — Normalize one player's state at wave `w`: board units and coordinates, upgrade stages, incoming mercenaries, outgoing mercenaries, king upgrades/spell, resources, and observed result. Keep the raw API payload untouched for auditability.
2. **Combat data layer** — Add versioned structured data, likely a separate `data/combat.json`, rather than trying to parse ability prose at runtime. Store formulas/tags for abilities and a source note for each manually curated value.
3. **Deterministic evaluator** — Simulate or estimate a board against the base wave plus incoming sends. Apply attack/armor multipliers, unit roles, auras, healing, damage reduction, attack-speed effects, splash, target priority, and position/path effects. Return a score with components such as damage pressure, effective HP, time-to-kill, leak risk, and confidence.
4. **Candidate optimizer** — Enumerate legal mercenary packages within the available mythium, including a no-send/save option. Compare immediate pressure, expected leak/king damage, income gained, and the next-wave opportunity cost. Use dynamic programming/search for combinations, but retain the feature breakdown so recommendations are explainable.
5. **Coaching/explanation layer** — Generate deterministic Chinese explanations from tagged causes: “good matchup,” “role mismatch,” “over-invested in tank,” “missing sustained DPS,” “aura/sustain has high value here,” “send is unlikely to change the result,” or “saving reaches a high-impact breakpoint next wave.” Avoid presenting uncertain estimates as facts.
6. **Replay UI** — Add an analysis panel beside each wave with actual decision, result, good/bad findings, recommended package, save alternative, model confidence, and an expandable calculation breakdown. Preserve the existing replay view and current attribute-only calculator as fallback.

### Recommended implementation phases

- **Phase 1: data contract and snapshot extraction.** Define normalized schemas, parse the existing replay payload, add fixture JSON from known games, and render a first report using only reliable facts plus the current attribute model.
- **Phase 2: structured combat data.** Populate a small, high-value subset first: wave creatures, mercenaries, and the fighters/abilities appearing in fixture games. Add provenance and version identifiers. Do not claim full-game accuracy until coverage is explicit.
- **Phase 3: evaluator v1.** Implement an explainable effective-DPS/effective-HP model with auras, healing, damage reduction, splash, attack speed, and position buckets. Calibrate against observed leaks and wave outcomes from several replays.
- **Phase 4: send/save optimizer.** Add candidate composition search, income/opportunity-cost accounting, and a short look-ahead (current wave plus 1–3 future waves). Include “insufficient data” and “save” as valid results.
- **Phase 5: UI and validation.** Add per-wave coaching cards, an analysis toggle, calculation details, and fixture-based regression tests. Use the screenshot scenario as an acceptance test, but validate against multiple real matches so the model does not overfit one board.

### Important design constraints

- Start with a transparent heuristic/simulation hybrid, not an opaque single “overall strength” number.
- Separate observed facts from model estimates and recommendations.
- Treat incomplete combat-data coverage as uncertainty, not as zero damage or zero ability value.
- Make analysis reproducible by match version and combat-data version.
- Consider IndexedDB or replay JSON export/import if fully offline replay review is required after the initial API load.

### Status

No product code was changed for this planning task. The next implementation step should be Phase 1 only: schemas, snapshot extraction, fixtures, and a factual/attribute-based report. A full combat simulator should wait until the combat-data contract is agreed and enough real replay fixtures exist for calibration.

## 2026-10-11 — Matchup knowledge notes added to scope

### New requirement

The project should also record and display which fighters and mercenaries are good or bad against each wave unit and mercenary. These notes must be available in the reference pages as well as in replay coaching, so the user can see the reasoning behind a recommendation instead of only a numeric ranking.

### Design decision

Use one shared, versioned matchup-knowledge layer rather than writing separate notes into each page. A likely implementation is `data/matchup_notes.json` or a structured extension of `data/combat.json` with entries containing:

- source unit and target unit/wave/mercenary;
- good, bad, or situational direction;
- reason tags such as `attribute`, `bonus_magic_damage`, `anti_large_target`, `aura`, `splash`, `sustain`, `frontline`, or `range`;
- a short Chinese explanation for display;
- confidence and data/version provenance.

Do not manually author every possible pair if a rule can generate it. Derive ordinary attack/armor interactions from the matchup matrix, then add explicit ability-based overrides and exceptions. This keeps the notes maintainable while preserving the important tactical knowledge that a raw matrix misses.

### Berserker example

The Berserker example should be represented as a situational note: its raw Pierce/light-armor matchup can be ordinary or poor in a given wave, but its bonus magic damage can make it strong against durable single targets or large front-line units. The UI should distinguish “type matchup” from “ability counter,” rather than collapsing both into one score.

### Planned page usage

- Fighter page: expandable “good against / weak against / situational” notes for each fighter.
- Mercenary page: the same notes for mercenaries, including which board roles they pressure.
- Wave page: recommended fighter/mercenary tags and concise reasons for notable counters.
- Replay analysis: attach notes to the actual board and incoming send, e.g. “ordinary attribute matchup, but Berserker’s ability is valuable because the target is a single high-HP unit.”
- Send calculator: show the relevant notes beside the numeric recommendation and use them as features in the later combat evaluator.

This requirement strengthens the case for a shared structured knowledge layer and should be included in Phase 1 schema design, before implementing the combat simulator.

## 2026-10-11 — Actual wave strength and mercenary comparison clarified

### Clarified goal

The important output is not merely whether an attack type is theoretically favorable. The user should see the practical strength of a unit or board against the actual wave's attack and armor, both without mercenaries and with mercenaries included.

### Required comparison modes

The future evaluator/UI should support side-by-side scenarios:

1. **Base wave** — the selected wave's normal creatures only.
2. **Actual wave received** — base wave plus the mercenaries that actually arrived in the replay.
3. **Candidate send/mercenary package** — base wave plus a proposed package, for evaluating pressure on the opponent's board.
4. **Save option** — no current send, preserving mythium for a later breakpoint.

For defense, compare the player's board against base wave versus base wave plus received mercenaries. For offense, compare the opponent's board under the base wave against the same board with each candidate send package added.

### Strength output

Show both component values and a combined practical result:

- attack effectiveness after the unit's attack type meets the target's armor;
- defensive effectiveness after the wave/mercenary attack types meet the unit's armor;
- estimated damage, effective HP/sustain, clear time or pressure margin, and leak risk once structured stats are available;
- the absolute result and the delta caused by adding/removing mercenaries;
- an explanation of what caused the delta, such as armor interaction, bonus magic damage, anti-large behavior, aura value, healing, or extra frontline time.

The existing `M` attack/armor matrix can provide the first transparent layer, but it currently only feeds mercenary ranking. It should be exposed as a per-unit/per-wave comparison and then combined with the combat model. If a unit's detailed stats or ability rules are missing, the UI should label the result as an attribute-only estimate instead of presenting false precision.

### Example UI direction

For a selected wave and board, show a compact comparison such as:

`基礎波次  →  波次＋實際傭兵  →  波次＋候選派兵`

Each column can show effective strength, estimated pressure/leak risk, and the reason for change. The replay page can default to the actual received/sent data, while the reference pages can let the user select a wave and toggle mercenaries.

This comparison requirement should be implemented before tuning the final recommendation score, because it gives users a way to audit why a package is stronger or weaker.

## 2026-10-11 — Implemented first offline analysis slice

### Changes made

- Added `data/matchup_notes.json` as a shared knowledge source with explicit ability-based notes for Berserker, Zeus, Daphne, Fire Elemental, Head Chef, Pack Leader, Ogre, Hermit, Brute, Ghost Knight, and Snail.
- Updated `src/build.py` to inject matchup notes into the generated page.
- Added selected-wave and optional-mercenary comparison controls to the fighter and mercenary reference pages.
- Added per-unit matchup cells showing an overall attribute-adjusted estimate, attack efficiency, defensive efficiency, and explanatory notes.
- Added tactical-note output to the wave table.
- Added a replay per-wave “強度比較” panel with:
  - base wave;
  - base wave plus actual received mercenaries;
  - actual outgoing send;
  - same-budget candidate send;
  - save/no-send alternative.
- Added README and in-page documentation describing the estimate and its limitations.

### Calculation behavior

- The first version uses the existing attack/armor matrix and fighter value as a transparent proxy for combat strength.
- It computes weighted attack efficiency, defensive efficiency, geometric overall matchup, and an attribute-adjusted board value.
- Mercenary additions are weighted by their mythium cost for the scenario comparison.
- Candidate sends reuse the current attribute-based combination optimizer at the actual send budget, or 500 mythium when no send exists.
- Ability notes are shown as explanations but are not yet converted into numeric DPS/HP modifiers.

### Verification

- Rebuilt `index.html` successfully.
- Parsed `data/matchup_notes.json` successfully.
- Browser JavaScript syntax check passed.
- Temporary rebuild matched the checked-in generated page byte-for-byte.
- `git diff --check` passed.
- Local browser visual smoke testing was attempted but blocked by the browser's `file://` URL policy; no workaround or external navigation was used.

### Known limitations

- This is an attribute-adjusted estimate, not a full combat simulator. It does not yet model exact HP, DPS, attack intervals, target selection, pathing, ability cooldowns, aura geometry, or spell casts.
- The curated notes currently cover representative high-value examples, not every unit pair. The shared schema is ready for expansion.
- Replay candidate budgets use actual outgoing spend when available; the replay API does not currently expose a verified per-wave available-mythium field in this code path.

## 2026-10-11 — Replay transfer, compact strength columns, hover calculations

### Request and decisions

- Right-click a player's board to load its wave, fighter counts, and mythium sent into the calculator. “Sent” is interpreted literally as the selected player's outgoing mercenaries; the import note explicitly labels this budget source.
- Reduce strength comparison to two estimates per player: base wave and wave plus received mercenaries. Display signed differences against the recorded fighter value, which is the baseline before attribute adjustment.
- Align all four analysis cards with the four boards using one four-column grid and one horizontal scroll container. This prevents independent wrapping or scrolling from misaligning players.
- Move detailed calculation explanations into a hover/focus/click tooltip. Existing attribute weighting is unchanged; tooltip text explains its exact assumptions and limitations.

### Changes

- Added delegated context-menu and keyboard board-import handlers. Duplicate fighters aggregate by name, unknown fighters are reported, and unrecognized send costs prevent a misleading budget import. Imports switch to the local draft without writing into a selected shared board.
- Fixed zero budget handling in import, persistence, shared-board loading/saving, and the calculator. Zero no longer becomes 720 or a minimum 20. Larger imported totals remain visible and usable.
- Replaced the long replay analysis cards with two values, green positive/red negative changes, and an explicit baseline label. Removed the candidate/save rows and their unused helper calculations from this view; the existing send calculator remains available through board import.
- Tooltips show original value, target weights, each fighter's attack/defense factors, weighted averages, square-root multiplier, rounding, and signed delta. Missing fighter/mercenary data or unsupported wave data produces an unavailable estimate.
- Updated README and regenerated `index.html`.

### Verification

- Added `tests/replay-ui.cjs`: executes the generated page in a Node VM with minimal DOM stubs and synthetic replay fixtures. Covers outgoing-vs-incoming budget selection, duplicate fighters, zero-budget reload, isolation from shared boards, unknown units, numeric +/- results, missing data, four-player grid order, and tooltip event handling.
- Build and these offline runtime checks passed; whitespace validation passed. These checks do not constitute a visual browser test. The previously recorded browser policy restriction on this local page remains in effect.

## 2026-10-11 — Correct imported budget to received mythium

- User clarified that board import must use the selected player's received mercenaries, superseding the previous outgoing-budget interpretation.
- Changed `importReplayBoard` to sum `mercenariesReceivedPerWave` for the selected wave. Updated the import message, board tooltip, error messages, and README. Empty received lists retain a zero budget.
- Updated regression assertions with different sent/received totals (500 sent versus 20 received), verifying import selects 20; the zero-received case keeps an outgoing send and still imports zero.
- Rebuilt `index.html`; all 8 regression checks and `git diff --check` passed.

## 2026-10-11 — Public official HP/DPS database, without an API key

### Request, evidence, and scope

- Initially investigated the official API for HP, damage, attack speed, range, and ability IDs. The existing importer deliberately retains only ID/name/icon/value/mythium/bounty, and no local API credential was available. The deployed replay proxy only accepts match queries.
- User then explicitly requested proceeding without the API. Used the public official guide at `https://beta.legiontd2.com/guide/units/` instead. The downloaded table is labelled `Last updated: 26.9` and provides factual HP, DPS, range, attack/armor types, ability names and wave counts. No credential, proxy change, deployment or external write was needed.
- Keep this public snapshot separate from existing `data/units.json` (26.9.hf3). The guide does not establish hotfix equivalence, so it would be misleading to relabel its numbers as API patch-accurate stats.
- The guide rounds DPS (e.g. Berserker 53), whereas its individual Berserker page displays 53.33. Store the guide's published precision consistently; do not infer attack intervals or bonus magic DPS from it. Only factual ability names are imported, not bulk ability prose or arbitrary skill multipliers.

### Changes

- Added `src/fetch_public_stats.py`, a standard-library no-key importer. It validates version, table headers, unique class/name identity, finite nonnegative stats, attack/armor types, coverage and waves 1–21 before atomically replacing its output. Supports an already downloaded official guide through `--html`. Import failures retain the existing snapshot.
- Created `data/combat_stats.json` from the downloaded official guide: **193 records (147 fighters, 21 creatures, 25 mercenaries)**. Includes source URL, acquisition timestamp, source version, published precision, unit source links and wave counts. Did not overwrite the existing versioned API metadata or modify its importer.
- Build embeds the combat snapshot offline with safe script-text escaping. Fighter, mercenary and wave pages show HP, approximate listed DPS, range, source links and limitations without additional table columns.
- Replay strength uses official HP/DPS and official attack/armor types when the complete composition is available. Outgoing attack efficiency is weighted by enemy HP; incoming damage by enemy DPS. Own DPS weights offense; own HP weights effective durability. Main values remain recorded fighter value multiplied by `sqrt(attack efficiency × durability efficiency)`, retaining the two-column signed-difference UI.
- Hover/focus/click calculations show each input, source version, full formula and an additional static force ratio `sqrt(effective HP × effective DPS / enemy HP / enemy DPS)`. This makes the extra quantity of identical-type mercenaries visible even when the primary matchup index is unchanged. This ratio is explicitly not a hold probability or leak prediction.
- Missing stats fall back to the previous value/attribute heuristic with a visible `屬性備援` label and reason. Four existing fighter names have no exact match: Heroic Scrappy, Mr. Brewpot, Heroic Mr. Brewpot, Heroic Rift Trader. No fuzzy or guessed mapping was introduced. W5/15/21 list `8x + Miniboss` without full secondary-unit stats, so their composition is not guessed either.
- Expanded README with refresh commands, model formulas, provenance, coverage gaps and scope. Send-combination ranking and reference-page attribute percentages retain their previous model; this change does not claim to simulate skills, summons, auras, targeting, geometry or combat duration.

### Verification and outcome

- Imported the real downloaded public guide successfully; reviewed Berserker, Drill Golem, Ghost Knight and Snail rows and all ambiguous wave counts.
- Rebuilt `index.html`; all **10 Node runtime regression checks** passed, including received-mythium board import, HP/DPS totals, mixed attack/armor weighting, duplicate mercenaries, lower force ratio with extra enemies, visible fallbacks, four-player alignment markup and tooltips.
- Added **6 Python importer tests**, all passing: numeric parsing and zero DPS, mixed-wave handling, missing version, invalid fields, missing/duplicate data, atomic persistence and preservation on failure.
- `git diff --check` passed. No visual browser verification was performed; the previously documented local-file browser policy block remains. No commit or deployment was requested or performed.
