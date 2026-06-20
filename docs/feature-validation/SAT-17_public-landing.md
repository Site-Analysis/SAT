# FVD — SAT-17 Public Landing Page

**Jira Ticket:** SAT-17
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)
**Stacked on:** `feat/frontend-redesign` (PR #69)

---

## Feature Overview

Public marketing/landing page for Qnit (served on `qnit.in`). Logged-out users see the
landing; authenticated users redirect to `/dashboard`. Carved out of the frontend base so
the base builds standalone (base ships a `redirect("/dashboard")` `app/page.tsx`).

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `11ae435` | SAT-Fallback | rebrand to Qnit + public landing page |
| `9502fed` | SAT-Fallback | landing copy fixes (Ranjitha, softened data-source tone) |

Ported into `Site-Analysis/SAT` as branch `feat/public-landing` (Phase 1, stacked).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File |
|---|---|---|
| 1 | Landing page component (hero, problem, modules, pricing) | `components/landing/LandingPage.tsx` |
| 2 | Landing styles (scoped module) | `components/landing/landing.module.css` |
| 3 | Root route renders landing when logged out, redirects to `/dashboard` when authed | `app/page.tsx` |
| 4 | CTAs route to `/login` | `components/landing/LandingPage.tsx` |

---

## Deferred (Phase 6 — domains)

The plan calls for landing CTAs to target `https://qnit.site/login` (landing on `qnit.in`,
app on `qnit.site`). Ported as-is with internal `/login` (the route exists in the base
shell, correct for same-origin/preview). Cross-domain absolute-URL rewrite is wired during
Phase 6 go-live (qnit.in → qnit.site), env-driven, to avoid breaking local/preview builds.

## Validation

`npm run build --workspace apps/web` compiles clean (landing component + landing-gate
`app/page.tsx`).
