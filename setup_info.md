# SmolVLA Implementation Plan

## Goal
Train SmolVLA on `gridnode016` and deploy for inference on Mac M1 (SO-101 setup).

## Cluster Setup (gridnode016)
**Target Node:** `gridnode016` (128 CPUs, 503GB RAM).
**Note:** Ensure you## 5. Training on Cluster (Corrected & Verified)

**Prerequisites:**
*   You are logged into the cluster (`ssh gridmaster`).
*   You have started a compute session on a GPU node (e.g., `qrsh -q mld.q@gridnode016 -l gpu=1`).

**Paste this entire block into your compute node terminal:**

```bash
# --- 1. Environment Setup (Ephemeral & Robust) ---
# Create environment in /tmp to avoid 'noexec' issues on home dir
export ENV_PATH="/tmp/$USER/smolvla_env_final"

# Load Conda
source ~/miniconda3/etc/profile.d/conda.sh

# Create env if it doesn't exist (using conda-forge for binary compatibility)
if [ ! -d "$ENV_PATH" ]; then
    echo "Creating environment in $ENV_PATH..."
    conda create -y -p "$ENV_PATH" python=3.10
    conda activate "$ENV_PATH"
    
    # Install critical dependencies via conda (specific versions for compatibility)
    # PyArrow 17.0.0 is required to avoid ABI mismatch with Pandas
    # Rerun-SDK 0.26.0 is required by LeRobot
    # libiconv is required by av/ffmpeg on this system
    conda install -y -c conda-forge \
        ffmpeg av pyarrow=17.0.0 pandas datasets \
        git-lfs cmake compilers libstdcxx-ng pkg-config cython h5py mujoco libiconv \
        rerun-sdk=0.26.0
        
    # Install PyTorch and other pip deps (newer versions required by LeRobot)
    pip install "torch>=2.5.0" "torchvision>=0.20.0" "accelerate"
    
    # Install LeRobot dependencies manually to avoid conflicts
    pip install "diffusers>=0.30.0" "draccus==0.10.0" "einops>=0.8.0" "wandb==0.21.4" \
        "jsonlines" "pynput" "pyserial" "termcolor" "hf_transfer" "deepdiff"
        
    # Install LeRobot in editable mode (using local source) without deps
    # This ensures we use the cluster's code but our controlled environment
    pip install -e . --no-deps
else
    conda activate "$ENV_PATH"
fi

# --- 2. Fix GLIBC/libstdc++ Issues ---
# Symlink the conda-provided libstdc++ to ensure compatibility
if [ -f "$CONDA_PREFIX/lib/libstdc++.so.6" ]; then
    export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
fi

# --- 3. Configure Cache (Ephemeral) ---
export TMPDIR="/tmp/$USER.$(hostname).$$"
mkdir -p "$TMPDIR"
export HF_HOME="$TMPDIR/hf_cache"
export HF_HUB_ENABLE_HF_TRANSFER=1

# --- 4. Login to Hugging Face ---
# Using the token provided for this project
huggingface-cli login --token "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" --add-to-git-credential

# --- 5. Run Training ---
echo "Starting training..."
# Note: --save_model and --push_to_hub flags are deprecated in newer LeRobot
# policy.repo_id handles the push.
python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id=mundgelenk/so101_training \
  --policy.type=act \
  --policy.repo_id=mundgelenk/so101_policy \
  --output_dir="$HOME/outputs/train/act_so101_policy" \
  --job_name=act_so101_policy \
  --policy.device=cuda \
  --wandb.enable=false \
  --batch_size=8 \
  --num_workers=4

echo "Training complete! Policy saved to mundgelenk/so101_policy"
```

## 6. Troubleshooting & Known Issues

This section documents the specific issues encountered on `gridnode016` and their resolutions.

### 1. GLIBCXX Version Not Found
*   **Error:** `ImportError: /usr/lib64/libstdc++.so.6: version 'GLIBCXX_3.4.29' not found`
*   **Cause:** The system's `libstdc++` is too old for the Conda packages.
*   **Fix:** Install `libstdcxx-ng` via Conda and force the system to use it:
    ```bash
    conda install -c conda-forge libstdcxx-ng
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
    ```

