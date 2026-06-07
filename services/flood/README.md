# Flood Service

Flood risk scoring with deterministic fallback output and GEE-ready placeholders.

## Port
8002

## Contract
`contracts/flood.yaml` — `POST /flood/analyze`

## Feature flag
`feature.flood.risk-analysis`

## Run (local)
```bash
cd services/flood
uvicorn app.main:app --reload --port 8002
```

## Run (docker)
```bash
cd /Volumes/LocalDrive/SAT
docker-compose up flood
```

## Endpoints

- `GET /health`
- `POST /flood/analyze`

## Notes

- Deterministic fallback logic is used until GEE integration is wired.
- GEE credentials are optional for local deterministic runs.

## FVD traceability

See `docs/feature-validation/SAT-07_flood-risk-analysis.md`.
