# AEC & Geospatial SaaS UX Principles

These principles apply to every design decision in Phases 4–9.
They are non-negotiable for SAT's user base (Indian architects, urban planners).

## The three laws of SAT's interface

### Law 1 — Map is primary
The map is always the dominant visual element.
- Analysis panels are secondary overlays.
- Layer controls are tertiary.
- The map must be reachable in ONE click from any screen.
- No layout decision may obscure more than 30% of the map canvas.

### Law 2 — Information density over whitespace
Architects read technical drawings. They are not overwhelmed by dense interfaces.
They ARE frustrated by information hidden behind extra clicks.
- Show the most important output immediately (e.g., overall flood risk score).
- Use progressive disclosure for sub-data (e.g., the 4 flood sub-scores on expand).
- Never paginate analysis results that fit on one panel.

### Law 3 — Colour encodes meaning only
Every colour must mean something specific.
- Decorative colour use is forbidden on any map-adjacent interface.
- Analysis module colours (flood red, sun orange, etc.) must be confirmed by
  the Architecture SME to match professional conventions.
- Never use a semantic colour (error red, warning amber) for decoration.

## Layer control requirements

Architects toggle layers constantly. This is a primary interaction, not secondary.
- Layer controls must be persistent and visible at all times on the map screen.
- Layer controls must not be buried in a settings menu.
- Individual layer toggles with visible state (on/off) are required.
- Loading state per layer is required (skeleton or spinner on the layer control).

## Competitor reference points

Study these when designing specific screens:

| Tool              | What to learn from it                                        |
|-------------------|--------------------------------------------------------------|
| Autodesk Forma    | Environmental analysis panel layout, score visualisation     |
| TestFit           | Density and precision of information on a single screen      |
| QGIS              | What NOT to do for non-GIS-expert users                      |
| Google Earth      | Map interaction conventions users already know               |

## Screen states — all required

Every screen must have all five states designed:
1. Loading (skeleton or spinner)
2. Empty (no site selected / no data)
3. Data (normal populated state)
4. Error (API failure, no data available for location)
5. Partial (some analysis modules loaded, others pending)

The Architecture SME must confirm the Error and Partial states are
professionally appropriate — architects will see these on real projects.

## Responsive targets

| Breakpoint | Priority | Notes                                    |
|------------|----------|------------------------------------------|
| 1440px     | Primary  | Architect workstation — design for this  |
| 1280px     | High     | Laptop                                   |
| 768px      | Medium   | Tablet — secondary use case              |
| < 768px    | Out of scope for Beta | Note as known gap             |
