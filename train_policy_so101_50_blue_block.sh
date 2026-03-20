#!/bin/bash
set -e

# --- 1. Environment Setup (Ephemeral & Robust) ---
export WANDB_API_KEY="4ae53d2dff22b35a3006642f6923e3fca2f2ccd9"
# Create environment in /tmp to avoid 'noexec' issues on home dir
export ENV_PATH="/tmp/$USER/smolvla_env_final"

# Load Conda
source ~/miniconda3/etc/profile.d/conda.sh

# Create env if it doesn't exist
if [ ! -d "$ENV_PATH" ]; then
    echo "Creating environment in $ENV_PATH..."
    conda create -y -p "$ENV_PATH" python=3.10
fi

source ~/miniconda3/etc/profile.d/conda.sh
conda activate "$ENV_PATH"

# Install critical dependencies via conda (idempotent, skips if installed)
conda install -y -c conda-forge \
    ffmpeg av pyarrow=17.0.0 pandas datasets \
    git-lfs cmake compilers libstdcxx-ng pkg-config cython h5py mujoco libiconv

# Install PyTorch and other pip deps (idempotent)
pip install "torch>=2.5.0" "torchvision>=0.20.0" "accelerate" "rerun-sdk==0.26.0"

# Install LeRobot dependencies
pip install "diffusers>=0.30.0" "draccus==0.10.0" "einops>=0.8.0" "wandb==0.21.4" \
    "jsonlines" "pynput" "pyserial" "termcolor" "hf_transfer" "deepdiff"

# Install LeRobot in editable mode
if [ -d "$HOME/lerobot" ]; then
    cd "$HOME/lerobot"
    pip install -e . --no-deps
    cd "$HOME"
else
     echo "Warning: lerobot directory not found at ~/lerobot. Cloning..."
     git clone https://github.com/huggingface/lerobot.git "$HOME/lerobot"
     cd "$HOME/lerobot"
     pip install -e . --no-deps
     cd "$HOME"
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

# --- 4. Run Training ---
echo "Starting training for policy_so101_50_blue_block..."

# Ensure we are in the lerobot repo for the script to run correctly (relative paths)
if [ -d "$HOME/lerobot" ]; then
    cd "$HOME/lerobot"
else
     echo "Error: lerobot directory not found even after setup attempt."
     exit 1
fi

python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id=mundgelenk/so101_50_blue_block \
  --policy.type=act \
  --policy.repo_id=mundgelenk/policy_so101_50_blue_block \
  --output_dir="$HOME/outputs/train/policy_so101_50_blue_block" \
  --job_name=policy_so101_50_blue_block \
  --policy.device=cuda \
  --wandb.enable=true \
  --wandb.entity=ferdinand-paar-fp-max-planck-institute-for-psycholinguistics \
  --wandb.project=lerobot-act \
  --batch_size=8 \
  --num_workers=4 \
  --save_model=true \
  --push_to_hub=true
