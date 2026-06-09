# SAT Copy Buyer Personas

Research basis: `/Volumes/LocalDrive/Site Analysis/PROJECT_OVERVIEW.md` §2 + Gemini Deep Research (B2B PropTech Copywriter Research Report, June 2026).

These are buying-committee personas — not UX personas. They describe who controls the decision, what copy must do to move them, and what will immediately disqualify a message.

---

## Persona 1: Head of Design

**Archetype names in Indian Tier-1 firms:** Design Principal, Design Director, Creative Head, Studio Head

**Firm examples:** Lead designer at Morphogenesis, Studio Lotus, Sanjay Puri Architects

### What they control
Strong veto power on any tool that touches the design workflow. If they reject it, it dies regardless of the BIM Head's enthusiasm or the MD's budget approval.

### What they fear (copy must address this first)
- Loss of design authorship — SAT "designs the building" for them
- Creative constraint — any tool that mandates process or restricts layout freedom
- Peer embarrassment — being seen as someone who outsources design judgment to software
- "Cookie-cutter" outputs — parametric tools that produce standardized massing without their spatial philosophy

### What moves them (copy levers)
- **Speed of iteration, not automation**: "Test three solar orientations before lunchtime" — they stay in control, SAT just removes the wait
- **Empirical defense of design decisions**: "Your NE orientation delivers 23% lower cooling load — now you have the data to defend it to the developer"
- **Design authorship preserved**: SAT shows options; the architect chooses. Always frame as augmentation, never automation
- **Peer vocabulary**: Use "passive design", "solar orientation", "thermal comfort", "daylighting quality" — the language of design excellence, not software efficiency

### What disqualifies copy instantly
- Any claim that SAT "optimizes" or "generates" design — architect reads this as displacement
- Efficiency/cost-savings framing — insults their creative identity
- Generic SaaS copy ("seamless workflow", "robust platform") — signals the vendor doesn't understand architecture
- Archibabble — fake technical jargon that sounds architectural but reveals no real knowledge

### Copy frame (use verbatim or adapt)
> "SAT doesn't design. It measures. You still make every decision — now you make them with IMD data behind you."

### Buying stage copy by funnel
- **Awareness**: Educational content — "How Indian architects use passive solar analysis to defend design to developers"
- **Consideration**: Case study showing design process unchanged but evidence-backed
- **Decision**: Free analysis of their actual project site ("See your site's solar data before the pitch")

---

## Persona 2: BIM / Digital Transformation Head

**Archetype names:** BIM Manager, Digital Delivery Head, Technology Lead, BIM Coordinator, CAD Manager

**Firm examples:** BIM heads at Hafeez Contractor Architects, CP Kukreja, DSP Design Associates

### What they control
Evaluates and writes the procurement spec. Determines whether SAT integrates with their existing stack (Revit, AutoCAD, IFC workflows). Their technical objections can block a sale even after the Principal approves the budget.

### What they fear
- Proprietary data formats that lock the firm in
- Inaccurate data that creates rework downstream
- Another tool that doesn't sync with Revit — another silo to manage
- Unverifiable data sources ("Where does this flood risk score come from?")

### What moves them
- **Open, verifiable data sources**: Name them explicitly — IMD, MERIT DEM, JRC Global Surface Water, NREL SPA, Open-Meteo. Source attribution is trust.
- **Export formats**: GeoJSON, IFC — formats they already use, no translation layer
- **API access**: Engineers want to know they can pull data programmatically
- **Reproducibility**: Same coordinates → same output, every time. Deterministic analysis.
- **Error reduction**: "Flag NBC setback violations before design is locked — not during the approval process"

### What disqualifies copy instantly
- "AI-powered" without explaining the data source — black box = trust killer
- Feature lists without technical specifics — "advanced analysis" means nothing to a BIM manager
- Vague integration claims — "integrates with your workflow" without naming Revit or IFC

### Copy frame (use verbatim or adapt)
> "Every analysis output is GeoJSON. Every data source is cited. No black box — you can verify exactly what SAT computed and why."

### Buying stage copy by funnel
- **Awareness**: Technical content — "How MERIT DEM elevation data improves flood risk accuracy vs standard SRTM"
- **Consideration**: API documentation samples, data accuracy specs, sample GeoJSON outputs
- **Decision**: Technical sandbox trial — let them run SAT on a known site and compare to their existing analysis

---

## Persona 3: Principal Architect / Managing Director

**Archetype names:** Founding Principal, Managing Partner, Director, CEO (for smaller firms)

**Firm examples:** Founding principals at Sanjay Puri, Studio Lotus; Managing Directors at Space Matrix, Edifice Consultants

### What they control
Final budget sign-off. Strategic technology decisions. Competitive positioning of the firm. The question they are always asking: "Does this win us more work?"

### What they fear
- Losing project pitches to competitors who show up with better sustainability data
- Sustainable design credentials eroding — clients now ask for evidence, not promises
- Long sales cycles and license commitments without proven ROI
- Expensive retraining and workflow disruption

### What moves them
- **Competitive differentiation**: "Your competitors are pitching sustainability claims. You're pitching passive cooling data."
- **Client-facing narrative**: "Your building will have 40% lower cooling load due to orientation — that's the line you can put in front of the developer"
- **Speed to value**: Concept-phase analysis means sustainability is baked in, not bolted on — no cost overruns
- **The Vastu bridge (India-specific)**: Sun path + wind analysis gives them empirical data to validate Vastu-compliant orientations to skeptical developers. "North-facing entry = 18% lower thermal load in June" is a line that sells apartments.
- **Pilot credibility**: "3 firms in Bengaluru's Tier-1 cohort" — scarcity + peer validation in a referral-heavy market

### What disqualifies copy instantly
- Pricing without ROI context — "₹50K/month" is high; "₹50K/month, recoverable in one saved revision cycle" is reasonable
- Abstract sustainability claims — "reduce your carbon footprint" is a poster, not a business case
- Long commitment requirements — Indian AEC buyers want to trial before they buy

### Copy frame (use verbatim or adapt)
> "While your competitor is explaining why their design is sustainable, you're showing the client the solar data. That's not a presentation. That's a closed deal."

### Buying stage copy by funnel
- **Awareness**: "How Tier-1 Indian firms are using environmental data to win developer projects"
- **Consideration**: ROI case study — time saved × billable rate × avoided rework = SAT value
- **Decision**: Pilot offer — "3 months, your actual site, your actual team"

---

## Cross-Persona Rules

1. **Never blend personas in a single asset** — one asset, one primary reader
2. **The buying committee sequence**: Principal sees the vision copy → BIM Head gets the technical spec → Head of Design gets the creative autonomy framing
3. **The referral network reality**: Indian Tier-1 firms trust peer recommendations over vendor claims. When possible, name a real firm as social proof — even a hypothetical "Morphogenesis-caliber workflow" anchors credibility
4. **Vastu bridge**: Relevant primarily for Principal (helps sell to residential developers) and Head of Design (scientific validation of intuitive decisions). Not relevant for BIM Head copy.
