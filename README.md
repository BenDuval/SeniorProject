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
- 4x Raspberry Pi 4 (or better)
- 4x LimeSDR Mini 2.0
- *[Add additional hardware here]*

---

## 📦 Setting Up DragonOS

1. Download DragonOS Pi64 image:  
   https://sourceforge.net/projects/dragonos-pi64/

2. Flash it to a microSD card using [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or [balenaEtcher](https://www.balena.io/etcher/)

3. Boot the Raspberry Pi with the flashed SD card.

4. Log in using default username and password. Most SDR tools (GNU Radio, GQRX, etc.) are already pre-installed.

---

## 📥 Getting the Project Files

Clone this repository to your local machine:

```bash
git clone https://github.com/your-username/senior-project.git
cd senior-project
```

---

## ▶️ Running the System

1. Boot up Raspberry Pi with LimeSDR attached.
2. Ensure DragonOS is running and GNU Radio is working.
3. Navigate to `ground_station/` to start the Ground node:

```bash
python3 main.py
```

---

## 🧩 System Layout

The system uses three types of nodes:

- **Ground**: Sends Master assignment via BPSK.
- **Master**: Sends commands and performs two-tone offset measurements.
- **Slave**: Echoes dual-tone signals and confirms participation.

Each node communicates using RF at 430 MHz (TX) and 435 MHz (RX), and coordination is handled using ZMQ signaling between scripts.



