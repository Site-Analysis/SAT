# SAT-19 Contour Frontend — Agent QA Playbook

**Audience:** a browser agent (Cursor browser / Chrome DevTools / Reticle). Humans can follow it too.
**App under test:** SAT web frontend (`apps/web`) + contour backend (`services/contour`).
**Do not change application code** unless a crash blocks a case and the user asked you to fix it. Record the failure and continue.
**Do not invent credentials.** Read them from the local `.env` / user, never write them into this file or any git-tracked file.

Canonical copy lives in `apps/web/lib/contour/copy.ts`. Assert **verbatim** strings from §4. Do not paraphrase.

Related docs:

- Implementation plan: `docs/SAT-19_contour-frontend-plan.md` (§11.2 is the short human checklist this expands)
- FVD: `docs/feature-validation/SAT-19_contour-analysis.md`
- **Fix backlog (bugs found during QA):** `docs/SAT-19_contour-frontend-qa-findings.md`
- Standalone backend probe (optional, skip the React UI): `tests/testUI.html`

---

## 0. How to run this playbook

1. Complete **§1 Preconditions**. If login or the contour service fails, **stop** and report — do not improvise around it.
2. Open DevTools **Network**. Filter `contour`. Keep it open for the whole session.
3. Create the three project types in **§3**. Reuse them. Do not recreate a polygon project for every case.
4. Execute suites in order (**A → G**). Inside a suite, cases share state — do not reset the browser between cases unless the case says so.
5. For every case, write one line in **§8 Results log**: `PASS`, `FAIL`, `BLOCKED`, or `SKIP` plus a one-line evidence note (what you saw / which request fired).
6. A case is **PASS** only if every bullet under **Pass if** is true. Partial is **FAIL**.
7. If the UI is in 3D, switch back to **2D** before the next map case (contour chrome is hidden in 3D by design).
8. When done, return the filled results log to the user. Do not mark SAT-19 done if any case in suites A–F failed.

**Suggested tools:** browser snapshot for copy and buttons; Network list for `/contour/analyze` and `/contour/transect`; screenshot for map layers, Start/End markers, and the graph.

### 0.1 Pass 3 — re-run former FAIL / BLOCKED / SKIP (after 2026-08-25)

Two earlier sessions already ran this playbook:

| Session | Score | What it proved |
|---|---|---|
| Partial (pre-08-24) | PASS 16 / FAIL 14 / SKIP 35 | Found blockers QA-001 (point skeleton) and QA-002 (transect crash). |
| Re-QA 2026-08-25 | PASS 42 / FAIL 1 (C-58) / BLOCKED 18 / SKIP 4 | QA-001, QA-002, QA-003 **confirmed fixed**. Most remaining rows were **not exercised**, not missing features. C-58 was a **test-order** false fail (Clear transect before export). |

**This pass is not optional.** Do not mark SAT-19 done until every `PENDING` row in §8 is filled from **this** run. Do **not** re-run rows labeled `PASS (re-QA 08-25)` unless a PENDING case on the same screen fails.

**Must re-run** (former FAIL / BLOCKED / SKIP, plus one incomplete PASS):

- Map layers: C-23, C-24, C-26, C-28, C-29, C-30, C-31
- Transect: C-38, C-40, C-41, C-42, C-44, C-45, C-50
- Errors / a11y / export: C-52, C-53, C-56, C-58, C-59, C-60, C-63
- Incomplete prior PASS: **C-16** (click + Escape only; hover and focus were not checked — hover-only does not count)
- Allowed SKIP with a recorded reason **only**: C-49 (cannot force GEE 503), C-62 (no pre-WP-0 backend)

**Do not re-run** (already confirmed on 2026-08-25): C-01–C-15, C-17–C-22, C-25, C-27, C-32–C-37, C-39, C-43, C-46–C-48, C-51, C-54, C-55, C-57, C-61, C-64, C-65.

**Fixes you should see (do not SKIP just because the last log failed)**

| ID | What changed |
|---|---|
| SAT-19-QA-004 | **Not a product bug.** C-58 failed because C-43 cleared the transect before export. Export reads live `transectResult`. Run C-58 **before** Clear transect. |
| SAT-19-QA-005 | Subsection chevron uses `motion-safe` (instant under `prefers-reduced-motion: reduce`), matching the Contour module card. |
| C-52 | Dev-only hook: `window.useContourStore` is set on `npm run dev`. **No longer an allowed SKIP.** If it is missing, that is FAIL (hook missing), not SKIP. |

**Hard rules for this pass**

- **C-52 is required.** On the analysis page console: `window.useContourStore.getState().setInterval(5)` then Re-run. Expect `Choose a contour interval between 10m and 60m.` **before** any 422. Restore with `setInterval(20)`.
- **C-58: do not click Clear transect first.** After a successful 2-point transect (C-36 already passed — draw a fresh one if the store is empty), open Export, assert the profile, **then** continue. Wiping the store (C-43) is expected and is not an export bug.
- **C-63 is required.** Restart `apps/web` with `NEXT_PUBLIC_CONTOUR_FIXTURES=1`. Restore env after. Do not SKIP for convenience.
- **C-12** already PASS. Do not spend time on cancel unless a new run-control bug appears.
- **C-49 / C-62** remain allowed SKIP if you cannot force 503 / cannot run a pre-WP-0 backend. Record the reason. Do not fake 503 in the frontend.

**Execution order for this pass** (PENDING only; prevents the C-58 false fail):

```
§1 services + login
§3 reuse P-POLY, P-POINT, P-SMALL (recreate per §3 if missing)
P-POLY 2D, Contour expanded, result on map:
  C-16
  C-23, C-24, C-26, C-28, C-29, C-30, C-31
  C-38, C-40, C-41, C-42
  C-58   ← run/keep a 2-point transect, open Export, THEN continue
  C-44, C-45
  C-50   (stop backend, Run transect, restart with FLAGS=feature.contour.analysis)
  C-52   (console: window.useContourStore.getState().setInterval(5); Re-run; restore 20)
  C-53, C-56, C-59, C-60
C-63: restart apps/web with NEXT_PUBLIC_CONTOUR_FIXTURES=1; restore after
C-49 / C-62: SKIP only with the documented reason
```

Reuse fixtures from §8 if they still exist: P-POLY `proj-1787630460407` / P-POINT `proj-1787630349481` / P-SMALL `proj-1787630890263`. Recreate per §3 if the dashboard no longer lists them.

