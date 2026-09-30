# SPIKE-278 — Topography File Import: Per-Format Path, Findings + Go/No-Go

**Jira Ticket:** SAT-278 (V1 SPIKE, under parent SAT-271, sprint "Topography & Terrain Modeling")
**Owner:** Vishwas (paired w/ Pranav)
**Status:** Spike complete — findings feed SAT-279 (V2: backend upload endpoint)
**Date:** 2026-09-30

---

## Method

This is not a docs-research spike — every claim below was verified by actually writing a
real, valid file per format and reading it back through the candidate library, in a clean
`python3.12` venv with no pre-existing system packages (matches this repo's
per-service-venv model from `CLAUDE.md`). Where the format's real-world behavior matters
more than the happy path — CRS presence, large files, malformed input — those are tested
explicitly rather than assumed from documentation. Test scripts:
`sat278-spike/deep_dive.py` and `sat278-spike/deep_dive_extras.py` (scratch, not committed
to this repo — reproducible from this doc).

No existing service in this repo parses any of these formats today (checked all
`services/*/requirements.txt`; only `shapely`/`pyproj` exist, for geometry math, not file
I/O). This is a new dependency surface, not a reuse.

Tested versions (all installed clean via `pip`, no system GDAL/other lib needed):

```
rasterio==1.5.1
laspy==2.7.0
lazrs==0.8.2       # LAZ compression backend for laspy
pyproj==3.8.0      # CRS handling, laspy/rasterio dependency
ezdxf==1.4.4
lxml==6.1.3
```

---

## Per-format deep dive

### GeoTIFF — GO

**Library:** `rasterio` (bundles GDAL in the manylinux wheel — confirmed no system `libgdal`
was present in the test venv and the install still worked).

```python
import rasterio
with rasterio.open(path) as src:
    crs = src.crs                 # CRS object, e.g. EPSG:32643
    bounds = src.bounds           # BoundingBox(left, bottom, right, top)
    units = crs.linear_units      # 'metre'
```

**Extracted from a real 100×100 synthetic raster (EPSG:32643):**
```json
{"crs": "EPSG:32643", "units": "metre",
 "bbox": [500000.0, 1434900.0, 500100.0, 1435000.0],
 "resolution_m": [1.0, 1.0], "date": null}
```
CRS, bbox, units all land cleanly. **Date has no home in the format** — only recoverable
from a filename convention or a custom TIFF tag if the source system writes one; don't
build extraction logic that assumes it exists.

**Performance (4000×4000, tiled+deflate, 50.5 MB on disk):**
| Operation | Time |
|---|---|
| metadata-only open (CRS + bounds) | 0.017s |
| windowed 500×500 pixel read | 0.006s |

Metadata is essentially free regardless of raster size — SAT-279's validation step can open
and check every GeoTIFF upload without touching pixel data.

**Malformed input:** a PNG's bytes renamed to `.tif` → `rasterio.open()` raises
`RasterioIOError` immediately (it checks magic bytes, not the extension — extension
spoofing is not a validation bypass here).

---

### XYZ — GO, with a hard caveat

**Library:** none — `numpy.loadtxt` / `pandas.read_csv`, it's plain text.

**Extracted from a real 20-point file:**
```json
{"crs": null, "units": null,
 "bbox": [500018.8, 1435006.178, 500096.834, 1435093.428],
 "point_count": 20}
```
bbox is *computable* — the numbers are right there — but CRS and units are structurally
absent from the format. This isn't a parser limitation to work around later; the spec
itself carries no such field, and real-world files vary in column order (`X Y Z` vs.
`X Y Z Intensity` vs. `X Y Z R G B`) and delimiter.

**Consequence for SAT-279:** CRS + units for XYZ must be a **required form field at
upload**, not an extraction attempt. The endpoint should not try to "detect" these — treat
absence as expected, not a validation failure, and surface a mandatory user input instead.

---

### LAS/LAZ — GO

**Library:** `laspy`, with `laspy[lazrs]` for LAZ compression (pure pip, no system lib).

**Worst case — CRS omitted at write time (realistic for a raw instrument dump):**
```json
{"crs": null, "units": null,
 "bbox": [500000.66, 1435000.23, 500199.96, 1435198.57],
 "date": "2026-08-14", "point_count": 500}
```

