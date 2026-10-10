"""Report figures for one site. Every value drawn comes from results/<site>.json or cached source data."""

import json
import math
import pickle
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import FancyArrowPatch, Polygon as MplPoly, Rectangle, Wedge
from PIL import Image
from rasterio.transform import from_bounds as tr_from_bounds
from rasterio.warp import Resampling, reproject
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from analyse import CACHE, read_ov, name_of
from sites import ROOT, SITES, TO_UTM, TO_WGS

plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 8, "axes.edgecolor": "#9a9a9a", "axes.linewidth": 0.6,
                     "xtick.color": "#555", "ytick.color": "#555", "axes.labelcolor": "#444"})
GREEN = "#4f7a2a"
DKGREEN = "#2f5617"
ORANGE = "#e8892b"
BLUE = "#2f7fd9"
LBLUE = "#9cc8f2"
GREY = "#8a8a8a"
TXT = "#2b2b2b"
FIG = ROOT / "figures"
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]


# ------------------------------------------------------------------ basics
def save(fig, name, jpg=False):
    FIG.mkdir(exist_ok=True)
    p = FIG / f"{S.id}_{name}.{'jpg' if jpg else 'png'}"
    kw = {"pil_kwargs": {"quality": 86}} if jpg else {}
    fig.savefig(p, dpi=220, bbox_inches="tight", pad_inches=0.02, **kw)
    plt.close(fig)
    return p


def imagery_utm(name, bounds, res):
    """Reproject an Esri mosaic (EPSG:3857) onto a UTM 43N grid covering bounds (minx, miny, maxx, maxy)."""
    meta = json.loads((CACHE / S.id / f"img_{name}.json").read_text())
    im = np.asarray(Image.open(CACHE / S.id / f"img_{name}.jpg").convert("RGB"))
    H, W = im.shape[:2]
    src_tr = tr_from_bounds(*meta["bounds_merc"], W, H)
    minx, miny, maxx, maxy = bounds
    w, h = int((maxx - minx) / res), int((maxy - miny) / res)
    dst_tr = tr_from_bounds(minx, miny, maxx, maxy, w, h)
    out = np.zeros((3, h, w), np.uint8)
    for b in range(3):
        reproject(im[..., b], out[b], src_transform=src_tr, src_crs="EPSG:3857", dst_transform=dst_tr, dst_crs="EPSG:32643",
                  resampling=Resampling.bilinear)
    return out.transpose(1, 2, 0), meta


def map_axes(bounds, aspect_w, img=None, res=0.5, fade=0.0, figw=7.0):
    minx, miny, maxx, maxy = bounds
    figh = figw * (maxy - miny) / (maxx - minx)
    fig, ax = plt.subplots(figsize=(figw, figh))
    ax.set_position([0, 0, 1, 1])
    if img:
        arr, meta = imagery_utm(img, bounds, res)
        if fade:
            arr = (arr * (1 - fade) + 255 * fade).astype(np.uint8)
        ax.imshow(arr, extent=[minx, maxx, miny, maxy], origin="upper", interpolation="bilinear")
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def bounds_for(geom, aspect, pad):
    """Bounds around geom with a target width/height aspect and padding (m)."""
    minx, miny, maxx, maxy = geom.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    w, h = maxx - minx + 2 * pad, maxy - miny + 2 * pad
    if w / h < aspect:
        w = h * aspect
    else:
        h = w / aspect
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def site_outline(ax, fill=True, color="white", lw=1.6, alpha=0.18, z=5):
    xs, ys = S.poly.exterior.xy
    if fill:
        ax.add_patch(MplPoly(np.c_[xs, ys], closed=True, fc=(0.55, 0.75, 0.45, alpha), ec="none", zorder=z))
    ax.plot(xs, ys, color=color, lw=lw, zorder=z + 1, solid_joinstyle="round")


def north_scale(ax, bounds, dark=False, corner="tr", scale_m=None):
    minx, miny, maxx, maxy = bounds
    w, h = maxx - minx, maxy - miny
    col = "#222" if dark else "white"
    # north badge
    nx_, ny_ = (maxx - 0.055 * w, maxy - 0.09 * h) if corner == "tr" else (minx + 0.055 * w, maxy - 0.09 * h)
    ax.add_patch(plt.Circle((nx_, ny_), 0.032 * w, fc="white", ec="#cfcfcf", lw=0.6, zorder=20))
    ax.annotate("", xy=(nx_, ny_ + 0.022 * w), xytext=(nx_, ny_ - 0.018 * w),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.2, mutation_scale=7), zorder=21)
    ax.text(nx_, ny_ - 0.019 * w, "N", ha="center", va="top", fontsize=5.5, color="#333", zorder=21, weight="bold")
    # scale bar
    if scale_m is None:
        cand = [10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000]
        scale_m = min(cand, key=lambda c: abs(c - w * 0.18))
    x0, y0 = minx + 0.04 * w, miny + 0.05 * h
    ax.add_patch(Rectangle((x0 - 0.012 * w, y0 - 0.03 * h), scale_m + 0.06 * w, 0.075 * h, fc="white", ec="none", alpha=0.85, zorder=19))
    for k in range(4):
        ax.add_patch(Rectangle((x0 + k * scale_m / 4, y0), scale_m / 4, 0.012 * h, fc="#333" if k % 2 == 0 else "white", ec="#333", lw=0.4, zorder=20))
    ax.text(x0, y0 + 0.02 * h, "0", fontsize=5, ha="center", va="bottom", zorder=21, color="#333")
    lab = f"{scale_m/1000:g} km" if scale_m >= 1000 else f"{scale_m} m"
    ax.text(x0 + scale_m, y0 + 0.02 * h, lab, fontsize=5, ha="center", va="bottom", zorder=21, color="#333")


