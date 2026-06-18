# Hardware Requirements

This course is computationally demanding, sitting at the intersection of three heavy processing workloads:
1. **Physics Simulation** (NVIDIA Isaac Sim / Gazebo)
2. **Visual Perception** (VSLAM, Depth Sensing, and Object Detection)
3. **Generative AI** (Vision-Language-Action Models & LLMs)

To successfully run the hands-on labs and the capstone project, you must choose between an **On-Premise Workstation** or a **Cloud-Native ("Ether") Lab** configuration.

---

## 1. The "Digital Twin" Workstation (On-Premise)

This is the most critical developer workstation. Standard laptops (like MacBooks or non-RTX Windows machines) will **not** work for NVIDIA Isaac Sim.

* **GPU (The Key Bottleneck):** NVIDIA RTX 4070 Ti (12GB VRAM) or higher. 
  * *Why:* You need high VRAM to load the USD (Universal Scene Description) assets for the robot and environment, while simultaneously running inference on local VLA (Vision-Language-Action) models.
  * *Recommendation:* An RTX 3090 or RTX 4090 with 24GB VRAM is ideal for complex reinforcement learning and Sim-to-Real training.
* **CPU:** Intel Core i7 (13th Gen+) or AMD Ryzen 9.
  * *Why:* Rigid body dynamics, physics solvers, and simulation loops are highly CPU-intensive.
* **RAM:** 64 GB DDR5 (32 GB is the absolute minimum, but you will experience crashes during high-fidelity scene rendering).
* **OS:** Ubuntu 22.04 LTS (Native or Dual-boot).
  * *Warning:* While NVIDIA Isaac Sim can run on Windows, ROS 2 (Humble/Iron) is native to Linux. A dedicated Linux installation ensures a friction-free development cycle.

---

## 2. The "Physical AI" Edge Kit (Desktop Setup)

Before deploying algorithms to a full-scale humanoid, students set up the "robotic nervous system" on a desk using this edge kit.

| Component | Recommended Model | Approx. Price | Function |
|---|---|---|---|
| **The Brain** | NVIDIA Jetson Orin Nano Super Dev Kit (8GB) | $249 | Industry standard for edge Embodied AI. Runs the ROS 2 inference stack. (Capable of 40 TOPS). |
| **The Eyes** | Intel RealSense D435i or D455 | $349 | Provides RGB-D (Color + Depth) visual data. The "i" version contains the IMU necessary for VSLAM. |
| **The Ears** | ReSpeaker USB Mic Array v2.0 | $69 | Far-field microphone for Voice-to-Action commands. |
| **Storage & Power**| 128GB High-Endurance MicroSD Card + Cables | $30 | Operating system boot disk and prototyping connectivity. |
| **Total** | | **~$700** | |

---

## 3. Robot Lab Deployment Options

Depending on budget and workspace constraints, three hardware tiers are supported:

### Option A: The "Proxy" Approach (Budget-Friendly)
Instead of a humanoid, you can use a quadruped (robot dog) or robotic arm. The core software principles (ROS 2, VSLAM, Isaac Sim) transfer 90% effectively.
* **Robot:** Unitree Go2 Edu (~$1,800 - $3,000)
* **Pros:** Highly durable, excellent ROS 2 support, affordable.

### Option B: The "Miniature Humanoid" Approach
* **Robot:** Unitree G1 (~$16,000) or Hiwonder TonyPi Pro (~$600)
* **Warning:** Cheap kits (like TonyPi) run on Raspberry Pi which cannot support NVIDIA Isaac ROS. They should only be used to study kinematics, with the Jetson Kit acting as the secondary brain.

### Option C: The "Premium" Humanoid Lab
* **Robot:** Unitree G1 Humanoid
* **Why:** It features a highly open SDK that allows students to inject custom ROS 2 controllers, walk dynamically, and train joints in Isaac Sim.

---

## 4. Option 2: The Cloud-Native "Ether" Lab (High OpEx)

If you do not have access to an RTX-enabled physical PC, you can configure a cloud-based GPU instance.

* **Instance Type:** AWS `g5.2xlarge` (NVIDIA A10G GPU, 24GB VRAM) or `g6e.xlarge`.
* **Software:** NVIDIA Isaac Sim on Omniverse Cloud (requires an Omniverse-compliant Amazon Machine Image).
* **Cost Structure:**
  * Instance cost: ~$1.50/hour (spot/on-demand).
  * Storage (EBS): ~$25/month.
  * Estimate per Student: **~$205 per quarter** (assuming 120 hours of usage).

### ⚠️ The Latency Trap
Directly controlling a real-world robot from a cloud server is dangerous due to network latency.
* **Solution:** Students must train models in the cloud, download the weight files, and flash them to the local **Jetson Orin Nano** for real-time edge execution.
