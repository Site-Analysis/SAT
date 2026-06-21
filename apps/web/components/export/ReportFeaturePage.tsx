"use client";

// One landscape report page per "visual" feature (sunpath / flood / rainfall /
// temperature / wind), matching the supplied template: a diagram centerpiece on
// the left, a primary chart + indicators + suitability + orientation on the
// right, and a key-stat strip across the bottom.
//
// Reuses the on-screen SVG/chart components so the report mirrors the live view:
//   sunpath  → <SunPanel>     (pure-SVG polar diagram, no Leaflet)
//   rainfall → <RainfallRadar>(pure-SVG radar)
//   others   → the module's primary <ModuleChart>

import type { ModuleId, ModuleResult, Severity, QualitativeTone } from "@/lib/stores/analysis";
import type { ExportSettings } from "@/components/layout/ExportDrawer";
import { ModuleChart } from "@/components/layout/ModuleChart";
import { SunPanel } from "@/components/layout/SunPanel";
import { RainfallRadar } from "@/components/map/RainfallRadar";

// Plain hex only — html2canvas chokes on oklch / CSS vars.
const C = {
  surface: "#FDFCFB",
  bg: "#F2EDE8",
  border: "#CFD6C4",
  text: "#3A3F3B",
  muted: "#7B8F83",
  faint: "#B8C4BB",
  primary: "#306223",
};

const SEVERITY_STYLE: Record<Severity, { bg: string; fg: string; label: string }> = {
  high:     { bg: "#F5E4E4", fg: "#C46A6A", label: "High risk"     },
  moderate: { bg: "#F8EDE0", fg: "#C4865A", label: "Moderate risk" },
  low:      { bg: "#E4F0E8", fg: "#5A8F6A", label: "Low risk"      },
  none:     { bg: "#E4F0E8", fg: "#5A8F6A", label: "Optimal"       },
};

const TONE_STYLE: Record<QualitativeTone, { bg: string; fg: string }> = {
  good:    { bg: "#E4F0E8", fg: "#5A8F6A" },
  warn:    { bg: "#F8EDE0", fg: "#C4865A" },
  bad:     { bg: "#F5E4E4", fg: "#C46A6A" },
  neutral: { bg: "#DAEBE3", fg: "#306223" },
};

interface ReportFeaturePageProps {
  moduleId: ModuleId;
  name: string;
  color: string;
  result: ModuleResult;
  settings: ExportSettings;
  /** Page width in px (matches the PDF paper size). */
  width: number;
}

// The hero (left) visual + the primary (right) chart, chosen per feature.
function pickVisuals(moduleId: ModuleId, result: ModuleResult) {
  const charts = result.charts ?? [];
  if (moduleId === "sunpath") {
    return { hero: <SunPanel result={result} />, primaryChart: charts[0] };
  }
  if (moduleId === "rainfall") {
    return { hero: <RainfallRadar result={result} size={260} />, primaryChart: charts[0] };
  }
  // flood / temperature / wind — no dedicated SVG diagram, anchor on the first
  // chart, surface the next one (if any) in the right column.
  return {
    hero: charts[0] ? <ModuleChart chart={charts[0]} height={240} animate={false} /> : null,
    primaryChart: charts[1] ?? charts[0],
  };
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 9, fontWeight: 700, color: C.muted,
      textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 8,
    }}>
      {children}
    </div>
  );
}