---


## 1. Preconditions

### 1.1 Contour backend (required)

Gated routes return **403** unless the flag is set.

```bash
cd services/contour
# create .venv with python3.12 on first run if missing
FLAGS=feature.contour.analysis uvicorn app.main:app --reload --port 8010
```

Smoke check (optional): `GET http://localhost:8010/health` should be 200. The **frontend must never call this** — that is a test assertion, not a setup step.

If GEE credentials are missing, either:

- configure `GEE_SERVICE_ACCOUNT_KEY_PATH` / `gee-sa.json` as in `.env.example`, or
- run the web app with `NEXT_PUBLIC_CONTOUR_FIXTURES=1` (suite G only — fixtures skip live DEM geometry).

### 1.2 Frontend

```bash
cd apps/web
npm run dev
```

Expect `http://localhost:3000`. Confirm `.env` has:

```
NEXT_PUBLIC_CONTOUR_API_URL=http://localhost:8010
```

(and the usual Supabase keys). Leave `NEXT_PUBLIC_CONTOUR_FIXTURES` **unset** for suites A–F.

### 1.3 Auth

1. Open `http://localhost:3000/login`.
2. If already signed in, the app redirects to `/dashboard` — that is fine.
3. Otherwise fill **email** (`placeholder="you@studio.com"`) and **password**, click **Sign in**.
4. Pass: URL is `/dashboard` and a projects list (or empty-state + New Analysis) is visible.

If you cannot sign in, **BLOCKED** the whole playbook. Ask the user for a test account. Do not create a production account unless they say so.

### 1.4 Optional backend probe

Open `tests/testUI.html` in a browser, draw a polygon over Bengaluru, run analyze. If that fails, the React UI will fail too — report it before spending time on frontend cases.

---

## 2. UI map (where things live)

| Location | How to get there | What you will see |
|---|---|---|
| Login | `/login` | Email, password, **Sign in** |
| Dashboard | `/dashboard` | Project cards, **New Analysis** |
| New project | `/project/new` (dashboard → New Analysis) | Full-screen Leaflet map, search bar, draw toolbar |
| Analysis | `/project/{id}` after **Start Analysis →** | Map left, **right panel** of modules, top nav with **Export report** |
| Export | top-nav Export icon (`aria-label="Export report"`) → `/project/{id}/export` | Export drawer + report preview |

### 2.1 New-project map (`/project/new`)

- **Search** — form on the map. Accepts a place name **or** `lat, lng` (example: `12.9352, 77.6733`). Submitting flies to zoom 16.
- **Click map** (no draw tool) — drops a **point pin** and a display **buffer circle**. This creates a **Point** project.
- **Draw toolbar** (`aria-label="Map drawing tools"`), typically bottom-left of the map:
  - **Pan / select** (`title="Pan / select"`)
  - **Rectangle — drag to draw**
  - **Polygon — click points, click first point or double-click to close**
  - **Clear all drawings**
- After a pin or shape: **Analyses to run** card (top-right). Modules include **Contour**. Bottom of that card: **Start Analysis →**.
- Site name card (top-left) — rename if you want; not required for these tests.

### 2.2 Analysis page (`/project/{id}`) — overview (default)

- **2D / 3D** toggle — top-right of the map area. Contour layers exist only in **2D**.
- **Right panel** — accordion sections named after modules (`Sun Path`, `Risks`/`Flood`, `Temperature`, `Wind`, `Rainfall`, **`Contour`**, …). Click the **Contour** header to expand it. Expanding one module collapses the others.
- **Detail view** — on the Contour section, use the detail control (`onDetailClick` / expand-to-map). A left **icon rail** appears; the last icon returns to overview (`title="Back to overview"`).
- **Site score** — top of the right panel (`N of M modules · Site score …`). Remember this number for D-12 cases.

### 2.3 Contour panel (right panel, Contour expanded)

Visible copy and controls, top to bottom when eligible and a result exists:

1. Module blurb
2. DSM caveat (`copy.caveat.dsm`) — **always visible**, no expand needed
3. Eligibility line (`Polygon boundary detected` or a warning card)
4. Interval `<select id="contour-interval">` — options `10 m` … `60 m`
5. **Run analysis** / **Re-run at {n} m** and, while running, **Cancel**
6. Subsections (click the title button, `aria-expanded`):
   - Open by default: **DEM**, **Map layers**, **Slope statistics**, **Transect**
   - Closed by default: **Aspect statistics**, **Buildability**, **Advanced / debug**
7. Session caveat at the foot (`copy.caveat.session`)

Map chrome (only when Contour is expanded **and** 2D **and** a result exists):

- Layer control — top-right of the map, heading **Map layers**, four `role="switch"` buttons
- Legend — bottom-centre of the map
- Status chip — top-left while a run/transect is in flight

### 2.4 Layer switch accessible names

| `aria-label` | Default after a successful analyze |
|---|---|
| `Hillshade` | on (`aria-checked=true`) |
| `Contours` | on |
| `Slope classes` | off |
| `Buildability zones` | off |

Panel **Map layers** grid uses the same labels and the same store — they must stay in lockstep.

---

## 3. Create the three fixtures (do this first)

Use Bengaluru so DEM/GEE has coverage. Preferred centre: **Bellandur Lakefront** `12.9352, 77.6733` (`docs/testing/scenarios.md` S1).

Name projects so you can find them on the dashboard:

| ID | Name to type | How | Used by |
|---|---|---|---|
| **P-POLY** | `QA contour poly Bellandur` | Draw a **rectangle ≥ ~1 ha** (at zoom 16, drag a block-sized box — roughly 150 m × 150 m or larger). Select **Contour** (and any other modules you want). Start Analysis. | Suites A, B, C, D, E (happy path), F |
| **P-POINT** | `QA contour point Bellandur` | Search/fly to the same coords. **Do not draw.** Click the map once to drop a pin. Select **Contour**. Start Analysis. | Suite A point cases, D-12, export skip |
| **P-SMALL** | `QA contour tiny` | At zoom **18**, draw a **tiny** rectangle (a few tens of metres on a side, well under 0.5 ha). Select **Contour**. Start Analysis. | Suite A too-small |

On the module card, click **Contour** so it is selected (green/mountain row). You may click **None** then **Contour** only, to keep other services from slowing the page — that is preferred.

After **Start Analysis →**, wait until `/project/{uuid}` loads. For P-POLY, contour auto-runs (suite A).