### 2. PyArrow/Pandas ABI Mismatch
*   **Error:** `OSError: Repetition level histogram size mismatch` during dataset loading.
*   **Cause:** Binary incompatibility between `pyarrow` and `pandas` (likely due to C++ ABI differences).
*   **Fix:** Downgrade `pyarrow` to version 17.0.0:
    ```bash
    conda install -c conda-forge pyarrow=17.0.0 pandas
    ```

### 3. Rerun SDK Version Conflict
*   **Error:** `pip` fails to resolve dependencies for `lerobot` because it requires `rerun-sdk>=0.24.0,<0.27.0`.
*   **Fix:** Explicitly install a compatible version via Conda:
    ```bash
    conda install -c conda-forge rerun-sdk=0.26.0
    ```

### 4. Build Failures (av, mujoco)
*   **Error:** `pip install` fails to build wheels for `av` or `mujoco` due to missing system libraries (`ffmpeg`, `libav*`).
*   **Fix:** Install these packages via Conda (which provides pre-built binaries) *before* running pip:
    ```bash
    conda install -c conda-forge ffmpeg av mujoco h5py cython pkg-config
    ```

### 5. Missing HF Transfer
*   **Error:** `ValueError: Fast download using 'hf_transfer' is enabled ... but 'hf_transfer' package is not available`.
*   **Fix:** Install the missing package:
    ```bash
    pip install hf_transfer
    ```

### 6. Missing libiconv (av/ffmpeg error)
*   **Error:** `ImportError: libiconv.so.2: cannot open shared object file: No such file or directory` (usually when importing `av`).
*   **Fix:** Install `libiconv` via Conda:
    ```bash
    conda install -c conda-forge libiconv
    ```

## 7. Model Upload & Monitoring

### Is the model done?
*   **No.** The training runs for **100,000 steps**.
*   **Current Status:** Running on `gridnode016` (Process ID `24106`).
*   **Checkpoints:** Saved every **20,000 steps**.

### How is the model uploaded?
1.  **Automatic:** The script is configured with `--push_to_hub=true`. It *should* upload checkpoints automatically every 20k steps.
2.  **Manual (Fallback):** If the automatic upload fails (e.g., due to network/timeout), you can manually push a checkpoint:
    ```bash
    # Run on gridnode016 inside the environment
    huggingface-cli upload mundgelenk/policy_test ~/outputs/train/act_policy_test/checkpoints/020000/pretrained_model .
    ```

