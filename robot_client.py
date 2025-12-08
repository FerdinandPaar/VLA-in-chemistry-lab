import zmq
import cv2
import numpy as np
import pickle
import time
from lerobot.common.robot_devices.robots.factory import make_robot
from lerobot.common.utils.utils import init_logging

# Configuration
ROBOT_TYPE = "so100"  # Change this if needed (e.g. 'koch', 'aloha')
ZMQ_SERVER = "tcp://localhost:5555"

def encode_image(img_array):
    # Encode as JPEG to save bandwidth
    ret, buf = cv2.imencode('.jpg', img_array, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes()

def main():
    init_logging()
    
    # 1. Connect to Robot
    print(f"Connecting to robot: {ROBOT_TYPE}...")
    # You might need to adjust the config path or arguments depending on your local setup
    robot = make_robot(ROBOT_TYPE)
    robot.connect()
    print("Robot connected!")

    # 2. Connect to ZMQ Server (Cluster via SSH Tunnel)
    print(f"Connecting to Inference Server at {ZMQ_SERVER}...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ZMQ_SERVER)
    print("ZMQ Connected!")

    # 3. Control Loop
    frequency = 30 # Hz
    period = 1.0 / frequency
    
    print("Starting control loop... Press Ctrl+C to stop.")
    try:
        while True:
            start_time = time.time()
            
            # Read Observation
            observation = robot.capture_observation()
            
            # Prepare data for server
            payload = {}
            for key, value in observation.items():
                if "image" in key:
                    # Assume value is [C, H, W] or [H, W, C] tensor/array
                    # LeRobot usually returns torch tensors [C, H, W] float 0-1 or int 0-255
                    # We need to convert to numpy uint8 [H, W, C] for cv2 encoding
                    
                    if hasattr(value, "cpu"): value = value.cpu().numpy()
                    
                    # If float 0-1, scale to 0-255
                    if value.dtype == np.float32 or value.dtype == np.float64:
                        if value.max() <= 1.0:
                            value = (value * 255).astype(np.uint8)
                    
                    # If [C, H, W], permute to [H, W, C]
                    if value.shape[0] == 3:
                        value = np.transpose(value, (1, 2, 0))
                        
                    # Convert RGB to BGR for OpenCV
                    value = cv2.cvtColor(value, cv2.COLOR_RGB2BGR)
                    
                    payload[key] = encode_image(value)
                elif "state" in key:
                    if hasattr(value, "cpu"): value = value.cpu().numpy()
                    payload[key] = value

            # Send to Server
            socket.send(pickle.dumps(payload))
            
            # Receive Action
            message = socket.recv()
            response = pickle.loads(message)
            
            if "error" in response:
                print(f"Server Error: {response['error']}")
                break
                
            action = response["action"]
            
            # Apply Action
            # Action is likely a list or numpy array. Robot expects tensor or array.
            robot.teleop_step(np.array(action))
            
            # Maintain Frequency
            elapsed = time.time() - start_time
            sleep_time = max(0, period - elapsed)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        robot.disconnect()
        socket.close()
        context.term()

if __name__ == "__main__":
    main()
