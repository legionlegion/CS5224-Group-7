from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from ultralytics import YOLO

import uvicorn

MODEL_PATH = Path("./best.pt")

app = FastAPI(title="YOLO Prediction API")
model = YOLO(str(MODEL_PATH))

ALLOWED_CLASSES = {
    "Bluebins",
    "Cardboard",
    "Glass",
    "Metal",
    "Paper",
    "Plastic",
    "Trash",
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

    results = model.predict(source=image, conf=conf, verbose=False)
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
    
    has_bluebin = "Bluebins" in detected_classes
    has_recyclable = any(
        class_name != "Bluebins" and class_name != "Trash"
        for class_name in detected_classes
    )

    return has_bluebin and has_recyclable
  
if __name__ == "__main__":
  uvicorn.run("main:app", host="127.0.0.1", port=5001, reload=True)