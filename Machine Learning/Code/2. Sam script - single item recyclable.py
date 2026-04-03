import sys
import os
import numpy as np
import csv
import argparse
from time import perf_counter
from PIL import Image 
import torch
import cv2
from huggingface_hub import hf_hub_download

# ---------- Relative Path Fix ----------

current_script_folder = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_folder, ".."))
model_path = os.path.join(project_root, "Segment-Anything Model 3")

if model_path not in sys.path:
    sys.path.append(model_path)

# ---------- Import SAM ----------

import sam3
from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor

print(f"Success! SAM3 imported from: {sam3.__file__}")
print(f"Is CUDA available? {torch.cuda.is_available()}")

# Edit these defaults if you want fixed values without typing CLI arguments every run.
IPHONE_INPUT_BASE = os.path.join(project_root, "Data", "Iphone")
category = "Cardboard"

CONFIG_DEFAULTS = {
    # Leave the last folder name blank here. Fill it later if needed.
    "input_source": os.path.join(IPHONE_INPUT_BASE, category),
    "output_base_folder": os.path.join(IPHONE_INPUT_BASE, f"Sam3 {category} output"),
    "word_prompt": "Cardboard on the floor",
    "threshold": 0.05,
    "ckpt_filename": "sam3.pt",
}

# Class ID mapping for YOLO labels.
CLASS_NAME_TO_ID = {
    "blue bins": 0,
    "metal can": 1,
    "newspaper": 2,
    "plastic bag": 3,
    "plastic bottle": 4,
    "cardboard": 5,
}

# ---------- Auto-Download Logic ---------- 

def ensure_checkpoint_exists(target_folder, filename):
    file_path = os.path.join(target_folder, filename)
    
    if os.path.exists(file_path):
        print(f"Checkpoint found at: {file_path}")
        return file_path
        
    print(f"Checkpoint not found at {file_path}")
    print("Initiating download from HuggingFace (facebook/sam3)...")
    
    try:
        # Download config (often required by model builders)
        hf_hub_download(repo_id="facebook/sam3", filename="config.json", local_dir=target_folder)
        
        # Download weights
        checkpoint_path = hf_hub_download(repo_id="facebook/sam3", filename=filename, local_dir=target_folder)
        print("Download complete.")
        return checkpoint_path
    except Exception as e:
        print(f"Failed to download model: {e}")
        sys.exit(1)

def build_processor(threshold, ckpt_filename="sam3.pt"):
    ckpt_path = ensure_checkpoint_exists(current_script_folder, ckpt_filename)
    model = build_sam3_image_model(
        checkpoint_path=ckpt_path,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    print("SAM Model built successfully.")
    processor = Sam3Processor(model, confidence_threshold=threshold)
    print(f"SAM Processor initialised (Threshold: {threshold}).")
    return processor

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run SAM3 single-object detection and save bbox and mask+bbox overlays."
    )
    parser.add_argument(
        "--input-source",
        default=CONFIG_DEFAULTS["input_source"],
        help="Input image file or folder path",
    )
    parser.add_argument(
        "--output-base-folder",
        default=CONFIG_DEFAULTS["output_base_folder"],
        help="Base output folder path",
    )
    parser.add_argument(
        "--word-prompt",
        default=CONFIG_DEFAULTS["word_prompt"],
        help="Text prompt for detection",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=CONFIG_DEFAULTS["threshold"],
        help="SAM confidence threshold",
    )
    parser.add_argument(
        "--ckpt-filename",
        default=CONFIG_DEFAULTS["ckpt_filename"],
        help="Checkpoint filename",
    )
    return parser.parse_args()

def list_image_paths(input_source):
    valid_ext = (".png", ".jpg", ".jpeg")
    if os.path.isfile(input_source):
        if input_source.lower().endswith(valid_ext):
            return [input_source]
        raise ValueError(f"Unsupported image type: {input_source}")

    if os.path.isdir(input_source):
        image_files = []
        for root, _, files in os.walk(input_source):
            for f in files:
                if f.lower().endswith(valid_ext):
                    image_files.append(os.path.join(root, f))
        return sorted(image_files)

    raise ValueError(f"Input source does not exist: {input_source}")


def infer_class_id_from_image_path(image_path):
    class_name = os.path.basename(os.path.dirname(image_path)).strip().lower()
    class_id = CLASS_NAME_TO_ID.get(class_name)
    if class_id is None:
        raise ValueError(
            f"Unknown class folder '{class_name}'. Expected one of: {sorted(CLASS_NAME_TO_ID.keys())}"
        )
    return class_id, class_name


def bbox_to_yolo_line(box, image_w, image_h, class_id):
    x1, y1, x2, y2 = box
    x_center = ((x1 + x2) / 2.0) / image_w
    y_center = ((y1 + y2) / 2.0) / image_h
    width = abs(x2 - x1) / image_w
    height = abs(y2 - y1) / image_h
    return f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"