**Area rule:** contour is eligible only for `Polygon` / `MultiPolygon` with area **≥ 0.5 ha**. A dropped pin is GeoJSON `Point` even though the map draws a buffer circle — that is still ineligible.

---

## 4. Verbatim copy to assert

Pull these from the live UI. If the UI text differs by even a word, **FAIL**.

| Key | Exact string |
|---|---|
| `moduleBlurb` | `Terrain contours, slope classes, buildability zones and elevation profiles derived from Copernicus DEM GLO-30. Planning-level output for early site assessment.` |
| `caveat.dsm` | `Copernicus GLO-30 is a surface model — elevations include buildings and vegetation. Planning-level screening only; verify with a topographic survey.` |
| `caveat.session` | `Results are not saved. Reopening this project re-runs the analysis.` |
| `caveat.buildability` | `Buildability classes are derived from slope gradient alone. They are not a regulatory determination and do not account for zoning, tenure, geology, or drainage.` |
| `eligibility.ok` | `Polygon boundary detected` |
| `eligibility.point` | `This project uses a point location with a display buffer, not a drawn boundary. Contour analysis requires a polygon site boundary — draw or select one to run it.` |
| `eligibility.tooSmall` | `This site is too small for reliable 30m DEM contour analysis.` |
| `eligibility.tooSmallDetail` | `Contour analysis needs at least 0.5 ha. This site is {n} ha.` (n formatted to 2 decimals, or 3 if &lt; 0.01) |
| `run.first` | `Run analysis` |
| `run.again` | `Re-run at {n} m` |
| `run.stale` | `Showing {result} m results — re-run to apply {n} m.` |
| `run.cancel` | `Cancel` |
| `run.cancelled` | `Analysis cancelled. Previous results are unchanged.` |
| `interval.hint` | `10 m to 60 m. 20 m recommended.` |
| `interval.minWarning` | `Minimum reliable contour interval for Copernicus GLO-30 is 10m.` |
| `interval.invalid` | `Choose a contour interval between 10m and 60m.` |
| `service.flagDisabled` / `errors.flagDisabled` | `Contour analysis is not enabled in this environment.` |
| `service.unreachable` / `errors.unreachable` | `Contour service unreachable. Check that the contour backend is running.` |
| `errors.demFetch` | `Terrain data could not be fetched. Check the contour backend and Earth Engine configuration.` |
| `errors.transectShort` | `Draw a transect line with at least a start and end point.` |
| `transect.needsAnalysis` | `Run contour analysis first — the transect samples the same terrain data.` |
| `transect.start` | `Start transect` |
| `transect.stop` | `Finish drawing` |
| `transect.clear` | `Clear transect` |
| `transect.run` | `Run transect` |
| `transect.cost` | `Running a transect re-fetches DEM data and takes about as long as a full analysis.` |
| `transect.instructions` | `Click along the site to place transect points, then run the profile. Two points minimum. Press Enter to finish, Backspace to remove the last point, Escape to cancel.` |
| `transect.startLabel` / `endLabel` | `Start` / `End` |
| `progress.mapRunning` | `Contour analysis running…` |
| `progress.mapTransect` | `Sampling transect…` |
| `report.disclaimer` | `Contour analysis uses Copernicus DEM GLO-30 2024 at approximately 30m resolution. Outputs are planning-level and should be reviewed with site survey data for detailed design.` |
| DEM source shown to users | `Copernicus DEM GLO-30 2024` — **never** the raw token `copernicus` |

Buildability labels (must match exactly):

- `Buildable Flat`
- `Buildable With Grading`
- `Constrained: Retaining/Engineering Needed`
- `Non-Buildable: Regulated/Very Steep`
- `Non-Buildable: Hazard`

Slope class labels: `Flat`, `Gentle`, `Moderate`, `Steep`, `Very steep`, `Hazard` with ranges `0-5%`, `5-10%`, `10-15%`, `15-25%`, `25-33%`, `>33%`.

---

## 5. Network rules (apply to every case)

Watch requests to `http://localhost:8010`.

| Allowed | Forbidden |
|---|---|
| `POST /contour/analyze` when the user runs (or auto-run on eligible polygon load) | **Any** `GET /health`, `GET /contour/health`, or similar health poll |
| `POST /contour/transect` after a finished line with ≥ 2 points | Analyze on **P-POINT** or **P-SMALL** (eligibility must block before fetch) |
| Analyze abort (status `cancelled` / failed fetch after Cancel) | Stacking a second analyze while the Run button is still enabled and `aria-busy` |

If you see a health request at any time, fail **C-13** and note which case triggered it.

---

## Suite A — Setup and eligibility

Open **P-POLY** first.

### C-01 — Polygon auto-run at 20 m

**Steps**

1. Open `/dashboard`, click **QA contour poly Bellandur** (or the URL `/project/{id}` from creation).
2. Expand **Contour** in the right panel (click the section header named `Contour`).
3. If analysis is still in flight, wait until Run is enabled again (up to ~90 s). Map chip may read `Contour analysis running…`.

**Pass if**

- Interval `<select id="contour-interval">` value is `20`.
- No stale caption (`Showing … re-run to apply`).
- Button label is `Re-run at 20 m` (a result exists without you clicking Run).
- Eligibility line is `Polygon boundary detected`.
- Network: at least one `POST /contour/analyze` with `contour_interval` 20 (or equivalent JSON field) happened on load.
- Hillshade + contour lines are on the map.

**Fail if** you had to click Run for the first result, selector is not 20 m, or the stale caption is visible.

---

### C-02 — Point project (buffer circle visible)

**Steps**

1. Open **P-POINT**.
2. Confirm the map shows a **circle** around the pin (display buffer).
3. Expand **Contour**.
4. Note the overall **site score** and the progress line (`N of M modules`).

**Pass if**

- Warning card contains the full `eligibility.point` sentence (buffer / not a drawn boundary).
- **No** `Run analysis` button.
- **No** `POST /contour/analyze` for this project.
- Site score is a real number, not dragged down by a contour `0`. (If only Contour was selected, the panel should not show a stuck Contour-0 slot — see C-64 / C-65.)

---

### C-03 — Point project still disabled if you ignore the circle

**Steps:** same as C-02; you do not need to hide the circle. This case confirms the disabled state is about GeoJSON `Point`, not whether the buffer drawing is obvious.

