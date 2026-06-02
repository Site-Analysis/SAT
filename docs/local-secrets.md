# Local secrets and env setup

SAT is a public repo. Never commit credentials or service account JSON.

## Local setup

1. Copy `.env.example` to `.env`.
2. Set Supabase values in `.env`:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
3. Create a local secrets folder at `secrets/`.
4. Place the GEE service account JSON at `secrets/service-account.json`.
5. Set GEE values in `.env`:
   - `GEE_PROJECT_ID`
   - `GEE_SERVICE_ACCOUNT_EMAIL`
   - `GEE_SERVICE_ACCOUNT_KEY_PATH=secrets/service-account.json`

## Safety rules

- Do not commit `.env` or any files under `secrets/`.
- Do not hardcode keys in source code.
