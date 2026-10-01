# SAT-19 Contour Analysis Frontend UI Requirements

## Purpose

This document defines the frontend user interface requirements for displaying the contour analysis backend outputs. It is intended for product, SME, design, and frontend review. It describes what the UI must show and how users should interact with contour analysis results, without prescribing frontend code or implementation details.

## Supported Backend Capabilities

The contour backend exposes the following user-facing capabilities:

- Health status for the contour service.
- Full contour analysis for polygon project boundaries.
- Contour line GeoJSON output.
- Slope classification GeoJSON output.
- Buildability classification GeoJSON output.
- Base64 PNG hillshade output.
- DEM metadata and terrain statistics.
- Transect elevation profile analysis from a drawn LineString.

The frontend must treat contour analysis as available only for projects with a polygon boundary. Point and circle projects must show a clear unavailable state.

## Primary User Flow

1. User opens a polygon project.
2. User navigates to the contour analysis module.
3. UI confirms that the project boundary is eligible.
4. User selects a contour interval and optional analysis offset.
5. User runs contour analysis.
6. UI displays DEM metadata, slope/aspect summaries, contour layers, slope layers, buildability layers, and hillshade.
7. User toggles map layers and elevation labels on or off from a single panel.
8. User activates the transect tool.
9. User draws a transect line across the site.
10. UI displays the transect line on the map with A/B section arrows and a matching elevation profile graph.
11. User hovers or scrubs across the graph or along the map section line.
12. A marker moves along the transect line on the map and on the graph together.

## Module Availability Requirements

### Polygon Projects

For polygon project boundaries, the contour module must be enabled and allow:

- Running contour analysis.
- Viewing contour layers.
- Viewing slope statistics.
- Viewing buildability zones.
- Drawing transects.
- Viewing transect profiles.

### Point Or Circle Projects

For point or circle projects, the contour module must not auto-buffer or invent a polygon. The UI must show a disabled state explaining:

- Contour analysis requires a polygon boundary.
- The current project geometry is not eligible.
- The user must create or select a polygon boundary to run contour analysis.

The disabled state should be visible in the contour panel itself, not hidden behind missing buttons or silent failures.

## Contour Analysis Control Panel

The contour panel must include:

- Module title: **Contour Analysis**.
- Short explanation of what contour analysis provides.
- Service status indicator.
- Polygon eligibility indicator.
- Contour interval selector.
- Analysis offset selector (0 / 50 / 100 / 200 m).
- Run analysis button.
- Loading state while the backend request is running.
- Error state if analysis fails.
- Warning if no contour lines pass through the selected area.
- Last-run summary after successful analysis.

## Contour Interval Selector

The UI must allow only backend-supported contour intervals:

- Minimum: 10m
- Maximum: 60m
- Recommended default: 20m

If the UI allows free numeric input, it must validate values before sending the request. Invalid values must show inline validation and must not wait for the backend 422 response.

When the selected interval is 10m, the UI must surface the backend warning:

> Minimum reliable contour interval for Copernicus GLO-30 is 10m.

This warning should be informative, not blocking.

## Analysis Offset Selector

The UI must offer an optional offset around the site polygon so surrounding contours show slope direction into the site.

- Presets: 0 m (site only), 50 m, 100 m, 200 m.
- Default: 0 m.
- Backend range: 0–500 m.
- DEM, contours, and hillshade are generated for the buffered extent.
- Slope and buildability statistics and fills remain clipped to the original site polygon.
- When offset is greater than 0, the map shows a dashed offset ring.
- Offset does not bypass the 0.5 ha eligibility gate on the original polygon.

## DEM Metadata Display

After successful analysis, the main panel must show:

- DEM source.
- Selected contour interval.
- Analysis offset, when greater than 0.
- Any backend warning that is not the empty-contour warning (that warning is shown at the run controls).

Do not show DEM resolution or Vertical RMSE on the main card.

Vertical RMSE may appear in Advanced / the detail report, with this explanation:

> Vertical RMSE should be no more than one-third of the contour interval. With 4 m RMSE, the smallest reliable contour interval is about 12 m.

