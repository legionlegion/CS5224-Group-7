import sys
import os
import torch
from huggingface_hub import hf_hub_download

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SAM3_PATH = os.path.join(PROJECT_ROOT, "Segment-Anything Model 3")

if SAM3_PATH not in sys.path:
    sys.path.append(SAM3_PATH)

from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor
SAM3_MODEL_ID = "facebook/sam3"
SAM3_CKPT_NAME = "sam3.pt"
SAM3_CFG_NAME = "config.json"

def ensure_checkpoint(target_dir):
    checkpoint_path = os.path.join(target_dir, SAM3_CKPT_NAME)
    if os.path.exists(checkpoint_path):
        print(f"Model found at: {checkpoint_path}")
        return checkpoint_path

    print(f"Downloading model files to: {target_dir} ...")
    hf_hub_download(repo_id=SAM3_MODEL_ID, filename=SAM3_CFG_NAME, local_dir=target_dir)
    return hf_hub_download(repo_id=SAM3_MODEL_ID, filename=SAM3_CKPT_NAME, local_dir=target_dir)


def main():
    print("Successfully imported SAM3 modules.")
    ckpt_path = ensure_checkpoint(SCRIPT_DIR)
    print("Checkpoint ready.")

    model = build_sam3_image_model(
        checkpoint_path=ckpt_path,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    print("SAM Model built successfully.")

    processor = Sam3Processor(model)
    print("SAM Processor initialised successfully.")
    return processor


if __name__ == "__main__":
    main()
