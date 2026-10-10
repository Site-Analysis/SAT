"""Turn cached data into results/<site>.json — the only source of every number printed in the report."""

import gzip
import heapq
import io
import json
import math
import sys
from datetime import datetime, timezone

import networkx as nx
import numpy as np
import pandas as pd
import pvlib
import pyarrow.parquet as pq
import rasterio
from pmtiles.reader import MmapSource, Reader
from PIL import Image
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject
from shapely import wkb
from shapely.geometry import LineString, MultiLineString, Point, Polygon, mapping, shape
from shapely.ops import transform, unary_union

from sites import ROOT, SITES, TO_UTM, TO_WGS

CACHE = ROOT / "cache"
YEARS = (2015, 2024)  # climate window (10 full years)
utm = lambda g: transform(lambda x, y, z=None: TO_UTM.transform(x, y), g)
wgs = lambda g: transform(lambda x, y, z=None: TO_WGS.transform(x, y), g)
COMPASS16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
compass = lambda deg: COMPASS16[int(((deg % 360) + 11.25) // 22.5) % 16]
COMPASS8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
compass8 = lambda deg: COMPASS8[int(((deg % 360) + 22.5) // 45) % 8]


def r(x, n=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)


# ---------------------------------------------------------------- geometry
def geometry(s):
    letters = [chr(65 + i) for i in range(len(s.vertices))]
    edges = []
    for e in s.edges():
        a, b = letters[e["i"]], letters[(e["i"] + 1) % len(letters)]
        # outward normal facing: bearing of edge rotated -90 (polygon CW?) -> test with a point
        nx_, ny_ = math.sin(math.radians(e["bearing"] + 90)), math.cos(math.radians(e["bearing"] + 90))
        probe = Point(e["mid"][0] + nx_ * 5, e["mid"][1] + ny_ * 5)
        face = (e["bearing"] + 90) % 360 if not s.poly.contains(probe) else (e["bearing"] - 90) % 360
        edges.append({"name": f"{a}–{b}", "len_m": r(e["len"]), "bearing": r(e["bearing"]), "faces": compass8(face),
                      "faces_deg": r(face), "a": e["a"], "b": e["b"], "mid": e["mid"]})
    minx, miny, maxx, maxy = s.poly.bounds
    mrr = s.poly.minimum_rotated_rectangle
    c = list(mrr.exterior.coords)
    sides = sorted([math.dist(c[i], c[i + 1]) for i in range(4)])
    long_side = max(range(4), key=lambda i: math.dist(c[i], c[i + 1]))
    ang = math.degrees(math.atan2(c[long_side + 1][0] - c[long_side][0], c[long_side + 1][1] - c[long_side][1])) % 180
    return {
        "area_m2": r(s.poly.area, 0), "area_ha": r(s.poly.area / 1e4, 2), "area_acre": r(s.poly.area / 4046.856, 2),
        "area_guntas": r(s.poly.area / 101.17, 0), "area_sqft": r(s.poly.area * 10.7639, 0),
        "perimeter_m": r(s.poly.length, 0), "n_edges": len(s.vertices),
        "centroid": [r(s.lat, 6), r(s.lon, 6)], "bbox_m": [r(maxx - minx, 0), r(maxy - miny, 0)],
        "study_extent_m": r(math.hypot(maxx - minx, maxy - miny), 0),
        "long_axis_deg": r(ang, 0), "rect_dims_m": [r(sides[2], 0), r(sides[0], 0)],
        "compactness": r(4 * math.pi * s.poly.area / s.poly.length ** 2, 2),
        "vertices_ll": [[r(TO_WGS.transform(*v)[1], 6), r(TO_WGS.transform(*v)[0], 6)] for v in s.vertices],
        "edges": [{k: v for k, v in e.items() if k not in ("a", "b", "mid")} for e in edges],
        "_edges_geom": edges,
        "surveys": [{**{k: v for k, v in sv.items() if k != "mutations"}, "mutations": sv["mutations"], "dist_m": r(sv["dist_m"], 0)}
                    for sv in s.survey_inside()],
    }


# ---------------------------------------------------------------- vector helpers
def read_ov(s, typ):
    p = CACHE / s.id / f"ov_{typ}.parquet"
    if not p.exists():
        return pd.DataFrame()
    df = pq.read_table(p).to_pandas()
    df["geom"] = [utm(wkb.loads(g)) for g in df["geometry"]]
    return df


def name_of(n):
    if isinstance(n, dict):
        return n.get("primary")
    return None


# ---------------------------------------------------------------- plan zones (PMTiles raster) + plan roads
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def plan_zones(s, plan_id, z=15):
    man = json.loads((CACHE / "plan" / "manifest.json").read_text())
    legend = man["plans"][plan_id]["legend"]
    cols = np.array([hex2rgb(l["colour"]) for l in legend], float)
    with open(CACHE / "plan" / f"{plan_id}.pmtiles", "rb") as f:
        rd = Reader(MmapSource(f))
        hdr = rd.header()
        n = 2**z
        lo1, la1, lo2, la2 = [*TO_WGS.transform(*s.poly.buffer(250).bounds[:2]), *TO_WGS.transform(*s.poly.buffer(250).bounds[2:])]

        def txy(lo, la):
            return (lo + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2 * n

        x1, y1 = txy(lo1, la2)
        x2, y2 = txy(lo2, la1)
        tiles = {}
        for tx in range(int(x1), int(x2) + 1):
            for ty in range(int(y1), int(y2) + 1):
                b = rd.get(z, tx, ty)
                if b:
                    tiles[(tx, ty)] = Image.open(io.BytesIO(b)).convert("RGBA")
    if not tiles:
        return None
    ts = next(iter(tiles.values())).size[0]
    W = (int(x2) - int(x1) + 1) * ts
    H = (int(y2) - int(y1) + 1) * ts
    mos = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (tx, ty), im in tiles.items():
        mos.paste(im, ((tx - int(x1)) * ts, (ty - int(y1)) * ts))
    arr = np.asarray(mos).astype(float)
    # pixel centres -> lon/lat -> utm
    py, px = np.mgrid[0:H, 0:W]
    fx = int(x1) + (px + 0.5) / ts
    fy = int(y1) + (py + 0.5) / ts
    lon = fx / n * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * fy / n))))
    ux, uy = TO_UTM.transform(lon, lat)
    from shapely import contains_xy

    def shares(geom):
        m = contains_xy(geom, ux, uy)
        rgb = arr[m][:, :3]
        a = arr[m][:, 3]
        rgb = rgb[a > 90]
        if len(rgb) == 0:
            return {}, 0
        d = ((rgb[:, None, :] - cols[None, :, :]) ** 2).sum(-1)
        idx = d.argmin(1)
        ok = d.min(1) < 40**2
        out = {}
        for i in np.unique(idx[ok]):
            out[legend[i]["label"]] = r(100 * (idx[ok] == i).sum() / m.sum(), 1)
        return dict(sorted(out.items(), key=lambda kv: -kv[1])), int(m.sum())

    inside, npx = shares(s.poly)
    ring, _ = shares(s.poly.buffer(150).difference(s.poly))
    mos.save(CACHE / s.id / f"plan_{plan_id}.png")
    meta = {"lon1": float(int(x1) / n * 360 - 180), "lon2": float((int(x2) + 1) / n * 360 - 180),
            "lat1": float(np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (int(y2) + 1) / n))))),
            "lat2": float(np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * int(y1) / n)))))}
    (CACHE / s.id / f"plan_{plan_id}.json").write_text(json.dumps(meta))
    return {"plan_id": plan_id, "zoom": z, "inside_pct": inside, "ring150_pct": ring, "pixels": npx,
            "legend": legend, "built_at": man["plans"][plan_id]["built_at"]}