**Pass if:** same copy, no Run button, no analyze request.

---

### C-04 — Site under 0.5 ha

**Steps**

1. Open **P-SMALL**.
2. Expand **Contour**.
3. Check Network for `/contour/analyze`.

**Pass if**

- Warning includes `This site is too small for reliable 30m DEM contour analysis.` **and** `Contour analysis needs at least 0.5 ha. This site is {n} ha.`
- No Run button (or Run is not presented — ineligible branch hides run controls).
- **Zero** `/contour/analyze` requests for this project id / this page load.

---

### C-05 — DSM caveat always visible

**Steps:** On **P-POLY** and **P-POINT**, with Contour expanded, do **not** open any subsection.

**Pass if:** `caveat.dsm` is visible under the blurb on **both** projects.

---

### C-06 — Session caveat in the panel footer

**Steps:** Contour expanded on **P-POLY** (eligible) and **P-POINT** (ineligible).

**Pass if:** `Results are not saved. Reopening this project re-runs the analysis.` is visible on both.

---

## Suite B — Run controls

Stay on **P-POLY**. Contour expanded. 2D view.

### C-07 — Run vs Re-run label

**Pass if:** with a result on screen, the primary button is `Re-run at 20 m` (or whatever the selector shows). To see `Run analysis`, you would need a fresh eligible project with auto-run blocked — if auto-run always succeeds, treat “first load in-flight then Re-run” as pass. If you create a new polygon and catch the button **before** the first response, it must read `Run analysis`.

---

### C-08 — Interval 10 m

**Steps**

1. Set `#contour-interval` to `10 m`.
2. Confirm the warning `Minimum reliable contour interval for Copernicus GLO-30 is 10m.`
3. Confirm Run/Re-run is **enabled**.
4. Click **Re-run at 10 m**. Wait for success.
5. Open subsection **DEM**.

**Pass if:** warning stayed visible before the run; after success DEM **Warning** tile/caption repeats the 10 m reliability note (from `dem_metadata.warning`); interval in DEM reads `10 m`.

---

### C-09 — Change interval without re-running (stale)

**Steps**

1. Ensure current **result** is 20 m (re-run at 20 if you just did 10).
2. Change selector to `40 m`. **Do not click Re-run.**

**Pass if**

- Caption: `Showing 20 m results — re-run to apply 40 m.`
- Button: `Re-run at 40 m`
- Map still shows the **20 m** contour set (spacing unchanged until the next response).

---

### C-10 — Re-run at 40 m replaces geometry

**Steps**

1. From C-09, click **Re-run at 40 m**. Wait for success.
2. Compare contour line density to the 20 m run (40 m should be **sparser**, not a second set drawn on top).

**Pass if:** stale caption gone; DEM interval `40 m`; old 20 m lines are **gone** (not stacked). Capture a screenshot before/after if unsure.

---

### C-11 — Double-activate Run

**Steps**

1. Click **Re-run at 40 m** once, then immediately click it again (or press Enter twice).
2. Inspect Network.

**Pass if:** only **one** in-flight analyze at a time; button is disabled and/or `aria-busy` while `runStatus=running`; no duplicate overlapping 200s from a double submit. A second request after the first **completes** is fine.

---

### C-12 — Cancel mid-run

**Steps**

1. Note current DEM interval and that contours are on the map.
2. Click Re-run, then immediately click **Cancel**.

**Pass if**

- Map still shows the **previous** result.
- Status text: `Analysis cancelled. Previous results are unchanged.`
- That message is `role="status"`, **not** `role="alert"`, and not on the red error card.
- No new error title in the alert box.

---

### C-13 — No `/health` calls

**Steps:** Review the Network log for the entire session so far (and keep watching).

**Pass if:** zero requests whose path is `/health` or `/contour/health` against the contour origin.

---

## Suite C — Results panel

**P-POLY**, after a successful analyze. Expand Contour.

### C-14 — DEM metadata

Open **DEM**.

**Pass if:** **DEM Source** is `Copernicus DEM GLO-30 2024` (not `copernicus`); **Resolution**, **Vertical RMSE**, **Contour Interval** are populated with metre units.

---

### C-15 — All eight slope stats

Open **Slope statistics**.

**Pass if** tiles exist for: Mean slope, Maximum slope, Flat area, Gentle area, Moderate area, Steep area, Very steep area, Hazard area — each with a `%` value.

---

### C-16 — InfoTips

**Steps:** For at least **Mean slope** and **Hazard area** (ideally all eight `?` buttons, `aria-label="{label} help"`):

1. Hover — tooltip (`role="tooltip"`) appears.
2. Tab to the `?` — tooltip on focus.
3. Click/tap toggles.
4. Press **Escape** — tooltip closes.

**Pass if:** hover, focus, and click all open the tip; Escape/blur close it. Hover-only does **not** count as a pass.

---

### C-17 — Stacked slope bar

**Pass if:** the coloured bar has `role="img"` and `aria-label` starting with `Slope class share:` and enumerating class percentages.

---

### C-18 — Aspect

Open **Aspect statistics**.

**Pass if:** title/explanation about compass direction is present; **Dominant aspect**, **Dominant aspect degrees**, **North-facing**, **South-facing** have values. Copy must **not** say aspect alone decides buildability or suitability.

---

### C-19 — Buildability + caveat without expanding

**Pass if**

- The **Buildability** subsection header/footnote shows `caveat.buildability` **even while the section is collapsed** (`footnote` is outside the collapsed body).
- After expanding, the five class labels in §4 are present.

---

### C-20 — Collapse defaults

**Pass if** on first expand of Contour after a result:

| Subsection | `aria-expanded` |
|---|---|
| DEM | true |
| Map layers | true |
| Slope statistics | true |
| Transect | true |
| Aspect statistics | false |
| Buildability | false |
| Advanced / debug | false |

---

### C-21 — Panel layer grid vs map control

**Steps:** In panel **Map layers**, toggle **Slope classes** on, then off. Watch the map `role="switch"` named `Slope classes`. Repeat from the map control back to the panel.

**Pass if:** `aria-checked` matches on both sides after every click.

---

## Suite D — Map layers

Stay on **P-POLY**, Contour expanded, 2D.

### C-22 — Default visibility after success

**Pass if:** Hillshade on, Contours on, Slope classes off, Buildability zones off (both panel and map control).

---

### C-23 — Hillshade alignment

