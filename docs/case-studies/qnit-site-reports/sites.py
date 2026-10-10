"""Site definitions: KML polygons, supplied cadastral records, plan screenshots."""

import math
import re
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, Polygon

ROOT = Path(__file__).resolve().parent
KML = Path("/root/.claude/uploads/507845f5-20bd-5a45-adb7-2573e0a1e57d/02d3938b-Case_Studies.kml")
SCREENSHOTS = Path("/tmp/claude-0/-home-user/507845f5-20bd-5a45-adb7-2573e0a1e57d/images")

TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
TO_WGS = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)


def _parse_kml(path=KML):
    text = path.read_text()
    out = {}
    for name, coords in re.findall(r"<name>(Site \d)</name>.*?<coordinates>\s*(.*?)\s*</coordinates>", text, re.S):
        pts = [tuple(map(float, c.split(",")[:2])) for c in coords.split()]
        out[int(name.split()[1])] = pts
    return out


# Supplied records (user message, 10 Oct 2026). Party names deliberately omitted.
RECORDS = {
    1: {
        "village": "Bannerughatta",
        "village_code": "613132",
        "taluk": "Anekal",
        "district": "Bengaluru Urban",
        "locality": "Bannerughatta, Anekal taluk, Bengaluru",
        "plan": "BDA LPA — RMP 2015 (approved) · RMP 2031 (draft)",
        "authority": "Bengaluru Development Authority (BDA)",
        "screenshot": "3.webp",
        "screenshot_caption": "Qnit 2031 plan layer — BDA RMP 2031 (draft): Agriculture zone, 45 m proposed road",
        "surveys": [
            {"sy": "21/*/*", "lat": 12.818392, "lon": 77.580804, "rccms": "No active cases", "cases": 0, "mutations": []},
            {"sy": "22/*/1", "lat": 12.818340, "lon": 77.581501, "rccms": "4 cases, all disposed", "cases": 4,
             "mutations": ["MR 2/2026-27 — dispute verdict pending entry (Shirastedar login)"]},
        ],
    },
    2: {
        "village": "Tindlu",
        "village_code": "625674",
        "taluk": "Hoskote",
        "district": "Bengaluru Rural",
        "locality": "Tindlu, Hoskote taluk, Bengaluru Rural",
        "plan": "Hoskote LPA Master Plan 2031 (Map 69/70)",
        "authority": "Hoskote Planning Authority (BMRDA)",
        "screenshot": "1.webp",
        "screenshot_caption": "Qnit 2031 plan layer — Hoskote MP 2031: Agriculture zone, STRR, forest to the south",
        "surveys": [
            {"sy": s, "lat": la, "lon": lo, "rccms": r, "cases": c, "mutations": []}
            for s, la, lo, r, c in [
                ("26/*/6", 12.991992, 77.854915, "8 disposed", 8), ("26/*/7", 12.991637, 77.855473, "8 disposed", 8),
                ("26/*/5", 12.991814, 77.855859, "8 disposed", 8), ("26/*/2", 12.991459, 77.856202, "8 disposed", 8),
                ("26/*/3", 12.991867, 77.856910, "8 disposed", 8), ("26/*/4", 12.991584, 77.857275, "8 disposed", 8),
                ("24/*/4", 12.991198, 77.857972, "2 disposed", 2), ("24/*/3", 12.991595, 77.857967, "2 disposed", 2),
                ("24/*/2", 12.991841, 77.858208, "2 disposed", 2), ("24/*/1", 12.992384, 77.858235, "2 disposed", 2),
                ("26/*/8", 12.992384, 77.856873, "8 disposed", 8), ("26/*/1", 12.992457, 77.856379, "8 disposed", 8),
                ("23/*/2", 12.992379, 77.859592, "No active cases", 0), ("22/*/1", 12.991757, 77.859077, "1 disposed", 1),
                ("21/*/3", 12.991135, 77.859415, "4 disposed", 4), ("21/*/2B", 12.991041, 77.860097, "4 disposed", 4),
                ("21/*/2A", 12.990826, 77.859957, "4 disposed", 4), ("23/*/1", 12.992771, 77.859094, "No active cases", 0),
                ("28/*/4", 12.992990, 77.858235, "No active cases", 0),
            ]
        ],
        # From the user's parcel-map screenshot of the KML area (no coordinates / no RCCMS supplied).
        "parcel_map_surveys": ["36", "37", "27/1–8", "28/1–6", "35/1–4", "29 (edge)", "32 (edge)", "34 (edge)"],
        "parcel_map_note": "Sy 35/*/1 circled on the supplied parcel map — purpose to confirm",
    },
    3: {
        "village": "Kogilu",
        "village_code": "938519",
        "taluk": "Yelahanka (Bengaluru North)",
        "district": "Bengaluru Urban",
        "locality": "Kogilu, Yelahanka, Bengaluru",
        "plan": "BDA LPA — RMP 2015 (approved) · RMP 2031 (draft)",
        "authority": "Bengaluru Development Authority (BDA)",
        "screenshot": "2.webp",
        "screenshot_caption": "Qnit 2031 plan layer — BDA RMP 2031 (draft): Residential zone, 18 m / 12 m proposed roads",
        "surveys": [
            {"sy": "28/*/XX", "lat": 13.099206, "lon": 77.609302, "rccms": "No active cases", "cases": 0, "mutations": []},
            {"sy": "27/*/1", "lat": 13.098375, "lon": 77.608508, "rccms": "No active cases", "cases": 0, "mutations": []},
        ],
    },
    4: {
        "village": "Sadahalli",
        "village_code": "625397",
        "taluk": "Devanahalli",
        "district": "Bengaluru Rural",
        "locality": "Sadahalli, Devanahalli taluk, Bengaluru Rural",
        "plan": "BIAAPA Master Plan 2021 (no 2031 plan published)",
        "authority": "Bangalore International Airport Area Planning Authority (BIAAPA)",
        "screenshot": None,
        "screenshot_caption": None,
        "surveys": [
            {"sy": "168/*/*", "lat": 13.201802, "lon": 77.649822, "rccms": "No active cases", "cases": 0, "mutations": []},
            {"sy": "169/*/*", "lat": 13.201740, "lon": 77.650809, "rccms": "Not reported", "cases": None, "mutations": []},
            {"sy": "186/*/*", "lat": 13.200486, "lon": 77.651217, "rccms": "Not reported", "cases": None, "mutations": []},
            {"sy": "188/*/*", "lat": 13.200591, "lon": 77.648406, "rccms": "Not reported", "cases": None, "mutations": []},
            {"sy": "189/*/*", "lat": 13.200862, "lon": 77.646668, "rccms": "1 case, disposed", "cases": 1, "mutations": []},
            {"sy": "190/*/*", "lat": 13.200883, "lon": 77.646024, "rccms": "Not reported", "cases": None, "mutations": []},
        ],
    },
}


