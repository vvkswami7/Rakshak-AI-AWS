# Sentinel-X Setup Guide

## Quick Start

### 1. Backend Setup (Python)

```bash
# Navigate to project root
cd /home/vivek/sentinel-x

# Create a copy of .env file and update with your credentials
cp .env.example .env

# Edit .env with your IBM credentials and camera URL
# CAMERA_URL=http://YOUR_IP:8080/video
# IBM_API_KEY=YOUR_IBM_KEY

# Install dependencies
pip install -r requirements.txt

# Run the backend
python main.py
```

Backend will start at: `http://localhost:8000`

### 2. Frontend Setup (React)

```bash
# In another terminal, navigate to dashboard
cd sentinel-dashboard

# Create a copy of .env file
cp .env.example .env

# Edit .env if needed (optional, defaults work for localhost)

# Install dependencies (first time only)
npm install

# Start the development server
npm start
```

Frontend will open at: `http://localhost:3000`

---

## Environment Variables

### Backend (.env in root)
- `IBM_API_KEY` - Your IBM Cloud API Key
- `CAMERA_URL` - IP Webcam stream URL (default: http://10.36.27.116:8080/video)

### Frontend (.env in sentinel-dashboard/)
- `REACT_APP_BACKEND_URL` - WebSocket URL for backend (default: ws://localhost:8000/ws)
- `REACT_APP_CAMERA_URL` - Camera stream URL (default: http://10.36.27.116:8080/video)

---

## Model Files

Models should be located in:
```
weights/
├── models/
│   ├── accident_v2.pt (custom accident detection)
│   ├── ambulance.pt
│   ├── damage.pt
│   ├── vehicle_counting.pt
│   └── yolov8n.pt (fallback)
```

---

## Dependencies Installed

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **opencv-python** - Video processing
- **ultralytics** - YOLO models
- **requests** - HTTP client
- **python-dotenv** - Environment variables

---

## Troubleshooting

### Camera Stream Not Working
- Check IP Webcam app is running on mobile device
- Verify IP address and port are correct
- Ensure both devices are on same network

### IBM Agent Not Triggering
- Verify IBM_API_KEY is correctly set in .env
- Check internet connection
- Review console logs for auth errors

### WebSocket Connection Failed
- Ensure backend is running: `python main.py`
- Check if port 8000 is available
- Verify REACT_APP_BACKEND_URL is correct

### Model File Not Found
- Ensure `weights/models/accident_v2.pt` exists
- Fallback model `yolov8n.pt` will be used if custom model missing

---

## Key Improvements Made

✅ Fixed empty requirements.txt
✅ Fixed model path (weights/models/accident_v2.pt)
✅ Made camera URL configurable via environment
✅ Optimized model loading (load once at startup)
✅ Added environment variable support (.env files)
✅ Improved error handling in React frontend
✅ Better logging for debugging
✅ Added WebSocket error handling
