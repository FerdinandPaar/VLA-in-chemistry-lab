### Metadata
- **Author**: Ferdinand Paar
- **Daily Note Link / Date**: [[2026-04-19]]
- **Tags**: #Ai #robotics 
- **Related**: [[SO-101 training]], [[Capita Selecta]]
## Overview

## Explaination 



## VLA 

#### 1. Vision-Language-Action (VLA) Fundamentals

A VLA is a unified neural network that integrates three distinct streams of data into a single output: robotic movement.**VLA****robotic movement** Unlike older systems that used separate models for "seeing" and "deciding," a VLA processes all information simultaneously.
- **Vision:**Vision: Processes real-time camera feeds (RGB images) from the robot's workspace and wrist.
- **Language:**Language: Receives a text-based instruction (the "task name") as a conditioning signal.
- **Action:**Action: Predicts a sequence of joint positions or velocities (often called "action chunks") to complete the task.

#### 2. Task-Naming (Behavior Switching)

Many current VLAs (like SmolVLA) don't actually "read" language to understand its meaning. Instead, they use **Task-Naming** as a **categorical switch**.

- **How it Works:**How it Works: The model learns a map between a specific text string and a specific visual behavior. The text acts as a **lookup key**.
    
- **The "Switch" Concept:** If you give the model the name "pick_lego", it "switches" its internal weights to focus on block-shaped objects and grasping motions. If you change the input to "wipe_table", it ignores the blocks and activates the motor patterns for sweeping motions.
    
- **Advantages:**
    
    - **Reduced Complexity:** The model doesn't need to understand grammar or synonyms.
    - **High Reliability:** It prevents "semantic drift" where the robot gets confused by slightly different ways of saying the same thing.

#### 3. Training Multiple Tasks

To make a single SmolVLA model perform multiple distinct tasks, you must follow a specific data pipeline.

- **Data Collection:**
    - Record ~50 episodes of **Task A** using the string `task_A` as the label.
    - Record ~50 episodes of **Task B** using the string `task_B` as the label.
        
- **Dataset Mixing:** Combine these recordings into one large training set.
    
- **The Learning Process:** During training, the model is shown the video of a task and the corresponding name. It learns: _"When I see this name, I must do these specific movements with these pixels."_

#### 4. Leaing the same model more task helps the vision Backbone but hurts the Action head 

VLA models like SmolVLA, adding more tasks creates a "tug-of-war" between learning better visual features and running out of brain capacity.  
**When Performance Gets BETTER (Generalization)**  

- **Visual Shared Learning:** Every new task teaches the model more about the world. If the model learns to "see" a red block for Task A, it is already better at "seeing" that same block for Task B.  
- **Robustness:** Multi-task models are often less twitchy because they have seen a wider variety of movements and lighting conditions.  
- **Transfer Learning:** A model that knows 10 tasks often learns the 11th task much faster than a model starting from zero.  
    
**When Performance Gets WORSE (Interference)**  

- **Task Interference:** This happens when two tasks are too similar. If "pick_cup" and "move_cup" both start with the same movement, the model might get confused halfway through and do the wrong one.  
- **Capacity Limits:** A model like SmolVLA has a fixed number of parameters (450M). Eventually, the "brain" gets full. Adding Task #50 might cause the model to perform worse on Task #1 because it has to "overwrite" some of that knowledge.  
- **Data Dilution:** If you have 1,000 demos for Task A and only 10 for Task B, Task A will "bully" the model, making it perform poorly on Task B even when given the correct name.  
    

**Summary Table**  

|Factor|Effect on Performance|
|---|---|
|Vision Backbone|Gets stronger with more variety.|
|Action Head|Can get confused if tasks look identical.|
|Small Models|Hit a ceiling sooner than large models.|

>[!Highlight] 
>**Look at:** **Validation Loss**. When training your SO-101, watch if the error rate on Task A goes up while you are training Task B. If it does, you have reached the capacity limit.

