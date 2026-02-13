# ===================================================================================
# main.py: SENTINEL-X - IBM Hackathon Edition 🚀
# Integating Edge AI (YOLO) with IBM watsonx Orchestrate + Evidence Archiving
# ===================================================================================

import cv2
import asyncio
import uvicorn
import time
import requests
import json
import threading
import os
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from dotenv import load_dotenv
from collections import deque

# Load environment variables
load_dotenv()

# PyTorch 2.6+ compatibility fix for loading model weights
import torch
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load

# --- ⚙️ CONFIGURATION ---
# UPDATE THIS with your IP Webcam IP
MOBILE_CAMERA_URL = os.getenv("CAMERA_URL", "your-camera-url-here")

# --- 🔑 CREDENTIALS ---
# IBM Cloud API Key
IBM_API_KEY = os.getenv("IBM_API_KEY", "YOUR_IBM_API_KEY_HERE") # ✅ SAFE
IBM_INTEGRATION_ID = "your-integration-id-here"
IBM_SERVICE_INSTANCE_ID = "your-service-instance-id-here"
IBM_REGION = "your-region-here"

# Telegram Bot (From your SIH Code)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE") # ✅ SAFE
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE") # ✅ SAFE

# Location Data (Hardcoded for Demo)
CAMERA_LAT = 15.4589
CAMERA_LON = 75.0078

# --- 📂 FILE SYSTEM SETUP ---
EVIDENCE_DIR = "evidence_archive"
os.makedirs(os.path.join(EVIDENCE_DIR, "crashes"), exist_ok=True)

# --- 🆕 FEATURE 1: SEVERITY CALCULATION ---
def calculate_accident_severity(vehicle_count, confidence, labels):
    """
    Calculate accident severity: MINOR, MODERATE, or SEVERE
    
    Rules:
    - SEVERE: 3+ vehicles OR high confidence crash + multiple vehicles
    - MODERATE: 2 vehicles + crash detection
    - MINOR: 1 vehicle OR low confidence
    """
    has_crash = any(k in str(labels).lower() for k in ["crash", "accident", "severe", "collision", "damage"])
    
    if vehicle_count >= 3 or (has_crash and vehicle_count >= 2 and confidence > 0.7):
        return "SEVERE"
    elif vehicle_count == 2 and has_crash:
        return "MODERATE"
    else:
        return "MINOR"

# --- 🆕 FEATURE 2: VEHICLE TYPE CLASSIFICATION ---
VEHICLE_TYPES = {
    "car": ["car", "automobile", "vehicle"],
    "truck": ["truck", "lorry", "van"],
    "motorcycle": ["motorcycle", "motorbike", "bike", "scooter"],
    "bus": ["bus", "coach"],
    "bicycle": ["bicycle", "cycle"],
    "person": ["person", "pedestrian", "human"]
}

def classify_vehicle_type(label):
    """Classify detected object into vehicle types"""
    label_lower = label.lower()
    
    for vehicle_type, keywords in VEHICLE_TYPES.items():
        if any(k in label_lower for k in keywords):
            return vehicle_type
    return "other"

