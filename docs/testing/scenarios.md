# Test Scenarios — SAT-Fallback

## Site Coordinates

| ID | Name | Lat | Lon | Context |
|----|------|-----|-----|---------|
| S1 | Bellandur Lakefront | 12.9352 | 77.6733 | Flood-prone lakebed, urban |
| S2 | Hebbal Lake Area | 13.0358 | 77.5946 | Dense urban, lake adjacency |
| S3 | Sarjapur Road | 12.8590 | 77.7890 | Residential outskirts |
| S4 | Whitefield Tech Corridor | 12.9698 | 77.7500 | Commercial/tech, flat |
| S5 | Devanahalli | 13.2437 | 77.7117 | Rural, near airport, low density |

## Domain Plausibility Ranges (Bengaluru)

| Module | Metric | Plausible Range |
|--------|--------|-----------------|
| Temperature | annual mean (°C) | 20–30 |
| Temperature | max monthly (°C) | 25–38 |
| Sunpath | peak solar elevation (°) | 60–90 |
| Sunpath | annual solar hours | 2000–3200 |
| Flood | risk_score | 0.0–1.0 |
| Wind | annual mean speed (m/s) | 1–8 |
| Rainfall | annual total (mm) | 700–1200 |
| Planning | far (floor-area ratio) | 1.0–4.0 |
| Infrastructure | connectivity_score | 0–100 |
| Geo | amenity categories | ≥1 |

## Test Taxonomy

1. **Health** — `/health` → 200 + `status` field
2. **Schema** — real endpoint → required fields present, correct types
3. **Domain** — values within plausible ranges
4. **Flag gate** — request without FLAGS env → expect 403 (skipped in live suite; FLAGS set)
5. **Edge** — extreme coords (0°N, 0°E ocean) → graceful 200 or 422, no 500
6. **Error** — missing required params → 422 Unprocessable Entity
