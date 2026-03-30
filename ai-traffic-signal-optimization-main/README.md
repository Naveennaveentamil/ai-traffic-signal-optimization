# AI-Driven Adaptive Traffic Signal Optimization System

Real-time intelligent traffic management system using AI, Computer Vision, and a web dashboard.  
Features vehicle detection, adaptive signal timing, emergency vehicle prioritization, and traffic congestion prediction.

## Features

- **Vehicle detection (YOLOv8 + OpenCV)**: Detect and count vehicles per lane from a video stream.
- **Dynamic traffic signal optimization**: Rule-based + ML-enhanced signal timing based on traffic density.
- **Emergency vehicle detection**: Detect ambulances/fire trucks and create a virtual green corridor.
- **ML traffic prediction**: Predict congestion level using a scikit-learn model and dummy historical data.
- **MongoDB storage**: Persist traffic counts, signal timings, and prediction history.
- **Web dashboard**: Modern dark-theme UI showing live counts, signal state, charts, and emergency alerts.
- **4-way junction simulation**: Animated lights and live updates from backend APIs.

## Project Structure

```text
project-root
 ├── backend/
 │    ├── app.py
 │    ├── routes/
 │    │    └── traffic_routes.py
 │    ├── services/
 │    │    ├── traffic_service.py
 │    │    └── emergency_service.py
 │    ├── models/
 │    │    └── mongo_models.py
 │    └── utils/
 │         └── config.py
 ├── ai/
 │    ├── yolo_detection.py
 │    ├── traffic_model.py
 │    └── dataset/
 │         └── traffic_data.csv
 ├── frontend/
 │    ├── index.html
 │    ├── style.css
 │    └── script.js
 ├── database/
 │    └── mongo_setup.py
 ├── requirements.txt
 └── README.md
```

## Prerequisites

- **Python** 3.10+ recommended
- **MongoDB** running locally on `mongodb://localhost:27017`
  - Default database: `traffic_db`
  - Collections will be created automatically: `traffic_events`, `signal_logs`, `predictions`
- A **sample traffic video** file (e.g. `sample_traffic.mp4`)
  - Place it here: `ai/dataset/sample_traffic.mp4`

> Note: YOLOv8 (from `ultralytics`) will automatically download default weights (e.g. `yolov8n.pt`) on first run if not present.

## Setup

From the project root:

```bash
pip install -r requirements.txt
```

If you use a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Running MongoDB initialization (optional)

```bash
python database/mongo_setup.py
```

This will test the MongoDB connection and ensure required collections exist.

## Running the Backend + Frontend

From the `backend` directory:

```bash
cd backend
python app.py
```

Then open the dashboard in your browser:

- `http://127.0.0.1:5000/`

The Flask app serves the frontend directly, so you only need this one process.

## Core API Endpoints

- `POST /api/process_video`
  - Body: `{ "source": "file", "path": "../ai/dataset/sample_traffic.mp4" }`
  - Response: vehicle counts per lane and emergency detection flag.

- `GET /api/get_signal`
  - Returns current signal state and green durations for the four-way junction.

- `POST /api/emergency`
  - Body: `{ "active": true }`
  - Enables or disables emergency green-corridor mode.

- `POST /api/predict`
  - Body: optional input features; if omitted, uses last observed counts.
  - Response: congestion level (e.g. low/medium/high) and numeric score.

The frontend calls these endpoints periodically to simulate real-time updates.

## Sample Data & Models

- **Dummy dataset**: `ai/dataset/traffic_data.csv`
  - Simple synthetic data with features like hour-of-day, day-of-week, and vehicle counts.
- **ML model**: `ai/traffic_model.py`
  - Trains a small `RandomForestRegressor` or `RandomForestClassifier` on the dummy data.
  - Model is (re)trained on startup for simplicity; in a production setup you would train offline and load from disk.

## Notes and Limitations

- This project is designed as an educational prototype:
  - Uses a **single sample video** instead of multiple real CCTV feeds.
  - Lane assignment is approximated by splitting the frame into regions.
  - Emergency detection is based on YOLO class names containing `ambulance`, `fire`, or `police` where available.
- You can replace `ai/dataset/sample_traffic.mp4` with your own CCTV video; just keep the path the same or update the config.

## Extending the Project

- Plug in multiple camera sources and map them to different junctions.
- Persist YOLO detections frame-by-frame for deeper analytics.
- Train a more advanced ML model for long-term congestion prediction.
- Secure the APIs and integrate authentication.

