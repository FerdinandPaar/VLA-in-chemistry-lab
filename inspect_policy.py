import sys
import os
import torch
import inspect

# Setup Path
sys.path.append(os.path.expanduser("~/lerobot/src"))

try:
    from lerobot.policies.act.modeling_act import ACTPolicy
except ImportError:
    print("Could not import ACTPolicy")
    sys.exit(1)

def main():
    print("--- INSPECTING ACT POLICY API ---")
    # Load model (using your path)
    local_path = os.path.expanduser("~/outputs/train/policy_so101_50_blue_block_a100/checkpoints/last/pretrained_model")
    
    try:
        policy = ACTPolicy.from_pretrained(local_path)
        print("Model Loaded.")
        
        # 1. Check for Normalization Methods
        print("\n[1] Looking for 'normalize' methods:")
        for attr in dir(policy):
            if "normalize" in attr:
                print(f" - policy.{attr}")
                
        # 2. Check source of select_action to see what it calls
        print("\n[2] Source code of 'select_action':")
        try:
            src = inspect.getsource(policy.select_action)
            print(src)
        except Exception as e:
            print(f"Could not get source: {e}")

    except Exception as e:
        print(f"Error loading model: {e}")

if __name__ == "__main__":
    main()
