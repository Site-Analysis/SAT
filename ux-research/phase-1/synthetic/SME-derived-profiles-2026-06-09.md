# SME-Derived Synthetic Profile Notes — 2026-06-09
Status: PENDING SME APPROVAL

**Source:** Joint interview session transcript (transcript.txt / SME_s_Interview.srt)
**SME present:** Unnamed advisor/founder, referred to as "sir" throughout session
**Additional SME present:** "Tanmay" (minor contribution)
**Note:** SME-specific profile questions (SA·Q1-6, SP·Q1-5, UP·Q1-6 from sme-questions.txt) were NOT directly posed in this session. Profile data below is derived from:
1. SME advisor's product commentary and strategic observations during the junior architect interview
2. Junior architects' first-hand descriptions of how senior architects and firms operate
3. Cross-referencing sme-questions.txt framework

All three profiles are labelled `[SYNTHETIC — SME-derived]`.

---

## Profile P3 — Senior Architect (Studio Lead, 5–12 yrs) [SYNTHETIC — SME-derived]

### Source evidence from session

**Ranjita on how senior architects work at Architecture Dialogue:**
> "Principal architects were two of them who knew about the site so that was the pre-study we could consider... it's only wherein the main architects do a bit of site analysis. You know, first we do a model run analysis from SketchUp model. And then we come up to conclusions from where our design process starts."

**Ranjita on site team + principal workflow:**
> "We have a site team specifically at the site and they give us all this data like about the soil and um even about the legal notes so they have contacts with the um lawyer or the legal team with the government like whoever are there and it like it happens all very you know from the site team we get the data and it comes to the principal architect and they let us know like these are the laws and these things we'll be following."

**SME on organizational data problems:**
> "Even so the entire context here is even though enterprises or architectural firms have premium data sources access available to them the data is still outdated... even when they go get the data online even after that when they do offline site visit the patterns are very different."

**Ranjita's Hyderabad example (galvanized steel rusting):**
> "In case this analysis would have been done prior properly according to the climate we would have got a list of materials we could use according to that climate which was missing right."

### Derived profile

**Role:** Senior Architect / Studio Lead at a mid-size Indian firm (Tier 1/2 city)
**Experience:** 5–12 years; managing 3–8 person project teams

**Day-to-day site analysis:**
- Receives project brief and defines scope of site analysis required
- Delegates physical site survey to site engineers + juniors; personally does digital pre-study
- Reviews and approves site analysis outputs from team
- Does SketchUp model-run analysis as primary analysis tool
- Has access to firm's historical project data for same geographies; uses as shortcuts

**Tools:**
- SketchUp (2026 paid version with plugins for sun/shadow/wind)
- Revit (for BIM pipeline; aware of site analysis plugins)
- Google Earth Pro (paid, firm account)
- Mapbox, OpenStreetMap
- Internal firm data repositories (previous project data, known contacts)

**Data sources:**
- Government contacts via site team (bypasses public portal chaos)
- Paid versions of tools + premium APIs where available
- Historical project data from same region
- Still encounters gaps: real-time data unavailable; land use history unknown

**Key gap (SA·Q4):**
- No tool that aggregates climate + soil + topography + regulations in one place
- Data from previous projects becomes stale within 2 years due to India's development speed
- Material specification decisions made without real-time climate data → rework costs (galvanized steel example)
- Presentation of site analysis to clients requires manual graphical work even after analysis is done

**Dashboard (SA·Q5):**
Likely: Climate overview + topography + regulations + material recommendations linked to climate data. Wants team members to see same dashboard so everyone works from same data source.

**Ideal tool (SA·Q6):**
A tool that fits between brief receipt and BIM — aggregates all site data automatically, flags material risks for climate zone, generates client-ready presentation output. Must export to Revit-compatible formats (critical for workflow).

**Regulatory handling:**
- Firm has established legal contacts and site team for regulatory procurement
- Still navigates DCR/NBC manually for new geographies
- Panchayat rules for small towns not digitized — pure relationship/manual

---

## Profile P4 — Senior Principal / Director (12+ yrs) [SYNTHETIC — SME-derived]

### Source evidence from session

**SME on tool adoption criteria:**
> "We cannot build 100 full proof on their own see because these people have been working for some time and they are coming across these scenarios and when we go and give a pitch they will ask this because they will immediately bring this scenario and then we will say currently we don't support it."

**SME on positioning strategy:**
> "I'm thinking of this tool as an inevitable part in the pipeline yeah overall architecture pipeline right between the time the people are architects are assigned or to do the site planning to the BIM in between the entire thing — can we position ourselves as a very inevitable kind of tool?"

