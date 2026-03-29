from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from ultralytics import YOLO

import os
import uvicorn

MODEL_PATH = Path("./best.pt")

app = FastAPI(title="YOLO Prediction API")
model = YOLO(str(MODEL_PATH))

ALLOWED_CLASSES = {
    "blue bins",
    "metal can",
    "newspaper",
    "plastic bag",
    "plastic bottle",
}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    conf = 0.7
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

    detected_classes = {
        pred["class_name"] for pred in predictions if pred["class_name"] in ALLOWED_CLASSES
    }
    recyclable_items = sorted(detected_classes)
    print(recyclable_items)
    return recyclable_items
  
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)