#!/bin/bash

# =============================================================================
# SmolVLA Environment Creation Script (Gridnode016 Compatible)
# =============================================================================
# This script creates a robust Conda environment for LeRobot/SmolVLA training.
# It incorporates fixes for:
# - GLIBC/libstdc++ compatibility
# - PyArrow/Pandas ABI mismatches (OSError: Repetition level histogram size mismatch)
# - Rerun SDK version conflicts
# - Build failures for 'av' and 'mujoco'
# =============================================================================

# Configuration
ENV_NAME="smolvla_env_final"
ENV_PATH="/tmp/$USER/$ENV_NAME"

# 1. Load Conda
echo ">>> Loading Conda..."
source ~/miniconda3/etc/profile.d/conda.sh

# 2. Create Environment
if [ -d "$ENV_PATH" ]; then
    echo ">>> Environment $ENV_PATH already exists. Skipping creation."
else
    echo ">>> Creating environment in $ENV_PATH..."
    conda create -y -p "$ENV_PATH" python=3.10
fi

# 3. Activate Environment
echo ">>> Activating environment..."
conda activate "$ENV_PATH"

# 4. Install Conda Dependencies (Binary Compatibility Layer)
# We use conda-forge for system libraries and difficult-to-build packages.
# - pyarrow=17.0.0: Critical fix for ABI mismatch with Pandas on this OS.
# - rerun-sdk=0.26.0: Required by LeRobot (newer versions conflict).
# - libstdcxx-ng: Fixes "version GLIBCXX_3.4.29 not found".
echo ">>> Installing Conda dependencies..."
conda install -y -c conda-forge \
    ffmpeg av \
    pyarrow=17.0.0 pandas datasets \
    git-lfs cmake compilers libstdcxx-ng pkg-config cython h5py mujoco libiconv \
    rerun-sdk=0.26.0

# 5. Install PyTorch (Pip)
# Newer LeRobot requires recent Torch versions.
echo ">>> Installing PyTorch..."
pip install "torch>=2.5.0" "torchvision>=0.20.0" "accelerate"

# 6. Install LeRobot Dependencies (Pip)
# Manually installing these avoids dependency resolution hell and build failures.
echo ">>> Installing LeRobot dependencies..."
pip install \
    "diffusers>=0.30.0" \
    "draccus==0.10.0" \
    "einops>=0.8.0" \
    "wandb==0.21.4" \
    "jsonlines" \
    "pynput" \
    "pyserial" \
    "termcolor" \
    "hf_transfer" \
    "deepdiff"

# 7. Install LeRobot (Editable Mode)
# We install in editable mode without dependencies to use the local code
# but rely on our carefully constructed environment.
echo ">>> Installing LeRobot in editable mode..."
if [ -d "src/lerobot" ]; then
    pip install -e . --no-deps
else
    echo "WARNING: Not in lerobot root directory. Skipping 'pip install -e .'"
fi

# 8. Final Configuration Hints
echo "============================================================================="
echo "Environment created successfully at: $ENV_PATH"
echo ""
echo "To use this environment:"
echo "  source ~/miniconda3/etc/profile.d/conda.sh"
echo "  conda activate $ENV_PATH"
echo ""
echo "GLIBC Fix (Run this before training):"
echo "  export LD_LIBRARY_PATH=\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH"
echo "============================================================================="