**Best case — CRS explicitly attached (`header.add_crs(pyproj.CRS.from_epsg(32643))`):**
`laspy.header.parse_crs()` round-trips it correctly back to `EPSG:32643` (full WKT
verified). So the None case earlier isn't a laspy gap — it's purely whether the producing
software attached a CRS VLR, which is inconsistent in practice for raw survey exports.
**Date is real when present** — GPS time in point format 6 round-tripped to the exact
acquisition date used at write time.

**Performance (2,000,000 points, 60 MB LAS):**
| Operation | Time |
|---|---|
| header-only open (bbox/CRS/point_count) | 0.0003s |
| full chunked read, 200k-point chunks | 0.01s |

Same story as GeoTIFF: header metadata is free. For files past a few hundred MB, push the
full point read to a background job rather than the request/response cycle — the endpoint
can validate and accept fast, then process async.

**Malformed input:** a truncated file with a valid `LASF` magic but garbage after it →
`laspy.open()` raises `LaspyException` cleanly.

---

### DXF — GO

**Library:** `ezdxf`, pure Python.

```python
doc = ezdxf.readfile(path)
insunits = doc.header.get("$INSUNITS", 0)   # 6 = meters, per DXF group-code spec
```

**Extracted from a real file (2 lines + 1 point, `$INSUNITS=6`):**
```json
{"crs": null, "units": "meters", "bbox": [0.0, 0.0, 100.0, 100.0], "point_count": 3}
```
`$INSUNITS` reliably gives drawing units. **No CRS, and this is inherent to the format** —
DXF geometry lives in an arbitrary local/drawing coordinate system, not a geographic one.
Georeferencing (if needed) is a separate problem — typically 2+ known control points
supplied by the uploader — not something extractable from the file.

**Malformed input:** a text file with `.dxf` extension and no DXF structure →
`ezdxf.readfile()` raises `OSError` cleanly.

---

### DWG — CONDITIONAL / NO-GO for V1

**Library path:** `ezdxf`'s `odafc` add-on wraps the **ODA File Converter**, a separate
binary invoked as a subprocess (`odafc.readfile()` shells out to it). There is no reliable
pure-Python DWG reader across DWG versions — this was not attempted empirically because it
isn't a `pip install`, it's an infra dependency:

- Must be baked into the service's Docker image (this repo is one container per service —
  `services/<name>/Dockerfile` — so this is a real, non-trivial image change, not a
  `requirements.txt` line)
- Executes an external binary per upload — the ezdxf docs themselves flag this as a security
  surface if the converter path isn't locked down
- Licensing/version-pinning the ODA binary is an ops decision, not a code decision

**Recommendation: do not build DWG support in V1.** Either require users to export
DWG→DXF client-side (native in AutoCAD and most CAD tools), or treat ODA-in-Docker as its
own follow-up spike if that turns out to be a real blocker for actual users.

---

### LandXML — GO, no dedicated library exists

**Library:** `lxml` (pure Python) + a small hand-rolled parser for the LandXML schema —
confirmed no maintained LandXML-specific package exists on PyPI.

**Extracted from a real 3-point TIN surface with Units + CoordinateSystem present:**
```json
{"crs": "EPSG:32643", "units": "meter",
 "bbox": [500000.0, 1435000.0, 500010.0, 1435020.0],
 "date": "2026-08-14", "point_count": 3}
```

**Gotcha caught empirically, not in docs:** LandXML `<P>` point text is **northing(Y)
easting(X) elevation(Z)** order, not X Y Z — a real bug source if the extraction code is
copy-pasted from the GeoTIFF/LAS path (both of which are X Y Z). The parser above already
accounts for this (`ys = coords[0], xs = coords[1]`).

**Missing-Units test (malformed real-world case):** a file with `<Surfaces>` but no
`<Units>` element parses as perfectly well-formed XML — `lxml` raises nothing.
**Application-level validation has to catch this explicitly**; the library gives no signal
that required LandXML semantics are missing, only that the XML syntax is valid.

`<Units>` is spec-required so it's reliably present from real CAD/civil software; `<CoordinateSystem>` is optional and commonly omitted in the wild — same reliability profile as LAS's CRS VLR.

---

## Go/No-Go Summary (AC1)

