# Backend

Flask REST API for the EcoBin Go recycling platform. Verifies user-submitted recycling activity (image + GPS), proxies image classification to the ML service, and manages user profiles, transactions, leaderboards, and bin lookups backed by Firestore.

## Stack

- Python 3.12
- Flask + flask-cors, served by gunicorn
- Firebase Admin SDK (Firestore + Auth)
- Containerized with Docker, deployed via GCP Cloud Build → Cloud Deploy → Cloud Run

## Layout

```
Backend/
├── API_endpoints.py      # Flask app, all REST routes
├── auth_middleware.py    # Firebase Bearer token verification decorator
├── API_test.py           # Endpoint tests
├── db/
│   ├── RecyclingBins.geojson      # NEA recycling bin geospatial data
│   └── init_referential_data.py   # Seeds referential collections
├── Dockerfile
├── cloudbuild.yaml       # GCP Cloud Build pipeline
├── requirements.txt
└── serviceAccountKey.json (gitignored)
```

## Key Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/verify-activity` | Verify recycling submission (image + GPS) via ML service |
| GET  | `/nearby-bins` | Bins within radius of supplied coords |
| GET  | `/leaderboard` | Ranked users, optionally by region |
| GET  | `/users/stats` | Authenticated user's points/history |
| GET  | `/users/rank/global` · `/users/rank/region` | User's ranking |
| PUT  | `/users/profile` | Update profile |
| GET  | `/regions` · `/districts` | Referential data |

All authenticated routes expect `Authorization: Bearer <Firebase ID token>`.

## Environment

```bash
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
ML_PREDICT_URL=http://127.0.0.1:5001/predict   # defaults to localhost ML service
```

## Quick Start

```bash
python3.12 -m venv venv
source venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate.bat      # Windows

pip install -r requirements.txt
python API_endpoints.py
```

Default port: 5000. CORS allows `http://localhost:3000`.

## Deploy (run from repo root)

```bash
# macOS
gcloud builds submit . \
  --project=<GCP_PROJECT_ID> \
  --config=Backend/cloudbuild.yaml \
  --region=<GCP_REGION> \
  --substitutions=COMMIT_SHA=manual-$(date +%s),SHORT_SHA=manual$(date +%H%M%S)

# Windows PowerShell
gcloud builds submit . `
  --project=<GCP_PROJECT_ID> `
  --config="Backend/cloudbuild.yaml" `
  --region=<GCP_REGION> `
  --substitutions="COMMIT_SHA=manual-$(Get-Date -UFormat %s),SHORT_SHA=manual$(Get-Date -Format HHmmss)"
```

Cloud Build pushes to Artifact Registry and triggers Cloud Deploy, which promotes through `dev → uat → prod` Cloud Run services. Manifests live in [Deploy/Backend/](../Deploy/Backend/).