export function ReportFeaturePage({ moduleId, name, color, result, settings, width }: ReportFeaturePageProps) {
  const sev = SEVERITY_STYLE[result.severity ?? "none"];
  const { hero, primaryChart } = pickVisuals(moduleId, result);

  const indicators = result.indicators ?? [];
  const quals = result.qualitative ?? [];
  const orientation = result.detailMetrics?.[0];
  const note = result.recommendations?.[0] ?? result.summary;

  // Bottom strip: prefer qualitative stats, fall back to top indicators.
  const stripItems = quals.length
    ? quals.slice(0, 4).map((q) => ({ label: q.label, value: q.value }))
    : indicators.slice(0, 4).map((i) => ({ label: i.label, value: `${i.value}${i.unit ? ` ${i.unit}` : ""}` }));

  return (
    <div data-export-page style={{
      width, background: C.surface, color: C.text, boxSizing: "border-box",
      padding: "26px 30px", fontFamily: "var(--font-inter), Arial, sans-serif",
      display: "flex", flexDirection: "column", gap: 16,
    }}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ width: 14, height: 14, borderRadius: 4, background: color, flexShrink: 0 }} />
        <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", color: C.text }}>
          {name}
        </span>
        <span style={{ fontSize: 10, fontWeight: 600, color: sev.fg, background: sev.bg, borderRadius: 5, padding: "3px 10px" }}>
          {sev.label}
        </span>
        <span style={{ marginLeft: "auto", fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "1px" }}>
          Qnit
        </span>
        <span style={{ fontSize: 26, fontWeight: 700, color, fontFamily: "var(--font-space-mono), monospace" }}>
          {result.score ?? "—"}<span style={{ fontSize: 12, color: C.faint }}>/100</span>
        </span>
      </div>

      {/* ── Body: hero centerpiece | right column ──────────────── */}
      <div style={{ display: "flex", gap: 20, flex: 1, minHeight: 0 }}>

        {/* Left — summary card + diagram */}
        <div style={{ width: "52%", display: "flex", flexDirection: "column", gap: 12 }}>
          {result.summary && (
            <div style={{
              background: C.bg, borderRadius: 8, padding: "11px 14px",
              borderLeft: `4px solid ${color}`, fontSize: 12, lineHeight: 1.5, color: C.text,
            }}>
              {result.summary}
            </div>
          )}
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
            {hero ?? <span style={{ fontSize: 11, color: C.muted }}>No diagram available.</span>}
          </div>
        </div>

        {/* Right — chart, indicators, suitability, orientation, note */}
        <div style={{ width: "48%", display: "flex", flexDirection: "column", gap: 14 }}>
          {primaryChart && (
            <div data-chart={`${name} — ${primaryChart.title}`}>
              <ModuleChart chart={primaryChart} height={140} animate={false} />
            </div>
          )}

          {indicators.length > 0 && (
            <div>
              <SectionLabel>Indicators · {indicators.length}</SectionLabel>
              {indicators.slice(0, 5).map((ind, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontSize: 11, color: C.text }}>{ind.label}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: C.text, fontFamily: "var(--font-space-mono), monospace" }}>
                      {ind.value}{ind.unit ? ` ${ind.unit}` : ""}
                    </span>
                  </div>
                  <div style={{ height: 5, background: C.bg, borderRadius: 3, overflow: "hidden" }}>
                    <div style={{ width: `${Math.max(0, Math.min(1, ind.barFraction)) * 100}%`, height: "100%", background: color, borderRadius: 3 }} />
                  </div>
                  {settings.citations && ind.citation && (
                    <div style={{ fontSize: 8, color: C.faint, marginTop: 2 }}>{ind.citation}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Suitability + orientation, two-up */}
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1, background: sev.bg, borderRadius: 8, padding: "10px 12px" }}>
              <SectionLabel>Suitability</SectionLabel>
              <div style={{ fontSize: 14, fontWeight: 700, color: sev.fg }}>{sev.label}</div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>Score {result.score ?? "—"}/100</div>
            </div>
            {settings.template === "detailed" && orientation && (
              <div style={{ flex: 1, background: C.bg, borderRadius: 8, padding: "10px 12px" }}>
                <SectionLabel>{orientation.group}</SectionLabel>
                {orientation.rows.slice(0, 3).map((row, ri) => (
                  <div key={ri} style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontSize: 10, color: C.muted }}>{row.label}</span>
                    <span style={{ fontSize: 10, fontWeight: 600, color: C.text, fontFamily: "var(--font-space-mono), monospace" }}>
                      {row.value}{row.unit ? ` ${row.unit}` : ""}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {note && (
            <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.5, borderTop: `1px solid ${C.bg}`, paddingTop: 8 }}>
              <span style={{ fontWeight: 700, color: C.text }}>Note · </span>{note}
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom key-stat strip ──────────────────────────────── */}
      {stripItems.length > 0 && (
        <div style={{ display: "flex", gap: 10 }}>
          {stripItems.map((s, i) => {
            const tone = quals.length ? TONE_STYLE[quals[i]?.tone ?? "neutral"] : TONE_STYLE.neutral;
            return (
              <div key={i} style={{ flex: 1, background: tone.bg, borderRadius: 7, padding: "8px 12px" }}>
                <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.3px" }}>{s.label}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: tone.fg, marginTop: 2 }}>{s.value}</div>
              </div>
            );
          })}
        </div>
      )}

      {settings.citations && result.data_source && (
        <div style={{ fontSize: 8.5, color: C.faint }}>Data source: {result.data_source}</div>
      )}
    </div>
  );
}
