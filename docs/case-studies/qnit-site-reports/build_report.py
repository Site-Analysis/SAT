"""Build the 13-page Qnit site report (HTML) for one site from results/<site>.json + figures/ + research/."""

import base64
import json
import math
import pickle
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Template
from shapely.ops import unary_union

from sites import ROOT, SITES

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
S = SITES[n]
R = json.loads((ROOT / "results" / f"{S.id}.json").read_text())
G = pickle.load(open(ROOT / "cache" / S.id / "geoms.pkl", "rb"))
FIG = ROOT / "figures"
ASSET = ROOT / "assets"
DATE = "10 Oct 2026"
REV = "Rev A"


def img(path):
    p = Path(path)
    mime = "image/png" if p.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


f = lambda name: img(next(FIG.glob(f"{S.id}_{name}.*"))) if list(FIG.glob(f"{S.id}_{name}.*")) else None
fmt = lambda v, d=0: f"{round(v, d):,.{max(d, 0)}f}"
geo, ter, cli, sol, lc = R["geometry"], R["terrain"], R["climate"], R["solar"], R["landcover"]
wst = R["wind"]["station"]
wmd = R["wind"]["model"]
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---- derived numbers (deterministic, from results + cached geometry)
streams = [x for x in G["streams"] if x["dist_m"] < 30]
sline = unary_union([x["geom"] for x in streams]) if streams else None
buf = {b: (S.poly.intersection(sline.buffer(b)).area if sline else 0.0) for b in (15, 25, 50)}
park10 = 0.10 * geo["area_m2"]
civic5 = 0.05 * geo["area_m2"]
q10 = cli["gumbel_1day_mm"]["10"]
vol_gross = q10 / 1000 * geo["area_m2"]
vol_now = 0.35 * vol_gross
vol_built = 0.75 * vol_gross
lakes = [l for l in R["water"]["lakes"] if l["class"] in ("lake", "reservoir")]
lake1 = dict(lakes[0] if lakes else R["water"]["lakes"][0])
lake1["name"] = lake1["name"] or "an unnamed lake"
drain1 = R["water"]["drains"][0]["dist_m"] if R["water"]["drains"] else None
proad = R["plan"]["roads"][0] if R["plan"]["roads"] else None
inf = R["infrastructure"]
af = R["airfields"]
poi = R["access"]["poi"]
sky = R["skyline"]
# vertical exaggeration of the printed transect (fig 7.2 x 1.05 in, axes ~92% x 70%)
tr = ter["transect"]
ve = ((0.70 * 1.05) / (tr["zmax"] - tr["zmin"] + 4)) / ((0.92 * 7.2) / tr["length_m"])
grocery = next((p for p in poi["Daily needs"] if p["cat"] in ("grocery_store", "supermarket", "convenience_store")), poi["Daily needs"][0])
walk_min = lambda m: round(m / 80)
sm = wst["seasons"]["SW monsoon (Jun–Sep)"]
wi = wst["seasons"]["Winter (Dec–Feb)"]
zone_in = (R["plan"]["zones"] or {}).get("inside_pct", {})
zone_top = next(iter(zone_in.items()), (None, None))
sens = R.get("sensitive", {})
research = json.loads((ROOT / "research" / f"site{n}.json").read_text())

V = dict(
    S=S, R=R, geo=geo, ter=ter, cli=cli, sol=sol, lc=lc, wst=wst, wmd=wmd, fmt=fmt, MON=MON, DATE=DATE, REV=REV,
    buf=buf, park10=park10, civic5=civic5, q10=q10, vol_gross=vol_gross, vol_now=vol_now, vol_built=vol_built, lake1=lake1,
    drain1=drain1, proad=proad, inf=inf, af=af, poi=poi, sky=sky, ve=ve, grocery=grocery, walk_min=walk_min, sm=sm, wi=wi,
    zone_top=zone_top, zone_in=zone_in, tr=tr, sens=sens, gen=R["generated_utc"][:16].replace("T", " "),
    fig={k: f(k) for k in ["hero", "boundary", "zoning_screenshot", "terrain", "transect", "sunpath", "sunpolar", "solar", "windmap",
                          "windrose", "comfort", "temperature", "runoff", "rainfall", "groundwater", "landscape", "context",
                          "skyline", "isochrones", "landuse_change", "density", "services", "airport"]},
    logo=img(ASSET / "tpl" / "Im5.png"), qmark=img(ASSET / "tpl" / "Im36.png"), geoace=img(ASSET / "tpl" / "Im28.png"),
    layers_cover=img(ASSET / "tpl" / "Im10.png"), layers_back=img(ASSET / "tpl" / "Im778.png"),
    ic_land=img(ASSET / "tpl" / "Im443.png"), ic_veg=img(ASSET / "tpl" / "Im445.png"), ic_built=img(ASSET / "tpl" / "Im447.png"),
    ph_court=img(ASSET / "photos" / "Mangaluru_tiles_Home.jpg"), ph_ver=img(ASSET / "photos" / "Melkoute.village_house.jpg"),
    ph_roof=img(ASSET / "photos" / "Village_House_in_Krishnarajapet.jpg"), ph_street=img(ASSET / "photos" / "Village_House_in_Malavalli.jpg"),
)

