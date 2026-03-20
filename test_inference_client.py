import zmq
import numpy as np
import pickle
import time
import cv2

# Configuration
ZMQ_SERVER = "tcp://localhost:5555"

def main():
    print(f"Connecting to Inference Server at {ZMQ_SERVER}...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ZMQ_SERVER)
    print("ZMQ Connected!")

    # Create dummy data
    # Image: Black 224x224 image
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    ret, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_bytes = buf.tobytes()

    # State: Dummy joint positions (assuming 6 DOFs for SO-100)
    state = np.zeros(6, dtype=np.float32)

    prompt = "pick up the blue block"

    payload = {
        "image_front": img_bytes, # Assuming key name, might need adjustment based on policy
        "state": state,
        "prompt": prompt
    }

    print(f"Sending payload with prompt: '{prompt}'")
    socket.send(pickle.dumps(payload))
    
    print("Waiting for response...")
    response_bytes = socket.recv()
    response = pickle.loads(response_bytes)
    
    if "error" in response:
        print(f"Server Error: {response['error']}")
    else:
        print(f"Received Action: {response['action']}")
        print("Test PASSED")

    socket.close()
    context.term()

if __name__ == "__main__":
    main()
