# 👁️ SmartEye – AI Surveillance System

> Real-time human detection and instant alerts powered by YOLOv8 edge AI

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=flat-square&logo=flask)
![Telegram](https://img.shields.io/badge/Telegram-Alerts-blue?style=flat-square&logo=telegram)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Live%20Demo-orange?style=flat-square)

---

##  Live Demo

** [ Click here for Live Demo](https://sanjana-0809-smarteyee.hf.space) **

---

SmartEye is an **AI-powered real-time surveillance system** that uses a browser camera and YOLOv8 deep learning model to detect humans in a live video feed. When a human is detected, it:

- Draws a **green bounding box** with confidence percentage around the detected person directly on the live feed
- Sends an **instant Telegram alert** with a captured snapshot
- Continues sending **repeat alerts** as long as the human remains in frame
- Automatically **re-arms** itself once the scene is clear
- Logs every event in a real-time **web dashboard**

Designed to run on low-cost edge devices like **Raspberry Pi**, making it a practical and affordable surveillance solution.

---

##  Features

| **Feature**             | **Description**                                              |
| ----------------------- | ------------------------------------------------------------ |
|  Real-time Detection  | YOLOv8 inference on every frame at 2+ FPS                    |
|  Bounding Box Overlay | Green box with confidence % drawn on live feed canvas        |
|  Alert State          | Box turns red and dashboard shows **ALERTED** when triggered |
|  Telegram Alerts      | Snapshot sent instantly on detection + repeat alerts         |
|  Live Dashboard       | FPS, uptime, detections, alerts sent — all live              |
|  System Logs          | Every event timestamped and displayed in real time           |
|  Auto Re-arm          | System resets to **ARMED** automatically when scene clears   |
|  Browser Camera       | No extra hardware needed — works with any webcam             |
|  Edge Optimized        | Runs on CPU, no GPU required                                 |


---

##  Dashboard Preview

The web dashboard shows:
- **Live Feed** with bounding box drawn directly on the browser canvas
- **Top bar** — ARMED / ALERTED status, Telegram status, live clock
- **Metrics bar** — Detections count, Alerts Sent, Live FPS, Uptime, Model status
- **System Status panel** — AI Model, Camera, Telegram, Edge Mode, Cooldown
- **Telegram Bot panel** — Chat ID, total sent, last alert time
- **Alert History** — last 8 alert/clear events
- **System Logs** — all events with timestamps

---

##  How It Works
```
1. Browser captures camera frame (320×180 JPEG) every 200ms
        ↓
2. Frame sent as base64 to Flask /process_frame endpoint
        ↓
3. YOLOv8 runs inference → returns bounding boxes + confidence scores
        ↓
4. Boxes normalized to 0–1 range and returned as JSON
        ↓
5. Browser canvas draws green box + "HUMAN XX%" label on live feed
        ↓
6. If human confirmed across multiple frames → Telegram alert sent
        ↓
7. Repeat alert sent every 8s while human remains in frame
        ↓
8. When human leaves → system auto re-arms after 3 clear frames
```

---

##  Project Structure
```
smarteye/
│
├── web_server.py       # Flask server + full frontend HTML/CSS/JS
├── detector.py         # YOLOv8 inference + detection logic + box normalization
├── config.py           # All thresholds, cooldowns, model settings
├── notifier.py         # Telegram alert sender
├── log_manager.py      # In-memory event logger
├── app.py              # Entry point
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container config for HuggingFace deployment
└── static/             # Static assets
```

---

##  Key Configuration (`config.py`)

| **Parameter**              | **Default** | **Description**                              |
| -------------------------- | ----------- | -------------------------------------------- |
| `CONF_THRESHOLD`           | 0.5         | Minimum confidence to count as detection     |
| `HUMAN_CONFIRM_COUNT`      | 2           | Consecutive detections before alert triggers |
| `ALERT_COOLDOWN`           | 8s          | Gap between repeat Telegram alerts           |
| `RESET_ON_NO_HUMAN_CHECKS` | 3           | Clear frames needed to re-arm                |
| `MIN_DETECTION_INTERVAL`   | 0.5s        | Minimum gap between inference runs           |
| `IMG_SZ`                   | 320         | YOLO inference image size                    |


---

##  Installation & Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/sanjana-0809/smarteye.git
cd smarteye
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:7860
```

### 5. Setup Telegram alerts
- Open Telegram → search `@BotFather` → send `/newbot` → copy the token
- Search `@userinfobot` → press Start → copy your Chat ID
- Paste both into the SmartEye setup screen when the app opens

---

##  Detection Logic

- Frames are sent from the browser to the backend every **200ms**
- YOLOv8 runs inference at most every **500ms** (configurable)
- A **sliding window of 2 frames** tracks detection history
- Alert triggers only when detection ratio ≥ 40% AND consecutive detections ≥ threshold
- This prevents false alerts from single-frame noise
- Box coordinates are **persisted for 8 frames** so the box doesn't flicker

---

##  Telegram Integration

Once configured with your Bot Token and Chat ID:
- **First detection** → alert sent immediately with snapshot image
- **Human still present** → repeat alert every 8 seconds
- **Scene clear** → system logs "Scene Clear. System Re-Armed."
- All alerts visible in the Alert History panel on the dashboard

---

##  Hardware (Raspberry Pi Deployment)

| **Component**       | **Purpose**                  |
| ------------------- | ---------------------------- |
| Raspberry Pi 4      | Edge AI processing           |
| USB Camera Module   | Live video capture           |
| Arduino Nano        | Sensor interfacing           |
| Radar Motion Sensor | Pre-trigger motion detection |
| Cooling Fan         | Thermal management           |


### SmartEye Enclosure
A custom 3D-printed enclosure houses all components with a front-facing camera module.

---

##  Technologies Used

- **YOLOv8** (Ultralytics) — object detection model
- **OpenCV** — image processing
- **Flask** — lightweight Python web server
- **HTML5 Canvas** — bounding box overlay on live feed
- **Telegram Bot API** — real-time alerts
- **HuggingFace Spaces** — cloud deployment

---

## 📽️ Demo Videos

- [▶ SmartEye Mechanism](https://github.com/sanjana-0809/smarteye/blob/main/SmartEye%20Mechanism.mp4) — internal working and hardware integration

---

##  Author

**Sanjana** — [github.com/sanjana-0809](https://github.com/sanjana-0809)

---

*SmartEye — because every space deserves intelligent protection.*
