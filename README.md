# SeniorProject

## Dual-Tone SDR Sync & Calibration System

This project is designed to synchronize multiple LimeSDR-powered nodes using BPSK and dual-tone signaling over RF. It establishes a reliable communication link between a Ground Station, Master Node, and multiple Slave Nodes for frequency offset measurement and calibration.

The system runs on Raspberry Pis each connected to a LimeSDR, and leverages GNU Radio for signal processing.

---

## 🛠️ Requirements

### 🧩 Software
- **DragonOS Pi64** (recommended OS; includes GNU Radio and other necessary libraries)    
  Download: https://sourceforge.net/projects/dragonos-pi64/
- Python 3.x
- ZMQ, NumPy, SciPy
- *[Add more software dependencies here]*

### 🔩 Hardware
- 4x Raspberry Pi 5   
- 4x LimeSDR Mini 2.0
- 4x External Power Bank
- 4x USB-C cables, 4x USB-A male to USB-A female   
- *[Add additional hardware here]*

---

## 📦 Setting Up DragonOS

1. Download DragonOS Pi64 image:  
   https://sourceforge.net/projects/dragonos-pi64/

2. Flash it to a microSD card using [Raspberry Pi Imager](https://www.raspberrypi.com/software/)   

3. Boot the Raspberry Pi with the flashed SD card.

4. Log in using default username and password. For DragonOS, the default username is 'ubuntu' and default password is 'dragon'.
Most SDR tools (GNU Radio, GQRX, etc.) are already pre-installed.

---

## 📥 Getting the Project Files

Clone this repository to your local machine:

```bash
cd ~/Documents
mkdir -p "Senior Project/Communication Protocol"
cd "Senior Project/Communication Protocol"   
git clone https://github.com/BenDuval/SeniorProject.git   
cd SeniorProject   
```

---
## ▶️ Running the System

Before running the full protocol, perform an initial setup test to ensure your nodes are functioning properly.   

### 🔌 LimeSDR Detection Test   
Make sure your LimeSDR Mini 2.0 is powered on. Then run the following command on each Raspberry Pi:    

```bash
LimeUtil --find
```

You should see an output indicating that the LimeSDR was detected. If not, check power and USB connection.   

### 🔧 Initial Node Test   
1. Boot into DragonOS on each node device.
2. Ensure the LimeSDR is powered on and recognized (see above).
3. Navigate to the cloned project folder:
```bash
cd ~/Documents/Senior\ Project/Communication\ Protocol/SeniorProject
```
### 🖥️ Node Script Naming

Each node already has a dedicated script in the repository:

- `node1.py` — for the device acting as Node1  
- `node2.py` — for the device acting as Node2  
- `node3.py` — for the device acting as Node3  

There is no need to rename any files — simply run the correct script on each respective device.

Then run the script like this:   

```bash
python3 node1.py
```
Make sure the identifier inside the script matches the role. You’ll find it near the bottom of each node script:   
```bash
self.identifier = "Node1"  # or "Node2", "Node3"
```
---

## 🧩 System Layout

The system uses three types of nodes:

- **Ground**: Sends Master assignment via BPSK.
- **Master**: Sends commands and performs two-tone offset measurements.
- **Slave**: Echoes dual-tone signals and confirms participation.

Each node communicates using RF at XXX MHz (TX) and XXX MHz (RX), and coordination is handled using ZMQ signaling between scripts.


## 🚀 Full System Operation (Coming Soon)

Once all nodes are running and idle, Ground can initiate the first Master assignment using BPSK. This begins the round of master-slave interactions and data collection. See `become_master()` in the source for details.

