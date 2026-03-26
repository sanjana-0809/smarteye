# SmartEye – AI Surveillance System

SmartEye is an AI-powered surveillance product designed for real-time intrusion detection using edge AI. The system captures live video through a dedicated camera module, detects humans using a YOLOv8 deep learning model, and automatically sends alerts through a Telegram bot.

It features a professional web-based command center dashboard to monitor the live camera feed, system logs, alert history, and system status in real time.

The product is built to run on low-cost edge devices like Raspberry Pi, enabling real-time monitoring without relying on cloud services — making it ideal for homes, small offices, and remote locations.

> **Note:** The live demo runs on a standard webcam for demonstration purposes. The actual SmartEye product uses a custom hardware setup with its own dedicated camera module, radar motion sensor, and 3D-printed enclosure as described below.

---

##  Live Demo

🌐 [https://sanjana-0809-smarteye.hf.space](https://sanjana-0809-smarteye.hf.space)

> The deployed version uses your system webcam. The full hardware product includes a dedicated USB camera module mounted inside a custom enclosure.

---

## Features

- Real-time human detection using YOLOv8
- Edge AI inference running locally on Raspberry Pi
- Instant Telegram alerts with captured image
- Professional web command center dashboard with live feed, alert history, system logs, and status
- Live camera feed streaming
- Automatic event logging with timestamps
- Low-latency detection optimized for edge devices

---

## Hardware Product

### SmartEye Enclosure
A custom 3D-printed enclosure designed to house the SmartEye surveillance system with a front-facing camera module.

### Internal Hardware Setup
The internal hardware architecture includes:
- Raspberry Pi (Edge AI processing)
- USB Camera Module
- Arduino Nano (sensor interfacing)
- Radar Motion Sensor
- Cooling Fan
- Power and communication connections

---

## System Architecture

```
Camera Module
      ↓
Edge AI Processing (YOLOv8)
      ↓
Intrusion Detection Logic
      ↓
Alert Generation
      ↓
Telegram Notification
      ↓
Web Dashboard Monitoring
```

---

## Technologies Used

**Programming**
- Python

**AI / Computer Vision**
- YOLOv8
- OpenCV

**Backend**
- Flask

**Frontend**
- HTML / CSS / JavaScript
- IBM Plex Mono & Sans (professional command center UI)

**Hardware**
- Raspberry Pi
- Arduino Nano
- USB Camera Module
- Radar Motion Sensor

**Communication**
- Telegram Bot API

---

## Dashboard

The SmartEye dashboard is a professional dark-themed command center interface showing:
- Live camera feed with HUD overlay
- Real-time metrics (detections, alerts sent, FPS, uptime, model status)
- System status panel
- Telegram bot connection status
- Alert history feed
- Full scrollable system logs

---

## System Demonstration

### SmartEye System Mechanism
[▶ Watch Mechanism Video](#)

This video demonstrates the internal working of the SmartEye system and hardware integration.

### Live Detection Demo
[▶ Watch System Demo](#)

A real-time demonstration showing:
- Human detection
- Alert triggering
- Live monitoring dashboard

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sanjana-0809/smarteye.git
cd smarteye
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and go to:
```
http://localhost:5000
```

---

##  Important Note

The deployed web demo at the link above uses your system webcam for demonstration. The actual **SmartEye product** is a standalone physical device with its own dedicated camera module, radar sensor, and custom enclosure — designed to be installed at a fixed location and run independently on a Raspberry Pi without needing a separate computer.

---

*Built with  by Sanjana*
