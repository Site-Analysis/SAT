// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { forwardRef } from "react";
import type { ModuleId, ModuleResult, Severity, SiteScore } from "@/lib/stores/analysis";
import type { Project } from "@/lib/stores/project";
import type { ExportSettings } from "@/components/layout/ExportDrawer";
import { ReportFeaturePage } from "@/components/export/ReportFeaturePage";

// ── Palette (plain hex — html2canvas-safe, no oklch/var) ────────────────────
const C = {
  primary: "#306223",
  surface: "#FDFCFB",
  bg: "#F2EDE8",
  border: "#CFD6C4",
  text: "#3A3F3B",
  muted: "#7B8F83",
  faint: "#B8C4BB",
  mint: "#DAEBE3",
};

// The 5 "visual" features get a full template page each (diagram-centric).
export const REPORT_MODULE_META: { id: ModuleId; name: string; color: string }[] = [
  { id: "sunpath",     name: "Sun Path",    color: "#F59E0B" },
  { id: "flood",       name: "Flood",       color: "#2563EB" },
  { id: "temperature", name: "Temperature", color: "#EF4444" },
  { id: "wind",        name: "Wind",        color: "#06B6D4" },
  { id: "rainfall",    name: "Rainfall",    color: "#1D4ED8" },
];

// Remaining data-only modules collapse into one compact summary page.
const DATA_MODULE_META: { id: ModuleId; name: string }[] = [
  { id: "zoning",           name: "Zoning Compliance" },
  { id: "zone",             name: "Zone & Land Use"   },
  { id: "planning",         name: "Site Capacity"     },
  { id: "infrastructure",   name: "Connectivity"      },
  { id: "soil",             name: "Soil Profile"      },
  { id: "waterConstraints", name: "Water Constraints" },
  { id: "growth",           name: "Growth Context"    },
  { id: "land",             name: "Title & Documents" },
  { id: "amenities",        name: "Amenities"         },
];

const SEVERITY_STYLE: Record<Severity, { bg: string; fg: string; label: string }> = {
  high:     { bg: "#F5E4E4", fg: "#C46A6A", label: "High risk"     },
  moderate: { bg: "#F8EDE0", fg: "#C4865A", label: "Moderate risk" },
  low:      { bg: "#E4F0E8", fg: "#5A8F6A", label: "Low risk"      },
  none:     { bg: "#E4F0E8", fg: "#5A8F6A", label: "Optimal"       },
};

function paperWidth(paperSize: string): number {
  // px at ~96dpi
  if (paperSize === "A4 Landscape") return 1123;
  if (paperSize === "A3") return 1000;
  return 794; // A4 portrait
}

interface ReportDocumentProps {
  project: Project | null;
  modules: Partial<Record<ModuleId, ModuleResult>>;
  siteScore: SiteScore | null;
  includedIds: ModuleId[];
  settings: ExportSettings;
}

const pageStyle: React.CSSProperties = {
  background: C.surface, padding: "32px 36px", boxSizing: "border-box",
  fontFamily: "var(--font-inter), Arial, sans-serif",
};

function ready(r: ModuleResult | undefined): r is ModuleResult {
  return !!r && !r.loading && !r.error;
}

