# SeniorProject

# Dual-Tone SDR Sync & Calibration System

This project is designed to synchronize multiple LimeSDR-powered nodes using BPSK and dual-tone signaling over RF. It establishes a reliable communication pipeline between a Ground Station, Master Node, and multiple Slave Nodes for frequency offset measurement and calibration.

The system runs on Raspberry Pis (or similar SBCs), each connected to a LimeSDR, and leverages GNU Radio for signal processing.

## Requirements

- Raspberry Pi OS (Debian-based)
- GNU Radio (3.10+ recommended)
- Python 3.x
- ZMQ, NumPy, SciPy

### Installing GNU Radio
Follow the official installation guide:
https://wiki.gnuradio.org/index.php/InstallingGR

Or use apt:
```bash
sudo apt update
sudo apt install gnuradio



---

### 🔧 **3. Cloning the Project**
Tell them how to get your files onto their Pi.

```markdown
## Getting the Project Files

Clone this repository to your local machine:

```bash
git clone https://github.com/your-username/senior-project.git
cd senior-project
