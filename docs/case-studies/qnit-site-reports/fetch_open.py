"""Fetch open data reachable from this environment (AWS S3 / GCS) into cache/<site>/.

Sources
- Copernicus GLO-30 DEM (copernicus-dem-30m, COG)          -> dem.tif
- ESA WorldCover 10 m 2020 v100 + 2021 v200 (esa-worldcover) -> wc2020.tif, wc2021.tif
- NASA POWER (nasa-power Zarr): MERRA-2 daily + hourly, CERES SYN1deg monthly -> power_*.csv
- NOAA ISD-lite hourly (noaa-isd-pds) for KIA / HAL / Bangalore city   -> cache/isd_<usaf>.csv
- NOAA GHCN-Daily Bangalore (noaa-ghcn-pds)                            -> cache/ghcn_IN009010100.csv
Every request is logged to cache/fetch_log.json (url, bytes, utc time).
"""

import gzip
import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import numcodecs
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.windows import from_bounds

from sites import ROOT, SITES

os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
os.environ.setdefault("GDAL_HTTP_PROXY", os.environ.get("HTTPS_PROXY", "").replace("http://", ""))
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

CACHE = ROOT / "cache"
LOG = CACHE / "fetch_log.json"
S = requests.Session()
S.verify = "/root/.ccr/ca-bundle.crt"