Recommended main-card labels:

- DEM Source
- Contour Interval
- Analysis offset

The DEM source should be human-readable. For the current backend value `copernicus`, display:

> Copernicus DEM GLO-30 2024

## Map Layer Requirements

There must be only one Map layers control, in the contour panel — not a second overlay on the map. The legend must live in that same panel so it does not sit on the site polygon.

The panel must support:

- Hillshade.
- Contours.
- Elevation labels.
- Slope classes.
- Buildability zones.

Each layer must have an independent visibility toggle. Elevation labels apply only while Contours is on. The legend must update based on visible layers.

### Recommended Default Layer State

After successful analysis:

- Hillshade: on.
- Contours: on.
- Elevation labels: on.
- Slope classes: off.
- Buildability zones: off.

This default keeps the initial map readable while still surfacing the primary terrain output.

## Hillshade Layer Requirements

The hillshade output must be displayed as a raster image overlay covering the analyzed polygon extent.

UI requirements:

- Show the hillshade beneath vector overlays.
- Use partial opacity so map context remains visible.
- Provide a layer toggle.
- Do not treat hillshade as a standalone map basemap.

## Contour Line Layer Requirements

Contour lines must render from `contour_geojson`.

Contour strokes must be topographic brown, not a rainbow/viridis elevation ramp:

- Regular contours: lighter brown, thinner.
- Index contours: darker brown, bolder.

Each contour line must use:

- `is_index` to distinguish index contours.
- `elevation` for labels/tooltips.

Frontend may ignore backend `color` / `line_weight` in favour of the brown cartographic style.

### Contour Labels

Elevation labels must be toggleable independently of other layers.

Requirements:

- Toggle label: **Elevation labels**.
- Informative copy: Elevation in metres, from mean sea level (EGM2008).
- Index contours should be visibly stronger than regular contours.
- Persistent haloed labels for index contours; thinned intermediate labels at higher zoom.
- Hovering a contour must show elevation in metres.
- Labels must use `m` as the unit.
- Labels must not overcrowd the map at low zoom levels.

## Slope Layer Requirements

Slope polygons must render from `slope_geojson`.

Each slope feature must use:

- `slope_class`.
- `slope_range_label`.
- `color`.

The UI must include a slope legend. Do not use “workable” / “not workable”. Legend rows show class, meaning, and range. Hide classes with 0% share.

| Class | Meaning | Range |
|---|---|---|
| FLAT | Low-gradient terrain | 0-5% |
| GENTLE | Mild slope | 5-10% |
| MODERATE | Noticeable grade | 10-15% |
| STEEP | Construction-sensitive slope | 15-25% |
| VERY_STEEP | Unstable, high-constraint terrain | 25-33% |
| HAZARD | Hazard-prone steep terrain | >33% |

## Buildability Layer Requirements

Buildability polygons must render from `buildability_geojson`.

Each buildability feature must use:

- `buildability_class`.
- `color`.

The UI must include a buildability legend with user-readable labels:

| Backend Class | Recommended UI Label |
|---|---|
| BUILDABLE_FLAT | Buildable Flat |
| BUILDABLE_WITH_GRADING | Buildable With Grading |
| CONSTRAINED_RETAINING | Constrained: Retaining/Engineering Needed |
| NON_BUILDABLE_REGULATED | Non-Buildable: Regulated/Very Steep |
| NON_BUILDABLE_HAZARD | Non-Buildable: Hazard |

## Slope Statistics UI Requirements

The slope statistics section must always show:

- Mean slope percentage.
- Maximum slope percentage.

Class-area tiles (flat, gentle, moderate, steep, very steep, hazard) must appear only when that class has a value greater than 0%.

### SME Review Requirement: Hoverable Explanations

Each slope statistic must include a hoverable help component explaining what the metric means.

Required help text:

| Statistic | Help Text |
|---|---|
| Mean slope | Average terrain slope across the analyzed polygon. Useful for understanding the general grading burden of the site. |
| Maximum slope | Steepest sampled slope within the analyzed polygon. Useful for identifying localized terrain constraints. |
| Flat area | Share of the site with slope between 0-5%. Low-gradient terrain. |
| Gentle area | Share of the site with slope between 5-10%. Mild slope; may need grading or drainage attention. |
| Moderate area | Share of the site with slope between 10-15%. Noticeable grade; may influence grading and drainage. |
| Steep area | Share of the site with slope between 15-25%. Construction-sensitive slope. |
| Very steep area | Share of the site with slope between 25-33%. Unstable, high-constraint terrain. |
| Hazard area | Share of the site with slope greater than 33%. Hazard-prone steep terrain; specialist review recommended. |

The hover interaction must also be accessible by keyboard focus or equivalent non-hover interaction.

## Aspect Statistics UI Requirements

The aspect statistics section must show:

- Dominant aspect direction.
- Dominant aspect degrees.
- North-facing percentage.
- South-facing percentage.

Recommended explanation:

> Aspect describes the compass direction that slopes face. It can influence solar exposure, drainage, vegetation, and thermal behavior.

The UI should avoid implying that aspect alone determines design suitability.

## Transect Tool Requirements

The transect tool lets users draw a LineString across the analyzed polygon and request an elevation profile.

The tool must include:

- Start transect button.
- Clear transect button.
- Confirm/run transect button.
- Instructional helper text.
- Loading state while transect analysis is running.
- Error state if transect analysis fails.

The transect tool should be disabled until:

- The project has a polygon boundary.
- Contour analysis is available for the project.

Recommended behavior:

- Allow transect drawing after contour analysis has run successfully.
- If transect drawing is allowed before analysis, clearly state that the backend will fetch DEM data when the transect is submitted.

## Transect Line Map Requirements

The map must clearly show the transect line drawn by the user.

Required visual elements:

- Dashed transect line.
- Distinct start point marker **A**.
- Distinct end point marker **B**.
- Filled section-cut arrows at both ends, perpendicular to the line, on the same side (left of A→B). A sits on/over the start arrow.
- Optional intermediate vertex markers.
- Clear selected/active visual state while drawing.

### SME Review Requirement: Clear Start And End Points

The start and end points must be visually distinct both on the map and on the graph.

Required labels:

- Start marker: **A**
- End marker: **B**

The same A/B labels and colors must be reused on the graph axis. Left of graph is A; right of graph is B.

## Transect Graph Requirements

The transect graph must display the elevation profile returned by `/contour/transect`.

Required graph elements:

- X-axis: distance along transect in metres.
- Y-axis: elevation in metres.
- Profile line.
- A label (left).
- B label (right).
- Minimum elevation value.
- Maximum elevation value.
- Total relief value.
- Total transect length.

### SME Review Requirement: Map Marker Follows Graph

When the user hovers, focuses, or scrubs along the elevation graph **or along the map section line**:

- A marker must appear on the transect line on the map.
- The graph must show a matching vertical hairline and point.
- The marker position must correspond to the nearest profile point.
- The active point details must be shown in a tooltip or readout.

The active point readout must include:

- Distance from A.
- Elevation.
- Slope percentage.
- Slope class.

The map marker must update continuously enough to feel connected to graph movement. It should not lag behind the user's hover/scrub interaction.

### SME Review Requirement: Start/End Consistency On Graph

The graph must make transect direction clear.

Requirements:

- Left side of graph corresponds to A.
- Right side of graph corresponds to B.
- A/B labels and colors must match the map markers.
- If the user reverses or redraws the transect, the graph must update direction accordingly.

## Transect Summary Requirements

The transect result panel must show:

- Total length in metres.
- Minimum elevation in metres.
- Maximum elevation in metres.
- Relief in metres.
- DEM source.
- Number of sampled points, if useful for debugging or SME review.

The summary should be located close to the graph so users understand that the values describe the currently selected transect.

## Error And Empty States

The frontend must show clear, user-readable messages for:

- Contour service offline.
- Feature flag disabled.
- Polygon missing.
- Project geometry not eligible.
- Polygon too small for 30m DEM analysis.
- Invalid contour interval.
- DEM fetch failure.
- GEE/auth/backend failure.
- Empty or invalid transect line.
- Successful analysis with no contour lines through the site (warning, not a failed run).

### Recommended Error Copy

| Backend/Scenario | UI Message |
|---|---|
| 403 Feature flag disabled | Contour analysis is not enabled in this environment. |
| Missing polygon | Contour analysis requires a polygon site boundary. |
| Site below 0.5 ha | This site is too small for reliable 30m DEM contour analysis. |
| Interval below 10m or above 60m | Choose a contour interval between 10m and 60m. |
| DEM fetch failure | Terrain data could not be fetched. Check the contour backend and Earth Engine configuration. |
| Transect line missing or invalid | Draw a transect line with at least a start and end point. |
| No contour lines at this interval | No contour lines pass through the selected area at this interval. Try a smaller contour interval or add an analysis offset around the polygon. |

The UI should preserve the user's drawn polygon and transect when an error occurs, unless the error is caused by geometry deletion.

## Loading And Progress Requirements

Contour analysis can take time because it fetches and processes DEM data.

The UI must show:

- A loading state on the run button.
- A panel-level progress/status message.
- A map-level indication that outputs are pending.
- Disabled duplicate-submit behavior while a request is active.

Recommended loading messages:

- Fetching DEM data...
- Generating contour lines...
- Computing slope and buildability...
- Rendering terrain layers...

If exact backend progress is unavailable, these may be displayed as general status copy rather than precise progress steps.

## Layer Legend Requirements

The frontend must provide a legend for every active thematic layer.

Required legends, shown in the panel (not over the polygon):

- Contour interval, plus a separate line: **Bolder line is the index contour.**
- Slope class color legend with meaning and range (omit 0% classes).
- Buildability class color legend.
- Hillshade opacity explanation.

## Report And Export Requirements

When contour analysis is included in reports or exports, the UI must include:

- DEM metadata.
- Slope statistics.
- Aspect statistics.
- Buildability summary.
- Map image or layer snapshot where supported.
- Transect graph and summary if a transect has been generated.

The report should clearly state:

> Contour analysis uses Copernicus DEM GLO-30 2024 at approximately 30m resolution. Outputs are planning-level and should be reviewed with site survey data for detailed design.

## Accessibility Requirements

The frontend must support:

- Keyboard access to contour controls.
- Keyboard or touch access to slope statistic explanations.
- Keyboard or touch access to transect graph point inspection.
- Sufficient contrast for contour, slope, and buildability layers.
- Non-color-only distinction for A/B transect points.
- Screen-reader labels for run buttons, toggles, graph, and map markers.

Hover-only behavior is not sufficient for SME review requirements. Any hoverable component must have an equivalent focus, click, or touch behavior.

## Visual Hierarchy Requirements

The UI should prioritize information in this order:

1. Eligibility and run controls.
2. Map terrain outputs.
3. DEM metadata and warnings.
4. Slope/buildability summaries.
5. Transect tool and profile.
6. Advanced details and debug information.

Avoid showing all raw backend outputs at once. The user should be able to expand or collapse detailed statistics as needed.

## Acceptance Criteria

The frontend UI is acceptable when:

- Polygon projects can run contour analysis from the UI.
- Point and circle projects show a disabled contour state.
- Contour, elevation labels, slope, buildability, and hillshade outputs can be toggled from a single panel.
- The legend is not drawn on top of the site polygon.
- DEM source, interval, optional offset, and warnings are visible after analysis. Resolution and RMSE are not on the main card.
- Slope statistics include hover/focus explanations and hide zero-value class tiles.
- Empty contour results show a warning suggesting a smaller interval or an analysis offset.
- The transect line has clear A/B markers and same-side section arrows on the map.
- The transect graph has A/B labels matching the map.
- Hovering the graph or the map section line moves a shared marker.
- Graph point readout shows distance, elevation, slope percentage, and slope class.
- Error states are understandable and preserve user input where possible.
- Export/report views can include contour summaries and transect results.