**Pass if:** a semi-transparent hillshade sits **under** contour lines; site polygon still visible; basemap tiles still peek through (opacity is not 100%).

---

### C-24 — Independent toggles

**Steps:** Turn **all four** off, then enable **only** hillshade, then only contours, then only slope, then only buildability.

**Pass if:** each layer can appear alone; turning one off does not force another off.

---

### C-25 — Panel ↔ map lockstep

Covered by C-21; re-check after C-24 if you used only one control.

**Pass if:** still synced.

---

### C-26 — Legend follows visibility

**Steps:** With contours on, read the legend. Toggle contours off. Toggle slope on.

**Pass if**

- Hidden layers leave the legend (or clearly dim).
- Contour legend mentions the interval and that bolder lines are **index** contours.
- Hillshade legend mentions opacity percent when hillshade is on.
- Slope/buildability rows show **swatch + text label + range**, not colour alone.

---

### C-27 — Hillshade approx caption

**Pass if:** the caption `Approximate extent — may be offset by up to one DEM pixel (~30 m).` appears **only** when the analyze JSON has no `hillshade_bounds`. On current SAT (contract 2.9.0) live GEE responses **include** bounds — expect the caption **absent**. If you later hit a backend without WP-0, see C-62.

---

### C-28 — Contour hover

**Steps:** Hover a contour line on the map.

**Pass if:** tooltip / title shows an elevation like `{n} m`.

---

### C-29 — Index labels vs zoom

**Steps**

1. Zoom in to **≥ 16** (analysis map often starts at 16). Look for persistent index-contour labels.
2. Count visible contour **labels** (not lines). Must be **≤ 40**.
3. Zoom out below 16. Labels must disappear.
4. During the zoom animation, labels must not freeze at old pixel positions (hide on zoomstart).

**Pass if:** labels only at zoom ≥ 16, cap 40, no jump/teleport during zoom.

---

### C-30 — Collapse and re-expand Contour

**Steps:** Toggle layers (e.g. slope on). Draw nothing yet, or keep an existing result. Collapse Contour (click the module header). Expand Contour again.

**Pass if:** result, layer toggles, and any transect state are **unchanged**. Map does not duplicate contour layers.

---

### C-31 — Detail view and back

**Steps:** Enter Contour **detail** (full map + floating card). Confirm layers still there. Click **Back to overview**.

**Pass if:** no reset, no duplicate layers, panel state intact.

---

### C-32 — 3D hides contour chrome

**Steps:** Overview, Contour expanded, result on map. Click **3D**.

**Pass if:** no contour GeoJSON, no hillshade overlay, no **Map layers** control, no contour legend over the 3D scene. Click **2D** to restore them.

---

### C-33 — Map status chip

**Steps:** Click Re-run and watch the map **before** it finishes.

**Pass if:** top-left chip `Contour analysis running…`. During transect run: `Sampling transect…`. Chip gone when idle.

---

## Suite E — Transect

**P-POLY**, successful analyze, Contour expanded, Transect subsection open, **2D**.

If you still have a transect from a previous attempt, click **Clear transect** first.

### C-34 — Gated until analysis succeeds

**How to see the gated state:** on **P-POINT** (no result) the Transect subsection is not shown; the ineligible panel has no run. On **P-POLY**, if you catch the panel **before** the first analyze returns, Transect should show `Run contour analysis first — the transect samples the same terrain data.` — not a grey dead button.

If auto-run is too fast, collapse is not enough (result persists). Accept C-34 as pass if **P-POINT** has no transect tools **and** the needs-analysis string exists in the product. Prefer: cancel the first run on a **new** polygon before it succeeds, then expand Transect.

**Pass if:** gated copy is `transect.needsAnalysis`, not an inert unlabelled control.

---

### C-35 — Cost copy when enabled

**Pass if:** after a successful analyze, Transect shows `transect.cost` and `transect.instructions`.

---

### C-36 — Draw 2-point transect and run

**Steps**

1. Click **Start transect**.
2. Click two points **inside the site polygon** (not far outside).
3. Click **Finish drawing** (or press Enter).
4. Click **Run transect**. Wait (this re-fetches DEM; can take tens of seconds).

**Pass if**

- Dashed dark line with a **white casing**.
- Start: **green circle** + `Start` label.
- End: **amber/orange diamond** (rotated square) + `End` label.
- Profile SVG and a numeric summary (length, min/max elevation, relief, sample count) appear.
- Network: `POST /contour/transect`.

---

### C-37 — Start/End distinguished three ways

**Pass if:** Start vs End differ by **shape**, **colour**, and **text** on the map **and** on the graph (graph: Start left, End right).

---

### C-38 — Keyboard draw

**Steps**

1. **Clear transect**. **Start transect**.
2. Click 3 points.
3. **Backspace** — last vertex gone (`n points` caption decreases).
4. Click a replacement point. **Enter** — drawing finishes.
5. **Start transect** again, click one point, press **Escape** — draft cancelled.

**Pass if:** Enter finishes (≥ 2 points), Backspace undoes, Escape cancels.

---

### C-39 — Toolbar is real buttons

**Pass if:** `Start transect`, `Finish drawing`, `Run transect`, `Clear transect`, and `Cancel` (while running) are `<button>`s with those accessible names — not icon-only unlabelled divs.

---

### C-40 — Pointer scrub on the graph

**Steps:** Hover/drag along the elevation SVG (`aria-label` begins with `Elevation profile along the drawn transect`).

**Pass if:** a marker on the **map** tracks the pointer without obvious lag; readout (`aria-live="polite"`) shows **Distance from start**, **Elevation**, **Slope**, **Slope class**.

---

### C-41 — Keyboard scrub

**Steps:** Tab to the graph SVG (`tabIndex=0`). Press Right, Left, Shift+Right, Home, End.

**Pass if:** one sample per arrow; ten with Shift; Home = start; End = end; `aria-live` readout updates.

---

### C-42 — Redraw reversed

**Steps:** Clear. Draw two points in the **opposite** order (old End first). Run transect.

**Pass if:** graph Start/End flip; map Start circle is at the new first click; End diamond at the new last click.

---

### C-43 — Clear transect

**Steps:** Click **Clear transect**.

**Pass if:** line, Start/End, graph, summary, and readout are all gone together.

---

### C-44 — Draw-tool exclusivity (AD-18)

**Steps** (overview 2D, Contour expanded so transect overlay is mounted):

