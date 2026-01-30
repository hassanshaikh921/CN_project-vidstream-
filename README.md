# StreamNest 🎥💬  
**Hybrid Client-Server / P2P Video Streaming (Python, TCP Sockets, OpenCV)**

StreamNest is a real-time video streaming system built as a **Computer Networks (CS3001)** final project. It implements a **hybrid Client-Server / P2P-inspired** architecture using **Python TCP sockets** for reliable transmission and **OpenCV** for video frame processing. Users can **stream video**, **join as viewers**, **chat live**, and view **network statistics** such as FPS, latency, bandwidth, and packet loss.

---

## ✨ Key Features

- ✅ Live Video Streaming (JPEG frames in real-time)
- ✅ Multi-Viewer Support (multiple clients can join a stream)
- ✅ Live Chat for all connected clients
- ✅ Per-User Resolution Control: `360p`, `480p`, `720p`, `1080p`
- ✅ Stream Statistics (Live):
  - FPS  
  - Bandwidth  
  - Latency  
  - Packet Loss
- ✅ Sequence Numbers for ordering and packet loss detection
- ✅ Streamer Lock (only one streamer allowed at a time)
- ✅ GUI-based Login & Controls using Tkinter

---

## 🎯 Project Objectives

- Develop a hybrid P2P / Client-Server streaming model  
- Enable real-time transmission of video frames  
- Ensure reliable communication using TCP  
- Minimize latency and packet loss  
- Provide smooth playback using OpenCV  
- Support multiple viewers simultaneously  
- Allow per-user quality selection  
- Implement real-time chat among connected users  

---

## 🏗️ Architecture Overview

StreamNest uses a **hybrid Client-Server architecture**:

- **Server**
  - Manages client connections
  - Handles synchronization
  - Broadcasts video frames to viewers

- **Streamer (Client)**
  - Selects a video file (MP4 / AVI / MKV)
  - Encodes frames into JPEG
  - Sends frames to the server using TCP

- **Viewer (Client)**
  - Receives frames from server
  - Decodes and displays frames using OpenCV
  - Chooses resolution independently

### Technologies Used

- **TCP Sockets** – reliable byte-stream transmission  
- **OpenCV** – frame capture, encoding, decoding, resizing  
- **Base64 Encoding** – safe JSON-based transmission  
- **Tkinter GUI** – interface, chat, and stream controls  
- **Threading** – parallel video, networking, and UI tasks  

---

## ⚙️ How the System Works

### 1. Application Start
- User enters a username
- Chooses:
  - **Start Streaming**
  - **Join Stream**

### 2. Streamer Mode
- Selects a video file
- Frames are encoded and sent to the server
- Server broadcasts frames to all viewers
- Streamer sees live network statistics

### 3. Viewer Mode
- Joins the active stream
- Receives and displays video in real-time
- Can change resolution dynamically
- Can chat and view live statistics

---

## 📊 Network Statistics Implementation

- **FPS**: calculated every 0.5 seconds based on processed frames  
- **Latency**: timestamp-based RTT estimation (`RTT / 2`)  
- **Packet Loss**: detected via skipped sequence numbers  
- **Bandwidth**: computed using bits received per second (sliding window)

---

## 🚀 Getting Started

> Adjust filenames if your repo structure differs.

### Requirements
- Python 3.x  
- OpenCV  
- Tkinter (bundled with Python on most systems)

### Install Dependencies
```bash
pip install opencv-python

Run Server
python server.py

Run Client
python client.py

```bash
pip install opencv-python
