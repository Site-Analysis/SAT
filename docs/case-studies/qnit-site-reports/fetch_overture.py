"""Overture Maps (release 2026-09-23.0, S3) per site -> cache/<site>/ov_<type>.parquet.

Overture stands in for Overpass/OSM (blocked from this environment); roads, water, land use and
infrastructure in Overture derive from OpenStreetMap, places from Meta/Microsoft/others.
"""

import os
import sys
import time

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from fetch_open import bbox_ll, log
from sites import ROOT, SITES

os.environ.setdefault("AWS_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
REL = "overturemaps-us-west-2/release/2026-09-23.0"
h, p = os.environ["HTTPS_PROXY"].replace("http://", "").split(":")
FS = pafs.S3FileSystem(anonymous=True, region="us-west-2", proxy_options={"scheme": "http", "host": h, "port": int(p)})

# type -> (theme, buffer m, columns)
TYPES = {
    "segment": ("transportation", 3500, ["id", "geometry", "subtype", "class", "names", "road_surface", "width_rules", "subclass"]),
    "building": ("buildings", 1600, ["id", "geometry", "subtype", "class", "height", "num_floors", "names"]),
    "place": ("places", 9000, ["id", "geometry", "names", "basic_category", "taxonomy", "confidence", "addresses"]),
    "water": ("base", 4000, ["id", "geometry", "subtype", "class", "names", "is_intermittent"]),
    "land_use": ("base", 2500, ["id", "geometry", "subtype", "class", "names"]),
    "infrastructure": ("base", 6000, ["id", "geometry", "subtype", "class", "names"]),
}


def fetch(site, typ):
    theme, buf, cols = TYPES[typ]
    out = ROOT / "cache" / site.id / f"ov_{typ}.parquet"
    if out.exists():
        return
    x1, y1, x2, y2 = bbox_ll(site, buf)
    d = ds.dataset(f"{REL}/theme={theme}/type={typ}/", filesystem=FS, format="parquet")
    have = set(d.schema.names)
    cols = [c for c in cols if c in have] + ["bbox"]
    f = (pc.field("bbox", "xmax") > x1) & (pc.field("bbox", "xmin") < x2) & (pc.field("bbox", "ymax") > y1) & (pc.field("bbox", "ymin") < y2)
    t = time.time()
    tb = d.to_table(columns=cols, filter=f)
    pq.write_table(tb, out)
    log(f"s3://{REL}/theme={theme}/type={typ}", tb.nbytes, f"bbox {x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f} rows={tb.num_rows}")
    print(f"  {typ}: {tb.num_rows} rows in {time.time() - t:.0f}s")


if __name__ == "__main__":
    which = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4]
    for n in which:
        print(SITES[n].name)
        for typ in TYPES:
            fetch(SITES[n], typ)