def tag(ax, x, y, text, fc=GREEN, fs=5.5, color="white", z=12):
    ax.text(x, y, text, fontsize=fs, color=color, ha="center", va="center", zorder=z, weight="bold",
            bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.3", fc=fc, ec="white", lw=0.5))


def label(ax, x, y, text, fs=6, color=TXT, ha="center", z=15, bold=False, box_=True):
    kw = dict(bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.4", fc="white", ec="#d8d8d8", lw=0.4, alpha=0.93)) if box_ else {}
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va="center", zorder=z, weight="bold" if bold else "normal", **kw)


def iter_lines(geom):
    t = geom.geom_type
    if t == "LineString":
        yield geom
    elif t in ("MultiLineString", "GeometryCollection"):
        for g in geom.geoms:
            yield from iter_lines(g)
    elif t == "Polygon":
        yield LineString(geom.exterior.coords)
    elif t == "MultiPolygon":
        for g in geom.geoms:
            yield LineString(g.exterior.coords)


def u2(lon, lat):
    return TO_UTM.transform(lon, lat)


# ------------------------------------------------------------------ figures
def fig_hero():
    b = bounds_for(S.poly, 1.67, 45)
    fig, ax = map_axes(b, 1.67, "hero", res=0.3)
    site_outline(ax, alpha=0.22)
    for i, (x, y) in enumerate(S.vertices):
        tag(ax, x, y, f"V{i+1}")
    north_scale(ax, b)
    return save(fig, "hero", jpg=True)


def fig_boundary():
    b = bounds_for(S.poly, 1.18, 60)
    fig, ax = map_axes(b, 1.18, "hero", res=0.3)
    site_outline(ax, alpha=0.12)
    g = pickle.load(open(CACHE / S.id / "geoms.pkl", "rb"))
    # plan roads (draft RMP 2031) and mapped streams/drains
    for p in g["proads"]:
        geom = p["geom"]
        for ln in iter_lines(geom):
            xs, ys = ln.xy
            ax.plot(xs, ys, color="#1d74d6", lw=1.2, ls=(0, (4, 2)), alpha=0.9, zorder=7)
    for st in g["streams"]:
        geom = st["geom"]
        for ln in iter_lines(geom):
            xs, ys = ln.xy
            ax.plot(xs, ys, color="#38c6f4", lw=1.6, zorder=8)
    for e in g["edges"]:
        (ax_, ay), (bx, by) = e["a"], e["b"]
        mx, my = (ax_ + bx) / 2, (ay + by) / 2
        nx_, ny_ = math.sin(math.radians(e["faces_deg"])), math.cos(math.radians(e["faces_deg"]))
        tag(ax, mx + nx_ * 16, my + ny_ * 16, e["name"], fc="#b8442f", fs=5.5)
    for i, (x, y) in enumerate(S.vertices):
        ax.plot(x, y, "o", ms=3.2, mfc="white", mec=GREEN, mew=1, zorder=9)
    north_scale(ax, b)
    if R["plan"]["roads"]:
        ax.plot([], [], color="#1d74d6", ls=(0, (4, 2)), lw=1.2, label=f"Draft RMP 2031 plan road ({'/'.join(sorted({str(int(p['row_m'])) for p in R['plan']['roads'] if p['row_m']}))} m)")
    ax.plot([], [], color="#38c6f4", lw=1.6, label="Mapped stream / drain")
    ax.legend(loc="lower right", fontsize=5, frameon=True, framealpha=0.9, edgecolor="#ddd", borderpad=0.5)
    return save(fig, "boundary", jpg=True)


def dem_grid():
    z = np.load(CACHE / S.id / "dem10.npy")
    t = json.loads((CACHE / S.id / "dem10.json").read_text())["transform"]
    H, W = z.shape
    xs = t[2] + (np.arange(W) + 0.5) * 10
    ys = t[5] - (np.arange(H) + 0.5) * 10
    return z, xs, ys


def hillshade(z, az=315, alt=45, res=10):
    gy, gx = np.gradient(z, res)
    slope = np.arctan(np.hypot(gx, gy) * 3)
    aspect = np.arctan2(-gx, gy)
    a, al = np.radians(az), np.radians(alt)
    return np.clip(np.sin(al) * np.cos(slope) + np.cos(al) * np.sin(slope) * np.cos(a - aspect), 0, 1)


def fig_terrain():
    t = R["terrain"]
    b = bounds_for(S.poly.buffer(80), 1.75, 70)
    fig, ax = map_axes(b, 1.75, "context", res=1.0, fade=0.35)
    z, xs, ys = dem_grid()
    cmap = LinearSegmentedColormap.from_list("t", ["#2e7fc8", "#7ec3d8", "#cfe8b8", "#f3d27a", "#e27b3c"])
    X, Y = np.meshgrid(xs, ys)
    sel = (X > b[0] - 50) & (X < b[2] + 50) & (Y > b[1] - 50) & (Y < b[3] + 50)
    vmin, vmax = np.nanmin(z[sel]), np.nanmax(z[sel])
    ax.contourf(X, Y, z, levels=np.arange(math.floor(vmin), math.ceil(vmax) + 1, 1), cmap=cmap, alpha=0.38, zorder=2)
    cs = ax.contour(X, Y, z, levels=np.arange(math.floor(vmin), math.ceil(vmax) + 1, 1), colors="#3b5f8a", linewidths=0.35, alpha=0.8, zorder=3)
    ax.clabel(cs, levels=cs.levels[::2], fontsize=4.5, fmt="%d", inline=True)
    site_outline(ax, alpha=0.05, color="white", lw=1.8)
    A, B = t["transect"]["A"], t["transect"]["B"]
    ax.plot([A[0], B[0]], [A[1], B[1]], color="#111", lw=0.9, ls=(0, (3, 2)), zorder=9)
    for p, n in ((A, "A"), (B, "B")):
        ax.plot(*p, "o", ms=4, color="#111", zorder=10)
        ax.text(p[0] + 12, p[1] + 12, n, fontsize=8, weight="bold", zorder=10, path_effects=HALO)
    lx, ly = t["low_pt"]
    hx, hy = t["high_pt"]
    ax.plot(lx, ly, "o", ms=4.5, mfc=BLUE, mec="white", zorder=11)
    label(ax, lx - 70, ly + 25, f"Low point · {t['low_pt_z']:.0f} m", fs=5.5)
    ax.plot(hx, hy, "o", ms=4.5, mfc=ORANGE, mec="white", zorder=11)
    label(ax, hx + 60, hy - 30, f"High point · {t['high_pt_z']:.0f} m", fs=5.5)
    d = math.radians(t["fall_dir_deg"])
    ax.add_patch(FancyArrowPatch((S.cx - 45 * math.sin(d), S.cy - 45 * math.cos(d)), (S.cx + 55 * math.sin(d), S.cy + 55 * math.cos(d)),
                                 arrowstyle="-|>", mutation_scale=12, color=BLUE, lw=1.6, zorder=12))
    label(ax, S.cx + 20, S.cy - 22, f"Fall {t['plane_slope_pct']:.1f}% → {t['fall_dir']}", fs=5.5, color=BLUE)
    # interval badge
    label(ax, b[0] + 0.12 * (b[2] - b[0]), b[3] - 0.07 * (b[3] - b[1]), f"Contour interval  {t['contour_interval_m']} m", fs=6)
    label(ax, b[2] - 0.14 * (b[2] - b[0]), b[1] + 0.07 * (b[3] - b[1]), f"{R['geometry']['area_m2']:,.0f} m²", fs=7, bold=True)
    north_scale(ax, b)
    return save(fig, "terrain", jpg=True)


def fig_transect():
    t = R["terrain"]["transect"]
    s = np.array([[p[0], p[1]] for p in t["samples"]])
    ins = np.array([p[2] for p in t["samples"]])
    fig, ax = plt.subplots(figsize=(7.2, 1.05))
    ax.fill_between(s[:, 0], s[:, 1].min() - 2, s[:, 1], color="#bfe3d6", alpha=0.9, lw=0)
    ax.plot(s[:, 0], s[:, 1], color="#2b8a6e", lw=1.1)
    if ins.any():
        x0, x1 = s[ins, 0].min(), s[ins, 0].max()
        ax.axvspan(x0, x1, color=GREEN, alpha=0.08, lw=0)
        ax.text((x0 + x1) / 2, s[:, 1].max() + 0.5, "Site", ha="center", fontsize=6, color=GREEN, weight="bold")
    ax.plot(s[0, 0], s[0, 1], "ko", ms=3)
    ax.plot(s[-1, 0], s[-1, 1], "ko", ms=3)
    ax.text(s[0, 0], s[0, 1] + 0.6, "A", fontsize=7, weight="bold")
    ax.text(s[-1, 0], s[-1, 1] + 0.6, "B", fontsize=7, weight="bold", ha="right")
    ax.set_xlim(0, s[-1, 0])
    ax.set_ylim(s[:, 1].min() - 1.5, s[:, 1].max() + 2.5)
    ax.set_xlabel("Distance (m)", fontsize=6)
    ax.set_ylabel("Elev. (m)", fontsize=6)
    ax.tick_params(labelsize=5.5)
    ax.grid(axis="y", color="#e6e6e6", lw=0.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.text(0.995, 0.93, "Section A – B · DSM 30 m", transform=ax.transAxes, ha="right", va="top", fontsize=5.5, color="#666")
    return save(fig, "transect")


def stereo(alt, R_):
    return R_ * np.tan(np.radians(90 - np.asarray(alt)) / 2) / math.tan(math.radians(45))


def fig_sunpath_map():
    so = R["solar"]
    b = bounds_for(S.poly, 1.26, 120)
    fig, ax = map_axes(b, 1.26, "context", res=0.6, fade=0.45)
    site_outline(ax, alpha=0.3, color=DKGREEN, lw=1.4)
    Rr = 0.44 * (b[3] - b[1])
    cx, cy = S.cx, S.cy
    ax.add_patch(plt.Circle((cx, cy), Rr, fc=(1, 0.95, 0.85, 0.25), ec="#999", lw=0.6, ls=(0, (3, 2)), zorder=6))
    for alt in (30, 60):
        ax.add_patch(plt.Circle((cx, cy), stereo(alt, Rr), fc="none", ec="#bbb", lw=0.4, ls=":", zorder=6))
    for az, l in ((0, "N"), (90, "E"), (180, "S"), (270, "W"), (45, "NE"), (135, "SE"), (225, "SW"), (315, "NW")):
        x, y = cx + (Rr + 14) * math.sin(math.radians(az)), cy + (Rr + 14) * math.cos(math.radians(az))
        ax.text(x, y, l, ha="center", va="center", fontsize=6 if len(l) == 1 else 5, weight="bold" if len(l) == 1 else "normal",
                color="#333", path_effects=HALO, zorder=8)
        ax.plot([cx, cx + Rr * math.sin(math.radians(az))], [cy, cy + Rr * math.cos(math.radians(az))], color="#cfcfcf", lw=0.3, zorder=6)
    styles = {"21 Jun": (ORANGE, "-", 1.6), "21 Mar": ("#f1b45c", "-", 1.1), "21 Dec": ("#c96d1a", (0, (4, 2)), 1.3)}
    for k, (c, ls, lw) in styles.items():
        cv = np.array([[p[0], p[1]] for p in so["curves"][k]])
        rr = stereo(cv[:, 1], Rr)
        ax.plot(cx + rr * np.sin(np.radians(cv[:, 0])), cy + rr * np.cos(np.radians(cv[:, 0])), color=c, lw=lw, ls=ls, zorder=7)
    for h, pts in so["hours"].items():
        pts = np.array(pts)
        if len(pts) < 3:
            continue
        rr = stereo(pts[:, 1], Rr)
        x, y = cx + rr * np.sin(np.radians(pts[:, 0])), cy + rr * np.cos(np.radians(pts[:, 0]))
        ax.plot(x, y, color="#e0a050", lw=0.4, alpha=0.7, zorder=7)
        i = 5 if len(x) > 5 else len(x) - 1  # June-ish point
        if int(h) in (6, 9, 12, 15, 18):
            ax.text(x[i], y[i], f"{int(h)}h", fontsize=5, color="#8a4a0a", zorder=9, path_effects=HALO, ha="center")
    # 9 am equinox sun marker
    cv = [p for p in so["curves"]["21 Mar"] if p[2] == "09:00"]
    if cv:
        az, alt = cv[0][0], cv[0][1]
        rr = stereo(alt, Rr)
        ax.plot(cx + rr * math.sin(math.radians(az)), cy + rr * math.cos(math.radians(az)), "o", ms=9, color=ORANGE, mec="white", mew=1.2, zorder=10)
    ax.plot([], [], color=ORANGE, lw=1.6, label="21 Jun")
    ax.plot([], [], color="#f1b45c", lw=1.1, label="21 Mar / 21 Sep")
    ax.plot([], [], color="#c96d1a", lw=1.3, ls=(0, (4, 2)), label="21 Dec")
    ax.legend(loc="lower right", fontsize=5.2, frameon=True, framealpha=0.92, edgecolor="#ddd")
    label(ax, cx, cy - 0.06 * (b[3] - b[1]), f"{R['geometry']['area_ha']:.2f} ha · {S.rec['village']}",
          fs=6, bold=True, color="white", box_=False)
    ax.texts[-1].set_bbox(dict(boxstyle="round,pad=0.35", fc=DKGREEN, ec="none"))
    north_scale(ax, b, corner="tl")
    return save(fig, "sunpath", jpg=True)


def fig_seasonal_polar():
    so = R["solar"]
    fig = plt.figure(figsize=(2.6, 2.5))
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    for k, (c, ls, lw) in {"21 Jun": (ORANGE, "-", 1.6), "21 Mar": ("#f1b45c", "-", 1.1), "21 Dec": ("#9a9a9a", (0, (4, 2)), 1.2)}.items():
        cv = np.array([[p[0], p[1]] for p in so["curves"][k]])
        ax.plot(np.radians(cv[:, 0]), 90 - cv[:, 1], color=c, lw=lw, ls=ls, label=k)
        i = int(np.argmax(cv[:, 1]))
        ax.plot(np.radians(cv[i, 0]), 90 - cv[i, 1], "o", ms=3, color=c)
    ax.set_rlim(0, 90)
    ax.set_rticks([10, 30, 50, 70])
    ax.set_yticklabels(["80°", "60°", "40°", "20°"], fontsize=5, color="#888")
    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(["N", "E", "S", "W"], fontsize=7, weight="bold")
    ax.grid(color="#dddddd", lw=0.5)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=5.5, frameon=False)
    return save(fig, "sunpolar")


def fig_solar_faces():
    so = R["solar"]
    f = so["faces_kwh"]
    fig = plt.figure(figsize=(3.6, 2.6))
    ax = fig.add_axes([0.0, 0.02, 0.56, 0.96], projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    vals = np.array([f[d] for d in dirs])
    cmap = LinearSegmentedColormap.from_list("o", ["#fde7c6", "#f6b15a", "#e3661f", "#b8320f"])
    norm = (vals - vals.min()) / (vals.max() - vals.min() + 1e-9)
    ax.bar(np.radians(np.arange(0, 360, 45)), vals, width=np.radians(40), color=cmap(norm), edgecolor="white", lw=0.8)
    for th, v in zip(np.arange(0, 360, 45), vals):
        ax.text(np.radians(th), v + 150, f"{v:,.0f}", ha="center", va="center", fontsize=5.2, color="#5a3008")
    ax.set_rlim(0, vals.max() + 300)
    ax.set_yticks([])
    ax.set_xticks(np.radians(np.arange(0, 360, 45)))
    ax.set_xticklabels(dirs, fontsize=6, weight="bold")
    ax.grid(color="#eee", lw=0.5)
    ax.spines["polar"].set_color("#ddd")
    ax.set_title("Wall kWh/m²·yr by facing", fontsize=5.5, color="#555", pad=8)
    # monthly GHI bars
    bx = fig.add_axes([0.66, 0.16, 0.33, 0.68])
    m = so["ghi_month_kwh"]
    bx.bar(range(12), m, color=[ORANGE if v == max(m) else "#f3c48e" for v in m], width=0.75)
    bx.set_xticks(range(12))
    bx.set_xticklabels(list("JFMAMJJASOND"), fontsize=5)
    bx.tick_params(axis="y", labelsize=5)
    bx.set_title("Horizontal kWh/m² per month", fontsize=5.5, color="#555", loc="left")
    for sp in ("top", "right"):
        bx.spines[sp].set_visible(False)
    bx.grid(axis="y", color="#eee", lw=0.5)
    return save(fig, "solar")


def rose_axes(fig, rect, rose, colors=None, title=None):
    ax = fig.add_axes(rect, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    tab = np.array(rose["table"])
    th = np.radians(np.arange(16) * 22.5)
    base = np.zeros(16)
    colors = colors or ["#d6e9fb", "#a9d1f6", "#72b2ef", "#3f8fe2", "#1f6fc9", "#0f4f99"]
    labs = ["<1", "1–2", "2–3", "3–4", "4–5", "≥5 m/s"]
    for k in range(tab.shape[1]):
        ax.bar(th, tab[:, k], width=np.radians(20), bottom=base, color=colors[k], edgecolor="white", lw=0.3, label=labs[k])
        base += tab[:, k]
    mx = base.max()
    step = 5 if mx > 12 else 2
    ticks = np.arange(step, mx + step, step)
    ax.set_rticks(ticks)
    ax.set_yticklabels([f"{t:g}%" for t in ticks], fontsize=4.5, color="#888")
    ax.set_rlabel_position(22)
    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(["N", "E", "S", "W"], fontsize=6.5, weight="bold")
    ax.grid(color="#dddddd", lw=0.4)
    ax.spines["polar"].set_color("#ddd")
    if title:
        ax.set_title(title, fontsize=5.5, color="#555", pad=2)
    return ax


def fig_windrose():
    st = R["wind"]["station"]
    fig = plt.figure(figsize=(2.1, 2.5))
    ax = rose_axes(fig, [0.06, 0.24, 0.88, 0.72], st["annual"])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=4.6, frameon=False, handlelength=1, columnspacing=0.8)
    return save(fig, "windrose")


def fig_wind_map():
    w = R["wind"]["station"]["seasons"]
    b = bounds_for(S.poly, 1.49, 330)
    fig, ax = map_axes(b, 1.49, "context", res=1.0, fade=0.38)
    site_outline(ax, alpha=0.35, color=DKGREEN, lw=1.4)
    # arrows: SW monsoon (from W) in blue, winter (from E) in teal — direction = towards
    sm = w["SW monsoon (Jun–Sep)"]
    wi = w["Winter (Dec–Feb)"]
    rng = np.random.default_rng(3)
    W_, H_ = b[2] - b[0], b[3] - b[1]
    for season, col, n, yband in ((sm, BLUE, 26, (0.08, 0.92)), (wi, "#26a69a", 9, (0.12, 0.88))):
        to = math.radians((season["prevailing_deg"] + 180) % 360)
        dx, dy = math.sin(to), math.cos(to)
        L = 0.13 * W_ * (season["mean_speed"] / 5.0)
        for _ in range(n):
            x0 = b[0] + rng.uniform(0.05, 0.95) * W_
            y0 = b[1] + rng.uniform(*yband) * H_
            if season is wi and abs(y0 - S.cy) < 0.18 * H_:
                continue
            ax.add_patch(FancyArrowPatch((x0, y0), (x0 + dx * L, y0 + dy * L), arrowstyle="-|>", mutation_scale=7,
                                         color=col, lw=1.1 if season is sm else 0.9, alpha=0.85 if season is sm else 0.75, zorder=8))
    ax.plot([], [], color=BLUE, lw=1.2, label=f"SW monsoon (Jun–Sep): from {sm['prevailing']}, {sm['mean_speed']} m/s mean")
    ax.plot([], [], color="#26a69a", lw=1.2, label=f"Winter (Dec–Feb): from {wi['prevailing']}, {wi['mean_speed']} m/s mean")
    ax.legend(loc="lower right", fontsize=5.2, frameon=True, framealpha=0.92, edgecolor="#ddd")
    for l in R["water"]["lakes"][:3]:
        pass
    north_scale(ax, b)
    return save(fig, "windmap", jpg=True)


WC_COL = {10: "#2f7d32", 20: "#a3a14a", 30: "#c9e39a", 40: "#f0d76a", 50: "#d6544a", 60: "#c9b59a", 80: "#3e9ce0", 90: "#5fb6a8"}
WC_NAME = {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up", 60: "Bare / sparse", 80: "Water", 90: "Wetland"}


def worldcover_utm(bounds, res=10, yr=2021):
    with rasterio.open(CACHE / S.id / f"wc{yr}.tif") as ds:
        minx, miny, maxx, maxy = bounds
        w, h = int((maxx - minx) / res), int((maxy - miny) / res)
        out = np.zeros((h, w), np.uint8)
        reproject(rasterio.band(ds, 1), out, dst_transform=tr_from_bounds(*bounds, w, h), dst_crs="EPSG:32643", resampling=Resampling.nearest)
    return out


def fig_comfort():
    b = bounds_for(S.poly.buffer(500), 1.31, 20)
    fig, ax = map_axes(b, 1.31, "context", res=1.5, fade=0.15)
    wc = worldcover_utm(b)
    rgba = np.zeros(wc.shape + (4,))
    for k, c in WC_COL.items():
        m = wc == k
        rgba[m, :3] = matplotlib.colors.to_rgb(c)
        rgba[m, 3] = 0.55
    ax.imshow(rgba, extent=[b[0], b[2], b[1], b[3]], origin="upper", zorder=3, interpolation="nearest")
    ring = S.poly.buffer(500)
    xs, ys = ring.exterior.xy
    ax.plot(xs, ys, color="white", lw=0.9, ls=(0, (4, 3)), zorder=6)
    site_outline(ax, alpha=0.0, color="white", lw=1.8)
    lc = R["landcover"]
    present = [k for k in WC_COL if (wc == k).mean() > 0.003]
    for k in present:
        ax.add_patch(Rectangle((0, 0), 0, 0, fc=WC_COL[k], alpha=0.75, label=WC_NAME[k]))
    ax.legend(loc="lower right", fontsize=5, frameon=True, framealpha=0.92, edgecolor="#ddd", ncol=2, handlelength=1)
    # annotate nearest lake edge
    lk = [l for l in R["water"]["lakes"] if l["class"] in ("lake", "reservoir", "pond")]
    if lk:
        tag(ax, S.cx, b[1] + 0.12 * (b[3] - b[1]), f"{lk[0]['name'] or 'Lake'} · {lk[0]['dist_m']:.0f} m {lk[0]['bearing']}", fc=BLUE, fs=5)
    pa = R.get("sensitive", {}).get("protected")
    if pa and pa["dist_m"] < 600:
        tag(ax, b[0] + 0.16 * (b[2] - b[0]), S.cy, f"{pa['name']} · {pa['dist_m']:.0f} m {pa['bearing']}", fc=DKGREEN, fs=4.6)
    tag(ax, S.cx, S.cy, f"Site · canopy {lc['canopy_site']:.0f}% ({lc['year']})", fc=DKGREEN, fs=5)
    label(ax, b[0] + 0.2 * (b[2] - b[0]), b[3] - 0.06 * (b[3] - b[1]), f"500 m ring: {lc['built_ring']:.0f}% built · {lc['canopy_ring']:.0f}% tree", fs=5)
    north_scale(ax, b)
    return save(fig, "comfort", jpg=True)


def fig_temperature():
    c = R["climate"]
    fig, ax = plt.subplots(figsize=(3.5, 2.35))
    x = np.arange(12)
    ax.fill_between(x, c["tmin"], c["tmax"], color="#f4e2d2", alpha=0.6, lw=0)
    ax.plot(x, c["tmax"], color="#a5532a", lw=1.4, label="Mean daily max")
    ax.plot(x, c["tmin"], color="#4f7f99", lw=1.4, label="Mean daily min")
    i = int(np.argmax(c["tmax"]))
    ax.annotate(f"{c['tmax'][i]:.1f}°", (i, c["tmax"][i]), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=5.5, color="#a5532a")
    j = int(np.argmin(c["tmin"]))
    ax.annotate(f"{c['tmin'][j]:.1f}°", (j, c["tmin"][j]), xytext=(0, -9), textcoords="offset points", ha="center", fontsize=5.5, color="#4f7f99")
    ax.set_xticks(x)
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], fontsize=5.5)
    ax.set_ylim(0, 40)
    ax.set_ylabel("°C", fontsize=7)
    ax.tick_params(axis="y", labelsize=5.5)
    ax.grid(axis="y", color="#e6e6e6", lw=0.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.32), ncol=2, fontsize=5.5, frameon=False)
    return save(fig, "temperature")


