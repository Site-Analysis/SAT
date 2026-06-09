# SAT UX Research Repository — Phase 1
# Step 6 — Research Repository Index

## Participant index

| # | Participant | Role | Type | Date | Transcript | Status |
|---|---|---|---|---|---|---|
| P01 | Rubina | Junior Architect — intern, international firm (USA commercial stores) | Real | 2026-06-09 | [P01-rubina-junior-architect-2026-06-09.md](transcripts/P01-rubina-junior-architect-2026-06-09.md) | ✅ Approved |
| P02 | Ranjita | Junior Architect — intern, Architecture Dialogue, Bangalore | Real | 2026-06-09 | [P02-ranjita-junior-architect-2026-06-09.md](transcripts/P02-ranjita-junior-architect-2026-06-09.md) | ✅ Approved |
| P03 | Synthetic | Senior Architect Studio Lead (5–12 yrs) | Synthetic — SME-derived | 2026-06-09 | [SME-derived-profiles-2026-06-09.md](synthetic/SME-derived-profiles-2026-06-09.md) | ✅ SME Approved (SA·Q3 follow-up pending 2026-06-11) |
| P04 | Synthetic | Senior Principal / Director (12+ yrs) | Synthetic — SME-derived | 2026-06-09 | [SME-derived-profiles-2026-06-09.md](synthetic/SME-derived-profiles-2026-06-09.md) | ✅ SME Approved (SP·Q3 follow-up pending 2026-06-11) |
| P05 | Synthetic | Urban Planner / M.Arch Student | Synthetic — SME-derived | 2026-06-09 | [SME-derived-profiles-2026-06-09.md](synthetic/SME-derived-profiles-2026-06-09.md) | ✅ SME Approved |

**Total participants:** 5 (2 real, 3 synthetic SME-derived)
**Interview guide version:** 1.0 — 2026-06-10
**Real interviews conducted:** 2026-06-09 (joint session, ~1h 49min)

---

## File index

| File | Description |
|---|---|
| `step-1-participant-profiles.md` | Participant screening criteria, profile definitions, enrollment status |
| `step-2-interview-guide.md` | Interview guide — 5 sections, 45–60 min, 5 SAT-priority flags |
| `transcripts/P01-rubina-junior-architect-2026-06-09.md` | Verbatim transcript P01, approved |
| `transcripts/P02-ranjita-junior-architect-2026-06-09.md` | Verbatim transcript P02, approved |
| `synthetic/SME-derived-profiles-2026-06-09.md` | SME-derived profile notes for P03–P05; includes product strategy observations |
| `interview-form.html` | Web interview form (also live at chiraghontec.github.io/UX-Interview) |

---

## Key findings summary (Phase 1)

### Top pain points — confirmed across both real participants
1. **No one-stop data source** — 20+ maps per district for hydrology alone (Rubina); data scattered across Google, KSRSAC, Bhuvan, IMD, state portals
2. **Real-time data missing** — websites say "updated" but data is stale; material errors traced directly to this (Ranjita: galvanized steel rusted in humid Hyderabad site → double labor cost)
3. **Data legitimacy unknown** — 43 students, 4 approved site analyses, all 4 different for the same site; no authoritative single source
4. **Representation is manual** — graphical sheets, photographs, sketches all done by hand even after data is collected
5. **Topography/contours most error-prone** — India lacks proper digital contour documentation; manual site team measurements are the most reliable source

### Tool landscape
- **Students/juniors:** SketchUp (paid plugins 2026), Ventrysky, Shadow Map, QGIS, Climate Consultant, Andrew Marsh software, Rhino+Grasshopper (AI-assisted Python)
- **Firms:** Google Earth Pro, Mapbox, OpenStreetMap, Revit (P01: "Revit can have SAT as a plugin")
- **Data portals:** KSRSAC (Karnataka hydrology), Bhuvan/ISRO (soil, via professor access), IMD (official climate), government taluka soil maps (via Google search)

### Product signals
- **Revit export non-negotiable** for senior-level sales conversations
- **Conversational UI / AI assistant** explicitly requested by P02: "me interacting with the website would be much better"
- **Pipeline position:** Between brief and BIM — not a BIM replacement
- **RAG architecture:** Static data (cultural context, long-run climate patterns) via RAG; dynamic data (real-time flood, recent construction) via live API
- **Professional service model viable:** Firms without site visit capacity would pay for a SAT-powered on-ground survey service

---

## Phase 1 completion checklist

- [x] ≥5 participant profiles approved (Step 1) — 2026-06-10
- [x] Interview guide approved (Step 2) — 2026-06-10
- [x] ≥5 participants recruited and confirmed (Step 3) — retroactive, 2026-06-10
- [x] All interviews conducted and recordings confirmed (Step 4) — 2026-06-09
- [x] All real transcripts approved (Step 5) — 2026-06-10
- [ ] SA·Q3 + SP·Q3 follow-up from SME — pending 2026-06-11
- [x] GitHub Issue created in SAT monorepo — https://github.com/Site-Analysis/SAT/issues/13

---

## Document status

| Field | Value |
|---|---|
| Created | 2026-06-10 |
| Phase gate | ✅ APPROVED — Chirag, 2026-06-10 |
| GitHub Issue | https://github.com/Site-Analysis/SAT/issues/13 |
| PO approval | ✅ APPROVE PHASE 1 — Chirag, 2026-06-10 |
| Outstanding | SA·Q3 + SP·Q3 SME follow-up — pending 2026-06-11, to be added to synthetic/SME-derived-profiles-2026-06-09.md |