# --- 🆕 FEATURE 3: INCIDENT HEATMAP TRACKING ---
class HeatmapTracker:
    """Track incident locations for heatmap"""
    def __init__(self, max_history=100):
        self.incidents = deque(maxlen=max_history)
    
    def add_incident(self, lat, lon, severity):
        self.incidents.append({
            "lat": lat,
            "lon": lon,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_hotspots(self):
        """Return clustered incident locations"""
        if not self.incidents:
            return []
        
        hotspots = []
        for incident in self.incidents:
            hotspots.append({
                "location": [incident["lat"], incident["lon"]],
                "severity": incident["severity"],
                "time": incident["timestamp"]
            })
        return hotspots

heatmap_tracker = HeatmapTracker()

# --- 🆕 FEATURE 4: QUEUE LENGTH ESTIMATION ---
class QueueEstimator:
    """Estimate queue length and wait time"""
    
    @staticmethod
    def estimate_queue_length(vehicle_count, avg_car_length=4.5):
        """
        Calculate queue length in meters
        Average car length: 4.5m
        """
        return vehicle_count * avg_car_length
    
    @staticmethod
    def estimate_wait_time(vehicle_count, signal_cycle_time=90):
        """
        Estimate wait time in seconds
        Assumes vehicles need ~2 seconds per vehicle to clear
        """
        clearance_time_per_vehicle = 2
        estimated_wait = vehicle_count * clearance_time_per_vehicle
        
        if estimated_wait > signal_cycle_time:
            return signal_cycle_time
        return max(0, estimated_wait)

# --- 🧠 IBM CONNECTION LOGIC ---
def get_ibm_token():
    """Exchanges API Key for a Bearer Token"""
    try:
        url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={IBM_API_KEY}"
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Auth Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Auth Exception: {e}")
        return None

def trigger_ibm_agent(confidence, severity="HIGH", vehicle_count=1, location="Pune_Main_Road"):
    """
    Sends a message to your IBM Agent to trigger the accident workflow.
    Now includes severity level and vehicle count.
    """
    global last_ibm_trigger_time
    
    # 1. Check Cooldown
    if time.time() - last_ibm_trigger_time < IBM_COOLDOWN:
        return {"status": "cooldown"}

    print(f"🚀 CALLING IBM WATSONX AGENT...")

    # 2. Get Auth Token
    token = get_ibm_token()
    if not token:
        return {"status": "auth_failed"}

    # 3. Construct Message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    user_message = (
        f"REPORT ACCIDENT: I have detected a vehicle crash. "
        f"Severity: {severity}. "
        f"Vehicles Involved: {vehicle_count}. "
        f"Confidence: {confidence:.0%}. "
        f"Location: {location}. "
        f"Time: {current_time}. "
        f"Dispatching emergency services required."
    )

    # 4. Send to IBM Agent
    url = f"https://api.{IBM_REGION}.orchestrate.ibm.com/v2/assistants/{IBM_INTEGRATION_ID}/message"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": { "message_type": "text", "text": user_message },
        "context": { "integrations": { "service_instance_id": IBM_SERVICE_INSTANCE_ID } }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            agent_text = "Alert Processed"
            try:
                agent_text = response_data.get('output', {}).get('generic', [{}])[0].get('text', 'Alert Processed')
            except:
                pass
            print(f"✅ IBM AGENT RESPONDED: {agent_text}")
            last_ibm_trigger_time = time.time()
            return {"status": "triggered"}
        else:
            print(f"❌ IBM Error {response.status_code}: {response.text}")
            return {"status": "failed"}
    except Exception as e:
        print(f"⚠️ Connection Error: {e}")
        return {"status": "error"}

# --- 📸 EVIDENCE & TELEGRAM LOGIC ---
def handle_alert_background(title, message, frame_copy, severity="NONE"):
    """
    Saves image and sends to Telegram in a separate thread to avoid lag.
    Now includes severity level in the alert.
    """
    print(f"📸 [EVIDENCE] Saving proof and sending to Telegram...", flush=True)
    try:
        # 1. Save Image Locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{timestamp}_{severity}_crash.jpg"
        filepath = os.path.join(EVIDENCE_DIR, "crashes", filename)
        
        # Verify frame is valid before saving
        if frame_copy is None or frame_copy.size == 0:
            print(f"❌ Frame is invalid/empty, cannot save", flush=True)
            return
        
        success = cv2.imwrite(filepath, frame_copy)
        if success:
            file_size = os.path.getsize(filepath)
            print(f"✅ Image Saved: {filepath} ({file_size} bytes)", flush=True)
        else:
            print(f"❌ Failed to save image to {filepath}", flush=True)
            return

        # 2. Send Photo to Telegram (WITH ERROR CHECKING)
        severity_emoji = "🔴" if severity == "SEVERE" else "🟡" if severity == "MODERATE" else "🟢"
        caption = f"🚨 SENTINEL-X ALERT: {title}\n{severity_emoji} Severity: {severity}\nInfo: {message}\nTime: {timestamp}"
        url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        try:
            print(f"📤 Sending photo to Telegram...", flush=True)
            with open(filepath, "rb") as img_file:
                response = requests.post(
                    url_photo,
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                    files={"photo": img_file},
                    timeout=15
                )
                if response.status_code == 200:
                    print(f"✅ Photo sent successfully to Telegram! Message ID: {response.json().get('result', {}).get('message_id', 'N/A')}", flush=True)
                else:
                    print(f"⚠️ Photo send failed: {response.status_code}", flush=True)
                    print(f"Response: {response.text}", flush=True)
        except Exception as e:
            print(f"❌ Photo send error: {type(e).__name__}: {e}", flush=True)

        # 3. Send Location
        url_loc = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendLocation"
        try:
            print(f"📍 Sending location to Telegram...", flush=True)
            response = requests.post(
                url_loc,
                data={"chat_id": TELEGRAM_CHAT_ID, "latitude": CAMERA_LAT, "longitude": CAMERA_LON},
                timeout=15
            )
            if response.status_code == 200:
                print("✅ Location sent successfully!", flush=True)
            else:
                print(f"⚠️ Location send failed: {response.status_code}", flush=True)
        except Exception as e:
            print(f"❌ Location send error: {type(e).__name__}: {e}", flush=True)
        
        print("📨 Telegram Alert Sequence Complete!", flush=True)

    except Exception as e:
        print(f"❌ Telegram/Save Error: {type(e).__name__}: {e}", flush=True)

# --- 🚀 FASTAPI & YOLO SETUP ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model
try:
    # TRY LOADING YOUR CUSTOM MODEL FIRST
    model = YOLO("weights/models/newbest.pt")
    print("✅ Loaded custom accident detection model")
except:
    print("⚠️ Custom model 'weights/models/newbest.pt' not found, loading standard 'yolov8n.pt'...")
    model = YOLO("yolov8n.pt")

# Global State
last_ibm_trigger_time = 0
last_snapshot_time = 0
IBM_COOLDOWN = 60       # IBM Agent Cooldown
SNAPSHOT_COOLDOWN = 15  # Evidence Saving Cooldown

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global last_snapshot_time

    await websocket.accept()
    print("✅ Frontend Connected")
    print(f"📷 Connecting to camera: {MOBILE_CAMERA_URL}")
    
    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                await asyncio.sleep(0.5)
                continue

            # Run YOLO
            # Lowered confidence to 0.4 to catch more potential accidents
            results = model(frame, verbose=False, conf=0.4) 
            accident_detected = False
            detections_list = []
            vehicle_count_by_type = {"car": 0, "truck": 0, "motorcycle": 0, "bus": 0, "bicycle": 0, "person": 0, "other": 0}
            total_vehicles = 0
            highest_conf = 0.0
            detected_labels = []

            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    
                    # 🔍 DEBUG PRINT: Show me EVERYTHING the model sees!
                    print(f"👀 I SEE: {label} (Confidence: {conf:.2f})") 

                    # 🆕 Classify vehicle type
                    vehicle_type = classify_vehicle_type(label)
                    if vehicle_type != "other":
                        vehicle_count_by_type[vehicle_type] += 1
                        total_vehicles += 1
                    
                    detected_labels.append(label)
                    detections_list.append({
                        "label": label, 
                        "conf": conf, 
                        "bbox": box.xyxy[0].tolist(),
                        "type": vehicle_type  # 🆕 Add vehicle type
                    })

                    # 🚨 TRIGGER CONDITION - SMART CONFIDENCE THRESHOLDS
                    critical_keywords = ["accident", "crash", "car_crash", "damage", "wreck", "severe", "collision"]
                    supporting_keywords = ["car", "vehicle", "person"]
                    
                    # High-confidence trigger: Critical keywords with >40% confidence
                    is_critical = any(k in label.lower() for k in critical_keywords)
                    
                    # Lower-confidence trigger: Supporting keywords need >70% confidence
                    is_supporting = any(k in label.lower() for k in supporting_keywords)
                    
                    if (is_critical and conf > 0.4) or (is_supporting and conf > 0.7):
                        accident_detected = True
                        highest_conf = conf
                        print(f"🔥 MATCH FOUND! Label: {label} (Confidence: {conf:.2f}) triggered the alert.")

            ibm_status = "idle"
            severity = "NONE"
            
            if accident_detected:
                current_time = time.time()
                
                # 🆕 Calculate Severity Level
                severity = calculate_accident_severity(total_vehicles, highest_conf, detected_labels)
                print(f"🚨 SEVERITY LEVEL: {severity} (Vehicles: {total_vehicles}, Confidence: {highest_conf:.2%})")
                
                # 🆕 Track on Heatmap
                heatmap_tracker.add_incident(CAMERA_LAT, CAMERA_LON, severity)
                
                # 🆕 Estimate Queue Length
                queue_length = QueueEstimator.estimate_queue_length(total_vehicles)
                wait_time = QueueEstimator.estimate_wait_time(total_vehicles)
                print(f"📊 QUEUE ANALYSIS: {queue_length:.1f}m length, ~{wait_time}s wait time")
                
                # 1. Trigger IBM (Agentic Workflow) with severity
                res = trigger_ibm_agent(confidence=highest_conf, severity=severity, vehicle_count=total_vehicles)
                if res["status"] == "triggered":
                    ibm_status = "active"

                # 2. Save Evidence & Telegram (Background Thread) with severity
                # We use a separate cooldown so we don't spam files
                if current_time - last_snapshot_time > SNAPSHOT_COOLDOWN:
                    last_snapshot_time = current_time
                    frame_copy = frame.copy() # Copy frame so async doesn't mess it up
                    t = threading.Thread(
                        target=handle_alert_background,
                        args=("CRITICAL ACCIDENT", f"Severity: {severity}, Vehicles: {total_vehicles}", frame_copy, severity),
                        daemon=False  # Wait for thread to complete before shutdown
                    )
                    t.start()
                    print("📸 Evidence capture thread started...", flush=True)

            await websocket.send_json({
                "detections": detections_list,
                "accident_alert": accident_detected,
                "ibm_agent_status": ibm_status,
                "severity": severity,  # 🆕 Feature 1: Severity Level
                "vehicle_count_by_type": vehicle_count_by_type,  # 🆕 Feature 2: Vehicle Types
                "total_vehicles": total_vehicles,
                "heatmap_hotspots": heatmap_tracker.get_hotspots(),  # 🆕 Feature 3: Incident Heatmap
                "queue_info": {  # 🆕 Feature 4: Queue Length & Wait Time
                    "estimated_queue_length_m": round(QueueEstimator.estimate_queue_length(total_vehicles), 1),
                    "estimated_wait_time_s": QueueEstimator.estimate_wait_time(total_vehicles),
                    "vehicle_count": total_vehicles
                }
            })

            await asyncio.sleep(0.05) 

    except WebSocketDisconnect:
        print("❌ Frontend Disconnected")
    finally:
        cap.release()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)