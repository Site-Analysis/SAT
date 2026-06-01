# FVD-15 — BIM/CAD Exports (PDF Report, IFC, GLTF/GLB)

**Jira Ticket:** — (extends FVD-05; no new ticket)
**Status:** Done — V3 in org repo (`Site-Analysis/SiteAnalysisToolV3`)
**Resolved:** 2026-05-26 (SiteAnalysisToolV3)
**Type:** Enhancement (extends FVD-05 PDF Report Generation)
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `frontend/src/lib/`
**Latest Commit:** `4bf53de` (2026-05-15, `Site-Analysis/SiteAnalysisToolV3` main)

---

## Feature Overview

**User Story:** As an architect, I want to export my site design as a PDF report, an IFC BIM file for Revit import, and a GLTF 3D model for rendering, so that I can share deliverables with clients and consultants.

**Business Value:** Three distinct export formats serving three audiences. PDF covers regulatory/compliance documentation with NBC 2016 summary. IFC provides interoperability with BIM authoring tools (Revit, ArchiCAD). GLTF/GLB enables web-based 3D sharing and renderer import. All three are generated client-side with no server round-trip.

---

## Acceptance Criteria (derived)

| # | Format | Acceptance Criterion |
|---|---|---|
| 1 | PDF | Title page with project name, site, climate zone generated |
| 2 | PDF | Building metrics table (GFA, floors, EUI, carbon) included |
| 3 | PDF | NBC 2016 compliance summary with COMPLIANT/WARNING/VIOLATION status |
| 4 | PDF | Viewport thumbnail captured and embedded |
| 5 | IFC | Buildings exported as IFC2x3 with storey hierarchy |
| 6 | IFC | Each floor exported as an IfcBuildingStorey with IfcSlab |
| 7 | IFC | Building envelope walls exported as IfcWall elements |
| 8 | GLTF | Buildings exported as GLB (binary GLTF) with geometry |
| 9 | GLTF | Materials (wall color from building type) applied to meshes |
| 10 | GLTF | Scene contains ambient and directional lighting |

---

## Code Traceability Matrix

| # | File | Function / Symbol |
|---|---|---|
| 1–4 | `lib/export-pdf.ts` | `generateProjectReport(options)` → `Blob` |
| 1 | `lib/export-pdf.ts` | `addTitlePage(doc, options, y, margin, contentWidth)` |
| 3 | `lib/export-pdf.ts` | `getStatusColor(status: ComplianceStatus)` — green/yellow/red |
| 3 | `lib/export-pdf.ts` | `statusText(status)` → `'COMPLIANT'|'WARNING'|'VIOLATION'` |
| 4 | `lib/variant-manager.ts` | `captureViewportThumbnail()` — canvas screenshot |
| — | `lib/export-pdf.ts` | `PdfReportOptions: {projectName, siteName, siteCenter, climateZone, buildings, metrics, variantCount}` |
| 5 | `lib/export-ifc.ts` | `exportBuildingsToIFC(buildings: UserBuilding[])` → `Blob` |
| 5 | `lib/export-ifc.ts` | `createOwnerHistory(ifcApi, modelID)` |
| 5 | `lib/export-ifc.ts` | `createIfcSite()`, `createIfcBuilding()` |
| 6 | `lib/export-ifc.ts` | `createIfcBuildingStorey(ifcApi, modelID, …, level, height, use)` |
| 6 | `lib/export-ifc.ts` | `createIfcSlab(ifcApi, modelID, …, building, elevation)` |
| 7 | `lib/export-ifc.ts` | `createIfcWalls(ifcApi, modelID, …, building)` |
| 8–10 | `lib/export-gltf.ts` | `exportBuildingsToGLTF(buildings: UserBuilding[])` → `Blob` |
| 8 | `lib/export-gltf.ts` | `createBuildingMesh(building)` → `THREE.Group` |
| 9 | `lib/export-gltf.ts` | `MeshStandardMaterial` with wall color from building material type |
| 10 | `lib/export-gltf.ts` | `THREE.AmbientLight(0xffffff, 0.6)` + `THREE.DirectionalLight(0xffffff, 0.8)` |
| 8 | `lib/export-gltf.ts` | `GLTFExporter.parse(scene, …, { binary: true })` |

---

## Implementation Breakdown

### PDF Report Pipeline

```
generateProjectReport(options: PdfReportOptions) → Blob
    └── jsPDF('p', 'mm', 'a4')
    └── Page 1: addTitlePage(doc, options)
        ├── Project name, site coordinates, climate zone
        ├── Generation timestamp, variant count
        └── Viewport thumbnail (captureViewportThumbnail → base64)
    └── Page 2: Building metrics table
        ├── Per-building: name, floors, GFA, EUI, carbon
        └── Portfolio totals
    └── Page 3: NBC 2016 compliance
        ├── FAR: achieved vs max → COMPLIANT/WARNING/VIOLATION
        ├── Ground coverage: achieved vs max
        ├── Setbacks: actual vs required
        └── Parking: provided vs minimum ECS
```

