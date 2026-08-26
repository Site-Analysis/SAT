// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Polyline, useMap } from "react-leaflet";
import type { LeafletMouseEvent } from "leaflet";
import type { CSSProperties } from "react";
import { copy } from "@/lib/contour/copy";
import { C, glassPill } from "@/components/contour/theme";
import { useContourStore } from "@/lib/stores/contour";
import { useDrawStore } from "@/lib/stores/draw";

export function TransectDrawTool() {
  const map = useMap();
  const mode = useDrawStore((s) => s.mode);
  const status = useContourStore((s) => s.transectStatus);
  const draft = useContourStore((s) => s.transectDraft);
  const add = useContourStore((s) => s.addTransectPoint);
  const undo = useContourStore((s) => s.undoTransectPoint);
  const finish = useContourStore((s) => s.finishTransectDrawing);
  const clear = useContourStore((s) => s.clearTransect);
  const [cursor, setCursor] = useState<[number, number] | null>(null);
  const host = map.getContainer().parentElement;
  const active = mode === "transect" && status === "drawing";

  useEffect(() => {
    return () => {
      if (useDrawStore.getState().mode === "transect") {
        useDrawStore.getState().setMode(null);
      }
    };
  }, []);

  useEffect(() => {
    if (!active) {
      setCursor(null);
      return;
    }
    const onClick = (e: LeafletMouseEvent) => {
      add([e.latlng.lat, e.latlng.lng]);
    };
    const onMove = (e: LeafletMouseEvent) => {
      setCursor([e.latlng.lat, e.latlng.lng]);
    };
    const onDbl = () => finish();
    map.on("click", onClick);
    map.on("mousemove", onMove);
    map.on("dblclick", onDbl);
    map.doubleClickZoom.disable();
    return () => {
      map.off("click", onClick);
      map.off("mousemove", onMove);
      map.off("dblclick", onDbl);
      map.doubleClickZoom.enable();
    };
  }, [active, add, finish, map]);

  useEffect(() => {
    if (!active) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        finish();
      } else if (e.key === "Backspace") {
        e.preventDefault();
        undo();
      } else if (e.key === "Escape") {
        e.preventDefault();
        clear();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active, finish, undo, clear]);

  const rubber =
    active && cursor && draft.length >= 1 ? [draft[draft.length - 1], cursor] as [number, number][] : null;

  const toolbar = host && (active || status === "ready" || status === "running") ? (
    <div
      style={{
        ...glassPill,
        position: "absolute",
        top: 72,
        left: 14,
        zIndex: 500,
        padding: "8px 10px",
        display: "flex",
        alignItems: "center",
        gap: 8,
        pointerEvents: "auto",
      }}
    >
      <span style={{ fontSize: 11, color: C.ink, fontWeight: 600 }}>{copy.transect.pointCount(draft.length)}</span>
      <button
        type="button"
        aria-label={copy.transect.stop}
        disabled={draft.length < 2}
        onClick={() => finish()}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={toolBtn}
      >
        {copy.transect.stop}
      </button>
      <button
        type="button"
        aria-label={copy.transect.clear}
        onClick={() => clear()}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={toolBtn}
      >
        {copy.transect.clear}
      </button>
      <button
        type="button"
        aria-label={copy.transect.cancel}
        onClick={() => clear()}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={toolBtn}
      >
        {copy.transect.cancel}
      </button>
    </div>
  ) : null;

  return (
    <>
      {rubber ? (
        <Polyline positions={rubber} pathOptions={{ color: C.ink, weight: 2, opacity: 0.45, dashArray: "4 6" }} />
      ) : null}
      {toolbar && host ? createPortal(toolbar, host) : null}
    </>
  );
}

const toolBtn: CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: C.ink,
  background: C.surface,
  border: `1px solid ${C.border}`,
  borderRadius: 999,
  padding: "4px 8px",
  cursor: "pointer",
};