**SME on org data strategy:**
> "We may approach some clients whom they might have gathered some data yes which is reasonably static over time yeah we don't know whatever and they may be there that may be their strengths. How do we help them our product help them to use that data and onboard that also into our database?"

**SME on professional service model:**
> "What if we have a team of experts who go conduct very detailed study of site. They do the site visit for the organization and we can offer that as a service. Professional service right? Use the tool and give a professional service. There are two parts. One is IP and the other one is professional service."

**Rubina on organizational approval:**
> "If they do have like good connections in the government run office, I think then it would be super easy for them to... because they are an established organization. So if that trust is there between the state government office and the organization then I think it's very easy for them to procure."

### Derived profile

**Role:** Principal Architect / Design Director at Tier 1/2 firm; oversees multiple concurrent projects
**Experience:** 12+ years; strategic business and quality decisions

**Site analysis oversight:**
- Does NOT do site analysis directly — reviews and signs off
- Establishes firm's site analysis standards and QC criteria
- Asks juniors/seniors: "what does the data tell us about massing/orientation?"
- Steps in when data is contradictory or when project risk is high

**Most common QC issues (SP·Q2):**
- Contour accuracy errors (from unreliable digital sources)
- Missing local regulations for non-home geographies
- Outdated material recommendations not tied to current climate data
- Inconsistent data sources across team members (e.g., four different wind readings for same site)

**Tool adoption blockers (SP·Q4):**
- Must fit into existing Revit/SketchUp workflow — no parallel pipeline
- Must export standard formats (IFC, DWG, etc.) — non-negotiable
- Team adoption: tool must be usable by juniors, not just seniors
- Data credibility: must be able to cite authoritative sources to clients and regulatory bodies
- Price: firm-level licensing model preferred over per-seat

**Strategic question:**
> "How do we hook them into our tool? We should cater to their strengths. How do we position ourselves as the inevitable one?"

**What would make them adopt SAT (derived from SME commentary):**
1. SAT ingests their existing project data repository → shows value immediately
2. SAT fills data gaps that their current process misses (real-time climate, flood, soil)
3. SAT generates client-ready presentation output → saves junior hours
4. SAT exports Revit-compatible files → fits their BIM pipeline
5. Professional service option: SAT team does site visits → useful for geographies firm doesn't know

**Ideal tool (SP·Q5):**
Organizational data layer: firm uploads its site data repository; SAT normalizes, vectorizes, augments with real-time sources, surfaces gaps. Every new project starts with "here's what we know + here's what's changed." Auto-generates site analysis report stub that team refines.

---

## Profile P5 — Urban Planner / M.Arch Student [SYNTHETIC — SME-derived]

### Source evidence from session

**Rubina (screen-share, soil/hydrology map workflow):**
> "We were doing an urban project and that was supposed to be um tied to another firm and it was supposed to be in real time... we overlapped our site map with this entire map uh scaled it down to how much ever it would fit in this entire map and then cropped out a smaller piece of it and then try to you know uh match it up with the legend over here."

**Rubina on data legitimacy:**
> "There is no collective... they all do go together and we cannot look at them as individual entities."

**Ranjita on pre-study for her Mandya thesis:**
> "Including the data on zoning and buildings and other impacts on the project. And next would be the zoning and the size of my particular site. That is considering the dimensions of it, such as the boundaries and the easements. Height restrictions and the site area. And access along with any future plans."

**Ranjita's workflow for large-scale study:**
> "So all that analysis and actually many more. Because when we go to the site we keep on getting many other thoughts... street patterns we have to figure out street sections we have to figure out the scale uh the hierarchy and the land views typologies um neighborhood relationships um and even like edge conditions surfaces materials natural and man-made features movement and circulation."

**SME on data types:**
> "We might have to identify what is static data and what is dynamic... when we take rainfall should be the time like the millimeters that we might turn static but the intensity might change even though."

### Derived profile

**Role:** Urban Planner or M.Arch student (final year) working on district/neighbourhood-scale projects in India
**Scale:** Works at 1:500 to 1:20,000 — larger than building plot; overlapping jurisdictions

**Geospatial data reliance (UP·Q1):**
- QGIS as primary desktop tool
- Bhuvan (ISRO) for soil/terrain — access often professor-mediated, not direct
- Survey of India topos — historical, often years out of date
- OpenStreetMap for base maps and road hierarchy
- State portals (e.g., KSRC for Karnataka hydrology) — extremely fragmented
- IMD for climate — CSV/raw files, not architect-friendly
- Missing/unreliable: real-time flood zone updates, CGWB groundwater (not easily queryable), land-use change data between Census cycles