export const ReportDocument = forwardRef<HTMLDivElement, ReportDocumentProps>(
  function ReportDocument({ project, modules, siteScore, includedIds, settings }, ref) {
    const width = paperWidth(settings.paperSize);

    const visual = REPORT_MODULE_META.filter((m) => includedIds.includes(m.id) && ready(modules[m.id]));
    const dataOnly = DATA_MODULE_META.filter((m) => includedIds.includes(m.id) && ready(modules[m.id]));

    const generated = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
    const coords = project?.coordinates || "—";

    return (
      <div ref={ref} style={{ width, background: C.surface, color: C.text }}>

        {/* ── Cover — brand header + overall score strip ─────────────── */}
        <div data-export-page style={{ ...pageStyle, paddingTop: 0 }}>
          <div style={{ background: C.primary, padding: "26px 32px", margin: "0 -36px 24px", color: "#fff" }}>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 6 }}>
              Qnit
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1.2 }}>
              {project?.name || "Untitled Project"}
            </div>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.7)", marginTop: 3 }}>Site Analysis Report</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 32px", marginTop: 16 }}>
              {[
                ["Location", project?.location || "—"],
                ["Coordinates", coords],
                ["Generated", generated],
                ["Report Type", settings.template === "detailed" ? "Detailed" : "Overview"],
              ].map(([label, value]) => (
                <div key={label}>
                  <div style={{ fontSize: 9, color: "rgba(255,255,255,0.5)", textTransform: "uppercase", letterSpacing: "0.4px" }}>{label}</div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.9)", fontWeight: 500, marginTop: 2 }}>{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Overall score strip across the visual features */}
          <div style={{
            background: C.mint, borderRadius: 6, padding: "7px 12px", marginBottom: 14,
            borderLeft: `4px solid ${C.primary}`, fontSize: 12, fontWeight: 700,
            color: C.text, textTransform: "uppercase", letterSpacing: "0.6px",
          }}>
            Overall Site Score
          </div>
          <div style={{ display: "flex", gap: 6, marginBottom: 24 }}>
            {visual.map((m) => (
              <div key={m.id} style={{ flex: 1, background: m.color, borderRadius: 6, padding: "12px 6px", textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#fff", fontFamily: "var(--font-space-mono), monospace" }}>
                  {modules[m.id]?.score ?? "—"}
                </div>
                <div style={{ fontSize: 8, color: "rgba(255,255,255,0.85)", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.4px" }}>{m.name}</div>
              </div>
            ))}
            <div style={{ flex: 1, background: C.primary, borderRadius: 6, padding: "12px 6px", textAlign: "center" }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#fff", fontFamily: "var(--font-space-mono), monospace" }}>
                {siteScore?.overall_score ?? "—"}
              </div>
              <div style={{ fontSize: 8, color: "rgba(255,255,255,0.85)", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.4px" }}>Overall</div>
            </div>
          </div>
          {siteScore?.verdict_text && (
            <div style={{ fontSize: 13, color: C.text, lineHeight: 1.5 }}>
              {siteScore.verdict_text}{siteScore.desc_text ? ` — ${siteScore.desc_text}` : ""}
            </div>
          )}
        </div>

        {/* ── Parcel & Title — only for projects created from a cadastral parcel ── */}
        {project?.parcel && (
          <div data-export-page style={pageStyle}>
            <div style={{
              background: C.mint, borderRadius: 6, padding: "7px 12px", marginBottom: 16,
              borderLeft: `4px solid ${C.primary}`, fontSize: 12, fontWeight: 700,
              color: C.text, textTransform: "uppercase", letterSpacing: "0.6px",
            }}>
              Parcel &amp; Title
            </div>
            {([
              ["Survey number", project.parcel.survey_no],
              ["Village", project.parcel.village],
              ["Hobli", project.parcel.hobli],
              ["Taluk", project.parcel.taluk],
              ["District", project.parcel.district],
              ["Parcel area", project.area_sqm ? `${Math.round(project.area_sqm).toLocaleString("en-IN")} m² (${(project.area_sqm / 4046.856).toFixed(2)} acres)` : "—"],
              ["Centroid", project.coordinates || "—"],
            ] as [string, string][]).map(([label, value]) => (
              <div key={label} style={{ display: "flex", padding: "7px 0", borderBottom: `1px solid ${C.bg}`, fontSize: 12 }}>
                <span style={{ width: 140, color: C.muted, flexShrink: 0 }}>{label}</span>
                <span style={{ fontWeight: 600, color: C.text }}>{value || "—"}</span>
              </div>
            ))}

            <div style={{ fontSize: 12, fontWeight: 700, color: C.text, margin: "18px 0 6px" }}>Court cases (RCCMS)</div>
            {!project.parcel.rtc || project.parcel.rtc.owners.length === 0
              ? <div style={{ fontSize: 11, color: C.muted }}>No active cases found.</div>
              : project.parcel.rtc.owners.map((o, i) => (
                  <div key={i} style={{ fontSize: 11, padding: "4px 0", borderBottom: `1px solid ${C.bg}` }}>
                    <span style={{ fontWeight: 600 }}>{o.owner_name || "—"}</span>
                    <span style={{ color: C.muted }}> · Survey {o.survey_no}{o.case_status ? ` · ${o.case_status}` : ""}{o.ack_no ? ` · Ack ${o.ack_no}` : ""}</span>
                  </div>
                ))}

            <div style={{ fontSize: 12, fontWeight: 700, color: C.text, margin: "18px 0 6px" }}>Mutations</div>
            {!project.parcel.rtc || project.parcel.rtc.mutations.length === 0
              ? <div style={{ fontSize: 11, color: C.muted }}>No mutations found.</div>
              : project.parcel.rtc.mutations.map((m, i) => (
                  <div key={i} style={{ fontSize: 11, padding: "4px 0", borderBottom: `1px solid ${C.bg}` }}>
                    <span style={{ fontWeight: 600 }}>{m.transaction_type || "—"}</span>
                    <span style={{ color: C.muted }}>{m.mr_number ? ` · MR ${m.mr_number}` : ""}{m.status ? ` · ${m.status}` : ""}{m.applicant ? ` · ${m.applicant}` : ""}</span>
                  </div>
                ))}

            <div style={{ fontSize: 9, color: C.muted, marginTop: 22, lineHeight: 1.5 }}>
              Parcel geometry is from the Karnataka e-Chawadi (Bhoomi) cadastral dataset; area is computed from that
              polygon, not from the record. Court-case and mutation data (RCCMS) is indicative and has not been
              independently verified — confirm against the official record before relying on it for title decisions.
            </div>
          </div>
        )}

        {/* ── One template page per visual feature ───────────────────── */}
        {visual.map((m) => (
          <ReportFeaturePage
            key={m.id}
            moduleId={m.id}
            name={m.name}
            color={m.color}
            result={modules[m.id]!}
            settings={settings}
            width={width}
          />
        ))}

        {/* ── Compact summary for data-only modules ──────────────────── */}
        {dataOnly.length > 0 && (
          <div data-export-page style={pageStyle}>
            <div style={{
              background: C.mint, borderRadius: 6, padding: "7px 12px", marginBottom: 16,
              borderLeft: `4px solid ${C.primary}`, fontSize: 12, fontWeight: 700,
              color: C.text, textTransform: "uppercase", letterSpacing: "0.6px",
            }}>
              Additional Modules
            </div>
            {dataOnly.map((m) => {
              const r = modules[m.id]!;
              const sev = SEVERITY_STYLE[r.severity ?? "none"];
              return (
                <div key={m.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 0", borderBottom: `1px solid ${C.bg}` }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.text, width: 140, flexShrink: 0 }}>{m.name}</span>
                  <span style={{ fontSize: 11, color: C.muted, flex: 1, lineHeight: 1.4 }}>{r.summary || "Analysis complete"}</span>
                  <span style={{ fontSize: 9, fontWeight: 600, color: sev.fg, background: sev.bg, borderRadius: 4, padding: "2px 7px", flexShrink: 0 }}>{sev.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: C.text, width: 28, textAlign: "right", fontFamily: "var(--font-space-mono), monospace", flexShrink: 0 }}>
                    {r.score ?? "—"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }
);
