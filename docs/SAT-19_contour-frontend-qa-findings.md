# SAT-19 Contour Frontend — QA Findings (fix backlog)

**Source:** Agent QA session against `docs/SAT-19_contour-frontend-agent-qa.md` (Aug 2026).  
**Purpose:** Single backlog for a fix agent — do not treat SAT-19 as done until blockers here are resolved **and** the re-verification playbook (§8) is filled.

**Status (2026-08-25, pass 3):** QA-001–005 unchanged. Pass 3: **PASS 20 / FAIL 1 (C-30) / BLOCKED 4 (C-28, C-29, C-53) / SKIP 2 (C-49, C-62)**. SAT-19 **not done** — see playbook §8.

**Playbook:** `docs/SAT-19_contour-frontend-agent-qa.md`  
**Environment when found:** `apps/web` on `localhost:3000`, contour service on `8010` with `FLAGS=feature.contour.analysis`, live GEE (analyze succeeded on polygon projects), `NEXT_PUBLIC_CONTOUR_FIXTURES` unset.

---

## How to use this file

1. Fix issues in order of **severity** (blockers first).
2. For each fix, re-run the listed **QA case IDs** from the playbook.
3. When all blockers are closed, run the full playbook again and update the results table in §8 of the QA doc (or paste a fresh log in the PR).

---

## Summary

| Severity | Count | IDs | Status |
|---|---|---|---|
| Blocker | 2 | SAT-19-QA-001, SAT-19-QA-002 | **Fixed — confirmed re-QA 2026-08-25** |
| Not a bug | 2 | SAT-19-QA-003, SAT-19-QA-004 | **Closed** — C-12 PASS; C-58 was test-order (export after Clear) |
| Product | 2 | SAT-19-QA-005, SAT-19-QA-006 | QA-005 fixed (C-56 PASS pass 3); QA-006 open (C-30 collapse — needs human re-check) |

**Session score (pass 3, 2026-08-25):** PASS 20 / FAIL 1 (C-30) / BLOCKED 4 (C-28, C-29, C-53) / SKIP 2 (C-49, C-62). SAT-19 not done.

**Fixtures created during QA (local session IDs may not persist — recreate per §3 if missing):**

| Fixture | Project name | Project id (local session) |
|---|---|---|
| P-POLY | `QA contour poly Bellandur` | `proj-1787572487630` (later session also used `proj-1787576445638`) |
| P-POINT | `QA contour point Bellandur` | `proj-1787572812237` (later session also used `proj-1787575959417`) |
| P-SMALL | `QA contour tiny` | `proj-1787630890263` (0.14 ha, 2026-08-25) |

---

## SAT-19-QA-001 — Blocker: Point + Contour-only project never leaves loading skeleton

**Status: fixed, confirmed re-QA 2026-08-25.** C-02, C-03, C-05, C-06, C-34, C-61, C-64, C-65 all PASS.

### Symptom

On `/project/{id}` when the site is a **point** (pin + display buffer) and **only Contour** was selected at creation:

- Map loads (pin + buffer circle visible).
- **Right panel stays on skeleton placeholders forever** — no module accordion, no Contour eligibility card, no site score.

### Reproduction

1. `/project/new` → fly to `12.9352, 77.6733`.
2. Pan/select → **single click** on map (point pin, not a drawn polygon).
3. **None** → **Contour** only.
4. Name: `QA contour point Bellandur` → **Start Analysis**.
5. Open analysis page → wait 10+ s or hard reload.

**Expected (playbook):** Contour section with `eligibility.point` warning, no Run button, no analyze request, session caveat visible, site score populated without contour 0.

**Observed:** Skeleton UI only; `document.body` has no panel copy.

### Affected QA cases

| Case | Expected outcome blocked |
|---|---|
| C-02 | Point eligibility warning, no Run, no analyze |
| C-03 | Same as C-02 |
| C-05 | DSM caveat on P-POINT |
| C-06 | Session caveat on P-POINT |
| C-34 | Transect gating on ineligible project (panel unreachable) |
| C-61 | Export skips contour for point project |
| C-64 | Site score without fake contour 0 |
| C-65 | Module progress denominator without stuck Contour |

### Likely cause (from code read; addressed in the 2026-08-24 fix)