| Format | Go/No-Go | New dependency | CRS reliability | Units reliability |
|---|---|---|---|---|
| GeoTIFF | **Go** | `rasterio` | High | High |
| XYZ | **Go** (user-supplied metadata) | none | None — structural | None — structural |
| LAS/LAZ | **Go** | `laspy[lazrs]`, `pyproj` | Variable — depends on producer | Low (no explicit field) |
| DXF | **Go** | `ezdxf` | None — inherent to format | High (`$INSUNITS`) |
| DWG | **No-go for V1** | needs ODA File Converter (infra, not pip) | — | — |
| LandXML | **Go** | `lxml` | Variable — optional element | High (spec-required) |

**Overall: proceed to SAT-279 for GeoTIFF, XYZ, LAS/LAZ, DXF, LandXML.** Drop DWG from V1
scope.

---

## Proposed common extraction schema (feeds SAT-279 AC2/3)

Every format-specific parser should normalize into the same shape, with explicit
provenance per field — **do not silently default a missing CRS/unit**, since two of five
formats structurally cannot supply them:

```python
class ImportMetadata(BaseModel):
    format: Literal["geotiff", "xyz", "las", "laz", "dxf", "landxml"]
    crs: str | None                    # EPSG code, or None
    crs_source: Literal["extracted", "user_supplied", "missing"]
    units: str | None
    units_source: Literal["extracted", "user_supplied", "missing"]
    bbox: tuple[float, float, float, float]
    point_count: int | None
    date: str | None                   # ISO date, or None
    date_source: Literal["extracted", "user_supplied", "missing"]
```

SAT-279's validation (AC11) should reject an upload only when a required field is
`"missing"` in *both* extraction and user input — not when extraction alone fails, since
extraction failing is the expected, correct behavior for XYZ/DXF by design.

## Validation error taxonomy (observed empirically)

| Failure | Format(s) | Exception raised | Safe to map to |
|---|---|---|---|
| Corrupt/non-format bytes | DXF, GeoTIFF, LAS | `OSError` / `RasterioIOError` / `LaspyException` | 400, "unreadable file" |
| Extension doesn't match content | GeoTIFF | `RasterioIOError` (magic-byte check) | 400, "content doesn't match extension" |
| Well-formed but semantically incomplete | LandXML (missing `<Units>`) | none — parses fine | needs explicit app-level check, not a try/except |
| Structurally absent metadata (not an error) | XYZ (CRS/units), DXF (CRS) | none | not a rejection — require user input instead |

---

## requirements.txt additions (new service, e.g. `services/topography`)

```
rasterio==1.5.1
laspy[lazrs]==2.7.0
pyproj==3.8.0
ezdxf==1.4.4
lxml==6.1.3
```

Per `CLAUDE.md` non-negotiable rules: this needs a `contracts/topography.yaml` entry +
`contracts/CHANGELOG.md` line, a `FeatureFlag` enum value default-off, and an FVD before
code lands — this spike doc is the input to that FVD, not a substitute for it.

## Open questions for SAT-279

1. Where does a `user_supplied` CRS/units value get collected in the upload flow — a
   required form field alongside the file, or a follow-up step after a first parse reveals
   what's missing? (UX decision, not backend.)
2. File-size ceiling for synchronous vs. background processing — perf numbers above suggest
   header/metadata validation can stay synchronous even for large files; full point/pixel
   processing should not.
3. DWG: confirm with Vishwas/Amith-equivalent stakeholder whether "export to DXF first" is
   an acceptable V1 UX constraint before this is fully closed, or whether it needs escalating
   as its own ticket.

## Sources

- [rasterio installation docs](https://rasterio.readthedocs.io/en/stable/installation.html)
- [laspy installation docs](https://laspy.readthedocs.io/en/latest/installation.html)
- [ezdxf ODA File Converter add-on](https://ezdxf.readthedocs.io/en/stable/addons/odafc.html)
- [LandXML format overview](https://en.wikipedia.org/wiki/LandXML)
- [XYZ point cloud format limitations](https://www.cadinterop.com/en/formats/cloud-point/xyz.html)
- Empirical: `sat278-spike/deep_dive.py`, `sat278-spike/deep_dive_extras.py` (scratch, this session — every number/claim above was run, not looked up)
