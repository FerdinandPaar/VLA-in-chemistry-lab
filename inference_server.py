import zmq
import torch
import numpy as np
import cv2
import pickle
import sys
import os

# 1. Setup Paths
sys.path.append(os.path.expanduser("~/lerobot/src"))

try:
    import lerobot
    from lerobot.policies.act.modeling_act import ACTPolicy
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import LeRobot. {e}")
    sys.exit(1)

def decode_image(img_bytes):
    """Decodes JPEG bytes to a PyTorch tensor (C,H,W) scaled 0-1."""
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    return img

def main():
    print("="*50)
    print("   INFERENCE SERVER (API Fixed + Chunking)")
    print("="*50)

    # 2. Load Model
    local_path = os.path.expanduser("~/outputs/train/policy_so101_50_blue_block_a100/checkpoints/last/pretrained_model")
    hub_id = "mundgelenk/policy_so101_50_blue_block_a100"
    
    if os.path.exists(local_path):
        load_path = local_path
        print(f"Loading LOCAL model: {load_path}")
    else:
        load_path = hub_id
        print(f"Loading HUB model: {load_path}")

    try:
        policy = ACTPolicy.from_pretrained(load_path)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        policy.to(device)
        policy.eval()
        
        # --- HOTFIX: DISABLE ENVIRONMENT STATE ---
        print("Applying Real-World Hotfix: Disabling 'observation.environment_state'...")
        if hasattr(policy.config, "use_environment_state"):
            policy.config.use_environment_state = False
        
        if "observation.environment_state" in policy.config.input_features:
            del policy.config.input_features["observation.environment_state"]
            
        print(f"SUCCESS: Model loaded on {device}")
        
    except Exception as e:
        print(f"FATAL: Failed to load model. {e}")
        return

    # 3. Start ZMQ
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://0.0.0.0:5555")
    print("\nServer listening on port 5555...")

    while True:
        try:
            # Receive
            msg = socket.recv()
            data = pickle.loads(msg)
            
            # Prepare Observation
            observation = {}
            for key, value in data.items():
                if "image" in key and isinstance(value, bytes):
                    img_tensor = decode_image(value).to(device)
                    # [C, H, W] -> [1, C, H, W]
                    observation[key] = img_tensor.unsqueeze(0)
                elif "state" in key:
                    state_tensor = torch.tensor(value).float().to(device)
                    # [D] -> [1, D]
                    observation[key] = state_tensor.unsqueeze(0)
            
            # 4. RUN INFERENCE (The Fix)
            with torch.no_grad():
                # We use the method discovered in inspect_policy.py
                # This handles normalization + inference + un-normalization internally
                # Returns [1, 100, 6]
                actions = policy.predict_action_chunk(observation)
            
            # 5. Send Chunk
            # Shape is [1, 100, 6] -> squeeze to [100, 6]
            action_chunk = actions.squeeze(0).cpu().numpy().tolist()
            
            socket.send(pickle.dumps({"action": action_chunk}))
            
        except Exception as e:
            print(f"Error processing request: {e}")
            socket.send(pickle.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()