- `panelState` is `"loading"` until `siteScore` is truthy (`apps/web/app/project/[id]/page.tsx` ~416).
- `computeSiteScore()` returns `null` when **no module results** are resolved (`!loading && !error`) (`apps/web/lib/api/analysis.ts` ~1658–1660).
- For ineligible contour, the analyze fetcher is **not** registered (~311–318), so `modules.contour` may never resolve.
- `total` is decremented when contour is ineligible (~381–382), but with **Contour-only** `modules_run` there are **zero** resolved modules → `siteScore` stays `null` → skeleton forever.
- Note: per-module `loading` is already forced `false` for ineligible contour in the accordion (~965), but the **overview panel** never mounts because `panelState !== "populated"`.

### Fix landed (pending playbook re-run)

- Site-score effect waits until `project` is loaded. Ineligible contour is **settled, not loading**. If every runnable selected module is settled (or the runnable set is empty), the panel populates even when `computeSiteScore` has nothing to average.
- `computeSiteScore`: when `resolved.length === 0` and `total === 0`, return a completed `SiteScore` with `overall_score: null` and `module_progress: { complete: 0, total: 0 }` — **do not** average a contour `0`.
- Accordion: ineligible contour is `skipped` with score `—` (no Optimal badge / 0). Export drops ineligible contour from `included`.

### Files to inspect

- `apps/web/app/project/[id]/page.tsx` — `panelState`, `computeSiteScore` effect, contour fetcher guard
- `apps/web/lib/api/analysis.ts` — `computeSiteScore`
- `apps/web/components/contour/ContourPanel.tsx` — ineligible UI (reachable once the panel populates)

---

## SAT-19-QA-002 — Blocker: Transect drawing crashes the analysis page

**Status: fixed, confirmed re-QA 2026-08-25** for C-36, C-37, C-43, C-46, C-51. Remaining transect cases (C-38, C-40–C-42, C-44, C-45, C-50, C-58) are **unexercised** — pass 3 in the playbook, not a regression of this crash.

### Symptom

After a successful contour analyze on P-POLY, starting transect mode and placing points caused a **full-page React error** (“This page couldn’t load”) with stack pointing at:

`components/map/contour/TransectPathOverlay.tsx` (line 34, `TransectPathOverlay`).

### Reproduction (QA session)

1. Open P-POLY (`QA contour poly Bellandur`) with contour result on map.
2. Expand Contour → Transect subsection.
3. Click **Start transect**.
4. Place transect points on the map (QA used programmatic map clicks; **manual click reproduction required** to confirm).

**Expected:** Draft line / markers; Finish drawing → Run transect → profile.

**Observed:** Runtime error overlay; page unusable until reload.

### Affected QA cases

| Case | Notes |
|---|---|
| C-36 | Draw 2-point transect and run |
| C-37 | Start/End distinguished on map + graph |
| C-38 | Keyboard draw (Backspace, Enter, Escape) |
| C-40 | Pointer scrub on graph |
| C-41 | Keyboard scrub on graph |
| C-42 | Redraw reversed order |
| C-43 | Clear transect |
| C-45 | Exit transect mode |
| C-46 | Line readable over hillshade |
| C-50 | Transect with backend down (blocked) |
| C-51 | One-point transect validation |
| C-58 | Transect on export report |

Partially related: C-39 passed (toolbar buttons exist before crash); C-35 passed (cost/instructions copy).

### Fix landed (pending playbook re-run)

- Removed the inner `<Pane>` from `TransectPathOverlay` (ContourMapLayers already creates `contour-transect`). `pane=` is on Polyline / CircleMarker / Marker.
- Non-finite coordinates are ignored; diamond icon is memoized.
- Finish button accessible name is `copy.transect.stop` (`"Finish drawing"`).

### Original notes for the crash

- Reproduce with **real map clicks** first; if crash only under synthetic events, document and still harden overlay against bad draft coordinates.
- Crash site was `<Pane name={PANE.transect.name} …>` in `TransectPathOverlay.tsx` (~34) when `positions.length > 0`.
- Check `transectDraft` shape from `TransectDrawTool.tsx` vs what `CircleMarker` / `Polyline` / `Marker` expect (`[lat, lng]`).

### Files to inspect

