# Status Report: SmolVLA Environment Setup

**Timestamp:** 2025-11-29T17:40:46+01:00
**Node:** `gridnode016`
**Conda Environment:** `/tmp/ferpaa/smolvla`

## Executive Summary
The environment setup on `gridnode016` has been challenging due to system restrictions (noexec on home), missing system libraries (`git-lfs`, `libstdc++`), and dependency conflicts (`av`, `pyarrow`, `lerobot` versions). We have successfully created the environment, installed `lerobot` and `pytorch`, but are currently blocked on verifying the `mundgelenk/so101_recordings` dataset due to a missing `meta/info.json` file and potential versioning issues.

## Timeline & Actions

### 1. Environment Creation
- **Issue:** `conda create -n smolvla` in default location failed.
  - *Error:* `Permission denied` (likely `noexec` on `/home` mount).
- **Resolution:** Created environment in `/tmp/ferpaa/smolvla`.
  - *Command:* `conda create -y -p /tmp/$USER/smolvla python=3.10 pip`

### 2. Dependency Installation
- **Issue:** `git clone` failed.
  - *Error:* `git-lfs: command not found`.
- **Resolution:** Installed `git-lfs` via conda.
- **Issue:** `pip install -e .[smolvla]` failed building wheels for `av` and `pyarrow`.
  - *Error:* Missing system libraries (`libavformat`, `cmake`).
- **Resolution:** Installed binary packages via `conda-forge`:
  - `av`, `ffmpeg`, `pyarrow`, `pandas`, `datasets`.
- **Issue:** `rerun-sdk` missing from pip.
  - **Resolution:** Installed `rerun-sdk` via conda.

### 3. PyTorch & GPU Setup
- **Action:** Verified GPU availability (`nvidia-smi` showed A100s).
- **Action:** Installed PyTorch with CUDA 12.1 support.
  - *Command:* `conda install -y pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia`

### 4. Visualization & Verification (Ongoing)
- **Issue:** `lerobot_dataset_viz.py` failed with `ModuleNotFoundError: No module named 'rerun'`.
  - *Resolution:* Installed `rerun-sdk`.
- **Issue:** `ImportError: /usr/lib64/libstdc++.so.6: version GLIBCXX_3.4.29 not found`.
  - *Cause:* System `libstdc++` is too old for conda binaries.
  - *Resolution:*
    1. Installed `libstdcxx-ng` via conda.
    2. Located `libstdc++.so.6.0.34` in conda env.
    3. Created symlink: `ln -sf $CONDA_PREFIX/lib/libstdc++.so.6.0.34 $CONDA_PREFIX/lib/libstdc++.so.6`.
    4. Exported `LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH`.
- **Issue:** `OSError: Repetition level histogram size mismatch` (Parquet error).
  - *Resolution:* Forced reinstall of `pyarrow` and `pandas` via conda.
- **Issue:** `RevisionNotFoundError` / `FileNotFoundError: meta/info.json`.
  - *Current Status:* The dataset `mundgelenk/so101_recordings` appears to be missing `meta/info.json` in the expected location.
  - *Action:* Currently inspecting repository file structure to determine correct version/tag.

## Current Environment State
- **Location:** `/tmp/ferpaa/smolvla`
- **Python:** 3.10
- **Key Packages:**
  - `lerobot`: 0.4.3 (editable)
  - `torch`: 2.6.0
  - `torchvision`: 0.21.0
  - `cuda`: 12.1
  - `rerun-sdk`: 0.26.0
  - `huggingface_hub`: 0.35.0

## Next Steps
1.  Identify the correct file structure of `mundgelenk/so101_recordings`.
2.  Create the missing git tag if necessary (as suggested by the error message).
3.  Run `lerobot_dataset_viz.py` to confirm dataset integrity.
4.  Proceed to training.
