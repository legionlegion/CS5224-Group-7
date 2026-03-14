import sys
import os
import torch
from huggingface_hub import hf_hub_download

# --- 1. SETUP PATHS ---
current_script_folder = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_folder, ".."))
model_path = os.path.join(project_root, "Segment-Anything Model 3")

if model_path not in sys.path:
    sys.path.append(model_path)

from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor
print("Successfully imported SAM3 modules.")

def download_ckpt_from_hf():
    SAM3_MODEL_ID = "facebook/sam3"
    SAM3_CKPT_NAME = "sam3.pt"
    SAM3_CFG_NAME = "config.json"
    
    target_folder = os.path.dirname(os.path.abspath(__file__))
    final_checkpoint_path = os.path.join(target_folder, SAM3_CKPT_NAME)
    
    if os.path.exists(final_checkpoint_path):
        print(f"Model found at: {final_checkpoint_path}")
        return final_checkpoint_path
    
    print(f"Downloading model to: {target_folder} ...")
    hf_hub_download(repo_id=SAM3_MODEL_ID, filename=SAM3_CFG_NAME, local_dir=target_folder)
    checkpoint_path = hf_hub_download(repo_id=SAM3_MODEL_ID, filename=SAM3_CKPT_NAME, local_dir=target_folder)
    
    return checkpoint_path

ckpt_path = download_ckpt_from_hf()
print("Checkpoint ready.")

model = build_sam3_image_model(
    checkpoint_path=ckpt_path,
    device="cuda" if torch.cuda.is_available() else "cpu"
)
print("SAM Model built successfully.")

processor = Sam3Processor(model)
print("SAM Processor initialised successfully.")