def fig_runoff():
    b = bounds_for(S.poly, 1.39, 260)
    fig, ax = map_axes(b, 1.39, "context", res=1.0, fade=0.5)
    z, xs, ys = dem_grid()
    hs = hillshade(z)
    X, Y = np.meshgrid(xs, ys)
    ax.imshow(hs, extent=[xs[0] - 5, xs[-1] + 5, ys[-1] - 5, ys[0] + 5], cmap="Greys_r", alpha=0.18, zorder=2)
    cs = ax.contour(X, Y, z, levels=np.arange(880, 925, 1), colors="#7a8f9e", linewidths=0.3, alpha=0.6, zorder=3)
    acc = np.load(CACHE / S.id / "acc30.npy")
    t30 = json.loads((CACHE / S.id / "acc30.json").read_text())["transform"]
    Ha, Wa = acc.shape
    ax_ = t30[2] + (np.arange(Wa) + 0.5) * 30
    ay_ = t30[5] - (np.arange(Ha) + 0.5) * 30
    lacc = np.log10(acc)
    m = np.ma.masked_less(acc, 30)
    ax.imshow(np.ma.masked_where(m.mask, lacc), extent=[ax_[0] - 15, ax_[-1] + 15, ay_[-1] - 15, ay_[0] + 15], origin="upper",
              cmap=LinearSegmentedColormap.from_list("b", ["#9fd3f7", "#1565c0"]), alpha=0.8, zorder=4, interpolation="nearest")
    g = pickle.load(open(CACHE / S.id / "geoms.pkl", "rb"))
    for l in g["lakes"]:
        geom = l["geom"]
        for p in (getattr(geom, "geoms", None) or [geom]):
            xs_, ys_ = p.exterior.xy
            ax.fill(xs_, ys_, color="#4aa3e6", alpha=0.35, zorder=4)
    for st in g["streams"] + g["drains"]:
        geom = st["geom"]
        for ln in iter_lines(geom):
            xs_, ys_ = ln.xy
            ax.plot(xs_, ys_, color="#38c6f4", lw=1.0, zorder=5)
    site_outline(ax, alpha=0.1, color="#111", lw=1.3)
    t = R["terrain"]
    path = np.array(t["outlet_path"])
    ax.plot(path[:, 0], path[:, 1], color="#0d47a1", lw=1.4, zorder=7)
    ax.add_patch(FancyArrowPatch(tuple(path[min(4, len(path) - 2)]), tuple(path[min(6, len(path) - 1)]), arrowstyle="-|>", mutation_scale=9, color="#0d47a1", zorder=8))
    lx, ly = t["low_pt"]
    ax.plot(lx, ly, "o", ms=5, mfc=BLUE, mec="white", zorder=9)
    tag(ax, lx - 5, ly + 40, f"Low point {t['low_pt_z']:.0f} m", fc="#0d47a1", fs=5)
    lk = [l for l in R["water"]["lakes"] if l["class"] in ("lake", "reservoir") and l["name"]]
    for l in lk[:2]:
        gg = [x for x in g["lakes"] if x["name"] == l["name"]][0]["geom"]
        c = gg.representative_point()
        if b[0] < c.x < b[2] and b[1] < c.y < b[3]:
            label(ax, c.x, c.y, l["name"], fs=5.5, color="#0d47a1")
    north_scale(ax, b)
    ax.add_patch(Rectangle((0, 0), 0, 0, fc="#1565c0", label="Modelled flow path (D8, 30 m)"))
    ax.plot([], [], color="#38c6f4", lw=1, label="Mapped stream / storm drain")
    ax.legend(loc="lower right", fontsize=5, frameon=True, framealpha=0.92, edgecolor="#ddd")
    return save(fig, "runoff", jpg=True)


