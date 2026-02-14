# Rakshak-AI: Requirements & System Architecture
## AI for Bharat Hackathon 2026 (Student Track) - Idea Phase

---

## 1. Project Overview

**Project Name:** Rakshak-AI (Intelligent Traffic Emergency Response)  
**Team Name:** Team Neural  
**Team Leader:** Vivekanand Swami  
**Problem Statement:** AI for Communities, Access & Public Impact  
**Category:** Healthcare & Public Safety  

---

## 2. Problem Statement & Solution Approach

### Problem:
- Emergency response delays due to manual accident detection and assessment
- Lack of real-time severity analysis for first responders
- Inefficient dispatch strategies leading to increased fatality rates in traffic accidents

### Solution:
**Rakshak-AI** - A Hybrid Edge-Cloud System for Intelligent Traffic Emergency Response

```
Edge Layer (Local)          →        Cloud Layer (AWS)           →     First Responders
─────────────────────────────────────────────────────────────────────────────────────
YOLOv8 Accident Detection   →   API Gateway + Lambda Functions   →   Dispatch Strategy
(Real-time video analysis)      (Data processing & storage)          (Medical priority)
                            →   Amazon Bedrock (Claude 3)         →   SMS/Email Alert
                                (Severity Analysis)
```

---

## 3. System Architecture & Components

### 3.1 Edge Layer - Local Accident Detection
**Technology:** YOLOv8 (Real-time Object Detection)
- **Purpose:** Detect traffic accidents and anomalies locally
- **Input:** CCTV/Traffic camera feeds
- **Output:** Bounding boxes, confidence scores, detected accident frames
- **Processing:** FastAPI server running on edge device
- **Latency:** <500ms per frame

**Features:**
- Real-time multi-object detection (vehicles, pedestrians, accidents)
- Frame rate: 30 FPS on edge hardware
- Confidence threshold: 0.65+

### 3.2 Cloud Layer - Data Processing & API Gateway
**AWS Services Used:**
1. **API Gateway:** REST API endpoint for edge devices
   - Authenticate edge device requests
   - Rate limiting & throttling
   - Request/response transformation

2. **Lambda Functions:** Serverless processing
   - Parse accident detection data
   - Format data for GenAI analysis
   - Trigger medical dispatch workflow

3. **DynamoDB:** Real-time data storage
   - Store accident incidents
   - Query historical patterns
   - Audit trail for emergency response

4. **CloudWatch:** Monitoring & Logging
   - Monitor API performance
   - Log all incident data
   - Create alerts for system failures

### 3.3 GenAI Layer - Severity Analysis & Dispatch Strategy
**Technology:** Amazon Bedrock Claude 3
- **Purpose:** Analyze crash severity and generate medical dispatch strategies
- **Input:** Accident detection data + frame analysis
- **Output:** 
  - Severity level (Critical/High/Medium/Low)
  - Recommended medical resources
  - Priority dispatch instructions
  - First responder alert message

**GenAI Workflow:**
```
Accident Data (YOLO Output)
         ↓
CloudWatch Event Triggered
         ↓
Lambda invokes Bedrock Claude 3
         ↓
Prompt: "Analyze this traffic accident..."
         ↓
GenAI Response: "Medical Dispatch Strategy"
         ↓
Alert First Responders via SMS/Email
```

---

## 4. Functional Requirements

### FR1: Real-time Accident Detection
- System SHALL detect traffic accidents from video feeds within 500ms
- System SHALL identify accident severity indicators (vehicle damage, casualties)
- System SHALL achieve >85% accuracy on benchmark accident dataset

### FR2: Cloud Data Ingestion
- System SHALL receive accident detection data via REST API
- System SHALL validate incoming data against schema
- System SHALL store validated data in DynamoDB with timestamp

### FR3: GenAI-Based Severity Analysis
- System SHALL analyze accident patterns using Claude 3
- System SHALL generate medical dispatch strategy within 2 seconds
- System SHALL provide structured JSON response with severity level, resources needed, priority instructions

### FR4: Alert & Notification System
- System SHALL send real-time alerts to registered first responders
- System SHALL include incident location, severity, and dispatch strategy in alert
- System SHALL log all notification delivery attempts

### FR5: Historical Analysis & Reporting
- System SHALL maintain incident database for pattern analysis
- System SHALL generate weekly/monthly incident reports
- System SHALL identify high-risk accident zones

---

## 5. Non-Functional Requirements

### Performance
- End-to-end latency: <3 seconds (Accident Detection → Dispatch Strategy)
- Edge processing: <500ms
- Cloud processing: <2 seconds
- API response time: <100ms

### Scalability
- Support minimum 10 concurrent edge devices
- Handle 100+ incidents per hour
- DynamoDB: On-demand billing for elasticity

### Reliability
- System uptime: >99% during business hours
- Automatic failover for Lambda functions
- Data backup: Daily snapshots to S3

### Security
- API authentication: AWS IAM roles
- Data encryption: TLS in-transit, AES-256 at-rest
- Audit logging: CloudTrail for all API calls

---

## 6. Technology Stack

