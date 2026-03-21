![9B187872-BFA1-4274-B8BE-935BC5F9C27B_1_105_c](https://github.com/user-attachments/assets/12988996-2923-41d1-98bb-d9d2ec4510cb)

# VLA-Lab-Automation: Scaling Vision-Language-Action Models in Chemistry Robotics

Research and implementation of **Vision-Language-Action (VLA)** models for generalizable lab automation, developed within the context of the **Big Chemistry Robotlab (BCRL) Nijmegen**.

This repository explores the transition from rigid, coordinate-based lab robotics to adaptive, AI-driven manipulation using **SmolVLA** and the **LeRobot** ecosystem.

## 🧠 Model Hub & Datasets
Weights, policies, and training datasets for this project are hosted on Hugging Face:
👉 **[mundgelenk Hugging Face Models](https://huggingface.co/mundgelenk/models)**

**Key Assets:**
* `smolvla_so101`: Custom VLA checkpoint for the SO-101 testbed.
* `so101_multitask_v3`: Multi-task imitation learning dataset for lab-bench scenarios.
* `policy_so101_50_blue_block_a100`: Optimized policy trained on A100 clusters.

---

## 🖥️ Compute Architecture: Cluster-to-Edge Pipeline
To handle the high parameter count of modern VLA models while maintaining real-time hardware control, the project utilizes a distributed inference setup:

* **Inference Node (Cluster):** Heavy lifting is performed on a remote node equipped with **4x NVIDIA A100 (40GB)**. This allows for high-frequency token generation and deep-model processing.
* **Execution Node (Edge):** An **Apple MacBook M1 Pro** acts as the dedicated execution node. It interfaces directly with the hardware via USB/Serial, receiving high-level actions from the cluster and managing the SO-101's motor control loops.

---

## 🤖 Robotic Hardware Ecosystem
The project bridges high-fidelity desktop prototyping with industrial lab standards.

### 1. SO-101 (The Research Testbed)
A DIY/Open-source 6-DOF robotic arm used as the primary platform for experimenting with **SmolVLA**. It serves as a controlled environment to benchmark how models handle layout shifts, object rotations, and non-deterministic vial positions.

### 2. UFactory Lite 6 & Opentrons OT-2
The industrial target environment. The project aims to enable the **UFactory Lite 6** to perform complex "inner-deck" manipulation inside the **OT-2 liquid-handling robot**—tasks like picking up pipettes or microtiter plates that traditionally require brittle, hard-coded coordinates.

---

## 🔬 Motivation: Why VLA for Labs?
Traditional lab automation depends on fixed coordinates and zero tolerance for variation. If a tube is shifted by 1cm, the script fails. 

**VLA models (SmolVLA, OpenVLA)** jointly interpret visual data and natural language, offering:
* **Natural Robustness:** Adaptation to camera noise, lighting changes, and layout shifts.
* **Semantic Understanding:** The ability to follow instructions like *"Pick up the blue vial"* without needing to know its exact XYZ coordinates in advance.
* **End-to-End Control:** Integrating perception, planning, and action into a single inference pass.

---

## 📊 Methodology & Benchmarking
The research evaluates performance across three levels of environmental complexity:
1.  **Stable Layouts:** Clean, calibrated environments.
2.  **Perturbed Layouts:** Objects shifted or rotated by 1–5cm.
3.  **Randomized Layouts:** Non-deterministic placements to test visual generalization limits.

---

## 🛠️ Technical Stack
* **Frameworks:** LeRobot, Hugging Face Transformers, PyTorch.
* **VLA Models:** SmolVLA, OpenVLA.
* **Communication:** Custom Cluster-to-MacBook inference bridge.
* **Hardware Control:** SO-101 (LeRobot compliant), UFactory Python SDK, Opentrons API.

---

### **Next Step Suggestion**
Since you are now using the MacBook specifically as an **execution node**, would you like me to help you draft a **Python script for the socket-based bridge**? 

This would allow the MacBook to stream the SO-101 camera feed to the A100 cluster and receive the predicted action tokens back with minimal latency.