def fig_rainfall():
    c = R["climate"]
    fig, ax = plt.subplots(figsize=(2.9, 1.42))
    x = np.arange(12)
    ax.bar(x, np.array(c["rain_p90"]) - np.array(c["rain_p10"]), bottom=c["rain_p10"], color="#dedede", width=0.8, label="Typical range (P10–P90)")
    ax.bar(x, c["rain_mean"], color=BLUE, width=0.42, label="Mean monthly rain")
    ax.axvspan(4.5, 10.5, color="#e9f3fd", zorder=-1)
    ax.text(7.5, max(c["rain_p90"]) * 1.02, "Wetter season", ha="center", fontsize=5, color="#3a6ea5")
    ax.set_xticks(x)
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], fontsize=4.6)
    ax.set_ylabel("Rainfall (mm)", fontsize=5.5)
    ax.tick_params(axis="y", labelsize=5)
    ax.set_ylim(0, max(c["rain_p90"]) * 1.15)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(loc="upper left", fontsize=4.5, frameon=False)
    return save(fig, "rainfall")


def fig_groundwater():
    t = R["terrain"]["transect"]
    s = np.array([[p[0], p[1]] for p in t["samples"]])
    fig, ax = plt.subplots(figsize=(7.2, 1.35))
    x = s[:, 0]
    g = s[:, 1]
    top = g.max() + 3
    # conceptual strata (depths from CGWB district profile: weathered zone 10–30 m; water 5–30 m bgl pre-monsoon)
    ax.fill_between(x, g, g - 2, color="#c58f5c", alpha=0.55, lw=0)  # soil
    ax.fill_between(x, g - 2, g - 22, color="#e7d7bf", alpha=0.85, lw=0, hatch="....", edgecolor="#cbb79a")  # weathered
    ax.fill_between(x, g - 22, g - 60, color="#c9c9c9", alpha=0.6, lw=0, hatch="xx", edgecolor="#b0b0b0")  # fractured gneiss
    wt = g - 18
    ax.fill_between(x, g - 30, g - 8, color="#7fb8e8", alpha=0.25, lw=0)
    ax.plot(x, wt, color=BLUE, lw=1, ls=(0, (4, 2)))
    ax.plot(x, g, color="#5a3d1e", lw=1.1)
    ins = np.array([p[2] for p in t["samples"]])
    if ins.any():
        x0, x1 = x[ins].min(), x[ins].max()
        ax.axvspan(x0, x1, ymin=0.86, ymax=0.93, color=GREEN, alpha=0.7)
        ax.text((x0 + x1) / 2, top + 1.5, "Site", ha="center", fontsize=6, color=GREEN, weight="bold")
    ax.text(x[0], top + 1.5, "A", fontsize=7, weight="bold")
    ax.text(x[-1], top + 1.5, "B", fontsize=7, weight="bold", ha="right")
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(g.min() - 62, top + 5)
    ax.set_yticks([])
    ax.set_xticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.legend(handles=[plt.Line2D([], [], color="#5a3d1e", lw=1.1, label="Ground (DSM section A–B)"),
                       plt.Line2D([], [], color=BLUE, lw=1, ls=(0, (4, 2)), label="Water table, conceptual (5–30 m bgl band)"),
                       Rectangle((0, 0), 1, 1, fc="#e7d7bf", hatch="....", ec="#cbb79a", label="Weathered gneiss, phreatic (10–30 m)"),
                       Rectangle((0, 0), 1, 1, fc="#c9c9c9", hatch="xx", ec="#b0b0b0", label="Jointed / fractured gneiss, semi-confined")],
              loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=5.2, frameon=False)
    return save(fig, "groundwater")


