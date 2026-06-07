# FVD-16 — Realtime Collaboration & Project Sharing

**Jira Ticket:** — (no ticket)
**Status:** Service layer done — in org repo; not yet wired to simulation UI
**Resolved:** 2026-05-26 (SiteAnalysisToolV3) — partial
**Type:** New Feature
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `frontend/src/services/collaborationService.ts`, `realtimeService.ts`, `simulationProjectService.ts`
**Latest Commit:** `4bf53de` (2026-05-15, `Site-Analysis/SiteAnalysisToolV3` main)

---

## Feature Overview

**User Story:** As a project lead, I want to invite team members to view or edit a simulation project in real time, so that architects and clients can collaborate on the same design without file sharing.

**Business Value:** Enables multi-user concurrent design review. Share tokens allow read-only access without login. Real-time presence (who is online) and object locking prevent conflicts. Project persistence to Supabase enables resume-from-anywhere. Complete service layer is built; the gap is wiring it to the simulation UI flow.

---

## Acceptance Criteria (derived)

| # | Acceptance Criterion |
|---|---|
| 1 | Save simulation project to Supabase with name, thumbnail, state |
| 2 | Load project by ID; read-only projects set `isReadOnly` flag |
| 3 | Share via public token (viewer) or private invite (editor) |
| 4 | List all projects owned by current user |
| 5 | Invite collaborator by email with viewer or editor role |
| 6 | Remove collaborator |
| 7 | Real-time presence: see which users are online in the project |
| 8 | Real-time model change broadcast to all connected clients |
| 9 | Object locking — per-object userId lock prevents concurrent edits |

---

## Code Traceability Matrix

| # | File | Function / Symbol |
|---|---|---|
| 1 | `services/simulationProjectService.ts` | `saveSimulationProject(state, thumbnail)` |
| 2 | `services/simulationProjectService.ts` | `loadSimulationProject(projectId)`, `loadSimulationProjectByToken(token)` |
| 2 | `hooks/useCollaborationStore.ts` | `isReadOnly` flag set when loading via share token |
| 3 | `services/simulationProjectService.ts` | `updateShareMode(projectId, mode)` — `'private'|'link-view'|'link-edit'` |
| 3 | `hooks/useCollaborationStore.ts` | `shareInfo: ShareInfo` — share URL + mode |
| 4 | `services/simulationProjectService.ts` | `getUserSimulationProjects()` |
| 4 | `services/simulationProjectService.ts` | `deleteSimulationProject(projectId)` |
| 5 | `services/collaborationService.ts` | `inviteCollaborator(projectId, email, role: 'viewer'|'editor')` |
| 6 | `services/collaborationService.ts` | `removeCollaborator(projectId, collaboratorId)` |
| 5–6 | `services/collaborationService.ts` | `getProjectCollaborators(projectId)` |
| 7 | `services/realtimeService.ts` | `joinProjectChannel(projectId, userId, onPresenceChange)` |
| 7 | `hooks/useCollaborationStore.ts` | `onlineUsers: PresenceState[]` — users currently in channel |
| 8 | `services/realtimeService.ts` | `broadcastModelChange(channel, change)` |
| 8 | `hooks/useCollaborationStore.ts` | Realtime subscription triggers store update |
| 9 | `hooks/useCollaborationStore.ts` | `lockedObjects: Record<objectId, userId>` |
| — | `services/realtimeService.ts` | `leaveProjectChannel(channel)` |
| — | `hooks/useCollaborationStore.ts` | Full persistence: `saveProject()`, `loadProject()`, `deleteProject()` |
| — | `types/collaboration.ts` | `Collaborator`, `SimulationCollaboratorRow`, `PresenceState`, `ExportProgress`, `ShareInfo` |

---

## Implementation Breakdown

### Architecture

