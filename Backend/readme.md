## Quick Start

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

python API_endpoints.py
```

## Deploy:
```bash
gcloud builds submit . \
  --project=cs5224-grp7-3bb27 \
  --config=Backend/cloudbuild.yaml \
  --region=us-west2 \
  --substitutions=COMMIT_SHA=manual-$(date +%s),SHORT_SHA=manual$(date +%H%M%S)
```
