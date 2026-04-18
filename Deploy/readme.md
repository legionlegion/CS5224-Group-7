# Deploy

GCP Cloud Run deployment manifests for all three services, orchestrated through Skaffold and Google Cloud Deploy delivery pipelines. Project ID and region are environment-specific — supply via `gcloud config` or CI variables.

## Layout

```
Deploy/
├── Backend/
├── Frontend/
└── ML/
```

Each service folder contains:

- `run-service-dev.yaml` · `run-service-uat.yaml` · `run-service-prod.yaml` — Knative Service manifests per environment
- `skaffold.yaml` — build/render config used by Cloud Deploy
- `clouddeploy.yaml` — delivery pipeline + targets (`dev`, `uat`, `prod`)

## Pipeline

```
git push → Cloud Build (per-service cloudbuild.yaml in service folder)
        → Artifact Registry (image push)
        → Cloud Deploy release
            ├── dev   (auto promote)
            ├── uat   (manual approval)
            └── prod  (manual approval)
        → Cloud Run service
```

Cloud Build artifacts are staged in a project-scoped GCS bucket (configured per environment).

## Service Configuration

| Service  | Memory | CPU | Scale  | Notes |
| -------- | ------ | --- | ------ | ----- |
| Frontend | 512Mi  | 1   | 0→10   | request-based scaling, startup-cpu-boost |
| Backend  | 512Mi  | 1   | 0→10   | request-based scaling |
| ML       | 2Gi    | 1   | 0→5    | CPU-based scaling (model warmup) |

All services use `run.googleapis.com/ingress: all`. Each service has its own per-environment Google Service Account, referenced from the corresponding `run-service-*.yaml` manifest.

## Secrets

- Dev manifests embed Firebase web config (public-by-design `NEXT_PUBLIC_FIREBASE_*` keys).
- Prod manifests use `REPLACE_ME` placeholders — inject via Secret Manager bindings or `gcloud run services update` before promotion.

## Common Commands

```bash
# Local build + deploy via Skaffold
skaffold run -p dev -f Deploy/Backend/skaffold.yaml

# Trigger a Cloud Deploy release manually
gcloud deploy releases create rel-$(date +%s) \
  --project=<GCP_PROJECT_ID> \
  --region=<GCP_REGION> \
  --delivery-pipeline=backend-pipeline \
  --source=Deploy/Backend
```

The service `cloudbuild.yaml` files (under `Backend/`, `Frontend/`, `Machine Learning/` at the repo root) wrap the above in CI form — see each service README for the exact `gcloud builds submit` command.