def plan_roads(s, plan_id, within=400):
    with gzip.open(CACHE / "plan" / f"{plan_id}.roads.geojson.gz") as f:
        fc = json.load(f)
    out = []
    zone = s.poly.buffer(within)
    for ft in fc["features"]:
        g = shape(ft["geometry"])
        lo, la = g.centroid.x, g.centroid.y
        if abs(lo - s.lon) > 0.02 or abs(la - s.lat) > 0.02:
            continue
        gu = utm(g)
        if not gu.intersects(zone):
            continue
        p = ft["properties"]
        out.append({"row_m": p.get("row_m"), "status": p.get("status"), "confidence": p.get("confidence"),
                    "name": p.get("road_name"), "dist_m": r(gu.distance(s.poly), 0), "touches": gu.distance(s.poly) < 15,
                    "geom": gu})
    return out


# ---------------------------------------------------------------- terrain
def dem_utm(s, buf=1500, res=10):
    with rasterio.open(CACHE / s.id / "dem.tif") as ds:
        minx, miny, maxx, maxy = s.poly.buffer(buf).bounds
        W, H = int((maxx - minx) / res), int((maxy - miny) / res)
        tr = rasterio.transform.from_origin(minx, maxy, res, res)
        dst = np.full((H, W), np.nan, "float32")
        reproject(rasterio.band(ds, 1), dst, dst_transform=tr, dst_crs="EPSG:32643", resampling=Resampling.bilinear)
    return dst, tr


def priority_flood(z):
    H, W = z.shape
    f = z.copy()
    closed = np.zeros_like(z, bool)
    pq_ = []
    for i in range(H):
        for j in (0, W - 1):
            heapq.heappush(pq_, (f[i, j], i, j)); closed[i, j] = True
    for j in range(W):
        for i in (0, H - 1):
            if not closed[i, j]:
                heapq.heappush(pq_, (f[i, j], i, j)); closed[i, j] = True
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    while pq_:
        e, i, j = heapq.heappop(pq_)
        for di, dj in nb:
            a, b = i + di, j + dj
            if 0 <= a < H and 0 <= b < W and not closed[a, b]:
                closed[a, b] = True
                if f[a, b] < e:
                    f[a, b] = e + 1e-4
                heapq.heappush(pq_, (f[a, b], a, b))
    return f


def d8(z, res):
    H, W = z.shape
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    dist = [math.hypot(a, b) * res for a, b in nb]
    rec = np.full((H, W, 2), -1, int)
    for i in range(H):
        for j in range(W):
            best, bk = 0, -1
            for k, (di, dj) in enumerate(nb):
                a, b = i + di, j + dj
                if 0 <= a < H and 0 <= b < W:
                    sl = (z[i, j] - z[a, b]) / dist[k]
                    if sl > best:
                        best, bk = sl, k
            if bk >= 0:
                rec[i, j] = (i + nb[bk][0], j + nb[bk][1])
    order = np.argsort(-z, axis=None)
    acc = np.ones((H, W))
    for idx in order:
        i, j = divmod(int(idx), W)
        a, b = rec[i, j]
        if a >= 0:
            acc[a, b] += acc[i, j]
    return rec, acc


