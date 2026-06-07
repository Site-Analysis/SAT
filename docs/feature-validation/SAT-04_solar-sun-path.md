# FVD-06 — Solar Position & Sun Path Diagram

**Jira Ticket:** SAT-TBD  
**Status:** Done  
**Resolved:** 2025-11-09  
**Type:** Story  
**Authors:** Karthik-J-Ramoo (Karthik)  
**Repository:** [Sprint0_User_Stories](https://github.com/Site-Analysis/Sprint0_User_Stories)

---

## Feature Overview

**User Story:** As an architect or solar designer, I want to visualize the sun's path across the sky for any location and date so that I can assess solar exposure, shading, and passive solar design opportunities for a site.

**Business Value:** Provides publication-quality Andrew Marsh–style polar sun path diagrams and precise NREL SPA solar position data (±0.0003° accuracy) for any global coordinate — enabling passive solar design, shading analysis, daylight studies, and photovoltaic layout planning without external tools.

---

## Commit Traceability

| Commit | Date | Author | Description |
|---|---|---|---|
| [`944c5b8`](https://github.com/Site-Analysis/Sprint0_User_Stories/commit/944c5b8) | 2025-11-09 | Karthik-J-Ramoo | Solar analysis — pvlib SPA, Andrew Marsh polar sun path diagram |

---

## Code Traceability Matrix

| # | Acceptance Criterion | Commit | File | Function / Class |
|---|---|---|---|---|
| 1 | Solar elevation angle returned for any lat/lon/datetime | `944c5b8` | `server.py` | `POST /solar-position` → `get_solarposition()` via pvlib |
| 2 | Solar azimuth returned | `944c5b8` | `server.py` | `SolarPositionResponse.azimuth` |
| 3 | Zenith, hour angle, declination returned | `944c5b8` | `server.py` | `SolarPositionResponse.zenith`, `.hour_angle`, `.declination` |
| 4 | Sunrise, sunset, solar noon times returned | `944c5b8` | `server.py` | `calculate_solar_events()` — 1-min resolution scan |
| 5 | Day length (hours) returned | `944c5b8` | `server.py` | `SolarPositionResponse.day_length` |
| 6 | Is-daytime boolean returned | `944c5b8` | `server.py` | `SolarPositionResponse.is_daytime` |
| 7 | Polar (Andrew Marsh–style) sun path diagram generated | `944c5b8` | `server.py` | `create_polar_sun_path()` — matplotlib polar axes |
| 8 | 3 seasonal paths on diagram (summer / equinox / winter) | `944c5b8` | `server.py` | `create_polar_sun_path()` — Jun 21, Mar 21, Dec 21 |
| 9 | Altitude rings at 10° intervals | `944c5b8` | `server.py` | `create_polar_sun_path()` — yticks 10°–90° |
| 10 | Azimuth labels at compass directions | `944c5b8` | `server.py` | `create_polar_sun_path()` — N/NE/E/SE/S/SW/W/NW |
| 11 | Hourly tick marks on sun path curves | `944c5b8` | `server.py` | `create_polar_sun_path()` — 60-min interval markers |
| 12 | Current solar position plotted on diagram | `944c5b8` | `server.py` | `create_polar_sun_path()` — `current_position` scatter point |
| 13 | Cartesian (azimuth vs elevation) diagram generated | `944c5b8` | `server.py` | `create_cartesian_sun_path()` |
| 14 | PNG returned as streaming binary response | `944c5b8` | `server.py` | `POST /sun-path` → `StreamingResponse(media_type="image/png")` |
| 15 | Raw JSON sun path data endpoint available | `944c5b8` | `server.py` | `POST /sun-path/data` → dict with daytime_positions, solar_events |
| 16 | Timezone auto-estimated from longitude if not provided | `944c5b8` | `server.py` | `get_timezone()` — `offset = longitude / 15` fallback |
| 17 | NREL SPA algorithm used (±0.0003° accuracy) | `944c5b8` | `server.py` | pvlib `solarposition.get_solarposition(method='nrel_numpy')` |
| 18 | 5-minute resolution sun path for smooth curves | `944c5b8` | `server.py` | `create_polar_sun_path()` — `freq='5min'` pandas DatetimeIndex |

---

## Implementation Breakdown

### Architecture
```
POST /solar-position
    └── get_timezone(tz_string, longitude, latitude)
    └── pvlib.solarposition.get_solarposition() [NREL SPA]
    └── calculate_solar_events() [1-min scan for rise/set/noon]
    └── SolarPositionResponse

POST /sun-path
    └── get_timezone()
    └── pvlib [5-min DatetimeIndex for full day]
    └── pvlib [3 seasonal dates — Jun 21, Mar 21/Sep 23, Dec 21]
    └── create_polar_sun_path() OR create_cartesian_sun_path()
    └── StreamingResponse(image/png)

POST /sun-path/data
    └── same pipeline → dict (JSON) instead of image
```

### Technology Stack
| Library | Role |
|---|---|
| `pvlib` | NREL SPA solar position algorithm — ±0.0003° accuracy |
| `matplotlib` | Polar and Cartesian sun path diagram rendering |
| `pandas` | DatetimeIndex generation (5-min/1-min resolution) |
| `pytz` | Timezone parsing and localization |

### Pydantic Models
```
SolarPositionRequest
├── latitude: float
├── longitude: float
├── datetime: str  (ISO 8601: "2025-06-21T12:00:00")
└── timezone: Optional[str]  (e.g. "Asia/Kolkata"; estimated if omitted)

SolarPositionResponse
├── elevation: float       (degrees above horizon; negative = below)
├── azimuth: float         (0–360°, clockwise from North)
├── zenith: float          (90 - elevation)
├── hour_angle: float
├── declination: float
├── sunrise: str           (ISO time)
├── sunset: str            (ISO time)
├── solar_noon: str        (ISO time)
├── day_length: float      (hours)
└── is_daytime: bool

SunPathRequest
├── latitude: float
├── longitude: float
├── date: Optional[str]    (default: today)
└── timezone: Optional[str]
```

### Polar Diagram Projection (Andrew Marsh Style)
The polar coordinate transform maps sky hemisphere to 2D circle:
- **Radial axis (r):** `r = 90 - elevation` — sun at horizon → r=90 (edge); sun at zenith → r=0 (center)
- **Angular axis (θ):** `θ = deg2rad(90 - azimuth)` — North at top, clockwise rotation
- **Altitude rings:** yticks at 10°, 20°, …, 80° altitude (labeled on diagram)
- **Seasonal paths:** 3 arcs for Jun 21 (summer solstice), Mar 21 (equinox), Dec 21 (winter solstice)
- **Resolution:** 5-minute `DatetimeIndex` → smooth curves (~144 points per day)
- **Hourly ticks:** every 60th minute on path curves
- **Current position:** scatter point in contrasting color

### Timezone Resolution
```
get_timezone(tz_string, longitude, latitude):
    if tz_string provided:
        try pytz.timezone(tz_string) → return
    else:
        offset = longitude / 15  (Earth rotation: 15°/hr)
        return pytz.FixedOffset(offset * 60)
```

### Solar Events Calculation
```
calculate_solar_events(latitude, longitude, date, tz):
    times = DatetimeIndex(freq='1min', full day)
    solar_pos = pvlib.solarposition.get_solarposition(times, lat, lon)
    sunrise = first time where elevation > 0
    sunset = last time where elevation > 0
    solar_noon = time of maximum elevation
    day_length = (sunset - sunrise).hours
```

---

## Automated Validation Plan

### AC-1, 2, 3: Solar position for Bangalore at solar noon
```bash
curl -X POST http://localhost:8001/solar-position \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 12.9716,
    "longitude": 77.5946,
    "datetime": "2025-06-21T12:30:00",
    "timezone": "Asia/Kolkata"
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Elevation:', d['elevation'])
print('Azimuth:', d['azimuth'])
print('Zenith:', d['zenith'])
print('Is daytime:', d['is_daytime'])
assert d['is_daytime'] == True
assert 0 <= d['azimuth'] <= 360
assert -90 <= d['elevation'] <= 90
print('✓ All checks pass')
"
# Expected: elevation ~70–80° (near zenith at summer noon, Bangalore ~12.97°N)
```

### AC-4, 5: Sunrise/sunset/day length
```bash
curl -X POST http://localhost:8001/solar-position \
  -H "Content-Type: application/json" \
  -d '{"latitude": 28.6139, "longitude": 77.2090, "datetime": "2025-12-21T12:00:00", "timezone": "Asia/Kolkata"}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Sunrise:', d['sunrise'])
print('Sunset:', d['sunset'])
print('Solar noon:', d['solar_noon'])
print('Day length:', d['day_length'], 'hours')
# Delhi winter: day ~10.5 hrs, sunrise ~07:10, sunset ~17:30
"
```

### AC-7, 8, 9, 10, 14: Polar sun path PNG generated
```bash
curl -X POST http://localhost:8001/sun-path \
  -H "Content-Type: application/json" \
  -d '{"latitude": 12.9716, "longitude": 77.5946, "date": "2025-06-21"}' \
  --output sun_path_bangalore.png
# Verify:
file sun_path_bangalore.png
# Expected: PNG image data, 1000x1000 or similar
ls -lh sun_path_bangalore.png
# Expected: > 50KB (rich diagram with 3 seasonal paths)
```

### AC-15: JSON sun path data endpoint
```bash
curl -X POST http://localhost:8001/sun-path/data \
  -H "Content-Type: application/json" \
  -d '{"latitude": 12.9716, "longitude": 77.5946, "date": "2025-06-21"}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Keys:', list(d.keys()))
# Expected: daytime_positions, solar_events (or similar)
print('Data points:', len(d.get('daytime_positions', [])))
# Expected: ~144 points (5-min resolution × ~12 daylight hours)
"
```

### AC-16: Timezone auto-estimation (no tz provided)
```bash
# No timezone — should auto-estimate from longitude 77.59° → UTC+5:11 ≈ IST
curl -X POST http://localhost:8001/solar-position \
  -H "Content-Type: application/json" \
  -d '{"latitude": 12.9716, "longitude": 77.5946, "datetime": "2025-06-21T06:00:00"}' \
  | python3 -c "import sys, json; d = json.load(sys.stdin); print('is_daytime:', d['is_daytime'])"
# Expected: no error, is_daytime depends on whether 06:00 local is past sunrise
```

### AC-17: NREL SPA accuracy verification
```bash
# Compare to known ephemeris data
# Solar noon at Bangalore on Jun 21 ≈ 12:24 IST; elevation ≈ 77.5°
curl -X POST http://localhost:8001/solar-position \
  -H "Content-Type: application/json" \
  -d '{"latitude": 12.9716, "longitude": 77.5946, "datetime": "2025-06-21T12:24:00", "timezone": "Asia/Kolkata"}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Elevation at ~solar noon: {d[\"elevation\"]:.2f}°')
# Expected: ~77–78° (within ±0.01° of known values)
print(f'Solar noon: {d[\"solar_noon\"]}')
"
```

### AC-13: Cartesian diagram
```bash
# If diagram_type parameter supported:
curl -X POST http://localhost:8001/sun-path \
  -H "Content-Type: application/json" \
  -d '{"latitude": 12.9716, "longitude": 77.5946, "diagram_type": "cartesian"}' \
  --output sun_path_cartesian.png
file sun_path_cartesian.png
# Expected: valid PNG
```
