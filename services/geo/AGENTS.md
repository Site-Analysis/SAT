# Geo Service — Agent Context

**Port:** 8004
**Contract:** TBD (no `contracts/geo.yaml` yet — create before code)
**Feature flag:** TBD — likely split into multiple:
  - `feature.geo.vegetation` (NDVI/EVI/SAVI from Sentinel-2)
  - `feature.geo.admin-boundaries` (FAO GAUL)
  - `feature.geo.pdf-report` (composite report generation)

## Source location
`Site-Analysis/SiteAnalysis_GEE/app/` — canonical multi-feature service:
- `gee_utils.py` — vegetation, admin lookup
- `pdf_generator.py` — report generation (FVD-05)
- `chart_generator.py` — infographic charts
- `map_renderer.py` — matplotlib map renders

## Architecture
- Catch-all for GEE-backed analyses not in their own service
- Likely splits later into `vegetation/`, `admin/`, `reports/` once features mature

## Endpoints (current source)
```
POST /analyze-location
POST /analyze-polygon
POST /generate-report   # returns PDF stream
```

## Gotchas
- This service may be heavyweight — consider splitting before migration
- PDF generation depends on `reportlab`, `matplotlib`, `pillow` — heavy dependencies
- See `docs/feature-validation/SAT-05_pdf-report-generation.md` for full traceability

## Migration checklist
- [ ] Decide: keep as monolith or split into vegetation/admin/reports?
- [ ] Create contract YAML (currently missing)
- [ ] Add feature flags for each sub-feature
- [ ] Migrate one sub-feature at a time, not the whole service
