# Machine Learning

FastAPI inference service that detects recyclable items in user-submitted photos. Trained YOLO11-Large model identifies six classes (blue bins, metal cans, newspapers, plastic bags, plastic bottles, cardboard), normalized by the Backend into the four user-facing categories: `Bluebins`, `Metal`, `Paper`, `Plastic`.

## Stack

- Python 3.12 (Python 3.13 currently breaks `pydantic_core`)
- FastAPI + Uvicorn
- Ultralytics YOLO11
- OpenCV (headless), Pillow
- SAM3 used offline for label-assist during dataset prep

## Layout

```
Machine Learning/
├── main.py            # FastAPI app exposing POST /predict
├── best.pt            # Trained YOLO11-Large weights (~51MB)
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml
└── Code/              # Training & data prep
    ├── 1-3 SAM scripts                          # SAM3 bbox / segmentation
    ├── 4. Yolo script - model training (...).ipynb
    ├── Image augmentation.ipynb
    └── Renaming_images.ipynb
```

See [Code/README.md](Code/README.md) for full training-pipeline details (SAM3 workflow, class mapping, augmentation, training params).

## Inference API

```
POST /predict
Content-Type: multipart/form-data
Field: file=<image>

→ 200 JSON: { "detections": ["plastic_bottle", "metal_can", ...] }
```

Called by Backend at `ML_PREDICT_URL` (default `http://127.0.0.1:5001/predict`, 10s timeout).

## Quick Start

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py        # listens on :5001 locally
```

### Mac LZMA error

```bash
brew install xz
pyenv uninstall 3.12.0
pyenv install 3.12.0
```

## Deploy (run from repo root)

> `best.pt` must NOT be gitignored at deploy time so it is included in the image.

```bash
# macOS
gcloud builds submit . \
  --project=<GCP_PROJECT_ID> \
  --config="Machine Learning/cloudbuild.yaml" \
  --region=<GCP_REGION> \
  --substitutions=COMMIT_SHA=manual-$(date +%s),SHORT_SHA=manual$(date +%H%M%S)

# Windows PowerShell
gcloud builds submit . `
  --project=<GCP_PROJECT_ID> `
  --config="Machine Learning/cloudbuild.yaml" `
  --region=<GCP_REGION> `
  --substitutions="COMMIT_SHA=manual-$(Get-Date -UFormat %s),SHORT_SHA=manual$(Get-Date -Format HHmmss)"
```

In production the container listens on `$PORT` (8080) via uvicorn. Cloud Run service has 2 GiB memory to load model weights and scales 0→5. Manifests in [Deploy/ML/](../Deploy/ML/).

Replace `<GCP_PROJECT_ID>` and `<GCP_REGION>` with your environment-specific values (typically sourced from `gcloud config` or CI secrets).