### How to Monitor?
*   **Process Check:** `ssh gridmaster "qrsh -q mld.q@gridnode016 'ps -ef | grep lerobot'"`
*   **Hugging Face:** Check [https://huggingface.co/mundgelenk/policy_test](https://huggingface.co/mundgelenk/policy_test)

### Command (Custom Dataset: mundgelenk/so101_recordings)
**Important:** Ensure `mundgelenk/so101_recordings` is in LeRobot v2 format. You can visualize/check it with `python lerobot/scripts/visualize_dataset.py --repo-id mundgelenk/so101_recordings`.

```bash
python src/lerobot/scripts/lerobot_train.py \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=mundgelenk/so101_recordings \
  --batch_size=64 \
  --steps=20000 \
  --save_model=true \
  --push_to_hub=true \
  --hub_model_id=mundgelenk/so101_policy
```

### Command (New Dataset: mundgelenk/record-test)
If you recorded a new dataset using the command above, use this training command:

```bash
python src/lerobot/scripts/lerobot_train.py \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=mundgelenk/record-test \
  --batch_size=64 \
  --steps=20000 \
  --save_model=true \
  --push_to_hub=true \
  --hub_model_id=mundgelenk/so101_policy
```

*Note: Verify `push_to_hub` and `hub_model_id` flags in `lerobot` documentation or help output (`python lerobot/scripts/train.py --help`). If not supported directly, upload manually:*
```bash
huggingface-cli upload mundgelenk/so101_policy outputs/train/
```

## Inference (Mac M1)
Run the trained policy on your local Mac.

### 1. Setup
```bash
# Assuming conda is installed
conda create -n smolvla-mac python=3.10 -y
conda activate smolvla-mac
git clone https://github.com/huggingface/lerobot.git
cd lerobot
pip install -e ".[smolvla]"
# Install torch for MPS (Metal Performance Shaders) if not automatically picked up
pip install --pre torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/nightly/cpu
```

### 2. Inference Script
Create a script `run_inference.py`:
```python
from lerobot.common.policies.smolvla.modeling_smolvla import SmolVLAPolicy
import torch

# Load the trained policy
policy = SmolVLAPolicy.from_pretrained("mundgelenk/so101_policy")
policy.eval()

# Move to MPS device for M1 acceleration
device = torch.device("mps")
policy.to(device)

# ... Add your inference loop here (camera input -> policy -> robot action) ...
```

## Troubleshooting & Environment Checks

### 1. Verify Environment Activation
Always verify you are using the correct Python interpreter after activating the environment.
```bash
which python
python -V
python -c 'import sys; print(sys.executable)'
```
*Expected:* Path should be inside your conda env (e.g., `/home/ferpaa/miniconda3/envs/smolvla/bin/python`). If it shows `/usr/bin/python`, the env is **not** active.

### 2. Common Issues & Fixes
- **GLIBC Mismatch:** If you see `GLIBC_2.27 not found`, use a PyTorch build compatible with the node's GLIBC (e.g., via conda or specific wheels).
- **Permission Denied (Bad Interpreter):** If the env is on a `noexec` mount, recreate it in a writable/exec path (e.g., `/tmp/$USER/lerobot_hpc`) or use `python -m lerobot...`.
- **W&B 403 Error:** Specify your entity/project explicitly:
  `--wandb.entity=ferdinand-paar-fp-max-planck-institute-for-psycholinguistics --wandb.project=lerobot-act`
- **Dataset Format:** Ensure `mundgelenk/so101_recordings` has `meta/info.json` and `data/*.parquet`. If missing, export to LeRobot format and tag it (e.g., `v0.3.4`).
- **CUDA Not Found:** Verify GPU visibility:
  ```bash
  nvidia-smi
  python -c 'import torch; print(torch.cuda.is_available())'
  ```

### 3. Cluster Login & Cache
Set ephemeral cache for speed and avoid permission issues:
```bash
export TMPDIR="/tmp/$USER.$(hostname).$$"
mkdir -p "$TMPDIR"
export HF_HOME="$TMPDIR/hf_cache"
mkdir -p "$HF_HOME"
export HF_HUB_ENABLE_HF_TRANSFER=1
```

## Creating a New Dataset

If the existing dataset is corrupted or unusable, you can record a new one using your local setup (Mac M1 + SO-101).

### Prerequisites (Local Mac)
1.  Ensure `lerobot` is installed on your Mac (see "Inference Setup" section).
2.  Connect your SO-101 robot.

### Recording Command
Run the following command on your Mac:

```bash
python lerobot/scripts/lerobot_record.py \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5A7C1223701 \
  --robot.id=ferdis_awesome_follower_arm \
  --robot.cameras='{"front": {"type": "opencv", "index_or_path": 1, "width": 320, "height": 240, "fps": 30}, "side": {"type": "opencv", "index_or_path": 0, "width": 320, "height": 240, "fps": 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5A7C1184361 \
  --teleop.id=ferdis_awesome_leader_arm \
  --display_data=true \
  --dataset.repo_id=mundgelenk/record-test \
  --dataset.num_episodes=2 \
  --dataset.single_task="Grab the Blue clip and put it in the box" \
  --dataset.video=true \
  --dataset.fps=30 \
  --dataset.reset_time_s=5 \
  --dataset.num_image_writer_processes=1 \
  --dataset.num_image_writer_threads_per_camera=4
```

*   **Note:** Verify the USB ports (`/dev/tty.usbmodem...`) match your actual connections.
*   **Cameras:** Configured for dual cameras (front: index 1, side: index 0) at 320x240, 30fps.

### Uploading
The `--push-to-hub true` flag will automatically upload the dataset to Hugging Face. Ensure you are logged in (`huggingface-cli login`).

### Verifying Format & Version (On Mac)
The `lerobot_record.py` script automatically creates the dataset in the correct **LeRobot v3.0 format** (Parquet files + `meta/info.json`).

To verify it before or after uploading:
1.  **Check structure:** Ensure the output folder contains `meta/info.json` and `data/*.parquet`.
2.  **Visualize:** Run the visualization script locally:
    ```bash
    python lerobot/scripts/lerobot_dataset_viz.py --repo-id mundgelenk/record-test --episode-index 0
    ```
    *(Note: If you haven't pushed yet, use `--root path/to/local/dataset` instead of `--repo-id`)*

3.  **Versioning:** The current LeRobot version (0.4.3) expects **v3.0** datasets. If you encounter version issues, ensure your dataset is tagged `v3.0` on Hugging Face.
