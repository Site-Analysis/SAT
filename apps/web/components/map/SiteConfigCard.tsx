// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useState } from "react";
import { Pencil, Check } from "lucide-react";
import { useDrawStore } from "@/lib/stores/draw";

const GLASS: React.CSSProperties = {
  background: "rgba(253,252,251,0.55)",
  backdropFilter: "blur(16px) saturate(160%)",
  WebkitBackdropFilter: "blur(16px) saturate(160%)",
  border: "1px solid rgba(255,255,255,0.6)",
  borderRadius: 14,
  boxShadow: "0 8px 30px rgba(58,63,59,0.18), inset 0 1px 0 rgba(255,255,255,0.45)",
  overflow: "hidden",
};

const label: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 600,
  color: "#7B8F83",
  textTransform: "uppercase" as const,
  letterSpacing: "0.05em",
};

function fmtDist(m: number) {
  return m >= 1000 ? `${(m / 1000).toFixed(2)} km` : `${Math.round(m)} m`;
}
function fmtArea(m2: number) {
  return m2 >= 10000 ? `${(m2 / 10000).toFixed(2)} ha` : `${Math.round(m2)} m²`;
}

interface Props {
  siteName: string;
  onSiteNameChange: (n: string) => void;
  lat: number;
  lng: number;
}

export function SiteConfigCard({ siteName, onSiteNameChange, lat, lng }: Props) {
  const { siteMeasurements, showDimensions, setShowDimensions } = useDrawStore();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft]     = useState(siteName);

  const commitEdit = () => {
    onSiteNameChange(draft.trim() || siteName);
    setEditing(false);
  };

  const hasMeasure = !!siteMeasurements;

  return (
    <div style={GLASS}>
      {/* ── Site name ─────────────────────────────── */}
      <div style={{
        padding: "10px 14px",
        borderBottom: "1px solid rgba(207,214,196,0.5)",
        display: "flex", alignItems: "center", gap: 8,
      }}>
        {editing ? (
          <>
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") commitEdit(); if (e.key === "Escape") setEditing(false); }}
              style={{
                flex: 1, height: 26, border: "1.5px solid #306223", borderRadius: 6,
                padding: "0 7px", fontSize: 13, fontWeight: 600, fontFamily: "inherit",
                color: "#3A3F3B", background: "#FDFCFB", outline: "none",
              }}
            />
            <button
              onClick={commitEdit}
              style={{ background: "none", border: "none", cursor: "pointer", color: "#306223", padding: 2, display: "flex" }}
            >
              <Check size={14} />
            </button>
          </>
        ) : (
          <>
            <span style={{ flex: 1, fontSize: 13, fontWeight: 700, color: "#3A3F3B", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {siteName || "Unnamed site"}
            </span>
            <button
              onClick={() => { setDraft(siteName); setEditing(true); }}
              title="Edit site name"
              style={{ background: "none", border: "none", cursor: "pointer", color: "#7B8F83", padding: 2, display: "flex" }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#306223"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#7B8F83"; }}
            >
              <Pencil size={13} />
            </button>
          </>
        )}
      </div>

      {/* ── Lat / Long ────────────────────────────── */}
      <div style={{ padding: "8px 14px", borderBottom: "1px solid rgba(207,214,196,0.35)", display: "flex", gap: 12 }}>
        <div>
          <div style={label}>Lat</div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#3A3F3B", marginTop: 2 }}>{lat.toFixed(5)}</div>
        </div>
        <div>
          <div style={label}>Long</div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#3A3F3B", marginTop: 2 }}>{lng.toFixed(5)}</div>
        </div>
      </div>

      {/* ── Measurements ──────────────────────────── */}
      <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <span style={label}>Perimeter</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: hasMeasure ? "#3A3F3B" : "#B8C4BB" }}>
            {hasMeasure ? fmtDist(siteMeasurements.perimeter) : "—"}
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <span style={label}>Area</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: hasMeasure ? "#3A3F3B" : "#B8C4BB" }}>
            {hasMeasure ? fmtArea(siteMeasurements.area) : "—"}
          </span>
        </div>

        {hasMeasure && siteMeasurements.angles.length > 0 && (
          <div>
            <div style={{ ...label, marginBottom: 4 }}>Vertex angles</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "3px 6px" }}>
              {siteMeasurements.angles.map((a, i) => (
                <span key={i} style={{
                  fontSize: 10, fontWeight: 600, color: "#306223",
                  background: "rgba(48,98,35,0.10)", border: "1px solid rgba(48,98,35,0.22)",
                  borderRadius: 3, padding: "1px 5px",
                }}>
                  {a}°
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Dimensions toggle ─────────────────────── */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginTop: 4, paddingTop: 8, borderTop: "1px solid rgba(207,214,196,0.4)",
        }}>
          <span style={label}>Dimensions</span>
          <button
            role="switch"
            aria-checked={showDimensions}
            onClick={() => setShowDimensions(!showDimensions)}
            style={{
              width: 36, height: 20, borderRadius: 10, border: "none", cursor: "pointer",
              background: showDimensions ? "#306223" : "#CFD6C4",
              position: "relative", transition: "background 0.18s", flexShrink: 0,
            }}
          >
            <span style={{
              position: "absolute", top: 2,
              left: showDimensions ? 18 : 2,
              width: 16, height: 16, borderRadius: "50%",
              background: "#FDFCFB",
              transition: "left 0.18s",
              boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
            }} />
          </button>
        </div>
      </div>
    </div>
  );
}