### sota VLAs for our usecase 
[SmolVLA](https://huggingface.co/blog/smolvla)
**SmolVLA-450M** is our open-source, compact yet capable VLA model. It is:
- Small enough to run on CPU, train on a single consumer GPU, or even a MacBook! 
- Trained on public, community-shared robotics data
- Released with full training and inference recipes
- Can be tested and deployed on very affordable hardware (SO-100, SO-101, LeKiwi, etc.)



This is a very hard problem the VLA in a lab environment is a unsolved problem targeted by a lot of people throughout my research. Nvidia also started working on this with their own model and also created a nice report about the similar topic. 

[NVIDIA Isaac GR00T N1.7](https://github.com/NVIDIA/Isaac-GR00T)

**GR00T-N1.7 is NVIDIA’** s flagship open-reasoning VLA model designed specifically for humanoid and generalist robots. It is:  

- **A "Reasoning" VLA:** Uses a dual-system architecture (System 2 for high-level reasoning and System 1 for high-frequency motor control) to handle complex, multi-step tasks.      
- **Built for Dexterity:** Trained on over 20,000 hours of human egocentric video, enabling finger-level control and contact-rich manipulation.  
- **Cross-Embodiment Capable:** Designed to control a variety of hardware, from single-arm manipulators to 22-DoF humanoid robots like the Unitree G1.  
- **Commercially Open:** Released under the Apache 2.0 license, allowing for full commercial use and deployment across NVIDIA’s Isaac and Jetson platforms.  
- **Highly Scalable:** Unlike smaller CPU-bound models, it is optimized for NVIDIA GPUs (RTX and Jetson) to provide real-time, low-latency performance.

Nvidia Project [link](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/02-how-to-take-this-course.html?linkId=100000417984647)
Nvidia [demo](https://x.com/NVIDIARobotics/status/2044933435530035236?s=20): 

<img width="1192" height="670" alt="image" src="https://github.com/user-attachments/assets/450b3b9d-166a-4f2b-b5de-b737fbf8f35f" />




### Comparison between SmolVLA and NVIDIA Isaac GROOT N1.7

| Feature            | SmolVLA-450M                | GR00T-N1.7                              |
| ------------------ | --------------------------- | --------------------------------------- |
| Size               | ~450 Million Parameters     | ~3 Billion Parameters                   |
| Primary Goal       | Efficiency & Accessibility  | Reasoning & Humanoid Dexterity          |
| Hardware inference | CPU, MacBook, Consumer GPU  | NVIDIA GPU (RTX / Jetson / Data Center) |
| Core Strength      | Lightweight, fast inference | Complex task decomposition              |
| Data Source        | LeRobot / Community Data    | Human Video + Synthetic Data            |
this is what we went for in this project since I only have the possibility to run inference on my consumer hardware (Macbook M1 Pro 16GB unified memory) this is one of the main bottle mix of VLA the parameter size seems small compare compared to LLMs (SmolVLA :450 M, Groot :3B) but each perimeter is way heavier on the RAM than in normal LLMs that's why I in general don't like the perimeter number as a description of the model since the distillation and the quantization place a big role I think that gigabyte is the best metric, which would be 0.9 for SmolVLA and 6.0 GB for **Groot**

| Metric                | SmolVLA-450M (X)  | GR00T-N1.7 (Y)      |
| --------------------- | ----------------- | ------------------- |
| Parameter Count       | ~450 Million      | ~3 Billion          |
| Size (FP16/BF16)      | ~0.9 GB           | ~6.0 GB             |
| Size (INT4 Quantized) | ~0.25 GB          | ~1.5 GB             |
| VRAM Requirement      | ~2–4 GB (Minimum) | ~16–24 GB (Minimum) |
Robotics models (VLAs) aren't like Chatbots. If a Chatbot takes 2 seconds to reply, it’s fine. If a robot takes 2 seconds to decide not to crash into a wall, it’s a disaster.  

- **SmolVLA** targets **25Hz+** on simple hardware because it’s tiny.  
    
- **GR00T-N1.7** is much more complex (~3B parameters). On an NVIDIA **Jetson Orin** (a dedicated robot chip), it struggles to hit 5Hz without heavy optimization. On an M1 Pro, without NVIDIA's specialized "Tensor Cores" and TensorRT acceleration, the "reasoning" speed would likely be too slow to actually control a robot in real-time.  

The good thing is both models can make use of the same trainingsdata and dataset 



## Execution 

### Training 

### general information of how to collect data 


![SO-ARM101 DIY Kit & Assembled Version ...](data:image/jpeg;base64,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)

The SO-101 is an open-source, 6-axis robotic arm specifically designed for AI imitation learning. It is primarily used with the Hugging Face LeRobot library to teach robots how to perform tasks by demonstrating them.  
**Core Components**  

- **Leader Arm:** A passive, low-friction arm that you move by hand. It acts as the "remote control" to teach the robot.  
    
- **Follower Arm:** The active robot arm that mirrors the leader's movements and eventually performs tasks autonomously.  
    
- **Intelligent Servos:** Typically Feetech STS3215 serial bus servos. They include magnetic absolute encoders for high-precision position data.  
    
- **Cameras:** Usually a dual-camera setup (one stationary for the workspace and one mounted on the wrist) to provide visual context for the AI.  
    
- **Main Controller:** A computer (usually Linux) or an edge device like an NVIDIA Jetson that runs the **LeRobot** Python library.


### what data did we collect



we collected 50 episodes where we move the test tube from the small stand into the big hole. 
Given the gripper gripping the part in a scissor like action instead

<img width="914" height="880" alt="image" src="https://github.com/user-attachments/assets/28f6b16c-dd07-4b84-a300-acc82efcd651" />



difference in the training data
<img width="1002" height="752" alt="image" src="https://github.com/user-attachments/assets/b2822cc0-ef22-473b-8e15-598e394d980d" />

<img width="1002" height="752" alt="image" src="https://github.com/user-attachments/assets/3b080843-9fdd-4244-8a76-857bc8bb91f2" />

<img width="1021" height="728" alt="image" src="https://github.com/user-attachments/assets/943ff62f-82b3-49d5-9e56-bb07d4587e7b" />





as we can see by the different ways to test tube can be in the rig, there was a lot of variance and noise already in performing seemingly the same task also the dripper then had to adapt to these situations and since we're working with a  Angular Grippers trying to grip a round object that's not always in the  same position basically only give us one point where the gripper actually grips the test tube. A parallel grippers would help a lot. 



**Angular (Scissor) Grippers:** The fingers pivot around a central point, mimicking a scissor motion. These are ideal for tight spaces or when you need the fingers to completely clear the object area when opened.

**Parallel Grippers:** The fingers move along a linear path to close in parallel. These are the industry standard for picking up rectangular or cylindrical objects because the clamping force is applied evenly across the surface.

<iframe width="560" height="315" src="https://www.youtube.com/embed/45ClRE2oxKQ?si=p_Pm2Pe0_2PB6fY8" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

here we see a 

Here is a successful run : https://youtu.be/NdbsRoq-Wh8?si=pb2wvlJ8dbzlM_D2 

<iframe width="560" height="315" src="https://www.youtube.com/embed/NdbsRoq-Wh8?si=-ULUw-XKdd3Hmkgq" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

>[!Highlights]
> for 10 runs of this with the same light conditions as in the training and the same environment as in the training the results were 9/10 successes




Here a video of some issues with the angular gripper: https://youtube.com/shorts/hJA40Uhh7Cs?feature=share

___


#### changing the starting position 

for the yellow fealds that where not represented in the trianingsdata the acuuracy went form 9/10 to 5/10 

<img width="751" height="736" alt="image" src="https://github.com/user-attachments/assets/adb83b04-8779-4b12-b07b-2c19ff953fd1" />


Learning the model around 3-5 tasks where it would need to pick it up out of different positions out of the rag would probably help it also with picking it up out of slots in the rag which were not represented in the training data

#### changing the lighting 

was not affecting it a lot as long as the preserved vision was still good if you would look at the camera feed. If it would be too much or too little lighting, that would also make the data collection via the camera feed difficult, that would then also influence the inference run.

#### Changing camera position 

After making all of the analysis I wanted to do I wanted to play with the top view camera position that completely broke the model even though I only moved it very very slightly. So before recording episodes, it should be considered to have a way to really fix the camera into position. 

<img width="1002" height="1302" alt="image" src="https://github.com/user-attachments/assets/b9b0bffd-ce88-4cde-81f9-dab8eaf65aad" />




### Training data collection with smolVLA 

```bash 
cd lerobot && conda activate lerobot
```


Test the robot connection by using teleport

```bash

lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5A7C1223701 \
  --robot.id=ferdis_awesome_follower_arm \
  --robot.cameras='{"front": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30,"rotation":0}, "side": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30,"rotation":0}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5A7C1184361 \
  --teleop.id=ferdis_awesome_leader_arm \
  --display_data=true
```

 in the teleport, we can nicely observe the lighting of the environment and we should be able to operate the robot by only looking at the camera since the VLA (Vision Language Action Model ) will later learn on this camera data so if we already have a hard time operating the robot via looking at the cameras, the VLA will also have it quite difficult. 

If all the lighting and the parameter settings are correct, we can start recording the episodes the current field of VLAs 

[[Hugging_Face]]

```bash 
python src/lerobot/scripts/lerobot_record.py \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5A7C1223701 \
  --robot.id=ferdis_awesome_follower_arm \
  --robot.cameras='{"front": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}, "side": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5A7C1184361 \
  --teleop.id=ferdis_awesome_leader_arm \
  --dataset.repo_id=mundgelenk/so101_50_pipe_in_hole \
  --dataset.num_episodes=50 \
  --dataset.single_task="Pipe in hole" \
  --dataset.push_to_hub=true \
  --display_data=true

```

keep in mind 

| Key             | Function      | What it does                                                                                                 | When to use it                                                                                     |
| --------------- | ------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| ➡️ Right Arrow  | Save & Next   | Successfully ends the current episode, saves the data, and preps for the next one.                           | The exact moment your robot successfully completes the task (e.g., dropping the pipe in the hole). |
| ⬅️ Left Arrow   | Scrap & Retry | Instantly deletes the current active episode and resets the timer so you can try that number again.          | If you drop the pipe, make a wrong move, or bump the camera during a take.                         |
| ⏹️ Escape [ESC] | Save & Quit   | Safely ends the entire recording session early, then packages and uploads everything you've recorded so far. | If you need to stop for the day before hitting your 50-episode target (e.g., stopping at 25).      |
to restart the training from the last episode that was recorded if something went wrong :

```bash 
python src/lerobot/scripts/lerobot_record.py \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5A7C1223701 \
  --robot.id=ferdis_awesome_follower_arm \
  --robot.cameras='{"front": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}, "side": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5A7C1184361 \
  --teleop.id=ferdis_awesome_leader_arm \
  --dataset.repo_id=mundgelenk/so101_50_pipe_in_hole \
  --dataset.num_episodes=50 \
  --dataset.single_task="Pipe in hole" \
  --dataset.push_to_hub=true \
  --display_data=true \
  --resume=true \
  --dataset.root=data/so101_50_pipe_in_hole

```

If all of the episodes are recorded, we can start training this. You can do this on your consumer hardware but I chose to do it on 4 A100 40 GB of the lab im working with. 
 to start the training we have to install lerobot on the server and connect it to the dataset thats on huggingface and think of the batch size and the epochs : 

this is the command we have to ececute on the cluster :

```bash 
cd lerobot && conda activate smolvla
```

```bash 
PYTHONPATH=src CUDA_VISIBLE_DEVICES=0 python src/lerobot/scripts/lerobot_train.py   
--policy.path=lerobot/smolvla_base   
--dataset.repo_id=mundgelenk/so101_50_pipe_in_hole   
--dataset.revision=main   
--job_name=smolvla_pipe_in_hole   
--output_dir=outputs/train/smolvla_pipe_in_hole   
--policy.repo_id=mundgelenk/smolvla_so101_pipe_in_hole   
--policy.push_to_hub=true   
--batch_size=16   
--steps=30000   
--save_freq=2500   
--wandb.enable=true   
--wandb.entity=ferdinand-paar-fp-max-planck-institute-for-psycholinguistics   --wandb.project=lerobot-smolvla   
--policy.empty_cameras=1   
--policy.use_amp=true   
--rename_map='{"observation.images.front": "observation.images.camera1", "observation.images.side": "observation.images.camera2"}'
```

[WandB](https://wandb.ai/ferdinand-paar-fp-max-planck-institute-for-psycholinguistics/lerobot-smolvla/runs/gn37arq2?nw=nwuserferdinandpaarfp)

I'm happy with the training run, looking at the loss it seems to have worked out quite well.


<img width="3300" height="1260" alt="image" src="https://github.com/user-attachments/assets/4578b887-7cd4-44be-94c9-9192072ac48b" />
<img width="3260" height="1362" alt="image" src="https://github.com/user-attachments/assets/7797811c-eb69-4a1c-a978-e1a2c89a70b9" />
<img width="3294" height="1284" alt="image" src="https://github.com/user-attachments/assets/980fb298-d6af-4ad1-92c0-496c60dbcba4" />
<img width="3282" height="1258" alt="image" src="https://github.com/user-attachments/assets/5bb1fcbb-27a7-4b76-885c-dd6db4391e1c" />


it was trained on 1 A100 40 GB

**Training Results**  
- **Loss:** Strong drop from 0.08 to 0.01. It flattened out at 30k steps.  
- **Stability:** Gradients are clean. No weird spikes.  
- **Learning Rate:** Correct warmup and decay. 
- **Hardware:** Flat 8GB memory usage. No leaks. CPU is barely working.


The model seems to be on [huggingface](https://huggingface.co/mundgelenk/smolvla_so101_pipe_in_hole). Now we have to run it in inference by running this bash command on the Macbook:

1 run: 

```bash 
# 1. Download the model locally
mkdir -p my_models
hf download mundgelenk/smolvla_so101_pipe_in_hole \
  --repo-type model \
  --local-dir my_models/smolvla_pipe_in_hole

# 2. Clean the config file
python -c 'import json; p="my_models/smolvla_pipe_in_hole/config.json"; d=json.load(open(p)); d.pop("pretrained_path", None); d.pop("rtc_config", None); json.dump(d, open(p,"w"), indent=4)'

# 3. Run Inference
python src/lerobot/scripts/lerobot_record.py \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5A7C1223701 \
  --robot.cameras='{"camera1": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}, "camera2": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' \
  --policy.path=my_models/smolvla_pipe_in_hole \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=5 \
  --dataset.repo_id=local/eval_run_$(date +%s) \
  --dataset.single_task="Pipe in hole" \
  --dataset.push_to_hub=false

```

to test the accuracy over 10 runs we can also run inference like this

```bash 
python src/lerobot/scripts/lerobot_record.py \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5A7C1223701 \
  --robot.cameras='{"camera1": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}, "camera2": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' \
  --policy.path=my_models/smolvla_pipe_in_hole \
  --dataset.num_episodes=10 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=20 \
  --dataset.repo_id=local/eval_run_$(date +%s) \
  --dataset.single_task="Pipe in hole" \
  --dataset.push_to_hub=false
```

# tuther outlook 

I think using the Nvidia model and not having to deal with the inference computer bottlenack dealing with and having a more professional setup where we can be sure that camera position lighting and objects in the environment stay consistent over trials. I think we can actually improve the performance massively and see the first glance of actual usefulness also in a lab environment so what I would do as the robotic lab would be to create a good environment of constant lighting and constant camera with around free camera angles 
