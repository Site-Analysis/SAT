// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useMemo, useRef } from "react";
import { copy } from "@/lib/contour/copy";
import { C } from "./theme";
import { useContourStore } from "@/lib/stores/contour";
import type { TransectResponse } from "@/lib/contour/types";

const W = 320;
const H = 160;
const PAD = { l: 36, r: 16, t: 18, b: 28 };

function xOf(d: number, total: number) {
  const inner = W - PAD.l - PAD.r;
  return PAD.l + (total > 0 ? (d / total) * inner : 0);
}
function yOf(e: number, min: number, max: number) {
  const inner = H - PAD.t - PAD.b;
  const span = max - min || 1;
  return PAD.t + inner - ((e - min) / span) * inner;
}

export function TransectProfileChart({ result }: { result: TransectResponse }) {
  const setActive = useContourStore((s) => s.setActiveProfileIndex);
  const crosshair = useRef<SVGGElement>(null);
  const points = result.points;
  const total = result.total_length_m;
  const min = result.min_elevation_m;
  const max = result.max_elevation_m;
  const pad = (max - min) * 0.05 || 1;
  const yMin = min - pad;
  const yMax = max + pad;

  const { line, area } = useMemo(() => {
    if (!points.length) return { line: "", area: "" };
    const coords = points.map((p) => `${xOf(p.distance_m, total).toFixed(1)},${yOf(p.elevation_m, yMin, yMax).toFixed(1)}`);
    const lineD = `M${coords.join("L")}`;
    const first = coords[0];
    const last = coords[coords.length - 1];
    const base = yOf(yMin, yMin, yMax).toFixed(1);
    const areaD = `${lineD}L${last.split(",")[0]},${base}L${first.split(",")[0]},${base}Z`;
    return { line: lineD, area: areaD };
  }, [points, total, yMin, yMax]);

  const interpolated = points.some((p) => p.lat == null || p.lng == null);

  function indexFromX(clientX: number, svg: SVGSVGElement) {
    const rect = svg.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * W;
    const inner = W - PAD.l - PAD.r;
    const t = Math.max(0, Math.min(1, (x - PAD.l) / inner));
    const dist = t * total;
    let best = 0;
    let bestD = Infinity;
    for (let i = 0; i < points.length; i++) {
      const d = Math.abs(points[i].distance_m - dist);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    }
    return best;
  }

  function moveCrosshair(i: number) {
    const p = points[i];
    if (!p || !crosshair.current) return;
    const x = xOf(p.distance_m, total);
    const y = yOf(p.elevation_m, yMin, yMax);
    crosshair.current.setAttribute("transform", `translate(${x} ${y})`);
    crosshair.current.style.display = "";
  }

  function onPointer(e: React.PointerEvent<SVGSVGElement>) {
    if (!points.length) return;
    const i = indexFromX(e.clientX, e.currentTarget);
    setActive(i);
    moveCrosshair(i);
  }

  function onKey(e: React.KeyboardEvent<SVGSVGElement>) {
    const cur = useContourStore.getState().activeProfileIndex ?? 0;
    let next = cur;
    if (e.key === "ArrowRight") next = Math.min(points.length - 1, cur + (e.shiftKey ? 10 : 1));
    else if (e.key === "ArrowLeft") next = Math.max(0, cur - (e.shiftKey ? 10 : 1));
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = points.length - 1;
    else return;
    e.preventDefault();
    setActive(next);
    moveCrosshair(next);
  }

  const startX = xOf(0, total);
  const endX = xOf(total, total);
  const startY = points[0] ? yOf(points[0].elevation_m, yMin, yMax) : H / 2;
  const endY = points.length ? yOf(points[points.length - 1].elevation_m, yMin, yMax) : H / 2;

  return (
    <div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        role="img"
        tabIndex={0}
        aria-label={copy.transect.graphAria}
        onPointerMove={onPointer}
        onPointerDown={onPointer}
        onPointerLeave={() => {
          setActive(null);
          if (crosshair.current) crosshair.current.style.display = "none";
        }}
        onKeyDown={onKey}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={{ display: "block", background: C.surface, borderRadius: 8, border: `1px solid ${C.border}` }}
      >
        <line x1={PAD.l} x2={W - PAD.r} y1={yOf(min, yMin, yMax)} y2={yOf(min, yMin, yMax)} stroke={C.border} strokeDasharray="3 3" />
        <line x1={PAD.l} x2={W - PAD.r} y1={yOf(max, yMin, yMax)} y2={yOf(max, yMin, yMax)} stroke={C.border} strokeDasharray="3 3" />
        <text x={PAD.l + 4} y={yOf(max, yMin, yMax) - 3} fontSize={9} fill={C.inkSoft}>{`${max.toFixed(0)} m`}</text>
        <text x={PAD.l + 4} y={yOf(min, yMin, yMax) + 11} fontSize={9} fill={C.inkSoft}>{`${min.toFixed(0)} m`}</text>
        <path d={area} fill={C.profileFill} />
        <path d={line} fill="none" stroke={C.accent} strokeWidth={2} strokeLinejoin="round" />
        <circle cx={startX} cy={startY} r={5} fill={C.start} stroke="#fff" strokeWidth={1.5} />
        <text x={startX} y={H - 8} textAnchor="middle" fontSize={9} fill={C.start} fontWeight={700}>
          {copy.transect.startLabel}
        </text>
        <rect
          x={endX - 4}
          y={endY - 4}
          width={8}
          height={8}
          fill={C.end}
          stroke="#fff"
          strokeWidth={1.5}
          transform={`rotate(45 ${endX} ${endY})`}
        />
        <text x={endX} y={H - 8} textAnchor="middle" fontSize={9} fill={C.end} fontWeight={700}>
          {copy.transect.endLabel}
        </text>
        <text x={PAD.l} y={H - 8} fontSize={9} fill={C.inkSoft}>0 m</text>
        <g ref={crosshair} style={{ display: "none" }} pointerEvents="none">
          <line x1={0} x2={0} y1={-H} y2={H} stroke={C.ink} strokeWidth={1} opacity={0.45} />
          <circle r={4} fill={C.accent} stroke="#fff" strokeWidth={1.5} />
        </g>
        <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={H - PAD.t - PAD.b} fill="transparent" />
      </svg>
      {interpolated ? (
        <div style={{ fontSize: 10, color: C.inkSoft, marginTop: 4 }}>{copy.transect.interpolated}</div>
      ) : null}
    </div>
  );
}
