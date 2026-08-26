// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

export const copy = {
  moduleTitle: "Contour Analysis",
  moduleBlurb:
    "Terrain contours, slope classes, buildability zones and elevation profiles derived from Copernicus DEM GLO-30. Planning-level output for early site assessment.",
  demSourceLabel: "Copernicus DEM GLO-30 2024",
  demSourceDetail: "DSM · ~30 m resolution · EGM2008 vertical datum",

  eligibility: {
    ok: "Polygon boundary detected",
    noBoundary: "Contour analysis requires a polygon site boundary.",
    point:
      "This project uses a point location with a display buffer, not a drawn boundary. Contour analysis requires a polygon site boundary — draw or select one to run it.",
    tooSmall: "This site is too small for reliable 30m DEM contour analysis.",
    tooSmallDetail: (area: string) => `Contour analysis needs at least 0.5 ha. This site is ${area} ha.`,
  },

  service: {
    flagDisabled: "Contour analysis is not enabled in this environment.",
    unreachable: "Contour service unreachable. Check that the contour backend is running.",
    degraded: "Terrain data could not be fetched on the last attempt.",
  },

  interval: {
    label: "Contour interval",
    hint: "10 m to 60 m. 20 m recommended.",
    invalid: "Choose a contour interval between 10m and 60m.",
    minWarning: "Minimum reliable contour interval for Copernicus GLO-30 is 10m.",
  },

  run: {
    first: "Run analysis",
    again: (interval: number) => `Re-run at ${interval} m`,
    stale: (resultInterval: number, interval: number) =>
      `Showing ${resultInterval} m results — re-run to apply ${interval} m.`,
    cancel: "Cancel",
    cancelled: "Analysis cancelled. Previous results are unchanged.",
  },

  dem: {
    source: "DEM Source",
    resolution: "Resolution",
    rmse: "Vertical RMSE",
    interval: "Contour Interval",
    warning: "Warning",
  },

  slopeHelp: {
    mean: "Average terrain slope across the analyzed polygon. Useful for understanding the general grading burden of the site.",
    max: "Steepest sampled slope within the analyzed polygon. Useful for identifying localized terrain constraints.",
    flat: "Share of the site with slope between 0-5%. Usually the most straightforward area for development.",
    gentle: "Share of the site with slope between 5-10%. Often buildable, but may require grading or drainage attention.",
    moderate: "Share of the site with slope between 10-15%. May affect road layout, foundation strategy, and stormwater movement.",
    steep: "Share of the site with slope between 15-25%. Likely to need careful grading, retaining, or design constraints.",
    verySteep: "Share of the site with slope between 25-33%. Typically highly constrained.",
    hazard: "Share of the site with slope greater than 33%. Should be treated as hazard-prone or generally unsuitable without specialist review.",
  },

  slopeLabels: {
    mean: "Mean slope",
    max: "Maximum slope",
    flat: "Flat area",
    gentle: "Gentle area",
    moderate: "Moderate area",
    steep: "Steep area",
    verySteep: "Very steep area",
    hazard: "Hazard area",
  },

  aspect: {
    title: "Aspect statistics",
    explanation:
      "Aspect describes the compass direction that slopes face. It can influence solar exposure, drainage, vegetation, and thermal behavior.",
    dominant: "Dominant aspect",
    dominantDeg: "Dominant aspect degrees",
    north: "North-facing",
    south: "South-facing",
  },

  sections: {
    dem: "DEM",
    layers: "Map layers",
    slope: "Slope statistics",
    aspect: "Aspect statistics",
    buildability: "Buildability",
    transect: "Transect",
    advanced: "Advanced / debug",
  },

  layers: {
    hillshade: "Hillshade",
    contours: "Contours",
    slope: "Slope classes",
    buildability: "Buildability zones",
  },

  transect: {
    start: "Start transect",
    stop: "Finish drawing",
    clear: "Clear transect",
    run: "Run transect",
    instructions:
      "Click along the site to place transect points, then run the profile. Two points minimum. Press Enter to finish, Backspace to remove the last point, Escape to cancel.",
    needsAnalysis: "Run contour analysis first — the transect samples the same terrain data.",
    cost: "Running a transect re-fetches DEM data and takes about as long as a full analysis.",
    empty: "No transect drawn yet.",
    running: "Sampling elevations along the transect…",
    interpolated: "Marker position is interpolated along the drawn line; start and end are exact.",
    startLabel: "Start",
    endLabel: "End",
    graphAria:
      "Elevation profile along the drawn transect. Use left and right arrow keys to move along the profile.",
    length: "Total length",
    minElev: "Minimum elevation",
    maxElev: "Maximum elevation",
    relief: "Relief",
    samples: "Sampled points",
    distance: "Distance from start",
    elevation: "Elevation",
    slopePct: "Slope",
    slopeClass: "Slope class",
    finish: "Finish",
    cancel: "Cancel",
    pointCount: (n: number) => `${n} point${n === 1 ? "" : "s"}`,
  },

  legend: {
    contours: (interval: number, index: number) =>
      `Contours — ${interval} m interval. Bolder lines are index contours, every ${index} m.`,
    hillshade: (opacity: number) =>
      `Hillshade — shaded relief at ${opacity}% opacity, drawn beneath all other layers.`,
    slopeTitle: "Slope class",
    buildabilityTitle: "Buildability",
    hillshadeApprox: "Approximate extent — may be offset by up to one DEM pixel (~30 m).",
  },

  progress: {
    fetching: "Fetching DEM data…",
    contours: "Generating contour lines…",
    slope: "Computing slope and buildability…",
    rendering: "Rendering terrain layers…",
    slow: "Large or steep sites can take up to 90 seconds.",
    typical: "Typical stages — the service does not report exact progress.",
    mapRunning: "Contour analysis running…",
    mapTransect: "Sampling transect…",
  },

  report: {
    disclaimer:
      "Contour analysis uses Copernicus DEM GLO-30 2024 at approximately 30m resolution. Outputs are planning-level and should be reviewed with site survey data for detailed design.",
  },

  caveat: {
    dsm: "Copernicus GLO-30 is a surface model — elevations include buildings and vegetation. Planning-level screening only; verify with a topographic survey.",
    buildability:
      "Buildability classes are derived from slope gradient alone. They are not a regulatory determination and do not account for zoning, tenure, geology, or drainage.",
    slopeLayer: "Slope is computed from 30 m DEM cells; features smaller than about 30 m are not resolved.",
    session: "Results are not saved. Reopening this project re-runs the analysis.",
  },

  errors: {
    flagDisabled: "Contour analysis is not enabled in this environment.",
    tooSmall: "This site is too small for reliable 30m DEM contour analysis.",
    interval: "Choose a contour interval between 10m and 60m.",
    inputs: "Contour analysis could not run with the current inputs.",
    demFetch:
      "Terrain data could not be fetched. Check the contour backend and Earth Engine configuration.",
    unreachable: "Contour service unreachable. Check that the contour backend is running.",
    missingPolygon: "Contour analysis requires a polygon site boundary.",
    transectShort: "Draw a transect line with at least a start and end point.",
    generic: "Contour analysis failed.",
    geometrySimplified: "Slope geometry simplified for display — tooltips are disabled on this layer.",
  },

  advanced: {
    contourFeatures: "Contour features",
    slopeFeatures: "Slope features",
    buildabilityFeatures: "Buildability features",
    sampleCount: "Transect samples",
    resultNonce: "Result nonce",
  },
} as const;