1. On `/project/new` this is easier to see with both toolbars; on the analysis page, transect mode sets the shared draw store to `"transect"`.
2. Click **Start transect**. Then try the map **polygon/rectangle** tool if it is visible on this page.
3. Each map click must belong to **exactly one** tool (either a transect vertex **or** a site polygon vertex, never both).
4. Reverse: if a site-draw tool can be armed, arm it, then **Start transect** — site drawing must yield.

DrawTools (**Pan / select**, **Rectangle**, **Polygon**) **are** mounted on `/project/{id}`. Do **not** SKIP this case. While transect is drawing, clicking Rectangle/Polygon must not steal map clicks — only transect vertices.

**Pass if:** no double-handling of a click.

---

### C-45 — Exit transect mode restores normal clicks

**Steps:** Finish or Escape out of transect drawing. Click the map.

**Pass if:** clicks no longer add transect vertices. Pan/select works.

---

### C-46 — Line readable over hillshade

**Steps:** Hillshade on. Look at the transect at zoom 15 and 17.

**Pass if:** white casing keeps the dashed line visible on both light and dark hillshade.

---

## Suite F — Errors, a11y, export, scoring

### C-47 — Backend stopped

**Steps**

1. On **P-POLY** with a result on screen, stop the uvicorn process (port 8010).
2. Click Re-run.

**Pass if:** title/detail includes `Contour service unreachable. Check that the contour backend is running.`; **previous** contours stay on the map.

Restart the backend with `FLAGS=feature.contour.analysis` before the next case.

---

### C-48 — Backend without FLAGS

**Steps**

1. Restart contour **without** `FLAGS` (or `FLAGS=` empty).
2. Re-run on **P-POLY**.

**Pass if:** `Contour analysis is not enabled in this environment.` (403 path). Restore `FLAGS=feature.contour.analysis` afterwards.

---

### C-49 — DEM / GEE 503

**Pass if:** when the service returns 503, UI title is `Terrain data could not be fetched. Check the contour backend and Earth Engine configuration.`; Re-run still available; prior result kept if there was one.

If you cannot force 503 (GEE healthy), **SKIP** with note — do not fake it in the frontend.

---

### C-50 — Transect with backend down

**Steps:** Successful analyze already on screen. Stop backend. Draw a 2-point transect, **Run transect**.

**Pass if:** mapped unreachable/dem error; **drawn line still on the map**. Restart backend after.

---

### C-51 — Transect with one point

**Steps:** Start transect, click **one** point, try **Finish drawing** (should stay disabled) and/or **Run transect**.

**Pass if:** cannot successfully run; if an error shows, it is `Draw a transect line with at least a start and end point.` Finish stays disabled while `draft.length < 2`.

---

### C-52 — Invalid interval

The UI only offers 10–60 via `<select>`. Do **not** patch production code to bypass it.

From DevTools console on the analysis page (after the contour bundle has loaded, `npm run dev` only):

```js
window.useContourStore.getState().setInterval(5)
```

**Do not SKIP.** If `window.useContourStore` is undefined, **FAIL** with note `store not on window` (the dev hook is missing). Otherwise click Re-run: the client must show `Choose a contour interval between 10m and 60m.` **before** a 422. Restore with `window.useContourStore.getState().setInterval(20)`.

---

### C-53 — Keyboard-only pass

**Steps:** Unplug from the mouse. Tab through Contour: interval → Run → (Cancel if running) → InfoTip `?` → layer switches → transect buttons → graph.

**Pass if:** every control is reachable; a visible focus ring (`focus-visible:ring`) appears; no keyboard trap.

---

### C-54 — Layer switches semantics

**Pass if:** map layer buttons have `role="switch"`, `aria-checked` true/false, and `aria-label` containing the layer name (`Hillshade`, `Contours`, `Slope classes`, `Buildability zones`).

---

### C-55 — Colour not the only cue

**Pass if:** legends include text + range; Start/End differ by shape **and** the words Start/End.

---

### C-56 — `prefers-reduced-motion`

**Steps:** In DevTools Rendering, emulate `prefers-reduced-motion: reduce`. Expand/collapse subsections and the Contour module card.

**Pass if:** those transitions do not animate (instant open/close). Map zoom animation is Leaflet-owned — do not fail the case for that.

---

### C-57 — PDF / report page content

**Steps**

1. **P-POLY** with a successful contour result.
2. Click **Export report** in the top nav.
3. Generate / preview the report (PDF or on-page preview). Find the Contour page.

**Pass if:** slope bar, DEM metadata, slope/aspect/buildability, `caveat.dsm`, `caveat.buildability`, and the verbatim `report.disclaimer` are all present.

---

### C-58 — Transect on the report

**Steps**

1. On **P-POLY**, run a 2-point transect (reuse the C-36/C-42 result if it is still on screen).
2. Open **Export report** **before** clicking **Clear transect**. (C-43 already passed on 2026-08-25 — do not re-clear first. Export reads live session `transectResult`; Clear wipes it by design.)
3. Find the Contour report visual.

**Pass if:** the profile (Start/End) appears on the Contour report visual.

---

### C-59 — Export uses the interval you ran

**Steps:** Re-run contour at **40 m**, then export (do not change the selector after the run).

**Pass if:** report/metadata interval is **40**, not hardcoded 20. Network on export, if it re-fetches, uses 40.

---

### C-60 — html2canvas / plain hex

**Pass if:** PDF generation does not throw colour-parse errors in the console. Contour report SVG uses hex fills (no `oklch` / CSS variables in that visual). If PDF succeeds, this case passes.

---

### C-61 — Point project export skips contour

**Steps:** Export **P-POINT**.

**Pass if:** there is **no** Contour results page claiming a score of 0; site score is not averaging in a fake contour zero.

---

### C-62 — Backend without WP-0 fields

Only if you can run an older contour service that omits `hillshade_bounds` and transect `lat`/`lng`.

**Pass if:** hillshade still draws from polygon bbox; legend shows the ~30 m offset caption; graph still scrubs; caption `Marker position is interpolated along the drawn line; start and end are exact.` is visible.

Otherwise **SKIP**.

---

### C-63 — Fixtures mode

**Steps:** Stop relying on GEE. Restart `apps/web` with `NEXT_PUBLIC_CONTOUR_FIXTURES=1`. Open **P-POLY**.

**Pass if:** analyze “succeeds” quickly with placeholder DEM stats (e.g. mean slope 8.4%); no live GEE requirement. Contour GeoJSON may be empty — that is expected for the fixture. Restore env after this case.

