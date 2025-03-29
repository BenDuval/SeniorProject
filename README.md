# SeniorProject

## Dual-Tone SDR Sync & Calibration System

This project is designed to synchronize multiple LimeSDR-powered nodes using BPSK and dual-tone signaling over RF. It establishes a reliable communication pipeline between a Ground Station, Master Node, and multiple Slave Nodes for frequency offset measurement and calibration.

The system runs on Raspberry Pis (or similar SBCs), each connected to a LimeSDR, and leverages GNU Radio for signal processing.

---

## 🛠️ Requirements

### 🧩 Software
- Raspberry Pi OS (Debian-based)
- GNU Radio (3.10+ recommended)
- Python 3.x
- ZMQ, NumPy, SciPy
- *[Add more software dependencies here]*

### 🔩 Hardware
- 4x Raspberry Pi 4 (or better)
- 4x LimeSDR Mini 2.0
- *[Add additional hardware here]*

---

## 📦 Installing GNU Radio

Follow the official installation guide: [GNU Radio Install Guide](https://wiki.gnuradio.org/index.php/InstallingGR)

Or use apt:

```bash
sudo apt update
sudo apt install gnuradio
```

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
2. Ensure GNU Radio is installed and working.
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