```
Supabase Backend:
  Tables:
    - simulation_projects: id, user_id, name, state (jsonb), thumbnail (url), share_mode, share_token
    - collaborators: id, project_id, user_id, invited_email, role, accepted, created_at
  Realtime:
    - Supabase Presence + Broadcast channels (per projectId)

Frontend Services:
  simulationProjectService.ts
    ├── saveSimulationProject()   → upsert simulation_projects row
    ├── loadSimulationProject()   → fetch by id
    ├── loadSimulationProjectByToken() → fetch by share_token (public)
    ├── getUserSimulationProjects() → list by user_id
    └── updateShareMode()         → set share_mode + generate token

  collaborationService.ts
    ├── inviteCollaborator()  → insert collaborators row
    ├── removeCollaborator()  → delete collaborators row
    └── getProjectCollaborators() → select join with profiles

  realtimeService.ts
    ├── joinProjectChannel()  → supabase.channel(projectId).track(presence).subscribe()
    ├── broadcastModelChange() → channel.send({ type: 'broadcast', event: 'model-change' })
    └── leaveProjectChannel() → channel.unsubscribe()

Zustand Store (useCollaborationStore):
    ├── Save/load/delete project actions
    ├── Collaborator CRUD
    ├── Presence state (onlineUsers[])
    ├── Locked objects map
    └── Export progress tracking
```

### Technology Stack

| Component | Technology |
|---|---|
| Database | Supabase PostgreSQL (`simulation_projects`, `collaborators`) |
| Realtime | Supabase Realtime (Presence + Broadcast) |
| Auth | Supabase Auth (JWT) — `AuthContext.tsx` |
| Schema | `backend/supabase-schema.sql` |
| State | Zustand (`useCollaborationStore.ts`) |

### Supabase Schema (relevant tables)

```sql
-- From backend/supabase-schema.sql
-- simulation_projects: project state + sharing
-- collaborators: project_id, invited_email, role, accepted
-- profiles: user_id join for name/avatar
```

---

## Automated Validation Plan

> Requires Supabase project configured with keys in `frontend/.env`.

### AC-1 & AC-4: Save and list projects

```typescript
import { saveSimulationProject, getUserSimulationProjects } from '@/services/simulationProjectService';

// Save:
const saved = await saveSimulationProject({ /* SimulationSaveState */ }, null);
console.assert(saved.id != null, 'Project ID missing after save');
console.log('Saved project ID:', saved.id);

// List:
const projects = await getUserSimulationProjects();
console.assert(projects.length > 0, 'Project list empty after save');
console.log('Projects:', projects.map(p => p.id));
```

### AC-2: Load project

```typescript
import { loadSimulationProject } from '@/services/simulationProjectService';
const loaded = await loadSimulationProject(saved.id);
console.assert(loaded.id === saved.id, 'Loaded ID mismatch');
console.log('✓ Load confirmed');
```

### AC-3: Share token generation

```typescript
import { updateShareMode } from '@/services/simulationProjectService';
const share = await updateShareMode(saved.id, 'link-view');
console.assert(share.shareUrl != null, 'No share URL generated');
console.log('Share URL:', share.shareUrl);
```

### AC-5: Invite collaborator

```typescript
import { inviteCollaborator, getProjectCollaborators } from '@/services/collaborationService';
await inviteCollaborator(saved.id, 'test@example.com', 'viewer');
const collaborators = await getProjectCollaborators(saved.id);
const invited = collaborators.find(c => c.invitedEmail === 'test@example.com');
console.assert(invited != null, 'Invited collaborator not found');
console.assert(invited.role === 'viewer', 'Wrong role');
console.log('✓ Collaborator invited');
```

### AC-7: Real-time channel join (manual UI check)

```bash
# Open two browser windows on same project
# Both should show the other user in presence list
# Check: useCollaborationStore.getState().onlineUsers.length === 2
```

---

## Outstanding Actions

1. **Not wired to simulation UI** — `useCollaborationStore` and services exist but `SimulationRoot` does not call `saveProject()` or show a collaborators panel. This is the primary gap. Wire save/load/share buttons to simulation toolbar.
2. **Supabase schema** — `backend/supabase-schema.sql` exists but relationship to Supabase project not confirmed. Run migrations before testing.
3. **Read-only enforcement** — `isReadOnly` flag is in store but no enforcement found in `SceneCanvas.tsx` to disable `TransformControls` when read-only.
4. **Object locking** — `lockedObjects` map exists in store but no locking logic found in `SceneCanvas.tsx` to prevent editing another user's selected object.
5. **Export progress** — `ExportProgress` type and `exportProgress` state exist in store but no export progress UI found.
6. **Jira ticket** — No story. Raise as new story in SAT backlog.
