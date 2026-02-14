# Rakshak-AI: Design Document
## Intelligent Traffic Emergency Response System
**AI for Bharat Hackathon 2026 (Student Track) - Idea Phase**

---

## 1. Executive Summary

**Rakshak-AI** is a hybrid Edge-Cloud system designed to detect traffic accidents in real-time and generate intelligent medical dispatch strategies using GenAI. This design document outlines the technical architecture, components, data flows, and implementation approach.

**Problem Addressed:** Emergency response delays due to manual accident detection and lack of real-time severity analysis.

**Solution:** Combine YOLOv8 edge AI with AWS cloud services and Claude 3 GenAI for autonomous emergency response coordination.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌──────────────┐
│  CCTV/Camera │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────┐
│  EDGE LAYER                     │
│  ┌───────────────────────────┐  │
│  │ YOLOv8 (Accident Detection)  │
│  │ FastAPI Server              │
│  │ Real-time Processing        │
│  │ <500ms latency              │
│  └───────────────────────────┘  │
└─────────────┬───────────────────┘
              │ (HTTPS API Call)
              ▼
┌─────────────────────────────────────┐
│  AWS CLOUD LAYER                    │
│  ┌───────────────────────────────┐  │
│  │ API Gateway                   │  │
│  │ (Authentication, Rate Limit)  │  │
│  └───────────────┬───────────────┘  │
│                  │                  │
│  ┌───────────────▼───────────────┐  │
│  │ Lambda Function               │  │
│  │ (Data Processing)             │  │
│  └───────────────┬───────────────┘  │
│                  │                  │
│  ┌───────────────▼───────────────┐  │
│  │ DynamoDB                      │  │
│  │ (Incident Storage)            │  │
│  └───────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  GENAI LAYER                        │
│  ┌───────────────────────────────┐  │
│  │ Amazon Bedrock (Claude 3)     │  │
│  │ Severity Analysis              │  │
│  │ Dispatch Strategy Generation  │  │
│  └───────────────┬───────────────┘  │
└─────────────────┼───────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
    ┌────────┐┌────────┐┌────────────┐
    │SNS/SES ││S3 Logs ││CloudWatch  │
    └────────┘└────────┘└────────────┘
        │
        ▼
    ┌──────────────┐
    │First Response│
    │(EMS, Police) │
    └──────────────┘
```

### 2.2 Layer Breakdown

#### **Edge Layer**
- **Component:** FastAPI + YOLOv8 on Local/Edge Device
- **Purpose:** Real-time accident detection from video feeds
- **Processing:** 
  - Captures frames at 30 FPS
  - Runs YOLOv8 inference (<500ms/frame)
  - Detects accidents, vehicles, obstacles
- **Output:** JSON with detections, confidence scores, bounding boxes

#### **Cloud Layer**
- **API Gateway:** 
  - REST endpoint: `POST /api/detect/accident`
  - Authentication via AWS IAM roles
  - Rate limiting (1000 req/min)
  - Request validation

- **Lambda Function:**
  - Triggered by API Gateway
  - Processes detection data
  - Validates confidence thresholds
  - Invokes Bedrock for analysis
  - Stores metadata in DynamoDB

- **DynamoDB:**
  - NoSQL database for incident records
  - Partition key: `incident_id`
  - Sort key: `timestamp`
  - TTL for old records (30 days)

#### **GenAI Layer**
- **Amazon Bedrock (Claude 3):**
  - Analyzes accident severity
  - Generates medical dispatch strategies
  - Returns: severity, resources, instructions
  - Processing time: <2 seconds

#### **Notification Layer**
- **SNS (Simple Notification Service):**
  - Sends SMS alerts
- **SES (Simple Email Service):**
  - Sends email notifications
- **CloudWatch:**
  - Logs all events
  - Creates alarms

---

## 3. Component Design

### 3.1 Edge Service (Backend)

**Technology:** Python 3.10 + FastAPI + YOLOv8

```python
# Architecture
FastAPI Server (Port 8000)
├── /health → Health check endpoint
├── /api/detect/upload → Upload frame for analysis
├── /api/incidents → Query incident history
└── /api/analytics → Analytics & reports

