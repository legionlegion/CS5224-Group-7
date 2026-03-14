import os
import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv

# ---------- Setup Paths ----------
load_dotenv()
current_script_folder = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_folder, ".."))

# Uses relative pathing based on project_root
category = os.getenv("CATEGORY")  # e.g., "cardboard", "glass", etc.---
raw_img_src = os.path.join(project_root, "Data", "Trashnet", category)

relative_path = os.getenv("ORIGINAL_OUTPUT_REL_PATH")
base_dir = os.path.join(project_root, relative_path)
mask_src = os.path.join(base_dir, "raw_binary_masks")

category_mapping = {"bluebins":0, "cardboard": 1, "glass": 2, "metal": 3, "paper": 4, "plastic": 5, "trash": 6}
class_label = category_mapping[category]

# Output folders
box_dir = os.path.join(base_dir, "largest_bounding_box")
overlay_dir = os.path.join(base_dir, "largest_bounding_box_raw_overlay")

for folder in [box_dir, overlay_dir]:
    os.makedirs(folder, exist_ok=True)

# ---------- Processing Logic ----------
mask_files = [f for f in os.listdir(mask_src) if f.endswith('.png')]
groups = {}
for f in mask_files:
    original_base = f.split('_obj_')[0]
    groups.setdefault(original_base, []).append(f)

print(f"Generating YOLO labels and RAW overlays for {len(groups)} images...")

for base_name, files in groups.items():
    # Identify the largest mask
    largest_filename = max([os.path.join(mask_src, f) for f in files], 
                           key=lambda x: np.sum(np.array(Image.open(x)) == 255))
    
    mask = np.array(Image.open(largest_filename))
    rows = np.any(mask == 255, axis=1)
    cols = np.any(mask == 255, axis=0)
    
    if not np.any(rows) or not np.any(cols): continue

    ymin, ymax = np.where(rows)[0][[0, -1]]
    xmin, xmax = np.where(cols)[0][[0, -1]]

    # Locate and Load the Raw Image using relative path
    raw_image = None
    for ext in ['.jpg', '.jpeg', '.png']:
        path = os.path.join(raw_img_src, base_name + ext)
        if os.path.exists(path):
            raw_image = cv2.imread(path)
            break
    
    if raw_image is not None:
        h, w = raw_image.shape[:2]
        
        # Calculate YOLO Normalized coordinates
        x_center = ((xmin + xmax) / 2.0) / w
        y_center = ((ymin + ymax) / 2.0) / h
        width = (xmax - xmin) / w
        height = (ymax - ymin) / h
        
        # Save .txt label
        with open(os.path.join(box_dir, f"{base_name}.txt"), "w") as f:
            f.write(f"{class_label} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
            
        # Draw on Raw Image
        cv2.rectangle(raw_image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 3)
        cv2.imwrite(os.path.join(overlay_dir, f"{base_name}_box_overlay.jpg"), raw_image)

print("Processing complete. Files stored in project directory.")