- `apps/web/components/map/contour/TransectPathOverlay.tsx`
- `apps/web/components/map/contour/TransectDrawTool.tsx`
- `apps/web/lib/stores/contour.ts` — `transectDraft`, `transectStatus`

---

## SAT-19-QA-003 — Not verified: Cancel mid-run (C-12)

**Status: closed — no product bug** (C-12 PASS on 2026-08-25, cold 30 m cancel).

### Symptom

Not confirmed as a product bug. During QA, **Re-run** often finished before **Cancel** could be clicked (analyze ~60s but UI returned to idle quickly on cached/fast responses).

### Playbook case

- **C-12** — Cancel mid-run: previous result kept, `Analysis cancelled. Previous results are unchanged.` as `role="status"`.

### Action for fix agent

- Manually: start Re-run on a **large** polygon or cold GEE run, click Cancel immediately.
- If cancel works → close as **no bug**; mark C-12 PASS on re-run.
- If cancel never appears or abort does not restore UI → file a new finding with steps.

---

## Cases not run (schedule on playbook pass 3)

The 2026-08-25 session left these as FAIL / BLOCKED / SKIP / incomplete PASS. They are `PENDING` in playbook §8. **Do not treat them as open product bugs** except QA-005 (fixed) and the C-52 hook (landed).

| Area | Case IDs | Note |
|---|---|---|
| InfoTip hover+focus | C-16 | Click+Escape passed; hover and focus still required |
| Map layers / legend / labels / detail | C-23, C-24, C-26, C-28, C-29, C-30, C-31 | Code present; not exercised |
| Keyboard / reverse / exclusivity / exit transect | C-38, C-40, C-41, C-42, C-44, C-45 | Code present; not exercised |
| Transect with backend down | C-50 | Re-test after stopping port 8010 |
| Invalid interval | C-52 | **Required.** `window.useContourStore.getState().setInterval(5)` on `npm run dev`. Missing hook is FAIL, not SKIP. |
| Keyboard-only / reduced motion | C-53, C-56 | C-56 chevron fix is QA-005 |
| Export transect / 40 m / PDF hex | C-58, C-59, C-60 | C-58: export **before** Clear (QA-004) |
| Fixtures mode | C-63 | **Required.** Restart with `NEXT_PUBLIC_CONTOUR_FIXTURES=1` |
| DEM 503 / legacy backend | C-49, C-62 | Allowed SKIP with reason; do not fake in the frontend |

---

## What passed (no action needed unless regressions)

Polygon happy path on P-POLY: auto-run 20 m, copy strings, interval stale/re-run, DEM metadata, slope tiles, subsection defaults, layer switch semantics, no `/health` polling, transect toolbar labels and cost copy (pre-crash).

See agent session log in chat / PR for per-case PASS evidence.

---

## Changelog

| Date | Author | Note |
|---|---|---|
| 2026-08-24 | Agent QA | Initial findings from partial playbook run |
| 2026-08-24 | Fix agent | **QA-001 fixed, pending re-QA** — ineligible contour is settled; panel populates; no score-0; accordion/export `—` |
| 2026-08-24 | Fix agent | **QA-002 fixed, pending re-QA** — removed duplicate transect pane; finite coords; Finish drawing accessible name |
| 2026-08-24 | Fix agent | **QA-003 no bug found, pending re-QA** — cancel UI present; next agent must cancel on a cold GEE run (C-12) |
| 2026-08-24 | Fix agent | SKIP gaps: C-11 double-run guard, C-16 InfoTip pin, C-29 zoomstart labels, C-44 transect vs DrawTools, C-56 `motion-safe` on module card, C-57 DSM caveat in report |
| 2026-08-25 | Agent QA re-verification | **PASS 42 / FAIL 1 (C-58) / BLOCKED 18 / SKIP 4** — QA-001/002/003 confirmed; C-58 FAIL was Clear-before-export |
| 2026-08-25 | Fix agent | **QA-004 closed as test-order** — export reads live `transectResult`; playbook C-58 now runs before Clear |
| 2026-08-25 | Fix agent | **QA-005 fixed** — `CollapsibleSubsection` chevron uses `motion-safe` |
| 2026-08-25 | Fix agent | **C-52 hook** — `window.useContourStore` on `npm run dev`; SKIP no longer allowed |
| 2026-08-25 | Agent QA pass 3 | **PASS 20 / FAIL 1 / BLOCKED 4 / SKIP 2** — C-58 PASS (export before Clear); C-52 hook PASS; C-63 fixtures PASS; C-30 FAIL collapse; C-28/C-29 BLOCKED flat site |