# Key Components
1. YOLOv8 Model
   - Input: Video frame (720p+)
   - Output: Detections with confidence
   - Models: yolov8n.pt (nano) - lightweight
   
2. FastAPI Server
   - Handles HTTP requests
   - Validates input
   - Calls AWS Lambda via API Gateway
   - Returns dispatch strategy
```

**API Endpoint Details:**

```
POST /api/detect/upload
├── Input: Multipart form data (image file)
├── Processing:
│   ├── Run YOLOv8 inference
│   ├── Extract detections (vehicles, obstacles)
│   ├── Calculate severity indicators
│   └── JSON payload to AWS Lambda
└── Output: Dispatch strategy + resources

Example Request:
POST http://localhost:8000/api/detect/upload
Content-Type: multipart/form-data
file=<accident_image.jpg>

Example Response:
{
  "status": "success",
  "accident_detected": true,
  "confidence": 0.92,
  "severity": "Critical",
  "resources_needed": [
    "Ambulances: 2",
    "Fire Brigade: 1",
    "Police: 2"
  ],
  "dispatch_priority": "IMMEDIATE",
  "estimated_response_time": "8-10 minutes",
  "dispatch_strategy": "Multi-trauma assessment required..."
}
```

### 3.2 Cloud Processing (AWS Lambda)

**Function Workflow:**

```
1. Trigger: API Gateway POST /api/detect/accident
   ↓
2. Parse incoming data (detection results, metadata)
   ↓
3. Validate confidence thresholds (>0.8 for critical)
   ↓
4. Construct prompt for Bedrock Claude 3
   ├── Include: vehicle count, detection confidence
   ├── Include: severity indicators (fire, injury)
   └── Include: location, timestamp
   ↓
5. Call Amazon Bedrock API
   ├── Model: claude-3-sonnet-20240229
   ├── Temperature: 0.3 (deterministic)
   └── Max tokens: 500
   ↓
6. Parse Bedrock response
   ├── Extract: severity level
   ├── Extract: resources needed
   └── Extract: dispatch instructions
   ↓
7. Store incident record in DynamoDB
   ├── incident_id (UUID)
   ├── timestamp
   ├── severity, vehicle_count, location
   ├── dispatch_strategy, resources
   └── response_time
   ↓
8. Trigger SNS notification
   ├── Message: Dispatch strategy text
   ├── Recipients: Registered responders
   └── Channels: SMS, Email via SES
   ↓
9. Return response to edge device
```

### 3.3 Data Models

#### **DynamoDB Table Schema**

```
Table Name: rakshak_incidents

Primary Key:
- incident_id (String, Partition Key) - UUID format
- timestamp (String, Sort Key) - ISO 8601 format

Attributes:
{
  "incident_id": "INC-2026-12345",
  "timestamp": "2026-02-14T10:30:45Z",
  "location": {
    "latitude": 15.4589,
    "longitude": 75.0078,
    "address": "Pune Main Road, Intersection A"
  },
  "detection": {
    "vehicle_count": 3,
    "detection_confidence": 0.92,
    "severity_indicators": ["severe_damage", "potential_casualties"],
    "object_classes": ["car", "truck", "motorcycle"]
  },
  "analysis": {
    "severity": "Critical",
    "resources_needed": {
      "ambulances": 2,
      "fire_brigade": 1,
      "police": 2,
      "traffic_control": 1
    }
  },
  "dispatch": {
    "strategy": "Multi-trauma assessment. Deploy all available...",
    "priority": "IMMEDIATE",
    "estimated_response_time_minutes": 9,
    "responder_notified": true,
    "notification_sent_at": "2026-02-14T10:30:47Z"
  },
  "resolution": {
    "status": "pending",
    "first_responder_eta": "2026-02-14T10:39:00Z",
    "scene_clear_time": "2026-02-14T11:05:30Z",
    "response_time_actual_minutes": 9
  },
  "ttl": 1708022400  // 30days auto-delete
}
```

#### **Lambda Request Payload**

```json
{
  "accident_data": {
    "confidence": 0.92,
    "vehicle_count": 3,
    "severity_indicators": ["fire_hazard", "casualties_likely"],
    "location": {
      "latitude": 15.4589,
      "longitude": 75.0078
    },
    "timestamp": "2026-02-14T10:30:45Z",
    "image_description": "Multi-vehicle collision at intersection with visible fire"
  }
}
```

#### **Bedrock Claude 3 Prompt Template**

```
System Prompt:
"You are an emergency response coordinator AI. Analyze traffic accidents and provide emergency dispatch strategies."

