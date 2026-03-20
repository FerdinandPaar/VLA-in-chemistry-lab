#!/bin/bash
set -e

# --- 1. Environment Setup (Ephemeral & Robust) ---
export WANDB_API_KEY="4ae53d2dff22b35a3006642f6923e3fca2f2ccd9"
export HF_TOKEN="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"
# Create environment in /tmp to avoid 'noexec' issues on home dir
export ENV_PATH="/tmp/$USER/smolvla_env_final"

# Load Conda
source ~/miniconda3/etc/profile.d/conda.sh

# Create env (Clean start)
if [ -d "$ENV_PATH" ]; then
    echo "Removing existing environment to ensure clean setup..."
    rm -rf "$ENV_PATH"
fi

echo "Creating environment in $ENV_PATH..."
conda create -y -p "$ENV_PATH" python=3.10

# Activate
source ~/miniconda3/etc/profile.d/conda.sh
conda activate "$ENV_PATH"

# Install critical dependencies via conda (force python=3.10 to prevent upgrade)
conda install -y -c conda-forge \
    python=3.10 \
    ffmpeg av pyarrow=17.0.0 pandas datasets \
    git-lfs cmake compilers libstdcxx-ng pkg-config cython h5py mujoco libiconv \
    rerun-sdk=0.26

# Install PyTorch and other pip deps
pip install "torch>=2.5.0" "torchvision>=0.20.0" "accelerate"

# Install LeRobot dependencies
pip install "diffusers>=0.30.0" "draccus==0.10.0" "einops>=0.8.0" "wandb==0.21.4" \
    "jsonlines" "pyserial" "termcolor" "hf_transfer" "deepdiff" "imageio" "gymnasium"

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
if [ -f "$CONDA_PREFIX/lib/libstdc++.so.6" ]; then
    export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
fi

# --- 3. Configure Cache ---
export TMPDIR="/tmp/$USER.$(hostname).$$"
mkdir -p "$TMPDIR"
export HF_HOME="$TMPDIR/hf_cache"
export HF_HUB_ENABLE_HF_TRANSFER=1

# --- 4. Run Training (A100 Optimized) ---
echo "Starting training for policy_so101_50_blue_block on A100..."

# Ensure we are in the lerobot repo
cd "$HOME/lerobot"

python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id=mundgelenk/so101_50_blue_block \
  --policy.type=act \
  --output_dir="$HOME/outputs/train/policy_so101_50_blue_block_a100" \
  --job_name=so101_a100_run \
  --batch_size=64 \
  --steps=30000 \
  --save_freq=2500 \
  --eval_freq=2500 \
  --save_checkpoint=true \
  --policy.push_to_hub=true \
  --policy.repo_id=mundgelenk/policy_so101_50_blue_block_a100 \
  --num_workers=8 \
  --policy.device=cuda \
  --wandb.enable=true \
  --wandb.entity=ferdinand-paar-fp-max-planck-institute-for-psycholinguistics \
  --wandb.project=lerobot-act
