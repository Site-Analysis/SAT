# Rollback Runbook — Qnit Production

Last verified: 2026-06-21 (Phase 6 go-live).

How to revert each tier of the live deployment to its last-known-good state. Infrastructure
identifiers (AWS account/instance IDs, EIP, security-group ID, Vercel project ID, Supabase
project ref, SSH key path) are **not** in this tracked file — read them from the untracked
`deployment/secrets-manifest.md`.

Topology recap:

| Tier | Where | Serves |
|---|---|---|
| Frontend | Vercel project `qnit-web` (Root Dir `apps/web`), domains `qnit.in` + `qnit.site` | One Next.js deployment, two domains, host-routing in `apps/web/proxy.ts` |
| Backend | Single AWS t3.medium EC2 (Mumbai `ap-south-1`), Docker Compose + Caddy | 10 FastAPI services behind `api.qnit.site` |
| Auth/DB | Supabase (Tokyo) | Auth only (localStorage/PKCE); `public` schema empty |
| DNS | GoDaddy | Apex A-records → Vercel anycast `76.76.21.21`; `api` A-record → EC2 EIP |

---

## 1. Frontend (Vercel)

**Fastest path — promote a previous deployment (no code change):**
1. Vercel dashboard → project `qnit-web` → Deployments.
2. Find the last-known-good Production deployment (status READY, prior to the bad one).
3. `⋯` → **Promote to Production**. Both `qnit.in` and `qnit.site` follow the same
   deployment, so they revert together.

CLI equivalent:
```bash
cd apps/web
vercel ls                        # list deployments, note the good URL
vercel promote <deployment-url>  # repoint Production at it
```

**If the bad state came from a bad commit on `main`:** revert the merge on GitHub
(`git revert -m 1 <merge-sha>` via PR), let Vercel rebuild from `main`. Promote-previous is
faster for an incident; the revert is the durable fix.

**Env-var regression:** Vercel dashboard → Settings → Environment Variables. Production env is
documented in `deployment/secrets-manifest.md`. After changing an env var, **redeploy** — env
changes do not apply to existing deployments.

---

## 2. Backend (EC2 + Docker Compose)

SSH access is locked to the admin IP in the security group (port 22). If your IP changed,
re-add it first (see §4). Key path + instance details: `deployment/secrets-manifest.md`.

```bash
ssh -i <key.pem> ubuntu@<eip>
cd ~/SAT
```

**Roll the stack back to a known-good commit:**
```bash
docker compose -f docker-compose.yml -f docker-compose.aws.yml down
git fetch origin && git checkout <prev-good-tag-or-sha>
docker compose -f docker-compose.yml -f docker-compose.aws.yml up -d --build
```

Keep last-known-good image tags before deploying a new build so you can repin without a rebuild:
```bash
docker images | grep sat            # note current tags before any new deploy
```

**Single bad service** (siblings healthy): `restart: unless-stopped` auto-recovers a crash. To
force one service:
```bash
docker compose -f docker-compose.yml -f docker-compose.aws.yml restart <service>
docker compose -f docker-compose.yml -f docker-compose.aws.yml ps      # confirm healthy
```

**Caddy / TLS regression:** config is `infra/Caddyfile` (path-prefix routing, incl. the
`/weather/*`→temperature alias and `/status/<svc>` health aliases). Certs are Let's Encrypt,
auto-renewed by Caddy; persisted in the Caddy data volume — do **not** delete that volume on a
rollback or you re-issue (and risk rate limits). `docker compose ... restart caddy` after a
Caddyfile change.

**Health check after any backend rollback** (no SSH needed, from anywhere):
```bash
for s in temperature sunpath flood wind rainfall geo planning infrastructure future-infra land-records; do
  printf "%-16s " "$s"; curl -s -o /dev/null -w "%{http_code}\n" https://api.qnit.site/status/$s
done
```
All ten must return `200`.

---

## 3. Database (Supabase)

The app uses Supabase for **auth only** — the `public` schema is empty and there are no
repo migrations (`migrations/` holds only a README; projects are in-memory zustand, ephemeral).
**There is no application data to roll back.** If schema is introduced later, add `.down.sql`
rollback notes alongside each migration and document the `supabase db` revert here.

Auth config (Site URL, redirect allow-list, providers) is dashboard state, not in git —
recorded in `deployment/secrets-manifest.md`. Revert there if an auth-URL change breaks login.

---

## 4. DNS (GoDaddy)

Prior/current record values to restore (these are public — resolvable via `dig`):

| Host | Type | Value |
|---|---|---|
| `qnit.site` `@` | A | `76.76.21.21` (Vercel) |
| `qnit.site` `api` | A | EC2 Elastic IP (see `deployment/secrets-manifest.md`) |
| `qnit.in` `@` | A | `76.76.21.21` (Vercel) |

DNS propagation lag means a DNS rollback is the **slowest** lever — prefer Vercel
promote-previous (§1) or a backend git checkout (§2) for an incident. Only touch DNS if the
EIP or Vercel anycast target itself changed.

**Re-add admin IP to SG port 22** (needed before SSH if your IP rotated):
```bash
MYIP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --region ap-south-1 \
  --group-id <sg-id> --protocol tcp --port 22 --cidr ${MYIP}/32
# revoke the stale one afterwards:
aws ec2 revoke-security-group-ingress --region ap-south-1 \
  --group-id <sg-id> --protocol tcp --port 22 --cidr <old-cidr>/32
```

---

## Incident decision order

1. **Frontend bug** → Vercel promote-previous (seconds).
2. **Backend bug** → `docker compose` checkout prev tag (a minute, on-box).
3. **One service down** → `restart: unless-stopped` self-heals; else `restart <service>`.
4. **DNS/cert** → last resort; slow propagation.

Stop and involve the user before: terminating/replacing the EC2 instance, deleting the Caddy
data volume, rotating the EIP, or any GoDaddy record delete.
