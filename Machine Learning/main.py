from io import BytesIO
import os
from pathlib import Path
import sys

if sys.version_info[:2] >= (3, 13):
    raise RuntimeError(
        "Machine Learning service requires Python 3.12 or earlier. "
        "Recreate the venv with python3.12 -m venv venv, reinstall requirements, and try again."
    )

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from ultralytics import YOLO

import os
import uvicorn

MODEL_PATH = Path("./best.pt")
DEFAULT_CONFIDENCE_THRESHOLD = 0.25

app = FastAPI(title="YOLO Prediction API")
model = YOLO(str(MODEL_PATH))

ALLOWED_CLASSES = {
    "blue bins",
    "metal can",
    "newspaper",
    "plastic bag",
    "plastic bottle",
}

CLASS_NAME_MAP = {
    "blue bins": "Bluebins",
    "metal can": "Metal",
    "newspaper": "Paper",
    "plastic bag": "Plastic",
    "plastic bottle": "Plastic",
}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    conf = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD))
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        image = Image.open(BytesIO(payload)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc
    results = model.predict(source=image, conf=0.25, verbose=False)
    res = results[0]

    predictions = []
    for box in res.boxes:
        class_id = int(box.cls[0])
        predictions.append(
            {
                "class_name": model.names.get(class_id, str(class_id)),
            }
        )

    detected_classes = set()
    for pred in predictions:
        raw_class_name = pred["class_name"]
        normalized_class_name = CLASS_NAME_MAP.get(raw_class_name, raw_class_name)
        if normalized_class_name in ALLOWED_CLASSES:
            detected_classes.add(normalized_class_name)

    # Return list of recyclable items (all detected except Trash)
    recyclable_items = list(detected_classes - {"Trash"})
    return recyclable_items
  
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)