User Prompt:
"Analyze this traffic accident and provide dispatch strategy:
- Vehicles involved: {vehicle_count}
- Detection confidence: {confidence}%
- Severity indicators: {indicators}
- Location: {latitude}, {longitude}
- Time: {timestamp}

Provide JSON response with:
1. severity (Critical/High/Medium/Low)
2. resources_needed (ambulances, fire_brigade, police count)
3. dispatch_strategy (text instructions for responders)
4. medical_priority (overview of medical needs)
5. estimated_response_time_minutes"
```

---

## 4. Data Flow Diagram

### 4.1 End-to-End Flow

```
STEP 1: ACCIDENT OCCURS
│
├─ Traffic camera captures frames
├─ YOLOv8 processes continuously at 30 FPS
└─ Accident detected (confidence > 0.8)

          ↓

STEP 2: EDGE PROCESSING
│
├─ Extract accident frame
├─ Calculate severity indicators
├─ Format detection data as JSON
└─ Prepare AWS API request

          ↓

STEP 3: CLOUD INGESTION
│
├─ API Gateway validates request
├─ Rate limiting check
├─ CloudWatch logs the event
└─ Trigger Lambda function

          ↓

STEP 4: LAMBDA PROCESSING
│
├─ Parse detection data
├─ Validate confidence (>0.75 threshold)
├─ DynamoDB record creation
└─ Prepare Bedrock prompt

          ↓

STEP 5: GENAI ANALYSIS (Bedrock Claude 3)
│
├─ Receive prompt from Lambda
├─ Analyze accident severity
├─ Generate dispatch strategy
├─ Estimate resources needed
└─ Return JSON response

          ↓

STEP 6: NOTIFICATION
│
├─ Parse Bedrock response
├─ Format dispatch message
├─ SNS triggers SMS/Email
├─ Update DynamoDB with notification status
└─ Send alert to first responders

          ↓

STEP 7: RESPONSE & TRACKING
│
├─ EMS/Police receive alert
├─ First responders acknowledge
├─ DynamoDB records response time
├─ CloudWatch tracks metrics
└─ Incident marked as "In Progress"

          ↓