**Zoning + FSI workflow (UP·Q2):**
- FSI calculated from local DCR documents (PDF, not machine-readable)
- Zoning overlays manually digitized or sourced from UDD/planning authority
- Land-use compatibility checked against town planning scheme — available in govt offices or via connections
- No single portal — "break the code" to find each document

**Environmental analysis (UP·Q3):**
- Flood zones: no single authoritative source; use state hydrology portal + manual overlay (as shown by Rubina)
- Heat islands: not explicitly tracked with tools — inferred from built density + surface material observations
- Wind corridors: Wint-O-Sky / Weather Sky for prevailing wind data; no urban-scale corridor mapping
- Tools: QGIS + Rhino/Grasshopper combo for parametric environmental analysis

**Key gap (UP·Q4):**
- No tool that: resolves multi-layer map overlaps automatically, provides FSI/DCR from a single query, gives real-time flood + groundwater data, and outputs client-ready maps
- Manual map-overlay process (overlap, scale, crop, legend-match) is the single biggest time sink

**Dashboard (UP·Q5):**
Search → location → auto-generate: base map + zoning overlay + FSI summary + flood zone + climate summary. Ability to upload own layer (e.g., site boundary) and have SAT calculate FSI, setbacks, environmental constraints in one step.

**Ideal tool (UP·Q6):**
One tool that resolves "which taluk am I in, which hydrology map applies, which DCR governs, what is the FSI here" from a single location input — with authoritative source citations so planner can present to review board.

---

## SME Observer Notes — Product Strategy

The following insights came from the SME advisor's commentary (not mapped to participant profiles but relevant for Phase 2):

1. **Expert-sourced data model:** SAT should allow authorized architects/experts to feed in manual site observations → credibility-weighted crowd-sourced data layer over time.

2. **RAG architecture decision:** Static data (cultural context, historical climate patterns) → RAG. Dynamic data (real-time rainfall intensity, recent construction activity) → live API. Must identify per-data-type which applies.

3. **Professional service adjacent to IP:** SAT tool + SAT team conducting site visits as a service — useful for firms without site visit capacity or unfamiliar geographies.

4. **Pipeline positioning is the adoption argument:** "Between brief receipt and BIM" is the slot. Not a standalone tool — an inevitable step. Every pitch should answer: "where do you currently get your site data? SAT replaces that step."

5. **North star metric question raised:** "We have to figure out our north star metric after this — there are a lot of problems existing in this domain but we have to stay aligned towards what we can do."

6. **Revit export non-negotiable for senior-level sales:** Multiple senior architect users will ask about Revit compatibility in first meeting. Must have an answer.

---

## Gap vs. SME questions file

SME questions file (`/Volumes/LocalDrive/SAT/ux-research/sme-questions.txt`) covers SA·Q1-6, SP·Q1-5, UP·Q1-6. Session coverage:

| Question | Covered in session? | Source |
|---|---|---|
| SA·Q1 (process day-to-day) | Partially | Ranjita describing Architecture Dialogue workflow |
| SA·Q2 (regulatory extra work) | Partially | Rubina/Ranjita on NBC + DCR friction |
| SA·Q3 (presenting to clients) | Not covered | Need follow-up |
| SA·Q4 (tool gap) | Partially | SME + junior architect observations |
| SA·Q5 (dashboard) | Inferred | From junior architect dashboard answers |
| SA·Q6 (ideal tool) | Partially | SME strategic commentary |
| SP·Q1 (oversight process) | Not directly | Inferred from team structure described by Ranjita |
| SP·Q2 (common QC issues) | Partially | Contour/wind data inconsistency examples |
| SP·Q3 (strategic decisions) | Not covered | Need follow-up |
| SP·Q4 (adoption blockers) | Good coverage | SME advisory commentary |
| SP·Q5 (ideal tool) | Good coverage | SME strategic commentary |
| UP·Q1 (geospatial sources) | Partial | Student-level (not planner-specific) |
| UP·Q2 (zoning overlays) | Partial | Pre-study methodology |
| UP·Q3 (environmental factors) | Partial | Flood/soil map workflow (screen-share) |
| UP·Q4 (tool gap) | Good | Map overlay pain point |
| UP·Q5 (dashboard) | Good | From junior architects + inferred |
| UP·Q6 (ideal tool) | Inferred | From session themes |

**Recommended follow-up:** SA·Q3 (client presentation dynamics) and SP·Q3 (strategic massing/orientation decisions) are not covered. Consider a 30-min async follow-up with a senior architect before Step 1 gate sign-off.

---

Status: PENDING SME APPROVAL
*SME advisor should review this doc and confirm: (1) profiles reflect real professionals in their network; (2) no disqualifying criteria are wrong; (3) product observations above are accurate to their intent.*