### Edge Computing
- **Programming Language:** Python 3.10+
- **Framework:** FastAPI 0.104.1
- **Object Detection:** YOLOv8 (Ultralytics)
- **HTTP Client:** Requests library
- **Environment Management:** python-dotenv

### Cloud Infrastructure (AWS)
- **API Management:** API Gateway
- **Compute:** Lambda Functions
- **Database:** DynamoDB
- **GenAI Model:** Amazon Bedrock (Claude 3)
- **Monitoring:** CloudWatch
- **Storage:** S3 for image backups
- **Logging:** CloudTrail

### Frontend/Monitoring Dashboard
- **Framework:** React.js
- **Purpose:** Visualize real-time incidents and dispatch status
- **Hosted on:** S3 + CloudFront

---

## 7. Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    TRAFFIC CAMERA FEED                           │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│        EDGE LAYER: YOLOv8 (FastAPI Server)                      │
│  • Detect accidents in real-time                                │
│  • Extract accident frames & metadata                           │
│  • Filter low-confidence detections                             │
└──────────────────────┬───────────────────────────────────────────┘
                       │ (HTTPS POST)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│        AWS API GATEWAY                                           │
│  • Authenticate edge device                                     │
│  • Rate limiting (1000 req/min)                                 │
│  • Transform request format                                     │
└──────────────────────┬───────────────────────────────────────────┘
                       │ (Event)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│        AWS LAMBDA FUNCTION                                       │
│  • Parse YOLO detection data                                    │
│  • Validate against schema                                      │
│  • Store metadata in DynamoDB                                   │
│  • Invoke Bedrock GenAI                                         │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│   AMAZON BEDROCK (Claude 3) - GenAI Layer                       │
│  • Analyze accident severity (Text + Bounding boxes)            │
│  • Generate medical dispatch strategy                           │
│  • Recommend resources & priority                               │
│  • Output: Severity + Instructions JSON                         │
└──────────────────────┬───────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌─────────┐  ┌──────────┐  ┌─────────────┐
    │DynamoDB │  │CloudWatch│  │SNS/SES      │
    │(Audit)  │  │(Alerts)  │  │(Notify EMS) │
    └─────────┘  └──────────┘  └─────────────┘
          │            │            │
          └────────────┼────────────┘
                       ▼
          ┌──────────────────────────┐
          │  First Responders        │
          │  (Ambulance, Police)     │
          │  Receive SMS/Email Alert │
          └──────────────────────────┘
```

---

## 8. Implementation Phases

### Phase 1: Prototype (This Hackathon)
- [ ] Edge detection with YOLOv8
- [ ] FastAPI integration
- [ ] AWS API Gateway setup
- [ ] Mock Bedrock GenAI connection
- [ ] DynamoDB schema & basic CRUD
- [ ] Alert notification system (email)

### Phase 2: Enhancement
- [ ] Improve detection accuracy (>90%)
- [ ] Real Bedrock integration
- [ ] React dashboard for incident visualization
- [ ] SMS notifications via Twilio
- [ ] Incident clustering and pattern analysis

### Phase 3: Production
- [ ] Load testing and optimization
- [ ] Security hardening & penetration testing
- [ ] Multi-region deployment
- [ ] Mobile app for first responders
- [ ] Analytics dashboard

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Detection Accuracy | >85% |
| End-to-End Latency | <3 seconds |
| False Positive Rate | <5% |
| System Uptime | >99% |
| API Response Time | <100ms |
| First Responder Alert Time | <10 seconds |

---

## 10. Dependencies & Licenses

### Python Packages
- `fastapi` - Web framework (MIT License)
- `uvicorn` - ASGI server (BSD License)
- `ultralytics` - YOLOv8 (AGPL License)
- `opencv-python` - Computer Vision (BSD License)
- `boto3` - AWS SDK (Apache 2.0)
- `requests` - HTTP client (Apache 2.0)

### AWS Services
- API Gateway (Pay per request)
- Lambda (Free tier: 1M requests/month)
- DynamoDB (On-demand pricing)
- CloudWatch (Basic monitoring free)
- Bedrock Claude 3 (Pay per token)

---

## 11. Deployment Instructions

### Prerequisites:
```bash
- Python 3.10+
- AWS Account with Bedrock access
- YOLO model (v8m recommended for edge devices)
- Linux/Windows/macOS with 4GB RAM minimum
```

### Quick Start:
```bash
# 1. Clone repository
git clone https://github.com/Team-Neural/Rakshak-AI-AWS.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure AWS credentials
aws configure

# 4. Set environment variables
cp .env.example .env
# Edit .env with your AWS region, DynamoDB table name, etc.

# 5. Run edge service
python main.py

# 6. Test with mock accident data
curl -X POST http://localhost:8000/api/detect/upload \
  -F "file=@test_frame.jpg"
```

---

## 12. Contact & Support

**Team Name:** Team Neural  
**Leader:** Vivekanand Swami  
**GitHub Repository:** Rakshak-AI-AWS  
**Problem Category:** AI for Communities, Access & Public Impact  

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Status:** Idea Phase - Ready for Review
