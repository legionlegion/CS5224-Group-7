# Machine Learning Code Folder

This folder contains scripts and experiment artifacts for a recyclable-item detection workflow using:

- SAM3 (Segment Anything Model 3) for prompt-based segmentation and auto-generated bounding boxes
- YOLO11 variants for object detection training and evaluation

## Folder Contents

- `1. Sam script - checkpoints download.py`
- `2. Sam script - single item recyclable.py`
- `3. Sam script - bins and recyclable.py`
- `4. Yolo script - model training (iphone).ipynb`
- `Image augmentation.ipynb`
- `Renaming_images.ipynb`
- `config.json`
- `sam3.pt`
- `yolo11l_iphone/` (YOLO training run outputs)

## What Each Script Does

### 1) Checkpoint setup

`1. Sam script - checkpoints download.py`

- Verifies SAM3 model files are available in this folder
- Downloads `config.json` and `sam3.pt` from Hugging Face repo `facebook/sam3` if missing
- Builds the SAM3 image model and processor to confirm setup works

### 2) Single recyclable item detection

`2. Sam script - single item recyclable.py`

- Runs SAM3 on a folder of images
- Uses a text prompt (`--word-prompt`) to segment a target item
- Converts mask to bounding box and saves:
  - bbox image (`*_bbox.jpg`)
  - YOLO label file (`*.txt`)
  - mask+bbox overlay image (`*_mask_bbox_overlay.jpg`)
- Writes `detection_summary.csv`

Default class mapping used for YOLO labels:

- 0: blue bins
- 1: metal can
- 2: newspaper
- 3: plastic bag
- 4: plastic bottle
- 5: cardboard

### 3) Add blue-bin labels on top of existing labels

`3. Sam script - bins and recyclable.py`

- Expects existing YOLO label files (typically from script 2)
- Detects `blue bins` with SAM3
- Appends a blue-bin YOLO line to existing label files when found
- Generates two-object overlay images showing recyclable item + blue bin
- Writes `detection_summary.csv` with status per image

## Notebook Workflow

`4. Yolo script - model training (iphone).ipynb`

The notebook is organized as a full end-to-end pipeline with section headers.

### 1) Import core utilities

- Imports shared packages used across data checks, dataset build, training, and inference.

### 2) Define classes and locate data root

- Defines class-to-ID mapping used for YOLO labels.
- Locates `Data/Iphone` from the current working directory.

### 3) Audit labels from SAM3 outputs

- Reads all `.txt` labels from:
  - `Data/Iphone/Sam3 Metal can output/bbox`
  - `Data/Iphone/Sam3 Newspaper output/bbox`
  - `Data/Iphone/Sam3 Plastic bag output/bbox`
  - `Data/Iphone/Sam3 Plastic bottle output/bbox`
- Parses YOLO rows (`class_id x_center y_center width height`) and prints class totals mapped to object names.

### 4) Build unified YOLO dataset

- Copies valid image/label pairs into `Data/Iphone/yolo_iphone_dataset/images` and `.../labels`.
- Cleans previous files for deterministic reruns.

### 5) Balance recyclable classes with augmentation

- Uses Albumentations transforms to increase recyclable classes toward target count.
- Preserves YOLO bbox format and writes augmented image/label pairs.

### 6) Split and train YOLO

- Creates train/val/test splits under `yolo_iphone_dataset/split`.
- Writes `iphone_dataset.yaml`.
- Trains YOLO with epoch-duration logging.

### 7) Summarize class counts in unified labels folder

- Reads all `.txt` files in `Data/Iphone/yolo_iphone_dataset/labels`.
- Prints total counts per class (mapped to object names).

### 8) Validation inference overlays

- Runs the trained model on validation images and saves predicted overlays.

### 9) OOS inference overlays

- Runs the trained model on out-of-sample images and saves predicted overlays.

## YOLO Training Artifacts

`yolo11l_iphone/` appears to be a completed training run and includes:

- `weights/best.pt`, `weights/last.pt`
- training curves and confusion matrices
- `results.csv` and `results.png`
- train/validation batch visualizations

From `yolo11l_iphone/args.yaml`:

- model: `yolo11l.pt`
- mode: `train`
- task: `detect`
- epochs: `100`
- batch: `16`
- image size: `640`

## Notes

- Script 2 infers class ID from the parent folder name of each image; ensure folder names match the class mapping keys exactly (case-insensitive).
- Script 3 expects existing label files in `<output-base-folder>/bbox`.
- If CUDA is available, both scripts use GPU automatically.
- Python dependencies are tracked in `requirements.txt`.
