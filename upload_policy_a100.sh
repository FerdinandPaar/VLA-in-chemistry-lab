#!/bin/bash
set -e

# --- Configuration ---
export HF_TOKEN="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"
export ENV_PATH="/tmp/$USER/smolvla_env_final"
export OUTPUT_DIR="$HOME/outputs/train/policy_so101_50_blue_block_a100"
export REPO_ID="mundgelenk/policy_so101_50_blue_block_a100"

echo "Using HF Token: ${HF_TOKEN:0:5}..."

# --- Activate Environment ---
source ~/miniconda3/etc/profile.d/conda.sh
if [ -d "$ENV_PATH" ]; then
    echo "Activating existing environment at $ENV_PATH..."
    conda activate "$ENV_PATH"
else
    echo "Error: Environment $ENV_PATH not found! Please re-run training setup."
    exit 1
fi

# --- Upload Logic ---
echo "Starting upload from $OUTPUT_DIR to $REPO_ID..."

python -c "
from huggingface_hub import HfApi
import os

api = HfApi()
repo_id = '$REPO_ID'
folder_path = '$OUTPUT_DIR'

print(f'Creating/Verifying repo: {repo_id}')
api.create_repo(repo_id=repo_id, exist_ok=True, repo_type='model')

print(f'Uploading folder: {folder_path}')
api.upload_folder(
    folder_path=folder_path,
    repo_id=repo_id,
    repo_type='model',
    ignore_patterns=['wandb/*']
)
print('Upload complete!')
"