CSS = """
@page { size: A4; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0; background: #fff }
body { font-family: 'Liberation Sans', Arial, Helvetica, sans-serif; color: #111; -webkit-print-color-adjust: exact; print-color-adjust: exact }
.page { width: 210mm; height: 297mm; position: relative; overflow: hidden; page-break-after: always; break-after: page }
.page:last-child { page-break-after: auto }
.kicker { position: absolute; left: 17.3mm; top: 17.2mm; font-size: 8.4pt; font-weight: 700; letter-spacing: .1pt }
.hrule { position: absolute; left: 17.3mm; top: 23.9mm; width: 149.5mm; border-top: .9pt solid #333 }
.qmark { position: absolute; left: 182.6mm; top: 15mm; width: 9.8mm }
.title { position: absolute; left: 17.3mm; top: 31.5mm; font-size: 21.5pt; font-weight: 700; letter-spacing: -.2pt }
.sub { position: absolute; left: 17.3mm; top: 43.6mm; font-size: 8.3pt; color: #555 }
.foot { position: absolute; left: 17.3mm; right: 17.5mm; top: 279.7mm; border-top: .6pt solid #c9c9c9; padding-top: 3.4mm; font-size: 8pt; display: flex; justify-content: space-between }
.foot b { font-size: 8.4pt }
.foot span { color: #666; font-size: 7.3pt }
.body { position: absolute; left: 17.3mm; right: 17.5mm; top: 55mm; bottom: 20mm }
.fig { width: 100%; border-radius: 2.2mm; display: block; object-fit: cover }
.cap { font-size: 6.6pt; color: #555; margin-top: 2.2mm; line-height: 1.35; letter-spacing: .1pt }
.cap b { font-weight: 400; color: #333; letter-spacing: .3pt }
.lbl { font-size: 7.3pt; font-weight: 700; color: #555; letter-spacing: .3pt; text-transform: uppercase }
.glbl { font-size: 7.6pt; font-weight: 700; color: #557a2e; letter-spacing: .3pt; text-transform: uppercase }
.big { font-size: 25pt; font-weight: 700; letter-spacing: -.3pt; margin: 2.2mm 0 1.6mm }
.mid { font-size: 13.5pt; font-weight: 700; margin: 2mm 0 1.5mm }
.small { font-size: 7.6pt; color: #555; line-height: 1.38 }
h2 { font-size: 13.5pt; margin: 0 0 2.2mm; padding-bottom: 2.2mm; border-bottom: .6pt solid #d4d4d4; font-weight: 700 }
p, .txt { font-size: 9pt; line-height: 1.38; margin: 0 }
.grey { color: #555 }
.row { display: flex; gap: 8mm }
.col { flex: 1; min-width: 0 }
.impl { position: absolute; left: 0; right: 0; bottom: 1.5mm; border-top: 1.1pt solid #777; padding-top: 3.6mm; background: #fff }
.impl .glbl { font-size: 7.4pt }
.impl p { font-size: 9pt; margin-top: 2mm; line-height: 1.36 }
table.t { width: 100%; border-collapse: collapse; font-size: 7.6pt }
table.t th { background: #eef4ec; text-align: left; font-weight: 700; padding: 2.3mm 2.2mm; border: .8pt solid #222; border-bottom: 1.3pt solid #222 }
table.t td { padding: 2.1mm 2.2mm; border: .8pt solid #222; vertical-align: top; line-height: 1.3 }
.kv div { font-size: 8.9pt; line-height: 1.55 }
.kv span { color: #555 }
.chip { display: inline-block; font-size: 6.3pt; padding: .5mm 1.6mm; border-radius: 3mm; background: #eef4ec; color: #3e6a1f; font-weight: 700; margin-left: 1mm; vertical-align: 1px }
.prio { display: flex; gap: 6mm; border-bottom: .6pt solid #ddd; padding: 3.6mm 0 3.4mm }
.prio .num { font-size: 27pt; font-weight: 700; color: #557a2e; width: 19mm; line-height: 1 }
.prio .h { font-size: 13.2pt; font-weight: 700; margin-bottom: 1.6mm }
.prio .e { font-size: 8.4pt; line-height: 1.35 }
.prio .a { font-size: 7.3pt; color: #666; margin-top: 1.6mm }
"""

PAGES = (ROOT / "templates" / f"{S.id}.html.j2").read_text()

V["streams_d"] = min((x["dist_m"] for x in streams), default=0)
html = f"<!doctype html><html><head><meta charset='utf-8'><title>{S.report_id} — {S.name}</title><style>{CSS}</style></head><body>" + Template(PAGES).render(**V) + "</body></html>"
out = ROOT / "out" / f"{S.report_id}.html"
out.write_text(html)
(ROOT / "out" / f"{S.report_id}.numbers.json").write_text(json.dumps({"buffers_m2": buf, "park10": park10, "civic5": civic5, "vol_now": vol_now,
                                                                       "vol_built": vol_built, "ve": ve}, indent=1))
print(out, len(html) // 1024, "KB")