---

### C-64 — D-12 site score (point vs no-contour)

**Steps**

1. Note **P-POINT** overall score (Contour was in `modules_run` but ineligible).
2. Create **P-POINT-NC**: same pin, **same other modules**, Contour **deselected**.
3. Compare overall scores (allow small drift if other services are live/non-deterministic — the test is that P-POINT is **not** ~0 or clearly lower **because** contour scored 0).

**Pass if:** including Contour on a point project does **not** inject a contour score of 0 into the average. Progress total on P-POINT should drop contour from the denominator (see C-65).

---

### C-65 — Module progress has no stuck Contour slot

**Steps:** On **P-POINT**, read `N of M modules` / `N / M modules complete`.

**Pass if:** M does **not** count an extra Contour module that can never complete. The Contour accordion may still list, but it should not stay `loading` forever (`loading` is forced false when ineligible). No permanent incomplete Contour chip.

---

## 6. Execution order (minimize setup)

For a **first** full run, A→G as written in the suites. For **pass 3** (former FAIL / BLOCKED / SKIP), use the order in **§0.1**. Do not restart at C-01.

```
§1 start services → login
§3 reuse P-POLY, P-POINT, P-SMALL (recreate if missing)
P-POLY 2D, Contour expanded:
  C-16
  C-23, C-24, C-26, C-28, C-29, C-30, C-31
  C-38, C-40, C-41, C-42
  C-58   ← transect still on screen; export BEFORE clear
  C-44, C-45
  C-50   (backend down)
  C-52   (window.useContourStore.setInterval(5))
  C-53, C-56, C-59, C-60
C-63 fixtures restart (required)
C-49, C-62  (allowed SKIP only with the notes in §0.1)
PASS (re-QA 08-25) rows: skip unless a PENDING case on that screen fails
```

---

## 7. Stop / blocked conditions

Stop the playbook and report if:

- Login fails
- `localhost:3000` or `localhost:8010` is down and you cannot start them
- Every analyze returns 403 even with FLAGS set (env not reaching uvicorn)
- The right panel has no **Contour** row (module not in `modules_run` — recreate the project with Contour selected)

Do not “fix” eligibility by converting a point to a polygon in the database.

---

## 8. Results log

**Status: PASS 3 COMPLETE (2026-08-25)** — All former `PENDING` rows filled from pass-3 browser run. **SAT-19 not done:** C-28, C-29, C-30, C-53 are FAIL/BLOCKED (see evidence).

Previous sessions: partial PASS 16 / FAIL 14 / SKIP 35 → re-QA 2026-08-25 PASS 42 / FAIL 1 (C-58 test-order) / BLOCKED 18 / SKIP 4. QA-001 / QA-002 / QA-003 confirmed fixed. QA-004 closed as test-order. QA-005 (C-56 chevron) fixed in product.