def detect_single_best(image_path, word_prompt, processor):
    # Use OpenCV as the single image source to keep orientation consistent
    # between inference and output rendering.
    original_bgr = cv2.imread(image_path)
    if original_bgr is None:
        raise ValueError(f"Could not load image: {image_path}")

    image = Image.fromarray(cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB))

    if torch.cuda.is_available():
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)
        start_event.record()
    else:
        start_ts = perf_counter()

    inference_state = processor.set_image(image)
    output = processor.set_text_prompt(state=inference_state, prompt=word_prompt)

    if torch.cuda.is_available():
        end_event.record()
        torch.cuda.synchronize()
        elapsed_time_ms = start_event.elapsed_time(end_event)
    else:
        elapsed_time_ms = (perf_counter() - start_ts) * 1000.0

    masks, boxes, scores = output["masks"], output["boxes"], output["scores"]

    if hasattr(scores, "cpu"):
        scores = scores.cpu().detach().numpy()
    if hasattr(masks, "cpu"):
        masks = masks.cpu().detach().numpy()
    if hasattr(boxes, "cpu"):
        boxes = boxes.cpu().detach().numpy()

    if scores is None or len(scores) == 0:
        return None, None, elapsed_time_ms

    best_idx = int(np.argmax(scores))
    return masks[best_idx], float(scores[best_idx]), elapsed_time_ms


def mask_to_binary(mask, image_h, image_w):
    mask_array = mask.squeeze() if getattr(mask, "ndim", 0) == 3 else mask
    mask_bin = (mask_array > 0).astype(np.uint8)

    # Some outputs can come as (W, H); transpose to (H, W) before resizing.
    if mask_bin.shape == (image_w, image_h):
        mask_bin = mask_bin.T

    if mask_bin.shape != (image_h, image_w):
        mask_bin = cv2.resize(mask_bin, (image_w, image_h), interpolation=cv2.INTER_NEAREST)

    return mask_bin * 255


def bbox_from_mask(mask_uint8):
    ys, xs = np.where(mask_uint8 > 0)
    if ys.size == 0 or xs.size == 0:
        return None

    x1 = int(xs.min())
    y1 = int(ys.min())
    x2 = int(xs.max())
    y2 = int(ys.max())
    return x1, y1, x2, y2


def save_outputs(image_path, mask, class_id, bbox_folder, overlay_folder):
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]

    original_bgr = cv2.imread(image_path)
    if original_bgr is None:
        raise ValueError(f"Could not load image: {image_path}")

    h, w = original_bgr.shape[:2]

    mask_uint8 = mask_to_binary(mask, h, w)
    bbox = bbox_from_mask(mask_uint8)
    if bbox is None:
        raise ValueError("Mask is empty after thresholding; cannot compute bbox from mask.")

    x1, y1, x2, y2 = bbox

    bbox_img = original_bgr.copy()
    cv2.rectangle(bbox_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(bbox_folder, f"{base_name}_bbox.jpg"), bbox_img)

    yolo_line = bbox_to_yolo_line((x1, y1, x2, y2), w, h, class_id)
    yolo_label_path = os.path.join(bbox_folder, f"{base_name}.txt")
    with open(yolo_label_path, "w", encoding="utf-8") as f:
        f.write(yolo_line + "\n")

    color_mask = np.zeros_like(original_bgr)
    color_mask[mask_uint8 > 0] = (0, 0, 255)
    overlay = cv2.addWeighted(original_bgr, 1.0, color_mask, 0.35, 0)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(overlay_folder, f"{base_name}_mask_bbox_overlay.jpg"), overlay)


def main():
    args = parse_args()

    if not args.input_source:
        raise ValueError(
            "Please provide input via --input-source or set CONFIG_DEFAULTS['input_source']."
        )

    input_source = os.path.abspath(args.input_source)
    output_base_folder = args.output_base_folder.strip() if args.output_base_folder else ""

    if not output_base_folder:
        source_name = os.path.basename(input_source)
        if os.path.isfile(input_source):
            source_name = os.path.basename(os.path.dirname(input_source))
        output_base_folder = os.path.join(os.path.dirname(input_source), f"Sam3 {source_name} output")

    output_base_folder = os.path.abspath(output_base_folder)

    image_paths = list_image_paths(input_source)
    if len(image_paths) == 0:
        print("No images found in input source.")
        return

    bbox_folder = os.path.join(output_base_folder, "bbox")
    overlay_folder = os.path.join(output_base_folder, "overlay")
    os.makedirs(bbox_folder, exist_ok=True)
    os.makedirs(overlay_folder, exist_ok=True)

    processor = build_processor(args.threshold, args.ckpt_filename)

    summary_rows = []
    print(f"Starting inference on {len(image_paths)} image(s) with prompt: '{args.word_prompt}'")

    for image_path in image_paths:
        filename = os.path.basename(image_path)

        try:
            mask, score, elapsed_ms = detect_single_best(image_path, args.word_prompt, processor)
            if mask is None:
                print(f"No detection: {filename} | Time: {elapsed_ms:.2f} ms")
                summary_rows.append([filename, 0, "", "", "", f"{elapsed_ms:.2f}"])
                continue

            class_id, class_name = infer_class_id_from_image_path(image_path)
            save_outputs(image_path, mask, class_id, bbox_folder, overlay_folder)
            print(f"Processed: {filename} | Best score: {score:.4f} | Time: {elapsed_ms:.2f} ms")
            summary_rows.append([filename, 1, f"{score:.6f}", args.word_prompt, class_name, f"{elapsed_ms:.2f}"])
        except Exception as e:
            print(f"Skipping {filename}: {e}")
            summary_rows.append([filename, 0, "", "", "", ""])

    summary_path = os.path.join(output_base_folder, "detection_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_name", "detected", "best_score", "prompt", "class_name", "inference_time_ms"])
        writer.writerows(summary_rows)

    print(f"Done. Outputs saved in: {output_base_folder}")
    print(f"BBox folder: {bbox_folder}")
    print(f"Overlay folder: {overlay_folder}")
    print(f"Summary CSV: {summary_path}")

if __name__ == "__main__":
    main()