class Site:
    def __init__(self, n):
        self.n = n
        self.ll = _parse_kml()[n]  # lon, lat ring (closed)
        self.rec = RECORDS[n]
        self.poly_ll = Polygon(self.ll)
        self.utm = [TO_UTM.transform(*p) for p in self.ll]
        self.poly = Polygon(self.utm)
        c = self.poly.centroid
        self.cx, self.cy = c.x, c.y
        self.lon, self.lat = TO_WGS.transform(c.x, c.y)
        self.id = f"S0{n}"
        self.report_id = f"QNIT-BLR-S0{n}"
        self.name = f"Site {n} — {self.rec['village']}"

    @property
    def vertices(self):
        return self.utm[:-1]

    def edges(self):
        out = []
        v = self.vertices
        for i in range(len(v)):
            a, b = v[i], v[(i + 1) % len(v)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            brg = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            out.append({"i": i, "a": a, "b": b, "len": math.hypot(dx, dy), "bearing": brg, "mid": mid})
        return out

    def survey_inside(self):
        res = []
        for s in self.rec["surveys"]:
            x, y = TO_UTM.transform(s["lon"], s["lat"])
            p = Point(x, y)
            res.append({**s, "inside": self.poly.contains(p), "dist_m": 0.0 if self.poly.contains(p) else p.distance(self.poly)})
        return res


SITES = {n: Site(n) for n in (1, 2, 3, 4)}

if __name__ == "__main__":
    for s in SITES.values():
        print(s.name, round(s.lat, 6), round(s.lon, 6), round(s.poly.area), round(s.poly.length), len(s.vertices))