### IFC Export Pipeline

```
exportBuildingsToIFC(buildings) → Blob (IFC2x3)
    └── web-ifc (dynamic import, lazy)
    └── ifcApi.Init() (WASM)
    └── CreateModel({ schema: IFC2X3 })
    └── createOwnerHistory → IfcOwnerHistory
    └── createIfcSite → IfcSite
    └── Per building:
        ├── createIfcBuilding → IfcBuilding
        └── Per floor (building.floors[]):
            ├── createIfcBuildingStorey(level, height, use)
            └── createIfcSlab(storey, building, elevation)
        └── createIfcWalls(building)  # envelope walls
    └── ifcApi.SaveModel → Uint8Array → Blob
```

### GLTF Export Pipeline

```
exportBuildingsToGLTF(buildings) → Blob (.glb)
    └── THREE.Scene
    └── AmbientLight + DirectionalLight
    └── Per building: createBuildingMesh(building) → THREE.Group
        ├── BoxGeometry (width × height × depth)
        ├── MeshStandardMaterial (wall color)
        └── Group positioned at local XZ coordinates
    └── GLTFExporter.parse(scene, { binary: true })
    └── ArrayBuffer → Blob('model/gltf-binary')
```

### Technology Stack

| Format | Library | Output |
|---|---|---|
| PDF | `jspdf` | A4 PDF Blob |
| IFC | `web-ifc` (WASM, dynamic import) | IFC2x3 Blob |
| GLTF | `three` + `GLTFExporter` | Binary GLB Blob |

---

## Automated Validation Plan

> All exports are pure client-side. Test in browser or with Node.js test harness.

### AC-1 to AC-4: PDF generation

```typescript
import { generateProjectReport } from '@/lib/export-pdf';
const blob = await generateProjectReport({
  projectName: 'Test Site',
  siteName: 'Bengaluru Central',
  siteCenter: { lat: 12.9716, lng: 77.5946 },
  climateZone: 'composite',
  buildings: [/* UserBuilding */],
  metrics: { /* MetricsSummary */ },
  variantCount: 3,
});
console.assert(blob.size > 0, 'PDF blob is empty');
console.assert(blob.type === 'application/pdf' || blob.type.includes('pdf'), `Unexpected MIME: ${blob.type}`);
console.log('PDF size:', blob.size, 'bytes');
// Save to test file for visual inspection:
// const url = URL.createObjectURL(blob); window.open(url);
```

### AC-5 to AC-7: IFC export

```typescript
import { exportBuildingsToIFC } from '@/lib/export-ifc';
const buildings = [/* UserBuilding with 3 floors */];
const blob = await exportBuildingsToIFC(buildings);
console.assert(blob.size > 0, 'IFC blob empty');
// Verify IFC text header:
const text = await blob.text();
console.assert(text.startsWith('ISO-10303-21') || text.includes('IFC'), 'Not valid IFC');
console.log('IFC size:', blob.size, 'bytes');
```

### AC-8 to AC-10: GLTF/GLB export

```typescript
import { exportBuildingsToGLTF } from '@/lib/export-gltf';
const blob = await exportBuildingsToGLTF(buildings);
console.assert(blob.size > 0, 'GLB blob empty');
// GLB magic bytes: 0x676C5446 = 'glTF'
const buffer = await blob.arrayBuffer();
const magic = new Uint8Array(buffer).slice(0, 4);
const magicStr = String.fromCharCode(...magic);
console.assert(magicStr === 'glTF', `Invalid GLB magic: ${magicStr}`);
console.log('GLB size:', blob.size, 'bytes');
```

---

## Outstanding Actions

1. **IFC coordinate system** — `createBuildingMesh()` uses `x=0, z=0` placeholders: "In a full implementation, convert lat/lng to meters". Real XZ offsets from site origin needed before IFC is useful in BIM software.
2. **IFC WASM size** — `web-ifc` WASM binary is large (~10 MB). Dynamic import is used (`lazy`) but loading time for IFC export may be slow on first use. Consider CDN pre-load or worker offload.
3. **PDF NBC section** — `generateProjectReport` signature accepts `metrics: MetricsSummary` and `buildings[]`. NBC compliance page requires `NBCSummary` data not obviously derived from buildings alone. Confirm data flow.
4. **Viewport thumbnail** — `captureViewportThumbnail()` in `variant-manager.ts` captures the Three.js canvas. Fails if canvas is not mounted when export is triggered from a non-simulation context.
5. **No export UI** — No export button/dialog found in V3 frontend that calls these functions. UI component (download dialog with format selection) needed.
6. **Jira ticket** — Extends FVD-05 (PDF). IFC and GLTF are new; raise separate story.