def log(url, nbytes, note=""):
    entries = json.loads(LOG.read_text()) if LOG.exists() else []
    entries.append({"url": url, "bytes": nbytes, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": note})
    LOG.write_text(json.dumps(entries, indent=1))


def get(url, **kw):
    for attempt in range(4):
        try:
            r = S.get(url, timeout=120, **kw)
            if r.status_code == 200:
                log(url, len(r.content))
                return r
            if r.status_code in (403, 404):
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"failed {url}")


def bbox_ll(site, buf_m):
    from sites import TO_WGS

    minx, miny, maxx, maxy = site.poly.buffer(buf_m).bounds
    lo1, la1 = TO_WGS.transform(minx, miny)
    lo2, la2 = TO_WGS.transform(maxx, maxy)
    return lo1, la1, lo2, la2


def read_window(url, bounds, out_path):
    with rasterio.open("/vsicurl/" + url) as ds:
        w = from_bounds(*bounds, ds.transform).round_offsets().round_lengths()
        a = ds.read(1, window=w)
        prof = ds.profile.copy()
        prof.update(width=a.shape[1], height=a.shape[0], transform=ds.window_transform(w), driver="GTiff",
                    tiled=False, compress="deflate")
        prof.pop("blockxsize", None)
        prof.pop("blockysize", None)
        with rasterio.open(out_path, "w", **prof) as dst:
            dst.write(a, 1)
    log(url, a.nbytes, f"window {bounds}")


def dem_url(lat, lon):
    t = f"Copernicus_DSM_COG_10_N{int(lat):02d}_00_E{int(lon):03d}_00_DEM"
    return f"https://copernicus-dem-30m.s3.amazonaws.com/{t}/{t}.tif"


def fetch_rasters(site):
    d = CACHE / site.id
    d.mkdir(parents=True, exist_ok=True)
    b = bbox_ll(site, 3000)
    if not (d / "dem.tif").exists():
        urls = sorted({dem_url(la, lo) for la in (b[1], b[3]) for lo in (b[0], b[2])})
        if len(urls) == 1:
            read_window(urls[0], b, d / "dem.tif")
        else:  # mosaic across 1-degree tile edges, windowed
            from rasterio.merge import merge

            srcs = [rasterio.open("/vsicurl/" + u) for u in urls]
            arr, tr = merge(srcs, bounds=b)
            prof = srcs[0].profile.copy()
            prof.update(width=arr.shape[2], height=arr.shape[1], transform=tr, driver="GTiff", tiled=False, compress="deflate")
            prof.pop("blockxsize", None)
            prof.pop("blockysize", None)
            with rasterio.open(d / "dem.tif", "w", **prof) as dst:
                dst.write(arr)
            for u in urls:
                log(u, arr.nbytes // len(urls), f"mosaic window {b}")
    for yr, ver in ((2020, "v100"), (2021, "v200")):
        p = d / f"wc{yr}.tif"
        if not p.exists():
            url = f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/{ver}/{yr}/map/ESA_WorldCover_10m_{yr}_{ver}_N12E075_Map.tif"
            read_window(url, bbox_ll(site, 2000), p)


# ---------- NASA POWER Zarr (point read) ----------
POWER = "https://nasa-power.s3.amazonaws.com"
_meta_cache = {}


def zmeta(store):
    if store not in _meta_cache:
        _meta_cache[store] = get(f"{POWER}/{store}/.zmetadata").json()["metadata"]
    return _meta_cache[store]


def zarr_array(store, name, chunk_index):
    m = zmeta(store)[f"{name}/.zarray"]
    key = ".".join(str(i) for i in chunk_index)
    r = get(f"{POWER}/{store}/{name}/{key}")
    if r.status_code == 404:  # chunk never written (e.g. future dates) -> fill value
        return np.full(m["chunks"], np.nan)
    buf = numcodecs.get_codec(m["compressor"]).decode(r.content)
    filters = m.get("filters") or []
    dtype = filters[-1]["astype"] if filters else m["dtype"]
    a = np.frombuffer(buf, dtype=dtype)
    for f in reversed(filters):
        a = numcodecs.get_codec(f).decode(a)
    return np.asarray(a, dtype=float).reshape(m["chunks"], order=m["order"])


def zarr_full_1d(store, name):
    m = zmeta(store)[f"{name}/.zarray"]
    n, c = m["shape"][0], m["chunks"][0]
    parts = [zarr_array(store, name, (i,)) for i in range((n + c - 1) // c)]
    return np.concatenate(parts)[:n]


def zarr_point_series(store, var, lat, lon):
    meta = zmeta(store)
    lats = zarr_full_1d(store, "lat")
    lons = zarr_full_1d(store, "lon")
    iy = int(np.argmin(abs(lats - lat)))
    ix = int(np.argmin(abs(lons - lon)))
    m = meta[f"{var}/.zarray"]
    nt, ct = m["shape"][0], m["chunks"][0]
    cy, cx = m["chunks"][1], m["chunks"][2]
    out = []
    for ti in range((nt + ct - 1) // ct):
        a = zarr_array(store, var, (ti, iy // cy, ix // cx))
        out.append(a[:, iy % cy, ix % cx])
    series = np.concatenate(out)[:nt].astype(float)
    fill = m.get("fill_value")
    if fill is not None:
        series[series == fill] = np.nan
    series[series < -900] = np.nan
    return series, float(lats[iy]), float(lons[ix])


def power_times(store):
    t = zarr_full_1d(store, "time")
    attrs = zmeta(store)["time/.zattrs"]
    units = attrs["units"]  # e.g. "days since 1981-01-01" or "hours since ..."
    step, _, origin = units.partition(" since ")
    base = pd.Timestamp(origin.strip()[:19])
    return base + pd.to_timedelta(t, unit={"days": "D", "hours": "h", "minutes": "min"}[step.strip()])


def fetch_power(site):
    d = CACHE / site.id
    jobs = {
        "power_daily.csv": ("merra2/temporal/power_merra2_daily_temporal_lst.zarr",
                            ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS10M"]),
        "power_hourly.csv": ("merra2/temporal/power_merra2_hourly_temporal_utc.zarr", ["WS10M", "WD10M", "T2M"]),
        "power_solar_monthly.csv": ("syn1deg/temporal/power_syn1deg_monthly_temporal_lst.zarr",
                                    ["ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN", "ALLSKY_SFC_SW_DNI", "ALLSKY_SFC_SW_DIFF"]),
    }
    for fname, (store, vars_) in jobs.items():
        p = d / fname
        if p.exists():
            continue
        times = power_times(store)
        df = pd.DataFrame(index=times)
        avail = {k.split("/")[0] for k in zmeta(store)}
        cell = None
        for v in vars_:
            if v not in avail:
                print("  missing", v, "in", store)
                continue
            s, la, lo = zarr_point_series(store, v, site.lat, site.lon)
            df[v] = s[: len(times)]
            cell = (la, lo)
        df.index.name = "time"
        df = df.dropna(how="all")
        df.attrs["cell"] = cell
        df.to_csv(p)
        (d / (fname + ".cell.json")).write_text(json.dumps({"store": store, "grid_lat": cell[0], "grid_lon": cell[1]}))
        print(" ", fname, df.index.min(), df.index.max(), len(df), "cell", cell)


# ---------- NOAA ----------
ISD = {"427056": "Kempegowda Intl Airport (VOBL)", "433025": "HAL Airport (VOBG)", "432950": "Bangalore city"}


def fetch_isd(usaf, years=range(2015, 2025)):
    p = CACHE / f"isd_{usaf}.csv"
    if p.exists():
        return
    frames = []
    for y in years:
        r = get(f"https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/{y}/{usaf}-99999-{y}.gz")
        if r.status_code != 200:
            continue
        txt = gzip.decompress(r.content).decode()
        df = pd.read_csv(io.StringIO(txt), sep=r"\s+", header=None,
                         names=["y", "m", "d", "h", "t", "td", "slp", "wd", "ws", "sky", "p1", "p6"])
        frames.append(df)
    df = pd.concat(frames)
    df.to_csv(p, index=False)
    print("  isd", usaf, len(df))


def fetch_ghcn(sid="IN009010100"):
    p = CACHE / f"ghcn_{sid}.csv"
    if not p.exists():
        r = get(f"https://noaa-ghcn-pds.s3.amazonaws.com/csv/by_station/{sid}.csv")
        p.write_bytes(r.content)


if __name__ == "__main__":
    CACHE.mkdir(exist_ok=True)
    which = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4]
    for n in which:
        s = SITES[n]
        print(s.name)
        fetch_rasters(s)
        fetch_power(s)
    for u in ISD:
        fetch_isd(u)
    fetch_ghcn()
