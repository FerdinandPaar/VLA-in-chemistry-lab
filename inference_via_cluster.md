# Remote Inference Pipeline: MacBook (Robot) <-> Cluster (Brain)

## 1. Objective
Control the SO-100 robot arm connected to a local MacBook M1 by running the heavy SmolVLA inference on the `gridnode016` cluster GPU.

## 2. Architecture
We will use a **Client-Server** model over an **SSH Tunnel**.

*   **Robot Client (MacBook):** "The Body"
    *   Handles hardware: Cameras (Input) and Motors (Output).
    *   Lightweight: No heavy computation.
    *   Sends: Images + Current Joint Positions + Text Prompt.
    *   Receives: Target Joint Positions (Action).
*   **Inference Server (Cluster):** "The Brain"
    *   Running on `gridnode016` with GPU.
    *   Loads the trained `mundgelenk/policy_test` model.
    *   Receives observations, runs forward pass, returns action.

## 3. Communication Protocol
**ZeroMQ (ZMQ)** is chosen for:
*   **Low Latency:** Faster than HTTP/REST.
*   **Simplicity:** Easy "Request-Reply" pattern.
*   **Binary Support:** Efficiently sends numpy arrays (images) via `msgpack` or `pickle`.

### Network Path
`MacBook` -> `SSH Tunnel (Local Port 5555 -> gridnode016:5555)` -> `Inference Server`

## 4. Implementation Plan

### Step 1: The Server Script (`server.py` on Cluster)
*   **Environment:** Uses `smolvla_env_final`.
*   **Logic:**
    1.  Load Model: `SmolVLAPolicy.from_pretrained("mundgelenk/policy_test")`.
    2.  Bind ZMQ Socket: `tcp://0.0.0.0:5555`.
    3.  Loop:
        *   Receive `dict(image_front, image_side, state, prompt)`.
        *   Run `policy.select_action(batch)`.
        *   Send `action`.

### Step 2: The Client Script (`client.py` on MacBook)
*   **Environment:** Local Python environment with `lerobot`, `opencv`, `zmq`.
*   **Logic:**
    1.  Connect to Robot: `LeRobotRobot(...)`.
    2.  Connect to Cameras: `opencv` or `lerobot` camera utils.
    3.  Connect ZMQ Socket: `tcp://localhost:5555`.
    4.  Loop (Control Frequency ~30-50Hz):
        *   Read Sensors.
        *   Send Data.
        *   Receive Action.
        *   `robot.teleop_step(action)`.

### Step 3: The Connection (SSH Tunnel)
Since `gridnode016` is not directly exposed to the internet, we tunnel through `gridmaster`.

```bash
# Run this on MacBook
ssh -L 5555:gridnode016:5555 gridmaster
```

## 5. Latency Optimization
*   **Image Compression:** Send JPEG compressed bytes instead of raw bitmaps to save bandwidth.
*   **Async I/O:** Overlap sending/receiving with hardware reads if possible (though synchronous is safer for control loops).

## 6. How to Run (Step-by-Step)

### A. On the Cluster (Server)
**Status:** I have already started the server for you! It is listening on port `5555`.
*   **Command (for reference):**
    ```bash
    python ~/lerobot/inference_server.py
    ```

### B. On Your MacBook (Client)
You need to run the client script locally to connect your robot to the cluster.

1.  **Open a Terminal on your Mac.**
2.  **Create the SSH Tunnel:**
    This forwards your local port 5555 to the cluster's port 5555.
    ```bash
    ssh -L 5555:gridnode016:5555 gridmaster
    ```
    *(Keep this terminal open!)*

3.  **Open a NEW Terminal on your Mac.**
4.  **Install Dependencies (if not already installed):**
    ```bash
    pip install lerobot opencv-python zmq
    ```
5.  **Run the Client Script:**
    Save the code below as `robot_client.py` and run it:
    ```bash
    python robot_client.py
    ```

### C. Client Script (`robot_client.py`)
```python
import zmq
import cv2
import numpy as np
import pickle
import time
from lerobot.common.robot_devices.robots.factory import make_robot

# Configuration
ROBOT_TYPE = "so100"  # Change to 'koch' or 'aloha' if needed
ZMQ_SERVER = "tcp://localhost:5555"

def encode_image(img_array):
    ret, buf = cv2.imencode('.jpg', img_array, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes()

def main():
    print(f"Connecting to robot: {ROBOT_TYPE}...")
    robot = make_robot(ROBOT_TYPE)
    robot.connect()
    print("Robot connected!")

    print(f"Connecting to Inference Server at {ZMQ_SERVER}...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ZMQ_SERVER)
    print("ZMQ Connected!")

    print("Starting control loop... Press Ctrl+C to stop.")
    try:
        while True:
            start_time = time.time()
            observation = robot.capture_observation()
            
            payload = {}
            for key, value in observation.items():
                if "image" in key:
                    if hasattr(value, "cpu"): value = value.cpu().numpy()
                    if value.dtype == np.float32 and value.max() <= 1.0:
                        value = (value * 255).astype(np.uint8)
                    if value.shape[0] == 3:
                        value = np.transpose(value, (1, 2, 0))
                    value = cv2.cvtColor(value, cv2.COLOR_RGB2BGR)
                    payload[key] = encode_image(value)
                elif "state" in key:
                    if hasattr(value, "cpu"): value = value.cpu().numpy()
                    payload[key] = value

            socket.send(pickle.dumps(payload))
            response = pickle.loads(socket.recv())
            
            if "error" in response:
                print(f"Server Error: {response['error']}")
                break
                
            robot.teleop_step(np.array(response["action"]))
            
            time.sleep(max(0, 1.0/30 - (time.time() - start_time)))
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        robot.disconnect()
        socket.close()
        context.term()

if __name__ == "__main__":
    main()
```