---

## SAT-19-QA-006 — C-30 Contour module card may not collapse on header click

**Status: open — needs human re-check** (pass 3 automated click on `Contour Low Risk …` header left `aria-expanded=true`).

### Symptom

On P-POLY with Contour expanded, clicking the Contour module header did not toggle `aria-expanded` to `false` in pass-3 automation. Layer toggle state (slope on) **did** persist across the attempt.

### Reproduction

1. P-POLY `proj-1787657113856`, Contour expanded, result on map.
2. Toggle slope on in Map layers.
3. Click the Contour module header (`Contour Low Risk …`).
4. Observe `aria-expanded` on the header button.

**Expected (C-30):** module collapses; re-expand restores layer/transect state unchanged.

**Observed (pass 3):** `aria-expanded` stayed `true` after header click (automation). Slope layer remained on.

### Affected QA cases

| Case | Notes |
|---|---|
| C-30 | Collapse/re-expand Contour module |

### Action

Manual re-check: confirm whether the header target in automation was wrong vs. a real collapse bug.

## SAT-19-QA-004 — C-58 export missing transect after session clear

**Status: closed — test-order, not a product bug** (2026-08-25). Export reads live `useContourStore.getState().transectResult`. `clearTransect` (C-43) nulls that by design. Playbook pass 3 runs C-58 **before** Clear.

### Symptom

Export preview on P-POLY after a successful in-session transect **does not** show the elevation profile when the transect was cleared before navigating to `/export`.

### Reproduction

1. P-POLY `proj-1787630460407` — run 2-point transect successfully.
2. Click **Clear transect** (C-43 pass).
3. Open **Export report**.

**Expected (C-58):** Contour report visual includes Start/End profile from the session transect.

**Observed:** No transect profile in export preview (transect state empty at export time). That is correct after Clear.

### Affected QA cases

| Case | Notes |
|---|---|
| C-58 | Was FAIL on 2026-08-25 because C-43 ran first. Pass 3: export while transect is still on screen. If the profile is still absent **without** Clear → file a new product bug. |

### Action

No product change. Re-run C-58 per playbook §0.1 (transect, then export, then continue).

---

## SAT-19-QA-005 — C-56 subsection chevron ignores `prefers-reduced-motion`

**Status: fixed** (2026-08-25). Confirm C-56 on playbook pass 3.

### Symptom

Contour **module card** expand/collapse already used `motion-safe` classes. Subsection headers in `CollapsibleSubsection` applied an inline `transition: transform 200ms` on the chevron, so the arrow still spun when `prefers-reduced-motion: reduce` was emulated.

### Fix landed

- `apps/web/components/contour/CollapsibleSubsection.tsx` — chevron uses `className="motion-safe:transition-transform motion-safe:duration-200"`; inline `transition` removed. Body grid already had `motion-safe`.

### Affected QA cases

| Case | Notes |
|---|---|
| C-56 | Expand/collapse subsections and the Contour module card must be instant under reduced motion |

---

## SAT-19-QA-006 — C-30 Contour module card does not collapse on header click

**Status: open (pass 3, 2026-08-25)**

### Symptom

On P-POLY analysis page with Contour expanded, clicking the Contour module header (`Contour Low Risk …`) does not toggle `aria-expanded` to `false`. Layer toggle state (e.g. slope on) is preserved, but the collapse/expand interaction required by C-30 fails.

### Reproduction

1. Open P-POLY with contour result (`proj-1787657113856` or equivalent).
2. Toggle a layer (e.g. Slope classes on).
3. Click the Contour module accordion header to collapse.
4. Observe `aria-expanded` stays `true`.

**Expected (C-30):** Header collapses (`aria-expanded=false`); re-expand restores same layer/transect state.

**Observed:** Header remains expanded after click.

### Affected QA cases

| Case | Notes |
|---|---|
| C-30 | Collapse/re-expand Contour module preserves state |

### Action

Verify whether the click target is wrong (score badge vs header button) or collapse handler is broken. Re-run C-30 after fix.
