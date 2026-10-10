"""Esri World Imagery (current) and Esri Wayback (dated releases) tile mosaics per site.

Writes cache/<site>/img_<name>.jpg + img_<name>.json (web-mercator bounds, zoom, source, release date).
"""

import io
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from fetch_open import S, bbox_ll, log
from sites import ROOT, SITES

ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
WAYBACK = "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{r}/{z}/{y}/{x}"
R = 6378137.0


def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def tile_xy(lon, lat, z):
    n = 2**z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile_bounds_merc(x, y, z):
    size = 2 * math.pi * R / 2**z
    minx = -math.pi * R + x * size
    maxy = math.pi * R - y * size
    return minx, maxy - size, minx + size, maxy


def _get_tile(url):
    for _ in range(3):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200 and r.content[:3] != b"<?x":
                return Image.open(io.BytesIO(r.content)).convert("RGB")
            if r.status_code == 404:
                return None
        except Exception:
            pass
    return None


def mosaic(site, name, buf_m, z, release=None):
    d = ROOT / "cache" / site.id
    out = d / f"img_{name}.jpg"
    if out.exists():
        return json.loads((d / f"img_{name}.json").read_text())
    lo1, la1, lo2, la2 = bbox_ll(site, buf_m)
    x1, y1 = tile_xy(lo1, la2, z)
    x2, y2 = tile_xy(lo2, la1, z)
    tx = range(int(x1), int(x2) + 1)
    ty = range(int(y1), int(y2) + 1)
    urls = {}
    for x in tx:
        for y in ty:
            urls[(x, y)] = (WAYBACK.format(r=release, z=z, y=y, x=x) if release else ESRI.format(z=z, y=y, x=x))
    with ThreadPoolExecutor(8) as ex:
        tiles = dict(zip(urls, ex.map(_get_tile, urls.values())))
    W, H = len(tx) * 256, len(ty) * 256
    img = Image.new("RGB", (W, H), (230, 230, 230))
    missing = 0
    for (x, y), t in tiles.items():
        if t is None:
            missing += 1
            continue
        img.paste(t.resize((256, 256)), ((x - tx[0]) * 256, (y - ty[0]) * 256))
    # crop to requested bbox
    px = lambda fx, fy: (int((fx - tx[0]) * 256), int((fy - ty[0]) * 256))
    (cx1, cy1), (cx2, cy2) = px(x1, y1), px(x2, y2)
    img = img.crop((cx1, cy1, cx2, cy2))
    mx1, my2 = merc(lo1, la2)
    mx2, my1 = merc(lo2, la1)
    meta = {"bounds_merc": [mx1, my1, mx2, my2], "bounds_ll": [lo1, la1, lo2, la2], "zoom": z, "size": img.size,
            "source": "Esri World Imagery" + (f" Wayback release {release}" if release else ""), "missing_tiles": missing,
            "tiles": len(urls)}
    img.save(out, quality=88)
    (d / f"img_{name}.json").write_text(json.dumps(meta))
    log((WAYBACK if release else ESRI).split("/tile")[0], sum(1 for t in tiles.values() if t) * 15000, f"{site.id} {name} z{z} {len(urls)} tiles")
    print(f"  {name}: z{z} {img.size} missing {missing}/{len(urls)}")
    return meta


def wayback_releases():
    cfg = json.loads((ROOT / "cache" / "waybackconfig.json").read_text())
    rel = sorted(((v["itemTitle"].split("Wayback ")[1].rstrip(")"), int(k)) for k, v in cfg.items()))
    return rel


def first_release(site, z, rel):
    """Earliest Wayback release whose tilemap has imagery at the site's centre tile."""
    x, y = tile_xy(site.lon, site.lat, z)
    for date, r in rel:
        u = f"https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tilemap/{r}/{z}/{int(y)}/{int(x)}"
        if S.get(u, timeout=30).json().get("data", [0])[0] == 1:
            return date, r
    return rel[-1]


PLAN = {  # name: (buffer m, zoom by site size)
    "hero": (90, {1: 19, 2: 17, 3: 19, 4: 17}),
    "context": (1400, {1: 16, 2: 15, 3: 16, 4: 15}),
    "wide": (3000, {1: 15, 2: 14, 3: 15, 4: 14}),
}

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4]
    rel = wayback_releases()
    last = rel[-1]
    for n in which:
        s = SITES[n]
        print(s.name)
        for name, (buf, zooms) in PLAN.items():
            mosaic(s, name, buf, zooms[n])
        zh = PLAN["hero"][1][n] - 1
        first = first_release(s, zh, rel)
        m0 = mosaic(s, "wb_first", 250, zh, release=first[1])
        m1 = mosaic(s, "wb_last", 250, zh, release=last[1])
        for nm, (date, r) in (("wb_first", first), ("wb_last", last)):
            p = ROOT / "cache" / s.id / f"img_{nm}.json"
            j = json.loads(p.read_text())
            j["release_date"] = date
            p.write_text(json.dumps(j))