def fig_landscape():
    b = bounds_for(S.poly.buffer(1000), 1.88, 0)
    fig, ax = map_axes(b, 1.88, "wide", res=3.0, fade=0.1)
    site_outline(ax, alpha=0.25, color="white", lw=1.6)
    g = pickle.load(open(CACHE / S.id / "geoms.pkl", "rb"))
    # observer at site centroid, cones to the three nearest named lakes
    ox, oy = S.cx, S.cy
    cols = ["#3e9ce0", "#2f9e6f", "#e8892b"]
    from shapely.geometry import Point as P_

    targets = []
    lu = read_ov(S, "land_use")
    if not lu.empty:
        prot = lu[lu["subtype"] == "protected"]
        for _, row in prot.iterrows():
            clip = row.geom.intersection(P_(ox, oy).buffer(1400))
            if not clip.is_empty and clip.area > 1e4:
                targets.append({"name": name_of(row["names"]) or "Protected area", "geom": clip, "dist_m": row.geom.distance(S.poly)})
                break
    named = [l for l in g["lakes"] if l["class"] in ("lake", "reservoir", "water", "pond") and l["area_ha"] >= 0.5]
    named = sorted(named, key=lambda l: (l["name"] is None, l["dist_m"]))
    for l in named[: 3 - len(targets)]:
        targets.append({"name": l["name"] or "Lake", "geom": l["geom"], "dist_m": l["dist_m"]})
    lk = targets
    for l, c in zip(lk, cols):
        geom = l["geom"]
        pts = np.array(geom.convex_hull.exterior.coords)
        ang = np.degrees(np.arctan2(pts[:, 0] - ox, pts[:, 1] - oy))
        a0 = math.degrees(math.atan2(geom.centroid.x - ox, geom.centroid.y - oy))
        rel = (ang - a0 + 180) % 360 - 180
        lo, hi = a0 + rel.min(), a0 + rel.max()
        rr = Point(ox, oy).distance(geom.centroid) + 150
        poly = [(ox, oy)] + [(ox + rr * math.sin(math.radians(a)), oy + rr * math.cos(math.radians(a))) for a in np.linspace(lo, hi, 20)]
        ax.add_patch(MplPoly(poly, closed=True, fc=c, ec="white", lw=0.8, ls=(0, (3, 2)), alpha=0.28, zorder=6))
        am = math.radians((lo + hi) / 2)
        dd = min(Point(ox, oy).distance(geom) + 80, 0.42 * (b[3] - b[1]) / max(abs(math.cos(am)), 0.35))
        lx_, ly_ = ox + dd * math.sin(am), oy + dd * math.cos(am)
        lx_ = min(max(lx_, b[0] + 0.12 * (b[2] - b[0])), b[2] - 0.12 * (b[2] - b[0]))
        ly_ = min(max(ly_, b[1] + 0.08 * (b[3] - b[1])), b[3] - 0.08 * (b[3] - b[1]))
        label(ax, lx_, ly_, f"{l['name']} · {l['dist_m']:.0f} m", fs=5.5, color="#0d3d66")
    ax.plot(ox, oy, "o", ms=6, color=DKGREEN, mec="white", mew=1.2, zorder=10)
    tag(ax, ox, oy + 120, "Observer · site centre", fc=DKGREEN, fs=5)
    for st in g["drains"]:
        geom = st["geom"]
        for ln in iter_lines(geom):
            xs_, ys_ = ln.xy
            ax.plot(xs_, ys_, color="#38c6f4", lw=1.1, zorder=5)
    north_scale(ax, b)
    return save(fig, "landscape", jpg=True)


