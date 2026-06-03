# Rainfall Service

Historical precipitation archive and summary statistics for points or polygons.

## Port

8004

## Contract

`contracts/rainfall.yaml`

## Feature flags

- `feature.rainfall.archive`
- `feature.rainfall.summary`

## Run (local)

```bash
cd services/rainfall
uvicorn app.main:app --reload --port 8004
```

## Run (docker)

```bash
cd /Volumes/LocalDrive/SAT
docker-compose up rainfall
```

## Swagger

- http://127.0.0.1:8004/docs

## Endpoints

- `GET /health`
- `GET /rainfall/archive`
- `POST /rainfall/summary`

## Example requests

Archive:

```bash
curl "http://127.0.0.1:8004/rainfall/archive?latitude=19.07&longitude=72.87&start_date=2023-01-01&end_date=2023-01-10"
```

Summary (point):

```bash
curl -X POST "http://127.0.0.1:8004/rainfall/summary" \
  -H "Content-Type: application/json" \
  -d '{"latitude":19.07,"longitude":72.87,"start_date":"2023-01-01","end_date":"2023-01-31"}'
```

Summary (polygon):

```bash
curl -X POST "http://127.0.0.1:8004/rainfall/summary" \
  -H "Content-Type: application/json" \
  -d '{"geometry":{"type":"Polygon","coordinates":[[[72.85,19.05],[72.90,19.05],[72.90,19.10],[72.85,19.10],[72.85,19.05]]]},"start_date":"2023-01-01","end_date":"2023-01-31"}'
```

## FVD traceability

See `docs/feature-validation/SAT-18_rainfall-analysis.md`. Acceptance criteria mapping is TODO.
