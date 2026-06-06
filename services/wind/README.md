# Wind Service

Wind analysis and climatology for sites. Current implementation uses deterministic synthetic data.

## Port

8003

## Contract

`contracts/wind.yaml`

## Feature flag

`feature.wind.analysis`

## Run (local)

```bash
cd services/wind
uvicorn app.main:app --reload --port 8003
```

## Run (docker)

```bash
docker-compose up wind
```

## Swagger

- http://127.0.0.1:8003/docs

## Endpoints

- `GET /health`
- `POST /wind/analyze`

## Example requests

Analyze:

```bash
curl -X POST "http://127.0.0.1:8003/wind/analyze" \
  -H "Content-Type: application/json" \
  -d '{"latitude":28.6139,"longitude":77.2090,"radius_meters":1000}'
```

## FVD traceability

See `docs/feature-validation/SAT-09_wind-analysis.md`.