STEP 8: RESOLUTION
│
├─ Responders clear scene
├─ Mark incident as "Resolved"
├─ Record actual response time
├─ Update analytics
└─ Generate incident report
```

---

## 5. API Specifications

### 5.1 POST /api/detect/accident

**Purpose:** Submit accident detection for analysis

**Request:**
```json
{
  "confidence": 0.92,
  "vehicle_count": 3,
  "severity_indicators": ["fire", "injury"],
  "location": [15.4589, 75.0078],
  "timestamp": "2026-02-14T10:30:45Z",
  "image_base64": "iVBORw0KGgoAAAANS..." // Optional
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "incident_id": "INC-2026-00001",
  "analysis": {
    "severity": "Critical",
    "confidence": 0.92,
    "resources": ["Ambulance x2", "Fire Brigade", "Police x2"],
    "dispatch_strategy": "IMMEDIATE dispatch. Multi-trauma...",
    "eta_minutes": 8
  },
  "notification": {
    "status": "sent",
    "channels": ["SMS", "Email"],
    "recipient_count": 5
  }
}
```

**Response (Error - 400):**
```json
{
  "status": "error",
  "code": "INVALID_CONFIDENCE",
  "message": "Confidence score below threshold (min: 0.75)"
}
```

### 5.2 GET /api/incidents

**Purpose:** Retrieve incident history

**Query Parameters:**
- `limit` (default: 10) - Number of records
- `days` (default: 7) - Days of history
- `severity` (optional) - Filter by severity

**Response:**
```json
{
  "status": "success",
  "total_count": 23,
  "critical_count": 5,
  "high_count": 8,
  "incidents": [
    {
      "incident_id": "INC-2026-00001",
      "timestamp": "2026-02-14T10:30:45Z",
      "severity": "Critical",
      "vehicle_count": 3,
      "location": [15.4589, 75.0078],
      "response_time_minutes": 9
    }
  ]
}
```

---

## 6. Technology Choices & Justification

| Technology | Choice | Why |
|-----------|--------|-----|
| **Edge AI** | YOLOv8 | Real-time detection, <500ms latency, lightweight |
| **Backend Framework** | FastAPI | Async support, automatic API docs, high performance |
| **Cloud Provider** | AWS | Bedrock for GenAI, Lambda for serverless, DynamoDB for scale |
| **Database** | DynamoDB | On-demand pricing, auto-scaling, high availability |
| **GenAI Model** | Claude 3 | Superior reasoning, medical context understanding |
| **Notification** | SNS/SES | Reliable, scalable, multi-channel support |
| **Monitoring** | CloudWatch | Native AWS integration, real-time alerts |
| **Frontend** | React.js | Interactive UI, real-time updates via WebSocket |

---

## 7. Security & Compliance

### 7.1 Authentication & Authorization
- API Gateway: IAM role-based access control
- Edge devices: Certificate-based authentication
- Database: Fine-grained access policies

### 7.2 Data Protection
- **In Transit:** TLS 1.3 encryption
- **At Rest:** AES-256 encryption in DynamoDB
- **Logging:** CloudTrail for audit trail
- **Retention:** 30-day TTL for incident records

### 7.3 Privacy
- GDPR compliant (incident data anonymized)
- No personally identifiable information stored
- Location data with privacy controls

---

## 8. Performance & Scalability

### 8.1 Performance Targets

| Metric | Target | Baseline |
|--------|--------|----------|
| Edge Detection | <500ms | Real-time |
| API Response | <100ms | Gateway response |
| Lambda Execution | <2s | Bedrock analysis |
| E2E Latency | <3s | Detection to dispatch |
| Notification Delivery | <10s | SNS native |

### 8.2 Scalability
- **Edge Devices:** Support 10+ concurrent devices at launch
- **Cloud Throughput:** 100+ incidents/hour
- **DynamoDB:** On-demand billing (auto-scales)
- **Lambda:** Concurrent executions: 1000+
- **Bedrock:** Pay-per-token (scales automatically)

---

## 9. Deployment Architecture

### 9.1 Development Setup
```bash
# Local development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Mock Bedrock testing (no AWS charges)
USE_MOCK_BEDROCK=true python main.py
```

### 9.2 Production Deployment
```
1. Docker containerize backend & frontend
2. Deploy backend to AWS ECS (Elastic Container Service)
3. Deploy frontend to S3 + CloudFront
4. Configure API Gateway
5. Lambda functions via SAM/Terraform
6. Enable CloudWatch monitoring
7. Setup SNS/SES notification pipelines
```

### 9.3 Infrastructure as Code (Terraform)
```
Key Resources:
- API Gateway REST API
- Lambda function (Python runtime 3.11)
- DynamoDB table
- SNS topic & SES configuration
- CloudWatch Log Groups
- IAM roles & policies
```

---

## 10. Testing Strategy

### 10.1 Unit Tests
- Bedrock mock responses
- Data validation functions
- API endpoint handlers

### 10.2 Integration Tests
- Edge → Cloud API communication
- Lambda → Bedrock interaction
- DynamoDB CRUD operations

### 10.3 Performance Tests
- Load testing: 100 incidents/sec
- Latency profiling: E2E response time
- Throughput validation

### 10.4 Security Tests
- API authentication validation
- SQL injection prevention
- Rate limiting effectiveness

---

## 11. Monitoring & Observability

### 11.1 Metrics
- **Detection Accuracy:** % correct accident identification
- **Response Time:** P50, P95, P99 latencies
- **Availability:** Uptime percentage
- **Cost:** Monthly AWS spend tracking

### 11.2 Logging
- CloudWatch Logs for all services
- Structured JSON logging
- Log retention: 30 days for incidents

### 11.3 Alerting
- Critical: Latency > 5 seconds
- Warning: Latency > 3 seconds
- Info: Incident volume trends

---

## 12. Future Enhancements

### Phase 2 (Next 3 months)
- [ ] Multi-camera support & coordination
- [ ] Real Bedrock integration (currently mock)
- [ ] React dashboard for incident visualization
- [ ] Mobile app for first responders
- [ ] SMS confirmation from responders

### Phase 3 (6+ months)
- [ ] Machine learning model retraining pipeline
- [ ] Advanced incident clustering
- [ ] Predictive hotspot analysis
- [ ] Multi-language support
- [ ] Integration with existing emergency dispatch systems

---

## 13. Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **False Detection** | Wastes resources | Confidence threshold tuning, multi-model ensemble |
| **Cloud Latency** | Delayed response | Edge processing, local caching |
| **Model Accuracy** | Missed incidents | Continuous retraining, human feedback loop |
| **AWS Downtime** | Service unavailable | Multi-region failover planning |
| **Privacy Violation** | Legal issues | Data anonymization, GDPR compliance |

---

## 14. Cost Estimation (Monthly)

### 14.1 AWS Costs (Estimate)
```
API Gateway: $0-35 (usage-based)
Lambda: $0-100 (1M free requests/month)
DynamoDB: $50-200 (on-demand)
Bedrock: $100-500 (token-based, test phase)
CloudWatch: $10-50
SNS/SES: $5-50
S3: $1-10
Total: $166-945/month
```

### 14.2 Development Costs
- Development: 4 engineers × 3 months
- Infrastructure: AWS + tools: ~$1000
- Testing & QA: Included in development

---

## 15. Success Criteria

### Hackathon Phase (Idea Submission)
✅ Complete technical specifications  
✅ Mock implementation of Bedrock  
✅ API design and documentation  
✅ Architecture diagrams  
✅ GitHub repository with code  

### Prototype Phase (If Selected)
✅ End-to-end system working  
✅ Real Bedrock integration  
✅ Live dashboard  
✅ Load testing completed  

### Production Phase
✅ >85% detection accuracy  
✅ <3 second E2E latency  
✅ 99.9% uptime  
✅ Live pilot with EMS partner  

---

## Appendix A: Glossary

- **YOLOv8:** Real-time object detection model
- **FastAPI:** Modern Python web framework
- **Lambda:** AWS serverless compute service
- **DynamoDB:** AWS NoSQL database
- **Bedrock:** AWS service providing access to foundation models
- **Claude 3:** Anthropic's latest LLM (via Bedrock)
- **SNS:** AWS Simple Notification Service
- **SES:** AWS Simple Email Service
- **TTL:** Time-to-Live (auto-delete records)
- **E2E:** End-to-End latency

---

## Appendix B: References

- YOLOv8 Documentation: https://docs.ultralytics.com/
- FastAPI: https://fastapi.tiangolo.com/
- AWS Bedrock: https://aws.amazon.com/bedrock/
- AWS Lambda: https://aws.amazon.com/lambda/
- DynamoDB: https://aws.amazon.com/dynamodb/

---

**Document Version:** 1.0  
**Generated:** February 2026  
**Team:** Team Neural  
**Leader:** Vivekanand Swami  
**Status:** Ready for Hackathon Submission ✅
