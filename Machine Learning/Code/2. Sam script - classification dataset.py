import sys
import os
import numpy as np
import pandas as pd
from PIL import Image 
import torch
import cv2
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
import shutil

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

load_dotenv()

print(f"Success! SAM3 imported from: {sam3.__file__}")
print(f"Is CUDA available? {torch.cuda.is_available()}")

# ---------- Settings (Loaded from .env) ---------- 

threshold = float(os.getenv("SAM_THRESHOLD"))
sam_word_prompt = os.getenv("SAM_WORD_PROMPT")

input_rel_path = os.getenv("ORIGINAL_DATA_REL_PATH")
input_folder_path = os.path.join(project_root, input_rel_path)

output_rel_path = os.getenv("ORIGINAL_OUTPUT_REL_PATH")
sam_output_folder_path = os.path.join(project_root, output_rel_path)

print(f"Cleaning up output directory: {sam_output_folder_path}")
if os.path.exists(sam_output_folder_path):
    shutil.rmtree(sam_output_folder_path)  # Deletes the folder and all contents
os.makedirs(sam_output_folder_path, exist_ok=True) # Recreates empty folder

# ---------- Auto-Download Logic ---------- 

def ensure_checkpoint_exists(target_folder, filename):
    """
    Checks if the checkpoint exists. If not, downloads it from HuggingFace.
    """
    file_path = os.path.join(target_folder, filename)
    
    if os.path.exists(file_path):
        print(f"✅ Checkpoint found at: {file_path}")
        return file_path
        
    print(f"⚠️ Checkpoint not found at {file_path}")
    print("⬇️ Initiating download from HuggingFace (facebook/sam3)...")
    
    try:
        # Download config (often required by model builders)
        hf_hub_download(repo_id="facebook/sam3", filename="config.json", local_dir=target_folder)
        
        # Download weights
        checkpoint_path = hf_hub_download(repo_id="facebook/sam3", filename=filename, local_dir=target_folder)
        print("✅ Download complete.")
        return checkpoint_path
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        sys.exit(1)

# ---------- Model Initialisation ---------- 
# ckpt_path or bpe_path can be specified here, both builds the same model, hence only one is needed.

ckpt_filename = os.getenv("CKPT_FILENAME", "sam3.pt")
ckpt_path = ensure_checkpoint_exists(current_script_folder, ckpt_filename)

# bpe_path = os.path.join(model_path, "sam3", "assets", "bpe_simple_vocab_16e6.txt.gz")

# if not os.path.exists(bpe_path):
#     print(f"❌ ERROR: BPE Vocab file not found at {bpe_path}")
#     sys.exit(1)

model = build_sam3_image_model(
    checkpoint_path=ckpt_path,  
    # bpe_path=bpe_path,          
    device="cuda" if torch.cuda.is_available() else "cpu"
)
print("SAM Model built successfully.")

processor = Sam3Processor(model, confidence_threshold=threshold)
print(f"SAM Processor initialised (Threshold: {threshold}, Prompt: '{sam_word_prompt}').")

# ---------- Inference Logic ---------- 

def predict_image_from_folder(folder_path, word_prompt):
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    output_list = []
    
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)

    print(f"Starting inference on {len(image_files)} images...")

    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"Skipping {image_file}: {e}")
            continue
        
        start_event.record()
        
        inference_state = processor.set_image(image)
        output = processor.set_text_prompt(state=inference_state, prompt=word_prompt)
        
        end_event.record()
        torch.cuda.synchronize()
        elapsed_time_ms = start_event.elapsed_time(end_event)
        
        masks, boxes, scores = output["masks"], output["boxes"], output["scores"]
        
        # Move to CPU immediately
        if hasattr(scores, 'cpu'): scores = scores.cpu().detach().numpy()
        if hasattr(masks, 'cpu'): masks = masks.cpu().detach().numpy()
        if hasattr(boxes, 'cpu'): boxes = boxes.cpu().detach().numpy()

        output_list.append((image_file, masks, boxes, scores))
        print(f"Processed: {image_file} | Time: {elapsed_time_ms:.2f} ms")
    
    return output_list

def save_segmented_objects(results, source_folder, base_output_folder):
    segmented_folder = os.path.join(base_output_folder, "raw_segmented_objects")
    masks_folder = os.path.join(base_output_folder, "raw_binary_masks")
    contours_folder = os.path.join(base_output_folder, "raw_contour_overlays")

    for folder in [segmented_folder, masks_folder, contours_folder]:
        os.makedirs(folder, exist_ok=True)

    detection_summary = []

    for filename, masks, boxes, scores in results:
        original_path = os.path.join(source_folder, filename)
        
        try:
            original_pil = Image.open(original_path).convert("RGBA")
            original_cv2 = cv2.cvtColor(np.array(original_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Could not load image {filename}: {e}")
            continue
        
        saved_count = 0
        base_name = os.path.splitext(filename)[0]

        # NOTE: No threshold check here. The processor already filtered low scores.
        for i, score in enumerate(scores):
            
            saved_count += 1
            unique_suffix = f"{base_name}_obj_{saved_count}"

            # --- Process Mask ---
            mask_array = masks[i]
            if mask_array.ndim == 3: mask_array = mask_array.squeeze()
            mask_uint8 = (mask_array > 0).astype(np.uint8) * 255
            
            # Resize mask to match original image dimensions
            if (mask_uint8.shape[1], mask_uint8.shape[0]) != original_pil.size:
                mask_uint8 = cv2.resize(mask_uint8, original_pil.size, interpolation=cv2.INTER_NEAREST)
            
            # Fixed DeprecationWarning: mode='L' is auto-inferred for uint8
            mask_image = Image.fromarray(mask_uint8)

            # --- Save Outputs ---
            mask_image.save(os.path.join(masks_folder, f"{unique_suffix}_mask.png"))

            segmented_image = Image.new("RGBA", original_pil.size, (0, 0, 0, 0))
            segmented_image.paste(original_pil, (0, 0), mask=mask_image)
            
            crop_box = mask_image.getbbox()
            if crop_box:
                segmented_image.crop(crop_box).save(os.path.join(segmented_folder, f"{unique_suffix}_cutout.png"))

            contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            overlay_img = original_cv2.copy()
            cv2.drawContours(overlay_img, contours, -1, (0, 255, 0), 2)
            cv2.imwrite(os.path.join(contours_folder, f"{unique_suffix}_contour.jpg"), overlay_img)

        detection_summary.append({
            "image_name": filename,
            "objects_detected": saved_count
        })
        print(f"Saved outputs for: {filename} | Objects: {saved_count}")

    df = pd.DataFrame(detection_summary)
    csv_path = os.path.join(base_output_folder, "detection_summary.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nCSV summary saved to: {csv_path}")

# ---------- Main Execution ---------- 
results = predict_image_from_folder(input_folder_path, sam_word_prompt)
save_segmented_objects(results, input_folder_path, sam_output_folder_path)