def terrain(s):
    z, tr = dem_utm(s, buf=1200, res=10)
    res = 10.0
    mask = ~geometry_mask([mapping(s.poly)], z.shape, tr)
    zin = z[mask]
    gy, gx = np.gradient(z, res)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    slope_pct = 100 * np.hypot(gx, gy)
    aspect = (np.degrees(np.arctan2(-gx, gy)) + 180) % 360  # downslope direction (0=N)
    # mean downslope over site from plane fit
    ii, jj = np.nonzero(mask)
    X = np.c_[tr.c + (jj + 0.5) * res, tr.f - (ii + 0.5) * res, np.ones(len(ii))]
    coef, *_ = np.linalg.lstsq(X, zin, rcond=None)
    plane_slope = 100 * math.hypot(coef[0], coef[1])
    plane_down = (math.degrees(math.atan2(-coef[0], -coef[1]))) % 360
    # low / high points
    lo_i = np.argmin(np.where(mask, z, np.inf))
    hi_i = np.argmax(np.where(mask, z, -np.inf))
    li, lj = divmod(int(lo_i), z.shape[1])
    hi, hj = divmod(int(hi_i), z.shape[1])
    xy = lambda i, j: (tr.c + (j + 0.5) * res, tr.f - (i + 0.5) * res)
    # transect along the plane's fall line through the centroid, extended 150 m past the site
    d = math.radians(plane_down)
    ux, uy = math.sin(d), math.cos(d)
    line = LineString([(s.cx - ux * 1000, s.cy - uy * 1000), (s.cx + ux * 1000, s.cy + uy * 1000)])
    inter = line.intersection(s.poly)
    (ax, ay), (bx, by) = list(inter.coords)[0], list(inter.coords)[-1]
    A = (ax - ux * 150, ay - uy * 150)
    B = (bx + ux * 150, by + uy * 150)
    L = math.dist(A, B)
    samples = []
    from scipy.ndimage import map_coordinates

    for k in range(int(L // 5) + 1):  # bilinear on the 10 m resample
        t = k * 5 / L
        x, y = A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t
        fj, fi = (x - tr.c) / res - 0.5, (tr.f - y) / res - 0.5
        v = map_coordinates(z, [[fi], [fj]], order=1)[0]
        samples.append([r(k * 5, 0), r(float(v), 2), s.poly.contains(Point(x, y))])
    zs = [p[1] for p in samples]
    # flow on 30 m grid (DEM native) for the catchment / flow lines
    z30, tr30 = dem_utm(s, buf=1200, res=30)
    zf = priority_flood(np.nan_to_num(z30, nan=np.nanmax(z30)))
    rec, acc = d8(zf, 30)
    m30 = ~geometry_mask([mapping(s.poly)], z30.shape, tr30)
    # outlet = in-site cell with max accumulation; follow downstream to 1 km
    oi = np.argmax(np.where(m30, acc, -1))
    oi, oj = divmod(int(oi), z30.shape[1])
    path = [(oi, oj)]
    i, j = oi, oj
    for _ in range(60):
        a, b = rec[i, j]
        if a < 0:
            break
        i, j = a, b
        path.append((i, j))
    xy30 = lambda i, j: (tr30.c + (j + 0.5) * 30, tr30.f - (i + 0.5) * 30)
    out_path = [xy30(*p) for p in path]
    upstream_cells = acc[oi, oj]
    # where does the downstream path go? nearest lake/drain is resolved later
    np.save(CACHE / s.id / "dem10.npy", z)
    np.save(CACHE / s.id / "acc30.npy", acc)
    (CACHE / s.id / "dem10.json").write_text(json.dumps({"transform": list(tr)[:6], "res": 10}))
    (CACHE / s.id / "acc30.json").write_text(json.dumps({"transform": list(tr30)[:6], "res": 30}))
    relief = float(np.nanmax(zin) - np.nanmin(zin))
    ctx = z[~np.isnan(z)]
    interval = 1 if relief < 15 else 2 if relief < 40 else 5
    sl_in = slope_pct[mask]
    cls = lambda p: "flat (<2%)" if p < 2 else "gentle (2–5%)" if p < 5 else "moderate (5–10%)" if p < 10 else "steep (>10%)"
    return {
        "dem": "Copernicus GLO-30 DSM (30 m, EGM2008), resampled to 10 m",
        "elev_min": r(np.nanmin(zin)), "elev_max": r(np.nanmax(zin)), "elev_mean": r(np.nanmean(zin)), "relief_m": r(relief),
        "ctx_min": r(ctx.min()), "ctx_max": r(ctx.max()),
        "slope_median_pct": r(np.nanmedian(sl_in)), "slope_p90_pct": r(np.nanpercentile(sl_in, 90)),
        "slope_class": cls(np.nanmedian(sl_in)), "plane_slope_pct": r(plane_slope, 2), "fall_dir_deg": r(plane_down, 0),
        "fall_dir": compass(plane_down), "contour_interval_m": interval,
        "share_lt5_pct": r(100 * np.mean(sl_in < 5)),
        "low_pt": [r(v, 1) for v in xy(li, lj)], "high_pt": [r(v, 1) for v in xy(hi, hj)],
        "low_pt_z": r(z[li, lj]), "high_pt_z": r(z[hi, hj]),
        "transect": {"A": A, "B": B, "length_m": r(L, 0), "relief_m": r(max(zs) - min(zs)), "samples": samples,
                     "zmin": r(min(zs)), "zmax": r(max(zs))},
        "outlet": [r(v, 1) for v in xy30(oi, oj)], "outlet_path": out_path, "upstream_ha": r(upstream_cells * 900 / 1e4, 1),
    }


# ---------------------------------------------------------------- climate
def load_power(s):
    d = pd.read_csv(CACHE / s.id / "power_daily.csv", parse_dates=["time"]).set_index("time")
    h = pd.read_csv(CACHE / s.id / "power_hourly.csv", parse_dates=["time"]).set_index("time")
    m = pd.read_csv(CACHE / s.id / "power_solar_monthly.csv", parse_dates=["time"]).set_index("time")
    return d, h, m


def climate(s):
    d, h, msol = load_power(s)
    cell = json.loads((CACHE / s.id / "power_daily.csv.cell.json").read_text())
    w = d[(d.index.year >= YEARS[0]) & (d.index.year <= YEARS[1])]
    mon = w.groupby(w.index.month)
    tmax = mon["T2M_MAX"].mean()
    tmin = mon["T2M_MIN"].mean()
    rain_m = w["PRECTOTCORR"].groupby([w.index.year, w.index.month]).sum().unstack()  # years x months
    rain_mean = rain_m.mean(0)
    rain_p10 = rain_m.quantile(0.1, 0)
    rain_p90 = rain_m.quantile(0.9, 0)
    annual = w["PRECTOTCORR"].groupby(w.index.year).sum()
    rainy = (w["PRECTOTCORR"] >= 2.5).groupby(w.index.year).sum()
    # annual max 1-day (full record, complete years)
    full = d[(d.index.year >= 1981) & (d.index.year <= 2025)]
    amax = full["PRECTOTCORR"].groupby(full.index.year).max()
    mu, sd = amax.mean(), amax.std()
    k = lambda T: -(math.sqrt(6) / math.pi) * (0.5772 + math.log(math.log(T / (T - 1))))
    gumbel = {T: r(mu + k(T) * sd, 0) for T in (2, 10, 25, 50, 100)}
    hottest = w["T2M_MAX"].idxmax()
    coolest = w["T2M_MIN"].idxmin()
    # wind (hourly, UTC -> IST)
    hw = h[(h.index.year >= YEARS[0]) & (h.index.year <= YEARS[1])].copy()
    hw.index = hw.index + pd.Timedelta(hours=5, minutes=30)
    return {
        "source": "NASA POWER — MERRA-2 daily/hourly", "grid": [cell["grid_lat"], cell["grid_lon"]], "years": list(YEARS),
        "tmax": [r(v) for v in tmax], "tmin": [r(v) for v in tmin],
        "tmax_peak": [r(tmax.max()), int(tmax.idxmax())], "tmin_low": [r(tmin.min()), int(tmin.idxmin())],
        "t_annual_mean": r(w["T2M"].mean()), "hottest_day": [str(hottest.date()), r(w.loc[hottest, "T2M_MAX"])],
        "coolest_night": [str(coolest.date()), r(w.loc[coolest, "T2M_MIN"])],
        "rain_mean": [r(v, 0) for v in rain_mean], "rain_p10": [r(v, 0) for v in rain_p10], "rain_p90": [r(v, 0) for v in rain_p90],
        "rain_annual_mean": r(annual.mean(), 0), "rain_annual_min": [int(annual.idxmin()), r(annual.min(), 0)],
        "rain_annual_max": [int(annual.idxmax()), r(annual.max(), 0)], "rainy_days": r(rainy.mean(), 0),
        "wettest_month": int(rain_mean.idxmax()), "rain_jun_nov_pct": r(100 * rain_mean[6:11].sum() / rain_mean.sum(), 0),
        "amax_1day_years": [int(amax.index.min()), int(amax.index.max())], "amax_1day_mean": r(mu, 0),
        "amax_1day_record": [int(amax.idxmax()), r(amax.max(), 0)], "gumbel_1day_mm": gumbel,
        "rh_mean": r(w["RH2M"].mean(), 0),
    }, hw, msol


def wind_rose(df, dcol, scol, calm=0.5):
    x = df[[dcol, scol]].dropna()
    x = x[(x[dcol] >= 0) & (x[dcol] <= 360)]
    n = len(x)
    bins = [0, 1, 2, 3, 4, 5, 99]
    calm_n = (x[scol] < calm).sum()
    y = x[x[scol] >= calm]
    sec = (((y[dcol] % 360) + 11.25) // 22.5).astype(int) % 16
    sb = np.digitize(y[scol], bins) - 1
    tab = np.zeros((16, len(bins) - 1))
    for a, b in zip(sec, sb):
        tab[a, min(b, len(bins) - 2)] += 1
    tab = 100 * tab / n
    tot = tab.sum(1)
    pre = int(np.argmax(tot))
    # vector-mean direction (from)
    u = -(y[scol] * np.sin(np.radians(y[dcol]))).mean()
    v = -(y[scol] * np.cos(np.radians(y[dcol]))).mean()
    vec_from = (math.degrees(math.atan2(-u, -v))) % 360
    return {"n": int(n), "calm_pct": r(100 * calm_n / n), "bins": bins[:-1], "table": [[r(c, 2) for c in row] for row in tab],
            "sector_pct": [r(t, 1) for t in tot], "prevailing": COMPASS16[pre], "prevailing_pct": r(tot[pre]),
            "prevailing_deg": pre * 22.5, "mean_speed": r(x[scol].mean(), 1), "vector_from": r(vec_from, 0),
            "vector_from_c": compass(vec_from), "p90_speed": r(x[scol].quantile(0.9), 1)}


STATION = {1: ("433025", "HAL Airport (VOBG)"), 2: ("427056", "Kempegowda Intl Airport (VOBL)"),
           3: ("427056", "Kempegowda Intl Airport (VOBL)"), 4: ("427056", "Kempegowda Intl Airport (VOBL)")}
STATION_LL = {"427056": (13.200, 77.700), "433025": (12.950, 77.668), "432950": (12.967, 77.583)}  # NOAA isd-history
SEASONS = {"Winter (Dec–Feb)": [12, 1, 2], "Pre-monsoon (Mar–May)": [3, 4, 5], "SW monsoon (Jun–Sep)": [6, 7, 8, 9],
           "Post-monsoon (Oct–Nov)": [10, 11]}


def wind(s, hw):
    out = {"model": {"source": "NASA POWER — MERRA-2 hourly, 10 m", "annual": wind_rose(hw, "WD10M", "WS10M")}}
    out["model"]["seasons"] = {k: wind_rose(hw[hw.index.month.isin(v)], "WD10M", "WS10M") for k, v in SEASONS.items()}
    # station
    usaf, sname = STATION[s.n]
    st = pd.read_csv(CACHE / f"isd_{usaf}.csv")
    st = st[(st.y >= YEARS[0]) & (st.y <= YEARS[1])].replace(-9999, np.nan)
    st["time"] = pd.to_datetime(dict(year=st.y, month=st.m, day=st.d, hour=st.h)) + pd.Timedelta(hours=5, minutes=30)
    st = st.set_index("time")
    st["ws"] = st["ws"] / 10.0
    st.loc[st["wd"] == 999, "wd"] = np.nan  # variable
    st.loc[(st["ws"] == 0), "wd"] = 0
    st_t = st["t"] / 10.0
    stn = {"source": f"NOAA ISD — {sname} hourly observations", "name": sname, "usaf": usaf, "annual": wind_rose(st, "wd", "ws")}
    lat0, lon0 = STATION_LL[usaf]
    sx, sy = TO_UTM.transform(lon0, lat0)
    stn["dist_km"] = r(math.hypot(sx - s.cx, sy - s.cy) / 1000, 1)
    stn["years"] = [int(st.index.year.min()), int(st.index.year.max())]
    stn["seasons"] = {k: wind_rose(st[st.index.month.isin(v)], "wd", "ws") for k, v in SEASONS.items()}
    stn["t_mean"] = r(st_t.mean())
    dd = st_t.groupby(st_t.index.date).agg(["max", "min", "count"])
    dd = dd[dd["count"] >= 18]
    stn["t_hottest"] = [str(dd["max"].idxmax()), r(dd["max"].max())]
    stn["t_coolest"] = [str(dd["min"].idxmin()), r(dd["min"].min())]
    stn["days_ge_35"] = r((dd["max"] >= 35).groupby(pd.to_datetime(dd.index).year).sum().mean(), 0)
    stn["afternoon_ws"] = r(st[(st.index.hour >= 12) & (st.index.hour <= 17)]["ws"].mean())
    out["station"] = stn
    return out


# ---------------------------------------------------------------- solar
def solar(s, msol):
    tz = "Asia/Kolkata"
    loc = pvlib.location.Location(s.lat, s.lon, tz=tz, altitude=900)
    days = {"21 Mar": "2026-03-21", "21 Jun": "2026-06-21", "21 Sep": "2026-09-21", "21 Dec": "2026-12-21"}
    curves = {}
    events = {}
    for k, dd in days.items():
        t = pd.date_range(f"{dd} 05:00", f"{dd} 19:00", freq="5min", tz=tz)
        sp = loc.get_solarposition(t)
        up = sp[sp.apparent_elevation > 0]
        curves[k] = [[r(a, 2), r(e, 2), ts.strftime("%H:%M")] for ts, a, e in zip(up.index, up.azimuth, up.apparent_elevation)]
        rs = loc.get_sun_rise_set_transit(pd.DatetimeIndex([pd.Timestamp(dd, tz=tz)]), method="spa")
        noon = sp.loc[sp.apparent_elevation.idxmax()]
        events[k] = {"sunrise": rs.sunrise.iloc[0].strftime("%H:%M"), "sunset": rs.sunset.iloc[0].strftime("%H:%M"),
                     "noon": rs.transit.iloc[0].strftime("%H:%M"), "noon_alt": r(noon.apparent_elevation),
                     "noon_az": r(noon.azimuth, 0),
                     "daylength_h": r((rs.sunset.iloc[0] - rs.sunrise.iloc[0]).total_seconds() / 3600, 2),
                     "rise_az": r(up.azimuth.iloc[0], 0), "set_az": r(up.azimuth.iloc[-1], 0)}
    # hourly analemma points (each month 21st, each hour)
    hours = {}
    for h_ in range(6, 19):
        pts = []
        for mth in range(1, 13):
            ts = pd.Timestamp(f"2026-{mth:02d}-21 {h_:02d}:00", tz=tz)
            sp = loc.get_solarposition(pd.DatetimeIndex([ts]))
            if sp.apparent_elevation.iloc[0] > 0:
                pts.append([r(sp.azimuth.iloc[0], 2), r(sp.apparent_elevation.iloc[0], 2)])
        hours[h_] = pts
    # irradiation from NASA POWER CERES SYN1deg monthly (kWh/m2/day)
    cell = json.loads((CACHE / s.id / "power_solar_monthly.csv.cell.json").read_text())
    m = msol[(msol.index.year >= YEARS[0]) & (msol.index.year <= YEARS[1])]
    m = m[m.index.month <= 12]
    mm = m.groupby(m.index.month).mean()
    dim = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    # monthly-mean irradiance in W/m2 -> kWh/m2 per month
    ghi_month = mm["ALLSKY_SFC_SW_DWN"].values * 24 * dim / 1000
    clr_month = mm["CLRSKY_SFC_SW_DWN"].values * 24 * dim / 1000
    dni_year = float((mm["ALLSKY_SFC_SW_DNI"].values * 24 * dim / 1000).sum())
    ghi_year = float(ghi_month.sum())
    # facade/roof annual irradiation: hourly clear-sky scaled to monthly all-sky/clear-sky ratio
    t = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="h", tz=tz)
    sp = loc.get_solarposition(t)
    cs = loc.get_clearsky(t, model="ineichen")
    ratio = pd.Series(ghi_month / clr_month, index=range(1, 13))
    k = t.month.map(ratio).values
    ghi, dni, dhi = cs.ghi * k, cs.dni * k ** 1.5, cs.dhi * (1 + (1 - k))  # cloudier -> more diffuse share
    ghi = ghi.clip(lower=0)
    faces = {}
    for name, (tilt, az) in {"Roof (flat)": (0, 180), **{f: (90, a) for f, a in zip(COMPASS8, range(0, 360, 45))}}.items():
        poa = pvlib.irradiance.get_total_irradiance(tilt, az, sp.apparent_zenith, sp.azimuth, dni.clip(lower=0), ghi, dhi.clip(lower=0),
                                                    albedo=0.2, model="isotropic")
        faces[name] = r(poa.poa_global.fillna(0).sum() / 1000, 0)
    model_scale = ghi_year / (ghi.sum() / 1000)
    norm = ghi_year / faces["Roof (flat)"]  # anchor the facade model to the measured horizontal total
    faces = {k: r(v * norm, 0) for k, v in faces.items()}
    return {
        "tz": "IST (UTC+5:30)", "curves": curves, "events": events, "hours": {str(k): v for k, v in hours.items()},
        "ghi_month_kwh": [r(v, 0) for v in ghi_month], "ghi_year_kwh": r(ghi_year, 0), "ghi_day_mean": r(ghi_year / 365, 2),
        "clear_year_kwh": r(clr_month.sum(), 0), "dni_year_kwh": r(dni_year, 0), "cloud_loss_pct": r(100 * (1 - ghi_year / clr_month.sum()), 0),
        "best_month": int(np.argmax(ghi_month) + 1), "worst_month": int(np.argmin(ghi_month) + 1),
        "faces_kwh": faces, "face_model_check": r(model_scale, 3), "grid": [cell["grid_lat"], cell["grid_lon"]],
        "source": "NASA POWER — CERES SYN1deg monthly", "years": list(YEARS),
    }


# ---------------------------------------------------------------- land cover
WC = {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up", 60: "Bare / sparse", 70: "Snow", 80: "Water",
      90: "Wetland", 95: "Mangroves", 100: "Moss"}


def landcover(s, yr=2021):
    with rasterio.open(CACHE / s.id / f"wc{yr}.tif") as ds:
        a = ds.read(1)
        res = {}
        for nm, g in (("site", s.poly), ("ring500", s.poly.buffer(500).difference(s.poly))):
            gm = mapping(wgs(g))
            m = ~geometry_mask([gm], a.shape, ds.transform, all_touched=False)
            v = a[m]
            res[nm] = {WC[k]: r(100 * (v == k).mean(), 1) for k in np.unique(v) if (v == k).mean() > 0.001}
    perm = lambda d: r(100 - d.get("Built-up", 0) - d.get("Water", 0), 0)
    return {"year": yr, "site": res["site"], "ring500": res["ring500"], "canopy_site": res["site"].get("Tree cover", 0),
            "canopy_ring": res["ring500"].get("Tree cover", 0), "permeable_site": perm(res["site"]), "permeable_ring": perm(res["ring500"]),
            "built_ring": res["ring500"].get("Built-up", 0)}


# ---------------------------------------------------------------- water & drains
def water(s):
    w = read_ov(s, "water")
    lakes = []
    for _, row in w.iterrows():
        g = row.geom
        if g.geom_type not in ("Polygon", "MultiPolygon") or g.area < 3000:
            continue
        lakes.append({"name": name_of(row["names"]), "class": row["class"], "area_ha": r(g.area / 1e4, 1),
                      "dist_m": r(g.distance(s.poly), 0), "bearing": compass8(math.degrees(math.atan2(g.centroid.x - s.cx, g.centroid.y - s.cy))),
                      "geom": g})
    lakes.sort(key=lambda d: d["dist_m"])
    streams = []
    for _, row in w.iterrows():
        g = row.geom
        if g.geom_type in ("LineString", "MultiLineString"):
            streams.append({"name": name_of(row["names"]), "class": row["class"], "dist_m": r(g.distance(s.poly), 0), "geom": g})
    streams.sort(key=lambda d: d["dist_m"])
    rk = json.loads((ROOT / "inputs" / "rajakaluve_primary.geojson").read_text())
    drains = []
    for ft in rk["features"]:
        g = utm(shape(ft["geometry"]))
        dd = g.distance(s.poly)
        if dd < 3000:
            drains.append({"dist_m": r(dd, 0), "geom": g})
    drains.sort(key=lambda d: d["dist_m"])
    return {"lakes": lakes[:8], "streams": streams[:8], "drains": drains[:6]}


# ---------------------------------------------------------------- context: buildings, roads, places, isochrones
WALK_KMH = 4.8


def context(s):
    b = read_ov(s, "building")
    b = b[[g.geom_type in ("Polygon", "MultiPolygon") for g in b.geom]].copy()
    b["dist"] = [g.distance(s.poly) for g in b.geom]
    b["inside"] = [s.poly.intersection(g).area > 0.5 * g.area for g in b.geom]
    ring = s.poly.buffer(500).difference(s.poly)
    b5 = b[(b.dist < 500) & (~b.inside)]
    cov = unary_union(list(b5.geom)).intersection(ring).area / ring.area if len(b5) else 0
    hh = pd.to_numeric(b5["height"], errors="coerce")
    ff = pd.to_numeric(b5["num_floors"], errors="coerce")
    est_h = np.where(hh.notna(), hh, ff * 3.2).astype(float)
    hknown = pd.Series(np.isfinite(est_h))
    inside = b[b.inside]
    return b, {
        "bld_inside_n": int(len(inside)), "bld_inside_footprint_m2": r(sum(g.area for g in inside.geom), 0),
        "bld_500_n": int(len(b5)), "bld_500_coverage_pct": r(100 * cov, 1), "bld_500_known_h_pct": r(100 * hknown.mean() if len(b5) else 0, 0),
        "bld_500_h_median": r(np.nanmedian(est_h) if hknown.any() else None), "bld_500_h_max": r(np.nanmax(est_h) if hknown.any() else None),
        "bld_500_footprint_median": r(np.median([g.area for g in b5.geom]) if len(b5) else None, 0),
        "bld_500_large_n": int(sum(g.area > 1500 for g in b5.geom)),
    }


def walk_graph(s):
    seg = read_ov(s, "segment")
    seg = seg[seg["subtype"] == "road"]
    seg = seg[~seg["class"].isin(["motorway"])]
    G = nx.Graph()
    key = lambda p: (round(p[0], 1), round(p[1], 1))
    for _, row in seg.iterrows():
        g = row.geom
        lines = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
        for ln in lines:
            c = list(ln.coords)
            for a, b_ in zip(c[:-1], c[1:]):
                G.add_edge(key(a), key(b_), w=math.dist(a, b_), cls=row["class"])
    # Overture splits at connectors -> endpoints coincide; snap near-coincident nodes (<1.5 m)
    return G, seg


def isochrones(s, G):
    nodes = np.array(list(G.nodes))
    pts = [tuple(n) for n in nodes]
    from shapely import contains_xy

    inside = contains_xy(s.poly.buffer(25), nodes[:, 0], nodes[:, 1])
    src = [pts[i] for i in np.nonzero(inside)[0]]
    if not src:
        d = np.hypot(nodes[:, 0] - s.cx, nodes[:, 1] - s.cy)
        src = [pts[int(d.argmin())]]
    dist = nx.multi_source_dijkstra_path_length(G, src, cutoff=3000, weight="w")
    out = {}
    for mins in (5, 10, 15):
        lim = WALK_KMH * 1000 / 60 * mins
        segs = []
        for u, v in G.edges():
            du, dv = dist.get(u), dist.get(v)
            if du is not None and dv is not None and min(du, dv) <= lim:
                segs.append(LineString([u, v]))
        poly = unary_union([g.buffer(45) for g in segs]).union(s.poly).buffer(20).buffer(-20)
        out[mins] = poly
    return dist, out, src


CATS = {
    "Transit": ["bus_station", "bus_stop", "train_station", "metro_station", "light_rail_and_subway_stations", "railway_station",
                "transportation", "public_transportation", "bus_service", "transport_interchange"],
    "Health": ["hospital", "clinic", "medical_center", "doctor", "pharmacy", "emergency_room", "health_and_medical", "dentist"],
    "Education": ["school", "elementary_school", "high_school", "middle_school", "preschool", "college_university", "education",
                  "private_school", "public_school", "university", "kindergarten"],
    "Daily needs": ["grocery_store", "supermarket", "convenience_store", "department_store", "market", "farmers_market",
                    "vegetable_store", "fruit_and_vegetable_store", "bakery", "pharmacy", "atms", "bank"],
}


def places(s, G, dist):
    p = read_ov(s, "place")
    p["cat"] = [((t or {}).get("primary") if isinstance(t, dict) else None) or bc for t, bc in zip(p["taxonomy"], p["basic_category"])]
    p["name"] = [name_of(n) for n in p["names"]]
    p["d_line"] = [g.distance(s.poly) for g in p.geom]
    nodes = np.array(list(G.nodes))
    keys = [tuple(n) for n in nodes]

    def net(g):
        d = np.hypot(nodes[:, 0] - g.x, nodes[:, 1] - g.y)
        i = int(d.argmin())
        nd = dist.get(keys[i])
        return None if nd is None else nd + float(d[i])

    out = {}
    for k, cats in CATS.items():
        sub = p[p["cat"].isin(cats) & p["name"].notna() & (p["confidence"] >= 0.6)].sort_values("d_line").head(25)
        rows = []
        for _, row in sub.iterrows():
            nd = net(row.geom)
            rows.append({"name": row["name"], "cat": row["cat"], "line_m": r(row.d_line, 0), "net_m": r(nd, 0),
                         "walk_min": r((nd or row.d_line * 1.3) / (WALK_KMH * 1000 / 60), 0), "x": row.geom.x, "y": row.geom.y})
        rows.sort(key=lambda d: d["net_m"] if d["net_m"] is not None else d["line_m"] * 1.3)
        out[k] = rows[:6]
    counts = {k: int(((p["cat"].isin(c)) & (p["d_line"] < 1000)).sum()) for k, c in CATS.items()}
    return out, counts, p


def named_places(p, patterns):
    res = {}
    for k, pat in patterns.items():
        m = p[p["name"].fillna("").str.contains(pat, case=False, regex=True)].sort_values("d_line")
        if len(m):
            row = m.iloc[0]
            res[k] = {"name": row["name"], "cat": row["cat"], "dist_m": r(row["d_line"], 0), "x": row.geom.x, "y": row.geom.y}
    return res


def roads_near(s):
    seg = read_ov(s, "segment")
    seg = seg[seg["subtype"] == "road"].copy()
    seg["d"] = [g.distance(s.poly) for g in seg.geom]
    seg["name"] = [name_of(n) for n in seg["names"]]
    major = {}
    for cls in ["motorway", "trunk", "primary", "secondary", "tertiary"]:
        sub = seg[seg["class"] == cls].sort_values("d")
        if len(sub):
            row = sub.iloc[0]
            major[cls] = {"name": row["name"], "dist_m": r(row.d, 0)}
    return seg, major


def infrastructure(s):
    inf = read_ov(s, "infrastructure")
    if inf.empty:
        return {}
    inf["d"] = [g.distance(s.poly) for g in inf.geom]
    inf["name"] = [name_of(n) for n in inf["names"]]
    out = {}
    for cls in ["power_line", "minor_line", "substation", "transformer", "tower", "pole", "water_tower", "pumping_station",
                "wastewater_plant", "water_works", "communication_tower", "aerodrome", "runway", "airport", "military_airport",
                "international_airport", "bus_station", "bus_stop", "railway_station", "station"]:
        sub = inf[inf["class"] == cls].sort_values("d")
        if len(sub):
            row = sub.iloc[0]
            out[cls] = {"name": row["name"], "dist_m": r(row.d, 0), "n_within_1km": int((sub.d < 1000).sum()),
                        "subtype": row["subtype"], "x": row.geom.centroid.x, "y": row.geom.centroid.y}
    return out, inf


def skyline(s, b, dem10, tr10):
    # E–W section through the centroid, ±600 m, 60 m corridor
    A = (s.cx - 600, s.cy)
    B = (s.cx + 600, s.cy)
    line = LineString([A, B])
    corr = line.buffer(30, cap_style=2)
    items = []
    for _, row in b.iterrows():
        g = row.geom
        if not g.intersects(corr):
            continue
        if row["height"] == row["height"] and row["height"] is not None:
            h, src = float(row["height"]), "tagged"
        elif row["num_floors"] == row["num_floors"] and row["num_floors"] is not None:
            h, src = float(row["num_floors"]) * 3.2, "floors"
        else:
            # footprint-based storey assumption (stated in caption)
            a = g.area
            h, src = (6.4 if a < 150 else 9.6 if a < 600 else 12.8), "assumed"
        x0, x1 = g.bounds[0] - A[0], g.bounds[2] - A[0]
        items.append({"x0": r(max(0, x0), 1), "x1": r(min(1200, x1), 1), "h": r(h, 1), "src": src, "inside": bool(row["inside"])})
    ground = []
    for k in range(0, 1201, 10):
        x, y = A[0] + k, A[1]
        j = int((x - tr10[2]) / 10)
        i = int((tr10[5] - y) / 10)
        ground.append([k, r(float(dem10[i, j]), 1)])
    site_span = line.intersection(s.poly)
    sx = [c[0] - A[0] for c in site_span.coords] if not site_span.is_empty else [0, 0]
    return {"A": A, "B": B, "buildings": items, "ground": ground, "site_x": [r(min(sx)), r(max(sx))],
            "n_tagged": sum(1 for i in items if i["src"] != "assumed"), "n": len(items)}


# ---------------------------------------------------------------- edges
def edge_conditions(s, geo, seg, b, lakes, drains, proads, landcover_arr=None):
    rows = []
    for e in geo["_edges_geom"]:
        ln = LineString([e["a"], e["b"]])
        strip = ln.buffer(35, cap_style=2).difference(s.poly)
        near_roads = seg[[g.intersects(ln.buffer(25, cap_style=2)) for g in seg.geom]]
        near_roads = near_roads[[g.intersection(ln.buffer(25, cap_style=2)).length > 0.4 * ln.length for g in near_roads.geom]]
        rd = None
        if len(near_roads):
            rr = near_roads.iloc[0]
            rd = {"class": rr["class"], "name": rr["name"]}
        pr = [p for p in proads if p["geom"].distance(ln) < 30 and p["geom"].intersection(ln.buffer(30, cap_style=2)).length > 0.3 * ln.length]
        bl = b[[(not ins) and g.intersects(strip) for g, ins in zip(b.geom, b.inside)]]
        rows.append({"edge": e["name"], "len_m": e["len_m"], "faces": e["faces"], "road": rd,
                     "plan_row_m": max([p["row_m"] for p in pr if p["row_m"]], default=None),
                     "plan_status": pr[0]["status"] if pr else None, "bld_n": int(len(bl)),
                     "bld_footprint_m2": r(sum(g.intersection(strip).area for g in bl.geom), 0),
                     "lake_m": r(min([l["geom"].distance(ln) for l in lakes], default=None), 0) if lakes else None,
                     "drain_m": r(min([d["geom"].distance(ln) for d in drains], default=None), 0) if drains else None})
    return rows


# ---------------------------------------------------------------- airfields
def airfields(s, inf, p):
    out = {}
    # KIA ARP from the SAT planning service's AAI table (services/planning/app/services/planning_service.py)
    kia = Point(*TO_UTM.transform(77.7063, 13.1979))
    out["KIA (VOBL) ARP"] = {"dist_km": r(kia.distance(Point(s.cx, s.cy)) / 1000, 1),
                             "bearing": compass(math.degrees(math.atan2(kia.x - s.cx, kia.y - s.cy))), "basis": "SAT AAI table"}
    hal = Point(*TO_UTM.transform(77.6632, 12.9500))
    out["HAL (VOBG) ARP"] = {"dist_km": r(hal.distance(Point(s.cx, s.cy)) / 1000, 1),
                             "bearing": compass(math.degrees(math.atan2(hal.x - s.cx, hal.y - s.cy))), "basis": "SAT AAI table"}
    # Yelahanka AFS — mapped aerodrome in Overture (land_use / infrastructure)
    lu = read_ov(s, "land_use")
    cand = []
    for df in (lu, inf):
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            nm = (name_of(row["names"]) or "")
            if row["class"] in ("aerodrome", "airport", "military_airport", "runway", "military") or "yelahanka air" in nm.lower() or "air force" in nm.lower():
                cand.append((row.geom.distance(Point(s.cx, s.cy)), nm, row["class"], row.geom))
    cand.sort(key=lambda c: c[0])
    if cand:
        dd, nm, cl, g = cand[0]
        out["Nearest mapped aerodrome"] = {"name": nm, "class": cl, "edge_km": r(g.distance(s.poly) / 1000, 1),
                                           "centroid_km": r(g.centroid.distance(Point(s.cx, s.cy)) / 1000, 1),
                                           "bearing": compass(math.degrees(math.atan2(g.centroid.x - s.cx, g.centroid.y - s.cy)))}
    return out


# ---------------------------------------------------------------- protected areas / quarries / sensitive land uses
def sensitive(s):
    lu = read_ov(s, "land_use")
    if lu.empty:
        return {}
    lu["name"] = [name_of(n) for n in lu["names"]]
    lu["d"] = [g.distance(s.poly) for g in lu.geom]
    out = {}
    pa = lu[(lu["subtype"] == "protected") & (lu["d"] < 20000) & np.array([g.area < 5e9 for g in lu.geom])].sort_values("d")
    if len(pa):
        row = pa.iloc[0]
        g = row.geom
        q = g.boundary.interpolate(g.boundary.project(Point(s.cx, s.cy)))
        out["protected"] = {"name": row["name"], "class": row["class"], "dist_m": r(row.d, 0), "inside": bool(g.intersects(s.poly)),
                            "bearing": compass8(math.degrees(math.atan2(q.x - s.cx, q.y - s.cy))), "area_km2": r(g.area / 1e6, 1)}
    qu = lu[lu["class"] == "quarry"].sort_values("d")
    out["quarries_1km"] = int((qu.d < 1000).sum())
    out["quarry_nearest_m"] = r(qu.d.iloc[0], 0) if len(qu) else None
    if len(qu):
        g = qu.iloc[0].geom
        out["quarry_bearing"] = compass8(math.degrees(math.atan2(g.centroid.x - s.cx, g.centroid.y - s.cy)))
    ind = lu[lu["class"] == "industrial"].sort_values("d")
    out["industrial_nearest_m"] = r(ind.d.iloc[0], 0) if len(ind) else None
    sch = lu[(lu["class"] == "school") & lu["name"].notna()].sort_values("d")
    out["school_nearest"] = {"name": sch.iloc[0]["name"], "dist_m": r(sch.iloc[0].d, 0)} if len(sch) else None
    return out


# ---------------------------------------------------------------- aerodrome obstacle surfaces (indicative ICAO Annex 14, code 4 precision)
AERODROME_ELEV = 915.0  # KIA aerodrome elevation, m AMSL (research: Wikipedia / AC-U-KWIK)


def airport_surfaces(s, inf):
    if inf is None or inf.empty:
        return None
    rw = inf[inf["class"] == "runway"]
    if rw.empty:
        return None
    z, tr = dem_utm(s, buf=0, res=10)
    pts = [Point(x, y) for x, y in s.vertices] + [Point(s.cx, s.cy)]
    names = [f"V{i+1}" for i in range(len(s.vertices))] + ["Centroid"]

    def ground(p):
        j = int((p.x - tr.c) / 10)
        i = int((tr.f - p.y) / 10)
        i = min(max(i, 0), z.shape[0] - 1)
        j = min(max(j, 0), z.shape[1] - 1)
        return float(z[i, j])

    runways = []
    strips = []
    for _, row in rw.iterrows():
        c = list(row.geom.coords)
        a, b = (c[0], c[-1]) if c[0][0] < c[-1][0] else (c[-1], c[0])  # a = west end
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        strip = LineString([(a[0] - 60 * ux, a[1] - 60 * uy), (b[0] + 60 * ux, b[1] + 60 * uy)])
        strips.append(strip)
        runways.append({"name": name_of(row["names"]), "a": a, "b": b, "u": (ux, uy), "len_m": r(L, 0),
                        "west_thr_ll": [r(TO_WGS.transform(*a)[1], 5), r(TO_WGS.transform(*a)[0], 5)]})
    ih = unary_union([st.buffer(4000) for st in strips])

    def approach(p, rwy):
        # approach to the west threshold (landing eastbound): inner edge 60 m before threshold, 300 m wide, 15% divergence
        ax_, ay_ = rwy["a"]
        ux, uy = rwy["u"]
        dx, dy = p.x - ax_, p.y - ay_
        along = -(dx * ux + dy * uy)  # metres west of threshold
        lat = abs(-dx * uy + dy * ux)
        d = along - 60
        if d < 0 or d > 15000:
            return None, along, lat
        half = 150 + 0.15 * d
        if lat > half:
            return None, along, lat
        h = 0.02 * min(d, 3000) + (0.025 * min(d - 3000, 3600) if d > 3000 else 0) + 0
        h = min(h, 150)
        return h, along, lat

    rows = []
    for nm, p in zip(names, pts):
        g = ground(p)
        cands = []
        dih = p.distance(ih)
        if ih.contains(p):
            cands.append(("Inner horizontal", 45.0))
        elif dih <= 2000:
            cands.append(("Conical", 45.0 + 0.05 * dih))
        best_app = None
        for rwy in runways:
            h, along, lat = approach(p, rwy)
            if h is not None:
                cands.append((f"Approach {rwy['name']}", h))
                best_app = (rwy["name"], along, lat)
        lim = min(cands, key=lambda c: c[1]) if cands else ("Outer horizontal", 150.0)
        top = AERODROME_ELEV + lim[1]
        rows.append({"pt": nm, "ground": r(g, 1), "surface": lim[0], "limit_above_aerodrome_m": r(lim[1], 1),
                     "top_amsl": r(top, 1), "height_avail_m": r(top - g, 1),
                     "in_approach": best_app is not None})
    geo_rw = []
    for rwy in runways:
        h0, along, lat = approach(Point(s.cx, s.cy), rwy)
        geo_rw.append({"name": rwy["name"], "len_m": rwy["len_m"], "west_thr": rwy["west_thr_ll"],
                       "centroid_west_of_thr_m": r(along, 0), "centroid_offset_m": r(lat, 0),
                       "dist_to_strip_m": r(Point(s.cx, s.cy).distance(LineString([rwy["a"], rwy["b"]])), 0)})
    mn = min(rows, key=lambda r_: r_["height_avail_m"])
    return {"aerodrome_elev": AERODROME_ELEV, "runways": geo_rw, "points": rows, "min_height_avail_m": mn["height_avail_m"],
            "min_pt": mn["pt"], "binding_surface": mn["surface"], "any_in_approach": any(r_["in_approach"] for r_ in rows),
            "in_inner_horizontal": bool(ih.intersects(s.poly)), "basis": "ICAO Annex 14 code-4 precision approach (indicative)"}


# ---------------------------------------------------------------- run
def run(n):
    s = SITES[n]
    res = {"site": n, "id": s.id, "name": s.name, "village": s.rec["village"], "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    geo = geometry(s)
    res["geometry"] = {k: v for k, v in geo.items() if not k.startswith("_")}
    print("geometry ok")
    res["terrain"] = terrain(s)
    print("terrain ok")
    clim, hw, msol = climate(s)
    res["climate"] = clim
    res["wind"] = wind(s, hw)
    res["solar"] = solar(s, msol)
    print("climate/wind/solar ok")
    res["landcover"] = landcover(s, 2021)
    res["landcover_2020"] = landcover(s, 2020)
    wat = water(s)
    res["water"] = {"lakes": [{k: v for k, v in l.items() if k != "geom"} for l in wat["lakes"]],
                    "streams": [{k: v for k, v in l.items() if k != "geom"} for l in wat["streams"]],
                    "drains": [{k: v for k, v in l.items() if k != "geom"} for l in wat["drains"]]}
    print("landcover/water ok")
    plan_id = {1: "BDA-RMP2031", 2: "BMRDA-HSK-MP2031", 3: "BDA-RMP2031", 4: None}[n]
    proads = plan_roads(s, plan_id) if plan_id else []
    res["plan"] = {"zones": plan_zones(s, plan_id) if plan_id else None,
                   "roads": sorted([{k: v for k, v in p.items() if k != "geom"} for p in proads], key=lambda d: d["dist_m"])}
    print("plan ok")
    b, ctx = context(s)
    res["context"] = ctx
    seg, major = roads_near(s)
    res["context"]["major_roads"] = major
    G, _ = walk_graph(s)
    dist, iso, src = isochrones(s, G)
    res["access"] = {"iso_area_ha": {k: r(v.area / 1e4, 0) for k, v in iso.items()}, "walk_kmh": WALK_KMH, "graph_nodes": G.number_of_nodes()}
    poi, counts, pl = places(s, G, dist)
    res["access"]["poi"] = poi
    res["access"]["counts_1km"] = counts
    res["access"]["named"] = named_places(pl, {"Yelahanka railway": r"yelahanka.*(junction|railway|station)", "Jakkur": r"jakkur",
                                               "SPARSH": r"sparsh", "Kogilu Cross": r"kogilu cross"})
    print("access ok")
    infr, inf = infrastructure(s)
    res["infrastructure"] = infr
    res["airfields"] = airfields(s, inf, pl)
    res["sensitive"] = sensitive(s)
    res["aerodrome"] = airport_surfaces(s, inf)
    z10 = np.load(CACHE / s.id / "dem10.npy")
    tr10 = json.loads((CACHE / s.id / "dem10.json").read_text())["transform"]
    res["skyline"] = skyline(s, b, z10, tr10)
    res["edges"] = edge_conditions(s, geo, seg.assign(name=[name_of(x) for x in seg["names"]]) if "name" not in seg else seg, b,
                                   wat["lakes"], wat["drains"], proads)
    out = ROOT / "results" / f"{s.id}.json"
    out.write_text(json.dumps(res, indent=1, default=lambda o: float(o) if isinstance(o, (np.floating,)) else int(o) if isinstance(o, np.integer) else str(o)))
    # keep heavy geometry for figures
    import pickle

    pickle.dump({"iso": iso, "src": src, "lakes": wat["lakes"], "streams": wat["streams"], "drains": wat["drains"], "proads": proads,
                 "edges": geo["_edges_geom"]}, open(CACHE / s.id / "geoms.pkl", "wb"))
    print("wrote", out)
    return res


if __name__ == "__main__":
    for a in sys.argv[1:] or ["3"]:
        run(int(a))
