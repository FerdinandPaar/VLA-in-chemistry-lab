# Policy Documentation: `mundgelenk/policy_so101_50_blue_block_a100`

## 1. Overview
*   **Model Name:** `policy_so101_50_blue_block_a100`
*   **Type:** ACT Policy
*   **Dataset:** `mundgelenk/so101_50_blue_block` (Revision `v3.0`)
*   **Training Hardware:** A100 GPU (on `gridnode016`)
*   **Hugging Face Repo:** [mundgelenk/policy_so101_50_blue_block_a100](https://huggingface.co/mundgelenk/policy_so101_50_blue_block_a100)
*   **WandB Run:** [View Logs](https://wandb.ai/ferdinand-paar-fp-max-planck-institute-for-psycholinguistics/lerobot-act/runs/ju6ky2yq)

---

## 2. Environment Setup
The training environment was created on `gridnode016` using a robust shell script (`train_policy_a100.sh`).

**Location:** `/tmp/$USER/smolvla_env_final` (created in `/tmp` to avoid home directory `noexec` restrictions).
**Python Version:** `3.10`

### Dependencies
1.  **Conda (conda-forge):**
    *   `python=3.10`
    *   Core: `ffmpeg`, `av`, `pyarrow=17.0.0`, `pandas`, `datasets`, `git-lfs`, `cmake`, `compilers`, `libstdcxx-ng`
    *   Sim/Vis: `mujoco`, `rerun-sdk=0.26` (Fixed version for compatibility)
    *   Util: `pkg-config`, `cython`, `h5py`, `libiconv`

2.  **Pip (PyTorch):**
    *   `torch>=2.5.0`, `torchvision>=0.20.0`, `accelerate`

3.  **Pip (LeRobot Extras):**
    *   `diffusers>=0.30.0`
    *   `draccus==0.10.0`
    *   `einops>=0.8.0`
    *   `wandb==0.21.4`
    *   `jsonlines`, `pyserial`, `termcolor`, `hf_transfer`, `deepdiff`
    *   **Crucial Additions:** `imageio`, `gymnasium` (Added to fix `ModuleNotFoundError`)
    *   **Removals:** `pynput` / `evdev` (Removed to avoid compilation errors on cluster kernel)

4.  **LeRobot:**
    *   Installed in editable mode from `~/lerobot` (`pip install -e . --no-deps`).

---

## 3. Training Command
The training was launched using the following command structure via `lerobot_train.py`:

```bash
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
```

### Execution Method
The script was executed on the cluster via:
```bash
qrsh -q mld.q@gridnode016 -now n 'bash ~/train_policy_a100.sh'
```

---

## 4. Authentication (HF & WandB)
Authentication was handled by exporting environment variables within the `train_policy_a100.sh` script before the training command.

*   **WandB:**
    ```bash
    export WANDB_API_KEY="<YOUR_KEY>"
    ```
    This enabled logging to the `lerobot-act` project.

*   **Hugging Face:**
    ```bash
    export HF_TOKEN="<YOUR_TOKEN>"
    ```
    This was injected **after** the initial training to enable the `push_to_hub` functionality.
    *   *Note:* The initial training run completed successfully but failed to push. A separate script `upload_policy_a100.sh` was used to manually upload the output directory using the token.

---

## 5. Inference via Cluster
Inference is run using `inference_server.py` on the cluster, which communicates with a local client via ZeroMQ.

### Key Configuration
Because the model resides in a local output directory (with full training history) rather than purely as a cached hub download, the inference script was modified to point to the specific checkpoint:

*   **Script:** `inference_server.py`
*   **Model Path:**
    ```python
    # Points to the 'pretrained_model' subdir of the last checkpoint
    pretrained_path = os.path.expanduser("~/outputs/train/policy_so101_50_blue_block_a100/checkpoints/last/pretrained_model")
    policy = ACTPolicy.from_pretrained(pretrained_path)
    ```

### How to Run
1.  **On the Cluster:**
    ```bash
    # Ensure you are on the node (e.g., via qrsh or ssh)
    conda activate /tmp/$USER/smolvla_env_final
    python inference_server.py
    ```
    (This starts the ZMQ server on port 5555).

2.  **On Local Client (MacBook):**
    Run your corresponding client script to send observations (images/state) and receive actions.
