# Parcel report — cadastral parcel → project → PDF

**Goal:** generate a PDF site-analysis report for one survey number, to share with a lead architect.

## Flow
1. User opens the Cadastral panel on the project page (flag `NEXT_PUBLIC_ENABLE_CADASTRAL_EXPLORER=1`),
   picks a village or searches a survey number, clicks a parcel.
2. Click card shows an **Analyse this parcel** button.
3. Button calls existing `createProject()` with the parcel polygon as `boundary`
   (area + centroid already computed there), attaches `project.parcel`, routes to `/project/[id]`.
4. Existing modules run on the site; existing `/project/[id]/export` builds the PDF.

## Data
`Project.parcel?: { survey_no, village, hobli, taluk, district, codes{dist,taluk,hobli,vlg}, rtc: RtcData | null }`
— snapshot at creation so the PDF is reproducible. Session-only storage, same as projects today.

## Report
New "Parcel & Title" page in `ReportDocument.tsx` after the cover, rendered only when `project.parcel`
exists, as a `data-export-page` node (PDF generator unchanged). Identity table, polygon area,
RCCMS cases/mutations, disclaimer that RCCMS data is indicative and unverified.

## Out of scope
Auth, server-side projects, boundary map snapshot (tile CORS vs html2canvas), ownership verification.

## Risks
Survey-number search needs `survey_index` (≈15 min background build on first cadastral start).
