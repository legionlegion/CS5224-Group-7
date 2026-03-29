## Quick Start

```bash
# Create virtual environment
python3.12 -m venv venv # Mac
py -3.12 -m venv .venv # Windows

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
.venv\Scripts\activate.bat 

# Install dependencies
pip install -r requirements.txt

python main.py
```

## Deploy: (run in root directory ../)
```bash
# Mac
gcloud builds submit . \
  --project=cs5224-grp7-3bb27 \
  --config=Backend/cloudbuild.yaml \
  --region=us-west2 \
  --substitutions=COMMIT_SHA=manual-$(date +%s),SHORT_SHA=manual$(date +%H%M%S)

# Windows Powershell
gcloud builds submit . `
  --project=cs5224-grp7-3bb27 `
  --config="Backend/cloudbuild.yaml" `
  --region=us-west2 `
  --substitutions="COMMIT_SHA=manual-$(Get-Date -UFormat %s),SHORT_SHA=manual$(Get-Date -Format HHmmss)"
```