def buildings_utm():
    b = read_ov(S, "building")
    return b[[g.geom_type in ("Polygon", "MultiPolygon") for g in b.geom]]


def fig_context():
    b = bounds_for(S.poly, 2.45, 380)
    fig, ax = map_axes(b, 2.45, "context", res=1.0, fade=0.72)
    bl = buildings_utm()
    seg = read_ov(S, "segment")
    seg = seg[seg["subtype"] == "road"]
    wmap = {"motorway": 3, "trunk": 3, "primary": 2.4, "secondary": 2, "tertiary": 1.5, "residential": 0.9, "unclassified": 0.8, "service": 0.5}
    for _, row in seg.iterrows():
        geom = row.geom
        if not geom.intersects(box(*b)):
            continue
        for ln in iter_lines(geom):
            xs_, ys_ = ln.xy
            ax.plot(xs_, ys_, color="#ffffff", lw=wmap.get(row["class"], 0.6) + 0.8, zorder=3, solid_capstyle="round")
            ax.plot(xs_, ys_, color="#c9c4bb" if row["class"] not in ("trunk", "primary", "secondary") else "#e7b46a",
                    lw=wmap.get(row["class"], 0.6), zorder=4, solid_capstyle="round")
    from matplotlib.collections import PatchCollection

    patches, cols = [], []
    for g in bl.geom:
        if not g.intersects(box(*b)):
            continue
        for p in (getattr(g, "geoms", None) or [g]):
            patches.append(MplPoly(np.array(p.exterior.coords)))
            a = p.area
            cols.append("#b9a68a" if a < 150 else "#a08c6f" if a < 600 else "#7f6f57")
    ax.add_collection(PatchCollection(patches, facecolors=cols, edgecolors="white", linewidths=0.15, zorder=5))
    site_outline(ax, alpha=0.35, color=DKGREEN, lw=1.5)
    sk = R["skyline"]
    A, B = sk["A"], sk["B"]
    ax.plot([A[0], B[0]], [A[1], B[1]], color="#111", lw=0.8, ls=(0, (4, 2)), zorder=9)
    tag(ax, A[0] + 15, A[1], "A", fc="#111", fs=6)
    tag(ax, B[0] - 15, B[1], "B", fc="#111", fs=6)
    label(ax, S.cx, S.cy + 0.13 * (b[3] - b[1]), f"Site {S.n} · {R['geometry']['area_ha']:.2f} ha", fs=6, bold=True, color=DKGREEN)
    for k, v in (R["context"]["major_roads"] or {}).items():
        pass
    north_scale(ax, b)
    ax.add_patch(Rectangle((0, 0), 0, 0, fc="#b9a68a", label="Building < 150 m²"))
    ax.add_patch(Rectangle((0, 0), 0, 0, fc="#a08c6f", label="150–600 m²"))
    ax.add_patch(Rectangle((0, 0), 0, 0, fc="#7f6f57", label="> 600 m² (apartment / institutional)"))
    ax.legend(loc="lower right", fontsize=5, frameon=True, framealpha=0.92, edgecolor="#ddd", ncol=3)
    return save(fig, "context", jpg=True)


def fig_skyline():
    sk = R["skyline"]
    fig, ax = plt.subplots(figsize=(7.2, 0.95))
    gr = np.array(sk["ground"])
    base = gr[:, 1].min() - 2
    ax.fill_between(gr[:, 0], base, gr[:, 1], color="#e9e4dc", lw=0)
    ax.plot(gr[:, 0], gr[:, 1], color="#8c7b62", lw=0.8)
    for it in sk["buildings"]:
        gz = np.interp((it["x0"] + it["x1"]) / 2, gr[:, 0], gr[:, 1])
        col = "#7aa35a" if it["inside"] else ("#b3a38b" if it["src"] == "assumed" else "#8b7a60")
        ax.add_patch(Rectangle((it["x0"], gz), max(3, it["x1"] - it["x0"]), it["h"], fc=col, ec="white", lw=0.3,
                               hatch="////" if it["src"] == "assumed" and not it["inside"] else None, alpha=0.95))
    x0, x1 = sk["site_x"]
    ax.axvspan(x0, x1, color=GREEN, alpha=0.08, lw=0)
    ax.text((x0 + x1) / 2, gr[:, 1].max() + 20, "Site", ha="center", fontsize=6, color=GREEN, weight="bold")
    ax.text(0, gr[0, 1] + 24, "A  West", fontsize=6, weight="bold")
    ax.text(1200, gr[-1, 1] + 24, "East  B", fontsize=6, weight="bold", ha="right")
    ax.set_xlim(0, 1200)
    ax.set_ylim(base, gr[:, 1].max() + 30)
    ax.set_yticks([])
    ax.set_xticks([0, 200, 400, 600, 800, 1000, 1200])
    ax.set_xticklabels([f"{v} m" for v in (0, 200, 400, 600, 800, 1000, 1200)], fontsize=5)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    return save(fig, "skyline")