| ID | Result | Prior (08-25) | Evidence (1 line) |
|---|---|---|---|
| C-01 | PASS (re-QA 08-25) | PASS | P-POLY auto-run 20 m, `Re-run at 20 m`, polygon detected, hillshade+contours on |
| C-02 | PASS (re-QA 08-25) | PASS | P-POINT `proj-1787630349481`: `eligibility.point` verbatim, buffer circle, no Run, 0 analyze |
| C-03 | PASS (re-QA 08-25) | PASS | Same as C-02; disabled for Point GeoJSON not buffer visibility |
| C-04 | PASS (re-QA 08-25) | PASS | P-SMALL `proj-1787630890263` 0.14 ha: too-small copy both strings, no Run, 0 analyze |
| C-05 | PASS (re-QA 08-25) | PASS | DSM `caveat.dsm` visible on P-POLY and P-POINT with Contour expanded |
| C-06 | PASS (re-QA 08-25) | PASS | Session caveat on P-POLY (eligible) and P-POINT (ineligible) |
| C-07 | PASS (re-QA 08-25) | PASS | `Re-run at {n} m` after a result exists |
| C-08 | PASS (re-QA 08-25) | PASS | 10 m warning + DEM interval 10 m |
| C-09 | PASS (re-QA 08-25) | PASS | Stale caption when selector ≠ result interval |
| C-10 | PASS (re-QA 08-25) | PASS | Re-run 40 m replaces 20 m lines |
| C-11 | PASS (re-QA 08-25) | PASS | Double Re-run at 20 m → `fetch` hook saw 1 `/contour/analyze` only |
| C-12 | PASS (re-QA 08-25) | PASS | Re-run at 30 m cancelled; `role="status"` + prior 20 m kept (QA-003 closed) |
| C-13 | PASS (re-QA 08-25) | PASS | Zero `/health` or `/contour/health` |
| C-14 | PASS (re-QA 08-25) | PASS | DEM Source `Copernicus DEM GLO-30 2024` |
| C-15 | PASS (re-QA 08-25) | PASS | Eight slope stat tiles with `%` |
| C-16 | PASS | PASS (incomplete) | Mean+Hazard `?`: click toggles `role="tooltip"`; `.focus()` opens; Escape closes; `aria-expanded` tracks open state |
| C-17 | PASS (re-QA 08-25) | PASS | Stacked bar `aria-label` starts `Slope class share:` |
| C-18 | PASS (re-QA 08-25) | PASS | Aspect NW 293°, N/S %; no buildability suitability claim in aspect copy |
| C-19 | PASS (re-QA 08-25) | PASS | `caveat.buildability` while Buildability collapsed |
| C-20 | PASS (re-QA 08-25) | PASS | Default subsection `aria-expanded` |
| C-21 | PASS (re-QA 08-25) | PASS | Panel Slope classes toggle synced map `aria-checked` both true |
| C-22 | PASS (re-QA 08-25) | PASS | Hillshade+Contours on; Slope+Buildability off |
| C-23 | PASS | BLOCKED | Hillshade pane + site polygon visible under contour stack; basemap shows through hillshade opacity |
| C-24 | PASS | BLOCKED | `setLayers` all-off then solo hillshade/contours/slope/buildability — map `aria-checked` matches each |
| C-25 | PASS (re-QA 08-25) | PASS | Lockstep reconfirmed via C-21 after slope toggle |
| C-26 | PASS | BLOCKED | Legend Hillshade opacity caption; slope rows Flat/Gentle/Moderate with text; contour interval when contours on |
| C-27 | PASS (re-QA 08-25) | PASS | ~30 m offset caption absent when bounds present |
| C-28 | BLOCKED | BLOCKED | Near-flat site (mean 0.3%): 0 contour line features in result — no path to hover for `{n} m` tooltip |
| C-29 | BLOCKED | BLOCKED | 0 index labels at zoom 16 on flat site; zoom cap ≤40 and hide-on-zoomstart not exercisable |
| C-30 | FAIL | BLOCKED | Contour module header click did not set `aria-expanded=false`; slope toggle state did persist |
| C-31 | PASS | BLOCKED | Full detail → map layers present; Back to overview restores panel without duplicate layers |
| C-32 | PASS (re-QA 08-25) | PASS | 3D: 0 map `role="switch"` in `.leaflet-top`; legend chrome off map |
| C-33 | PASS (re-QA 08-25) | PASS | Map chip / busy during re-run |
| C-34 | PASS (re-QA 08-25) | PASS | P-POINT: no Start transect; transect subsection absent when ineligible |
| C-35 | PASS (re-QA 08-25) | PASS | `transect.cost` and `transect.instructions` |
| C-36 | PASS (re-QA 08-25) | PASS | 2-point transect on P-POLY: no crash, Start/End markers, profile 211 samples |
| C-37 | PASS (re-QA 08-25) | PASS | Start/End differ by shape+label on map; graph SVG present |
| C-38 | PASS | BLOCKED | 3pts→Backspace→2→finish; Escape with 1 draft pt → idle/0 pts (keyboard) |
| C-39 | PASS (re-QA 08-25) | PASS | Toolbar buttons labeled; Finish drawing accessible name |
| C-40 | PASS | BLOCKED | SVG mousemove → `aria-live` Distance/Elevation/Slope/Slope class updates |
| C-41 | PASS | BLOCKED | Home=0, ArrowRight=1, Shift+ArrowRight=11, End=13 on profile SVG |
| C-42 | PASS | BLOCKED | Reversed click order → `transectSubmitted` Start/End flip |
| C-43 | PASS (re-QA 08-25) | PASS | Clear transect removed line, Start/End, graph; Run disabled. **Do not re-run before C-58.** |
| C-44 | PASS | BLOCKED | Rectangle tool click did not add transect vertex while transect drawing; transect clicks add vertices only |
| C-45 | PASS | BLOCKED | After Escape: status idle; map click does not grow `transectDraft` |
| C-46 | PASS (re-QA 08-25) | PASS | Dashed transect line + Start/End visible over hillshade during C-36 |
| C-47 | PASS (re-QA 08-25) | PASS | Backend stopped → unreachable copy; prior contours remained on map |
| C-48 | PASS (re-QA 08-25) | PASS | Backend without FLAGS → `Contour analysis is not enabled in this environment.` |
| C-49 | SKIP | SKIP | GEE healthy; cannot force 503 without faking frontend |
| C-50 | PASS | BLOCKED | Port 8010 stopped → `POST /contour/transect` failed unreachable copy; 2-pt `transectSubmitted` retained |
| C-51 | PASS (re-QA 08-25) | PASS | One-point draft: Finish drawing stayed disabled |
| C-52 | PASS | SKIP | `window.useContourStore.getState().setInterval(5)` → `Choose a contour interval between 10m and 60m.` before fetch; restored 20 |
| C-53 | BLOCKED | BLOCKED | Full unplugged keyboard-only tab pass not executed (39 focusables present; not verified end-to-end) |
| C-54 | PASS (re-QA 08-25) | PASS | Map switches: `role="switch"` + `aria-label` |
| C-55 | PASS (re-QA 08-25) | PASS | Map Start/End labels during transect; legend has text+interval |
| C-56 | PASS | BLOCKED | Emulated `prefers-reduced-motion: reduce` → DEM subsection `transition-duration: 0s`; chevron has `motion-safe` |
| C-57 | PASS (re-QA 08-25) | PASS | Export preview: slope bar, DEM, `caveat.dsm`, buildability caveat, disclaimer |
| C-58 | PASS | FAIL | Client-side Export with live `transectResult`; Contour preview shows Start/End (QA-004 test-order avoided) |
| C-59 | PASS | BLOCKED | Re-run 40 m → `resultInterval` 40; export preview `40 m interval` |
| C-60 | PASS | BLOCKED | Download PDF clicked; no `oklch` in contour report SVGs; no colour-parse console errors |
| C-61 | PASS (re-QA 08-25) | PASS | P-POINT export: site score —, no Contour results page with score 0 |
| C-62 | SKIP | SKIP | No legacy pre-WP-0 contour backend available |
| C-63 | PASS | SKIP | `NEXT_PUBLIC_CONTOUR_FIXTURES=1` restart → analyze fast; mean slope 8.4% fixture; env restored after |
| C-64 | PASS (re-QA 08-25) | PASS | P-POINT score — / 0 of 0 modules; no contour 0 in average |
| C-65 | PASS (re-QA 08-25) | PASS | P-POINT `0 / 0 modules complete`; Contour accordion `—` not loading |

**Counts (pass 3 — 2026-08-25):** PASS 20 / FAIL 1 (C-30) / BLOCKED 4 (C-28, C-29, C-53) / SKIP 2 (C-49, C-62) / PASS (re-QA 08-25 retained) 41.

**Environment notes:** `FLAGS=feature.contour.analysis`, `NEXT_PUBLIC_CONTOUR_API_URL=http://localhost:8010`, `NEXT_PUBLIC_CONTOUR_FIXTURES` unset for A–F (set only for C-63, restored after), live GEE (`gee-sa.json` + service account email).

**Fixtures (pass 3):** P-POLY recreated `proj-1787657113856` (`QA contour poly Bellandur`, 16.14 ha, Bellandur). Prior §8 session IDs stale in new browser tab.

**Closed blockers (do not re-open unless a PENDING case fails):**

1. SAT-19-QA-001 — point + Contour-only skeleton — confirmed 2026-08-25.
2. SAT-19-QA-002 — transect overlay crash — confirmed 2026-08-25.
3. SAT-19-QA-003 — C-12 cancel timing — PASS 2026-08-25.
4. SAT-19-QA-004 — C-58 export after Clear — test-order; re-run C-58 before Clear.
5. SAT-19-QA-005 — C-56 subsection chevron ignored `prefers-reduced-motion` — product fix landed; confirm on this pass.
