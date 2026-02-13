"""
Mock Bedrock Service - Simulates Amazon Bedrock Claude 3 API Responses
For testing and development purposes without consuming Bedrock tokens

Author: Team Neural
Hackathon: AI for Bharat 2026
"""

import json
import random
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockBedrockClient:
    """
    Mock client that simulates AWS Bedrock (Claude 3) responses for accident analysis.
    
    Usage:
        client = MockBedrockClient()
        response = client.analyze_accident(accident_data)
    """
    
    # Severity levels
    SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]
    
    # Resource types for dispatch
    RESOURCES = {
        "Critical": {
            "ambulances": 2,
            "fire_brigade": 1,
            "police": 2,
            "traffic_control": 1
        },
        "High": {
            "ambulances": 1,
            "fire_brigade": 0,
            "police": 1,
            "traffic_control": 1
        },
        "Medium": {
            "ambulances": 1,
            "fire_brigade": 0,
            "police": 1,
            "traffic_control": 0
        },
        "Low": {
            "ambulances": 0,
            "fire_brigade": 0,
            "police": 1,
            "traffic_control": 0
        }
    }
    
    # Medical dispatch strategies by severity
    DISPATCH_STRATEGIES = {
        "Critical": [
            "IMMEDIATE dispatch required. Multi-trauma assessment. Alert trauma center. "
            "Activate full emergency response protocol. ETA: 8-10 minutes.",
            "Life-threatening injuries suspected. Deploy all available ambulances with paramedic teams. "
            "Contact nearest hospital ICU. Prepare OR for emergency procedures.",
            "Severe crash with potential entrapment. Dispatch fire brigade for extrication. "
            "Multiple casualty management required. Activate mutual aid from adjacent stations."
        ],
        "High": [
            "Urgent response needed. Moderate injuries likely. Standard ambulance dispatch sufficient. "
            "Advise hospital to prepare emergency department. ETA: 10-12 minutes.",
            "Significant vehicle damage detected. Deploy ambulance with basic life support. "
            "Clear accident scene within 30 minutes for traffic flow. Traffic signal adjustment recommended.",
            "Injury probability high. Dispatch paramedic unit. Advise drivers to avoid area. "
            "Coordinate with traffic control for vehicle removal."
        ],
        "Medium": [
            "Standard response appropriate. Minor to moderate injuries expected. "
            "Single ambulance sufficient. Clear scene quickly to minimize traffic impact.",
            "Moderate damage without severe injury indicators. Police for traffic management only. "
            "Expect 15-minute scene duration for documentation.",
            "Non-critical incident. Police dispatch for incident report. Minor medical support may be needed. "
            "Traffic flow will resume within 20 minutes."
        ],
        "Low": [
            "Low risk incident. Police dispatch for traffic control. Standard response time acceptable. "
            "May clear independently if all parties cooperative.",
            "Minimal damage and low injury risk. Log incident for records. "
            "Traffic disruption minimal. No immediate medical intervention required.",
            "Non-emergency incident. Arrange police visit for routine documentation. "
            "Traffic flow largely unaffected. Handle as routine accident report."
        ]
    }
    
    # Medical considerations by severity
    MEDICAL_CONSIDERATIONS = {
        "Critical": [
            "Spinal injury protocol mandatory until cleared",
            "Prepare for multiple casualties triage",
            "Initiate CPR protocols if needed",
            "Arrange trauma surgery availability",
            "Monitor for internal bleeding",
            "Prepare ICU bed immediately"
        ],
        "High": [
            "Standard trauma assessment protocol",
            "Monitor vital signs continuously",
            "Arrange hospital admission capability",
            "Assess for hidden injuries",
            "Establish IV access during transport"
        ],
        "Medium": [
            "Basic trauma assessment",
            "Monitor for delayed shock symptoms",
            "Hospital observation recommended",
            "Document all injuries for insurance"
        ],
        "Low": [
            "First aid treatment sufficient",
            "Advise on follow-up medical consultation",
            "Document for insurance/legal purposes"
        ]
    }
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize Mock Bedrock Client
        
        Args:
            use_mock (bool): If True, uses mock responses. If False, would use real API.
        """
        self.use_mock = use_mock
        self.model = "claude-3-sonnet-20240229"
        self.region = "us-east-1"
        logger.info(f"MockBedrockClient initialized (Mock Mode: {self.use_mock})")
    
    def analyze_accident(self, accident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze accident data and generate dispatch strategy using mock Claude 3
        
        Args:
            accident_data (dict): Contains:
                - confidence: float (0-1) detection confidence
                - vehicle_count: int number of vehicles involved
                - location: tuple (lat, lon)
                - severity_indicators: list of detected issues
                - timestamp: datetime
                - image_description: str description of scene
        
        Returns:
            dict: Contains dispatch strategy, severity level, resources needed, etc.
        """
        logger.info(f"Analyzing accident data: confidence={accident_data.get('confidence', 0.8)}")
        
        # Extract key information
        confidence = accident_data.get("confidence", 0.8)
        vehicle_count = accident_data.get("vehicle_count", 2)
        severity_indicators = accident_data.get("severity_indicators", [])
        location = accident_data.get("location", (0.0, 0.0))
        
        # Determine severity level based on multiple factors
        severity = self._calculate_severity(confidence, vehicle_count, severity_indicators)
        
        # Generate dispatch strategy
        dispatch_strategy = self._generate_dispatch_strategy(severity)
        
        # Get resources needed
        resources = self.RESOURCES[severity].copy()
        
        # Get medical considerations
        medical_considerations = random.sample(
            self.MEDICAL_CONSIDERATIONS[severity],
            min(3, len(self.MEDICAL_CONSIDERATIONS[severity]))
        )
        
        # Calculate response time based on severity
        response_time = self._calculate_response_time(severity)
        
        # Build response
        response = {
            "status": "success",
            "analysis_timestamp": datetime.now().isoformat(),
            "severity_level": severity,
            "confidence_score": round(confidence, 3),
            "vehicle_count": vehicle_count,
            "dispatch_priority": "IMMEDIATE" if severity == "Critical" else "URGENT" if severity == "High" else "STANDARD",
            "dispatch_strategy": dispatch_strategy,
            "resources_needed": self._format_resources(resources),
            "resources_json": resources,
            "medical_dispatch_instructions": "\n".join(
                [f"• {item}" for item in medical_considerations]
            ),
            "medical_dispatch_list": medical_considerations,
            "estimated_response_time_minutes": response_time,
            "location": {
                "latitude": location[0],
                "longitude": location[1]
            },
            "severity_justification": self._get_severity_justification(
                confidence, vehicle_count, severity_indicators
            )
        }
        
        logger.info(f"Analysis complete. Severity: {severity}, Priority: {response['dispatch_priority']}")
        return response
    
    def _calculate_severity(self, confidence: float, vehicle_count: int, indicators: List[str]) -> str:
        """
        Calculate severity level based on multiple factors
        """
        severity_score = 0
        
        # Confidence score impact (0-0.4 points)
        if confidence > 0.9:
            severity_score += 0.3
        elif confidence > 0.75:
            severity_score += 0.2
        else:
            severity_score += 0.1
        
        # Vehicle count impact (0-0.3 points)
        if vehicle_count >= 3:
            severity_score += 0.3
        elif vehicle_count == 2:
            severity_score += 0.2
        else:
            severity_score += 0.1
        
        # Severity indicators impact (0-0.3 points)
        hazard_keywords = ["fire", "explosion", "injury", "casualty", "damage", "severe"]
        hazard_count = sum(1 for ind in indicators if any(kw in ind.lower() for kw in hazard_keywords))
        severity_score += min(0.3, (hazard_count * 0.1))
        
        # Add randomness for simulation (±0.05)
        severity_score += random.uniform(-0.05, 0.05)
        severity_score = max(0, min(1, severity_score))  # Clamp between 0-1
        
        # Map score to severity level
        if severity_score >= 0.7:
            return "Critical"
        elif severity_score >= 0.5:
            return "High"
        elif severity_score >= 0.3:
            return "Medium"
        else:
            return "Low"
    
    def _generate_dispatch_strategy(self, severity: str) -> str:
        """Generate a dispatch strategy based on severity"""
        return random.choice(self.DISPATCH_STRATEGIES[severity])
    
    def _calculate_response_time(self, severity: str) -> int:
        """Calculate estimated response time in minutes"""
        base_times = {
            "Critical": (8, 12),      # 8-12 minutes
            "High": (10, 15),         # 10-15 minutes
            "Medium": (15, 20),       # 15-20 minutes
            "Low": (20, 30)           # 20-30 minutes
        }
        min_time, max_time = base_times[severity]
        return random.randint(min_time, max_time)
    
    def _format_resources(self, resources: Dict[str, int]) -> str:
        """Format resources dictionary into readable string"""
        formatted = []
        resource_names = {
            "ambulances": "Ambulances",
            "fire_brigade": "Fire Brigade Units",
            "police": "Police Units",
            "traffic_control": "Traffic Control Officers"
        }
        
        for key, value in resources.items():
            if value > 0:
                formatted.append(f"{resource_names[key]}: {value}")
        
        return ", ".join(formatted) if formatted else "Non-emergency response"
    
    def _get_severity_justification(self, confidence: float, vehicle_count: int, indicators: List[str]) -> str:
        """Provide justification for severity determination"""
        reasons = []
        
        if confidence > 0.85:
            reasons.append(f"High detection confidence ({confidence:.1%})")
        
        if vehicle_count >= 3:
            reasons.append(f"Multiple vehicles involved ({vehicle_count} vehicles)")
        elif vehicle_count == 2:
            reasons.append("Two vehicles involved in accident")
        
        if indicators:
            if any("fire" in ind.lower() or "explosion" in ind.lower() for ind in indicators):
                reasons.append("Fire/explosion hazard detected")
            if any("injury" in ind.lower() or "casualty" in ind.lower() for ind in indicators):
                reasons.append("Potential casualties indicated")
            if any("severe" in ind.lower() or "damage" in ind.lower() for ind in indicators):
                reasons.append("Significant vehicle damage noted")
        
        return "Determination based on: " + "; ".join(reasons) if reasons else "Standard accident analysis applied"
    
    def get_incident_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get mock incident history (simulates DynamoDB query)
        
        Args:
            limit (int): Number of incidents to return
        
        Returns:
            dict: Mock incident history
        """
        incidents = []
        severity_distribution = ["Critical", "High", "Medium", "Low"]
        
        for i in range(min(limit, 10)):
            incident = {
                "incident_id": f"INC-2026-{2000 + i:05d}",
                "timestamp": f"2026-02-{random.randint(1,13):02d}T{random.randint(8,18):02d}:{random.randint(0,59):02d}:00Z",
                "severity": random.choice(severity_distribution),
                "vehicle_count": random.randint(1, 5),
                "location": {
                    "latitude": 15.4 + random.uniform(-0.5, 0.5),
                    "longitude": 75.0 + random.uniform(-0.5, 0.5)
                },
                "response_time_minutes": random.randint(8, 30)
            }
            incidents.append(incident)
        
        return {
            "status": "success",
            "total_incidents": random.randint(20, 100),
            "critical_count": random.randint(5, 15),
            "high_count": random.randint(8, 20),
            "medium_count": random.randint(10, 25),
            "low_count": random.randint(15, 40),
            "incidents": incidents
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection and basic functionality
        
        Returns:
            dict: Connection test results
        """
        logger.info("Testing Bedrock connection...")
        return {
            "status": "success",
            "service": "bedrock",
            "model": self.model,
            "region": self.region,
            "mock_mode": self.use_mock,
            "timestamp": datetime.now().isoformat(),
            "message": "Mock Bedrock service is operational"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize mock client
    client = MockBedrockClient(use_mock=True)
    
    # Test 1: Connection test
    print("=" * 60)
    print("TEST 1: Connection Test")
    print("=" * 60)
    result = client.test_connection()
    print(json.dumps(result, indent=2))
    
    # Test 2: Critical accident
    print("\n" + "=" * 60)
    print("TEST 2: Critical Accident Analysis")
    print("=" * 60)
    critical_accident = {
        "confidence": 0.95,
        "vehicle_count": 3,
        "severity_indicators": ["severe damage", "potential casualties", "fire hazard"],
        "location": (15.4589, 75.0078),
        "timestamp": datetime.now(),
        "image_description": "Multi-vehicle collision at intersection"
    }
    result = client.analyze_accident(critical_accident)
    print(json.dumps(result, indent=2))
    
    # Test 3: Low severity accident
    print("\n" + "=" * 60)
    print("TEST 3: Low Severity Accident Analysis")
    print("=" * 60)
    low_accident = {
        "confidence": 0.52,
        "vehicle_count": 1,
        "severity_indicators": ["minor scratch"],
        "location": (15.5, 75.1),
        "timestamp": datetime.now(),
        "image_description": "Single vehicle minor incident"
    }
    result = client.analyze_accident(low_accident)
    print(json.dumps(result, indent=2))
    
    # Test 4: Incident history
    print("\n" + "=" * 60)
    print("TEST 4: Incident History")
    print("=" * 60)
    history = client.get_incident_history(limit=5)
    print(json.dumps(history, indent=2))
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