def fig_isochrones():
    g = pickle.load(open(CACHE / S.id / "geoms.pkl", "rb"))
    iso = g["iso"]
    b = bounds_for(iso[15], 1.08, 120)
    fig, ax = map_axes(b, 1.08, "wide", res=2.5, fade=0.62)
    for mins, col, a in ((15, "#cfe6c1", 0.6), (10, "#8fc27a", 0.55), (5, "#3f7f2a", 0.6)):
        geom = iso[mins]
        for p in (getattr(geom, "geoms", None) or [geom]):
            ax.add_patch(MplPoly(np.array(p.exterior.coords), closed=True, fc=col, ec="white", lw=0.5, alpha=a, zorder=4 + (15 - mins) / 5))
    site_outline(ax, alpha=0.6, color="#1d3b10", lw=1.2, z=8)
    icons = {"Transit": ("#1e6fd9", "B"), "Health": ("#d63a3a", "+"), "Education": ("#e08a1e", "E"), "Daily needs": ("#7b3fb3", "D")}
    for k, (c, sym) in icons.items():
        for p in R["access"]["poi"][k][:3]:
            if b[0] < p["x"] < b[2] and b[1] < p["y"] < b[3]:
                ax.plot(p["x"], p["y"], "o", ms=6.5, color=c, mec="white", mew=0.8, zorder=10)
                ax.text(p["x"], p["y"], sym, color="white", fontsize=4.5, ha="center", va="center", weight="bold", zorder=11)
    infra = R["infrastructure"]
    if "bus_stop" in infra:
        bs = infra["bus_stop"]
        ax.plot(bs["x"], bs["y"], "s", ms=5, color="#1e6fd9", mec="white", zorder=10)
    for mins in (5, 10, 15):
        geom = iso[mins]
        top = max((getattr(geom, "geoms", None) or [geom]), key=lambda p: p.area)
        y = top.bounds[3]
        xs = [c[0] for c in top.exterior.coords if abs(c[1] - y) < 1]
        label(ax, xs[0] if xs else S.cx, y - 25, f"{mins} min", fs=5, bold=True, color=DKGREEN)
    north_scale(ax, b)
    return save(fig, "isochrones", jpg=True)


