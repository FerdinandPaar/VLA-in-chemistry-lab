import zmq
import torch
import numpy as np
import cv2
import pickle
import sys
import os

# Force add src to path
sys.path.append("/home/ferpaa/lerobot/src")
print(f"DEBUG: sys.path: {sys.path}")

try:
    import lerobot
    print(f"DEBUG: lerobot file: {lerobot.__file__}")
except ImportError as e:
    print(f"DEBUG: Could not import lerobot: {e}")

from lerobot.policies.act.modeling_act import ACTPolicy

def decode_image(img_bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Format: [C, H, W] and float 0-1
    img = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    return img

def main():
    print("Loading model: mundgelenk/policy_test...")
    # Load policy directly
    policy = ACTPolicy.from_pretrained("mundgelenk/policy_test")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    policy.to(device)
    policy.eval()
    print(f"Model loaded on {device}!")

    # Setup ZMQ
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://0.0.0.0:5555")
    print("Server listening on port 5555...")

    while True:
        try:
            # Receive message
            msg = socket.recv()
            data = pickle.loads(msg)
            
            # Prepare observation for model
            observation = {}
            
            for key, value in data.items():
                if "image" in key and isinstance(value, bytes):
                    img_tensor = decode_image(value).to(device)
                    # Add batch dimension: [1, C, H, W]
                    observation[key] = img_tensor.unsqueeze(0)
                elif "state" in key:
                    state_tensor = torch.tensor(value).float().to(device)
                    # Add batch dimension: [1, D]
                    observation[key] = state_tensor.unsqueeze(0)
            
            # Run inference
            with torch.no_grad():
                action = policy.select_action(observation)
            
            # Action is [1, D], convert to list
            action_list = action.squeeze(0).cpu().numpy().tolist()
            
            # Send reply
            socket.send(pickle.dumps({"action": action_list}))
            
        except Exception as e:
            print(f"Error: {e}")
            socket.send(pickle.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
