# SunPath Service — Agent Context

**Port:** 8001
**Contract:** `contracts/sunpath.yaml`
**Feature flag:** `feature.sunpath.diagram`
**FVD:** `docs/feature-validation/SAT-06_solar-sunpath.md`

## Source location
`/Volumes/LocalDrive/Site Analysis/Site-Analysis-Tool/src/Backend/SunPath/`
Also: `Site-Analysis/Sprint0_User_Stories/server.py` (Andrew Marsh polar diagram reference)

## Architecture
- pvlib SPA (Solar Position Algorithm) for sun angle calculation
- Matplotlib polar plot — Andrew Marsh-style sun path diagram
- No external API; pure compute

## Endpoint
```
GET /sunpath?lat={lat}&lon={lon}&date={ISO date}
POST /sunpath/diagram   # returns PNG
```

## Gotchas
- Timezone: pvlib needs `pytz` localized datetime; UTC vs local time errors are common
- Matplotlib backend must be `Agg` for headless server: `matplotlib.use("Agg")` before pyplot import
- Diagram PNG returned as `StreamingResponse(media_type="image/png")`

## Migration checklist
- [ ] Copy `app/` directory
- [ ] requirements: pvlib, matplotlib, numpy, pandas, fastapi, uvicorn
- [ ] Wire flag check
- [ ] Dockerfile (no data volume needed)
- [ ] Add `tests/sunpath_smoke.py`