def fig_landuse_change():
    b = bounds_for(S.poly, 1.75, 110)
    a1, m1 = imagery_utm("wb_first", b, 0.7)
    a2, m2 = imagery_utm("wb_last", b, 0.7)
    w = a1.shape[1]
    comb = a2.copy()
    comb[:, : w // 2] = a1[:, : w // 2]
    fig, ax = map_axes(b, 1.75, None)
    ax.imshow(comb, extent=[b[0], b[2], b[1], b[3]], origin="upper")
    xm = (b[0] + b[2]) / 2
    ax.axvline(xm, color="white", lw=1.4, zorder=8)
    ax.plot(xm, (b[1] + b[3]) / 2, "o", ms=9, color="white", mec="#999", zorder=9)
    ax.text(xm, (b[1] + b[3]) / 2, "‹›", fontsize=6, ha="center", va="center", zorder=10, color="#444")
    site_outline(ax, alpha=0.0, color="#ffe066", lw=1.3)
    tag(ax, b[0] + 0.1 * (b[2] - b[0]), b[3] - 0.08 * (b[3] - b[1]), m1["release_date"][:4], fc="white", color="#222", fs=6)
    tag(ax, b[2] - 0.1 * (b[2] - b[0]), b[3] - 0.08 * (b[3] - b[1]), m2["release_date"][:4], fc="white", color="#222", fs=6)
    north_scale(ax, b)
    return save(fig, "landuse_change", jpg=True)


def fig_density():
    b = bounds_for(S.poly.buffer(1200), 1.78, 0)
    fig, ax = map_axes(b, 1.78, "wide", res=3.0, fade=0.8)
    bl = buildings_utm()
    cx = np.array([g.centroid.x for g in bl.geom])
    cy = np.array([g.centroid.y for g in bl.geom])
    ar = np.array([g.area for g in bl.geom])
    m = (cx > b[0]) & (cx < b[2]) & (cy > b[1]) & (cy < b[3])
    hb = ax.hexbin(cx[m], cy[m], C=ar[m], reduce_C_function=np.sum, gridsize=26, extent=(b[0], b[2], b[1], b[3]),
                   cmap=LinearSegmentedColormap.from_list("g", ["#e6f2ec", "#9fd0b8", "#3f9a76", "#155c43"]), mincnt=1, alpha=0.82,
                   linewidths=0.2, edgecolors="white", zorder=4)
    site_outline(ax, alpha=0.0, color="#0b3d2a", lw=1.5, z=8)
    ax.add_patch(MplPoly(np.array(S.poly.exterior.coords), closed=True, fc="#164f39", alpha=0.85, zorder=7))
    tag(ax, S.cx, S.cy - 160, "Site", fc="#164f39", fs=5.5)
    cb = fig.add_axes([0.73, 0.06, 0.22, 0.035])
    plt.colorbar(hb, cax=cb, orientation="horizontal")
    cb.tick_params(labelsize=4.5)
    cb.set_title("Built footprint m² / cell", fontsize=4.8, pad=2)
    north_scale(ax, b, corner="tl")
    return save(fig, "density", jpg=True)


def fig_services():
    b = bounds_for(S.poly, 1.38, 520)
    fig, ax = map_axes(b, 1.38, "context", res=1.0, fade=0.68)
    seg = read_ov(S, "segment")
    seg = seg[seg["subtype"] == "road"]
    for _, row in seg.iterrows():
        geom = row.geom
        if not geom.intersects(box(*b)):
            continue
        maj = row["class"] in ("trunk", "primary", "secondary", "tertiary", "motorway")
        for ln in iter_lines(geom):
            xs_, ys_ = ln.xy
            ax.plot(xs_, ys_, color="#f0a646" if maj else "#d3cec6", lw=1.6 if maj else 0.6, zorder=3)
    g = pickle.load(open(CACHE / S.id / "geoms.pkl", "rb"))
    for l in g["lakes"]:
        geom = l["geom"]
        for p in (getattr(geom, "geoms", None) or [geom]):
            xs_, ys_ = p.exterior.xy
            ax.fill(xs_, ys_, color="#7cc3f2", alpha=0.6, zorder=2)
    for st in g["streams"]:
        geom = st["geom"]
        for ln in iter_lines(geom):
            xs_, ys_ = ln.xy
            ax.plot(xs_, ys_, color="#38c6f4", lw=0.9, ls=(0, (3, 1.5)), zorder=4)
    for st in g["drains"]:
        geom = st["geom"]
        for ln in iter_lines(geom):
            xs_, ys_ = ln.xy
            ax.plot(xs_, ys_, color="#0b67c2", lw=1.8, zorder=5)
    inf = read_ov(S, "infrastructure")
    sym = {"substation": ("s", "#d32f2f", 8), "transformer": ("^", "#e57373", 4.5), "power_line": (None, "#d32f2f", 1.0),
           "minor_line": (None, "#ef9a9a", 0.6), "water_tower": ("D", "#1565c0", 5.5), "wastewater_plant": ("h", "#6d4c41", 7),
           "bus_stop": ("o", "#1e6fd9", 3.2), "communication_tower": ("*", "#7b1fa2", 6)}
    for _, row in inf.iterrows():
        k = row["class"]
        if k not in sym or not row.geom.intersects(box(*b)):
            continue
        m, c, s_ = sym[k]
        if m is None:
            for ln in (getattr(row.geom, "geoms", None) or [row.geom]):
                if ln.geom_type == "LineString":
                    xs_, ys_ = ln.xy
                    ax.plot(xs_, ys_, color=c, lw=s_, ls=(0, (5, 2)), zorder=6)
        else:
            p = row.geom.centroid
            ax.plot(p.x, p.y, m, ms=s_, color=c, mec="white", mew=0.6, zorder=8)
    site_outline(ax, alpha=0.3, color=DKGREEN, lw=1.5, z=9)
    label(ax, S.cx, S.cy, f"Site\n{R['geometry']['area_ha']:.2f} ha", fs=6, bold=True, color=DKGREEN)
    hs = [plt.Line2D([], [], color="#0b67c2", lw=1.8, label="Primary storm drain (rajakaluve)"),
          plt.Line2D([], [], color="#38c6f4", lw=0.9, ls=(0, (3, 1.5)), label="Stream / drain (mapped)"),
          plt.Line2D([], [], color="#f0a646", lw=1.6, label="Arterial / collector road"),
          plt.Line2D([], [], marker="s", color="#d32f2f", lw=0, ms=5, label="Power substation"),
          plt.Line2D([], [], marker="^", color="#e57373", lw=0, ms=4, label="Transformer"),
          plt.Line2D([], [], marker="D", color="#1565c0", lw=0, ms=4, label="Water tank / tower"),
          plt.Line2D([], [], marker="o", color="#1e6fd9", lw=0, ms=3.5, label="Bus stop")]
    ax.legend(handles=hs, loc="lower right", fontsize=4.8, frameon=True, framealpha=0.93, edgecolor="#ddd", ncol=2)
    north_scale(ax, b, corner="tl")
    return save(fig, "services", jpg=True)


def screenshot_crop():
    fn = S.rec.get("screenshot")
    if not fn:
        return None
    im = Image.open(SCREEN / fn).convert("RGB")
    W, H = im.size
    # drop the left legend panel and right control strip; keep the map
    crop = im.crop((int(W * 0.30), int(H * 0.0), int(W * 0.94), int(H * 0.97)))
    p = FIG / f"{S.id}_zoning_screenshot.jpg"
    crop.save(p, quality=88)
    return p


def fig_airport():
    inf = read_ov(S, "infrastructure")
    rw = inf[inf["class"] == "runway"]
    if rw.empty:
        return None
    runways = []
    for _, row in rw.iterrows():
        c = list(row.geom.coords)
        a, b_ = (c[0], c[-1]) if c[0][0] < c[-1][0] else (c[-1], c[0])
        runways.append((name_of(row["names"]), a, b_))
    thr_x = min(r_[1][0] for r_ in runways)
    cx = (S.poly.bounds[0] + thr_x + 900) / 2
    cy = (S.cy + np.mean([r_[1][1] for r_ in runways])) / 2
    W_ = (thr_x + 900) - S.poly.bounds[0] + 1400
    H_ = W_ / 0.95
    b = (cx - W_ / 2, cy - H_ / 2, cx + W_ / 2, cy + H_ / 2)
    fig, ax = map_axes(b, 0.95, "airport", res=6.0, fade=0.35)
    strips = []
    for nm, a, b_ in runways:
        L = math.dist(a, b_)
        ux, uy = (b_[0] - a[0]) / L, (b_[1] - a[1]) / L
        strips.append(LineString([(a[0] - 60 * ux, a[1] - 60 * uy), (b_[0] + 60 * ux, b_[1] + 60 * uy)]))
        # approach funnel to the west threshold
        px_, py_ = -uy, ux
        e0 = (a[0] - 60 * ux, a[1] - 60 * uy)
        d = 6600
        e1 = (e0[0] - d * ux, e0[1] - d * uy)
        w0, w1 = 150, 150 + 0.15 * d
        poly = [(e0[0] + w0 * px_, e0[1] + w0 * py_), (e1[0] + w1 * px_, e1[1] + w1 * py_), (e1[0] - w1 * px_, e1[1] - w1 * py_), (e0[0] - w0 * px_, e0[1] - w0 * py_)]
        ax.add_patch(MplPoly(poly, closed=True, fc="#2f7fd9", ec="#1d5fae", lw=0.6, alpha=0.16, zorder=4))
        ax.plot([a[0], a[0] - 9000 * ux], [a[1], a[1] - 9000 * uy], color="#1d5fae", lw=0.6, ls=(0, (5, 3)), zorder=5)
        ax.plot([a[0], b_[0]], [a[1], b_[1]], color="#222", lw=3.2, solid_capstyle="butt", zorder=6)
        ax.plot([a[0], b_[0]], [a[1], b_[1]], color="white", lw=0.5, ls=(0, (3, 3)), zorder=7)
        lab = "09L / 27R" if a[1] == max(r_[1][1] for r_ in runways) else "09R / 27L"
        tag(ax, a[0] + 900, a[1] + (260 if "L /" in lab else -260), lab, fc="#222", fs=5)
    ih = unary_union([st.buffer(4000) for st in strips])
    cone = unary_union([st.buffer(6000) for st in strips])
    for geom, col, ls in ((ih, "#d9480f", "-"), (cone, "#f08c00", (0, (4, 3)))):
        xs_, ys_ = geom.exterior.xy
        ax.plot(xs_, ys_, color=col, lw=1.1, ls=ls, zorder=8)
    site_outline(ax, alpha=0.75, color="#7a1d00", lw=1.0, z=9)
    ax.patches[-1].set_facecolor((0.95, 0.45, 0.15, 0.85))
    A = R["aerodrome"]
    tag(ax, S.cx, S.poly.bounds[1] - 420, f"Site · indicative top ≈ {960:.0f} m AMSL", fc="#7a1d00", fs=5)
    label(ax, b[0] + 0.5 * W_, b[3] - 0.05 * H_, "Inner horizontal: 45 m above aerodrome (4 km)", fs=5, color="#d9480f")
    label(ax, b[0] + 0.5 * W_, b[3] - 0.10 * H_, "Conical: +5% to 6 km  ·  Approach: 2% then 2.5%", fs=5, color="#a65c00")
    north_scale(ax, b)
    return save(fig, "airport", jpg=True)


from sites import SCREENSHOTS as SCREEN

ALL = [fig_hero, fig_boundary, fig_terrain, fig_transect, fig_sunpath_map, fig_seasonal_polar, fig_solar_faces, fig_wind_map,
       fig_windrose, fig_comfort, fig_temperature, fig_runoff, fig_rainfall, fig_groundwater, fig_landscape, fig_context, fig_skyline,
       fig_isochrones, fig_landuse_change, fig_density, fig_services, screenshot_crop, fig_airport]

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    S = SITES[n]
    R = json.loads((ROOT / "results" / f"{S.id}.json").read_text())
    only = sys.argv[2:]
    for f in ALL:
        if only and f.__name__ not in only:
            continue
        try:
            print(f.__name__, f())
        except Exception as e:
            import traceback

            traceback.print_exc()
            print("FAILED", f.__name__, e)
