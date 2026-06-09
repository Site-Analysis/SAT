# Phase 1 — Research Findings (COMPLETE)
# SAT UX Research — 2026-06-09/10

## Status

Phase 1 is **COMPLETE and APPROVED** as of 2026-06-10.
All artifacts at: `/Volumes/LocalDrive/SAT/ux-research/phase-1/`
GitHub Issue: https://github.com/Site-Analysis/SAT/issues/13

---

## Participants

| # | Name | Role | Type | Status |
|---|------|------|------|--------|
| P01 | Rubina | Junior Architect — intern, international firm (USA commercial interior) | Real | ✅ Approved |
| P02 | Ranjita | Junior Architect — intern, Architecture Dialogue, Bangalore | Real | ✅ Approved |
| P03 | Synthetic | Senior Architect Studio Lead (5–12 yrs) | SME-derived | ✅ SME Approved |
| P04 | Synthetic | Senior Principal / Director (12+ yrs) | SME-derived | ✅ SME Approved |
| P05 | Synthetic | Urban Planner / M.Arch Student | SME-derived | ✅ SME Approved |

**Outstanding:** SA·Q3 (client presentation workflow) + SP·Q3 (massing/orientation decisions)
follow-up from SME — pending 2026-06-11. Will be added to synthetic profiles doc.

---

## Confirmed tool landscape

### Student / Junior Architect tools
| Tool | Use | Notes |
|------|-----|-------|
| SketchUp (2026, paid plugins) | 3D modelling, sun path plugin | Paid tier needed for analysis plugins |
| Ventrysky | Wind analysis | Confirmed spelling — not "Wint-O-Sky" |
| Shadow Map | Shadow simulation | |
| QGIS | GIS analysis | Used by urban-planning-track students |
| Climate Consultant | Climate data analysis | UCLA tool |
| Andrew Marsh software | Sun + climate analysis | Confirmed — Andrew Marsh (not a firm name) |
| Rhino + Grasshopper | Parametric, AI-assisted Python scripts | |

### Firm tools (SME-derived, Senior+)
| Tool | Use |
|------|-----|
| Google Earth Pro | Site context, massing study |
| Mapbox | Custom map styling |
| OpenStreetMap | Base data |
| Revit | BIM — non-negotiable for senior-level export |

### Data portals (confirmed by participants)
| Portal | Data type | Notes |
|--------|-----------|-------|
| KSRSAC (https://ksrsac.karnataka.gov.in/) | Hydrology, soil, topography | Karnataka state portal; P01 showed overlap on screen |
| Bhuvan / ISRO | Soil maps | Requires professor access credential in some institutions |
| IMD (India Meteorological Dept.) | Official climate data | Considered authoritative |
| Google (general search) | Taluka-level soil maps | Last resort; quality variable |

---

## Confirmed pain points (ranked by frequency)

### 1. No one-stop data source [BLOCKER — all participants]
- "20 maps for one district" for hydrology data alone (P01 — Rubina)
- Data scattered across Google, KSRSAC, Bhuvan, IMD, state portals
- 43 students, 4 approved site analyses — all 4 different for same site

### 2. Stale / unverifiable data [MAJOR FRICTION — P01, P02, P03, P05]
- Websites say "updated" but data is months/years stale
- P02 (Ranjita): galvanized steel rusted at Hyderabad area site → double labor cost
  because climate/humidity data was wrong/missing
- No single authoritative source feels trustworthy

### 3. Manual representation [MAJOR FRICTION — P01, P02]
- Graphical sheets, photographs, hand-sketches all manual even after data is collected
- P02 did morning/afternoon/evening timeline mapping — 9 site visits to Mandya for thesis
- No automated output format acceptable for submission/presentation

### 4. Topography/contour data gap [MAJOR FRICTION — P01, P05]
- India lacks proper digital contour documentation
- Manual site team measurements are the MOST RELIABLE source
- P01 quote: "manual levels 1000× better than digital in India"

### 5. Tool-switching friction [MAJOR FRICTION — all]
- No tool does everything → 4–6 tools minimum per analysis
- No export format that connects analysis → BIM
- P01: "Revit can have SAT as a plugin" — this is the senior-level integration need

---

## Key verbatim quotes

> "20 maps for one district"
> — P01 Rubina, on hydrology data collection

> "Manual levels 1000× better than digital in India"
> — P01 Rubina, on topographic accuracy

> "Revit can have SAT as a plugin"
> — P01 Rubina, on integration

> "Me interacting with the website would be much better"
> — P02 Ranjita, on wanting a conversational AI interface

> "[the steel] rusted ... double labor cost"
> — P02 Ranjita, on real consequence of missing humidity/climate data

---

## Dashboard desires (confirmed)

**P01 Rubina's dashboard layout:**
- Section 1: Topography
- Section 2: Climate (rainfall as separate tab)
- Section 3: Regulations
- Persistent — always accessible, not buried

**P02 Ranjita's flow:**
1. Search → enter lat/lon or district name
2. Results tabs: Sunpath | Wind | Rainfall | Regulations
3. AI sounding board for compliance questions
4. Auto-generate report

---

## Product signals confirmed

| Signal | Evidence | Priority |
|--------|----------|----------|
| Revit export non-negotiable | P01 quote + SME P04 | Must-have for enterprise sales |
| Conversational UI / AI assistant | P02 quote "me interacting with website" | Differentiator |
| Pipeline position: between brief and BIM | SME observation | Positioning |
| RAG for static / live API for dynamic | SME technical architecture suggestion | Architecture |
| Professional survey service model | SME: "firms without site visit capacity would pay" | Revenue stream |
| North star metric | TBD — SME to advise | Outstanding |

---

## SME observations (product strategy)

- **Architecture:** RAG for static data (cultural context, long-run climate patterns); live API for dynamic (real-time flood, recent construction updates)
- **Business model:** Professional service model viable — firms without on-ground capacity would pay for SAT-powered survey service
- **Pipeline position:** Between brief and BIM — not a BIM replacement, not a GIS tool
- **Export:** Revit export is non-negotiable for adoption at senior/principal level
- **Org data ingest:** Senior principals want to bring their own project data into SAT (P04 blocker)
- **Adoption blockers (P04):** Revit fit, standard file export, team usability, data credibility, licensing

---

## Design implications for Phase 2+

1. **Information architecture:** Topography | Climate (Rainfall sub-tab) | Regulations — matches P01's mental model, aligned with P02's tab-based flow
2. **Search entry:** Lat/lon + district name + map pin — multiple entry points confirmed
3. **Report export:** Must be present before Beta; auto-generate is table-stakes
4. **AI / conversational layer:** High demand — plan as Phase 5+ feature (not MVP)
5. **Revit export:** Phase 5+ or dedicated integration track
6. **Offline/degraded mode:** Topography data fallback — document clearly when digital data is less reliable than manual survey

---

## Outstanding items

- [ ] SA·Q3 (Senior Architect — client presentation workflow) — SME follow-up due 2026-06-11
- [ ] SP·Q3 (Senior Principal — massing/orientation decision flow) — SME follow-up due 2026-06-11
- [ ] North star metric — SME to advise
- [ ] Phase 2: Synthesis & Analysis begins next (Steps 7–10)
