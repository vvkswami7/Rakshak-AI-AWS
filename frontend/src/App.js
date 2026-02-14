import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { AlertTriangle, CheckCircle, Activity, MapPin, Radio } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for Leaflet marker icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function App() {
  const [status, setStatus] = useState("disconnected");
  const [accidentAlert, setAccidentAlert] = useState(false);
  const [ibmStatus, setIbmStatus] = useState("idle");
  const [detections, setDetections] = useState([]);
  const [logs, setLogs] = useState([]);
  const [evidenceHistory, setEvidenceHistory] = useState([]);
  const [severity, setSeverity] = useState("NONE");  // 🆕 Feature 1
  const [vehicleCountByType, setVehicleCountByType] = useState({});  // 🆕 Feature 2
  const [heatmapHotspots, setHeatmapHotspots] = useState([]);  // 🆕 Feature 3
  const [queueInfo, setQueueInfo] = useState({});  // 🆕 Feature 4
  
  // CONFIGURATION
  // 1. Backend URL (Python WebSocket)
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "ws://localhost:8000/ws";
  // 2. Camera URL (Direct IP Webcam Stream) - Ensure this matches your Python config!
  const CAMERA_URL = process.env.REACT_APP_CAMERA_URL || "your_camera_url_here"; 

  useEffect(() => {
    const ws = new WebSocket(BACKEND_URL);

    ws.onopen = () => {
      setStatus("connected");
      addLog("✅ System Connected to Edge Server.");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      addLog("❌ Connection Error - Is main.py running?");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setDetections(data.detections || []);
      setSeverity(data.severity || "NONE");  // 🆕 Feature 1
      setVehicleCountByType(data.vehicle_count_by_type || {});  // 🆕 Feature 2
      setHeatmapHotspots(data.heatmap_hotspots || []);  // 🆕 Feature 3
      setQueueInfo(data.queue_info || {});  // 🆕 Feature 4
      
      // IMPROVED: Make the alert "Sticky"
      if (data.accident_alert) {
        setAccidentAlert(true);
        if (!accidentAlert) {
          addLog("🚨 CRITICAL: Accident Detected!");
          // Record this detection in evidence history
          const timestamp = new Date().toLocaleTimeString();
          const highestConf = data.detections && data.detections.length > 0 
            ? Math.max(...data.detections.map(d => d.conf))
            : 0;
          setEvidenceHistory(prev => [{
            id: Date.now(),
            timestamp: timestamp,
            detections: data.detections || [],
            confidence: highestConf,
            severity: data.severity || "NONE",  // 🆕 Include severity in history
            status: "active"
          }, ...prev]);
        }
      } 
      // Removed the "else" block so it stays RED until you refresh.
      // This ensures you don't miss it during the demo!

      // Update IBM Status
      if (data.ibm_agent_status !== ibmStatus) {
        setIbmStatus(data.ibm_agent_status);
        if (data.ibm_agent_status === 'active') {
          addLog("🤖 IBM Watson Agent Triggered!");
        }
      }
    };

    ws.onclose = () => setStatus("disconnected");

    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accidentAlert, ibmStatus]); 

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [`[${time}] ${msg}`, ...prev.slice(0, 5)]);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 font-mono">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
        <div className="flex items-center gap-3">
          <Activity className="text-blue-500" size={32} />
          <div>
            <h1 className="text-2xl font-bold tracking-widest">SENTINEL-X</h1>
            <p className="text-xs text-gray-400">IBM DEV DAY HACKATHON EDITION</p>
          </div>
        </div>
        <div className="flex gap-4">
          <StatusBadge label="EDGE SERVER" active={status === 'connected'} />
          <StatusBadge label="IBM AGENT" active={ibmStatus === 'active'} color="purple" />
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: LIVE FEED & ALERTS */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Alert Banner */}
          {accidentAlert ? (
            <div className={`border p-6 rounded-lg animate-pulse flex items-center gap-4 ${
              severity === "SEVERE" ? "bg-red-600/30 border-red-500" : 
              severity === "MODERATE" ? "bg-yellow-600/30 border-yellow-500" : 
              "bg-orange-600/30 border-orange-500"
            }`}>
              <AlertTriangle className={`${
                severity === "SEVERE" ? "text-red-500" : 
                severity === "MODERATE" ? "text-yellow-500" : 
                "text-orange-500"
              }`} size={48} />
              <div>
                <h2 className={`text-3xl font-bold ${
                  severity === "SEVERE" ? "text-red-500" : 
                  severity === "MODERATE" ? "text-yellow-500" : 
                  "text-orange-500"
                }`}>ACCIDENT DETECTED</h2>
                <p className={`${
                  severity === "SEVERE" ? "text-red-300" : 
                  severity === "MODERATE" ? "text-yellow-300" : 
                  "text-orange-300"
                }`}>🆕 Severity: <span className="font-bold">{severity}</span> | Dispatching Emergency Protocols via IBM Watson...</p>
              </div>
            </div>
          ) : (
            <div className="bg-green-900/20 border border-green-500 p-6 rounded-lg flex items-center gap-4">
              <CheckCircle className="text-green-500" size={48} />
              <div>
                <h2 className="text-2xl font-bold text-green-500">SYSTEM NORMAL</h2>
                <p className="text-green-300">Monitoring traffic flow. No incidents.</p>
              </div>
            </div>
          )}

          {/* Live Camera View */}
          <div className="bg-black rounded-lg overflow-hidden border border-gray-700 relative h-96">
            <div className="absolute top-4 left-4 z-10 bg-red-600 px-2 py-1 rounded text-xs font-bold animate-pulse">LIVE FEED</div>
            
            <img 
              src={CAMERA_URL} 
              alt="Live Feed" 
              className="w-full h-full object-cover opacity-80"
              onError={(e) => {
                e.target.style.display='none';
              }} 
            />
            
            {/* Fallback Text */}
            <div className="absolute inset-0 flex items-center justify-center -z-10">
              <span className="text-gray-600">Waiting for Camera Stream...</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: MAP & LOGS */}
        <div className="space-y-6">
          
          {/* Map Section with FEATURE 3: Incident Hotspots */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-64">
            <h3 className="flex items-center gap-2 font-bold mb-2 text-gray-300">
              <MapPin size={18} /> LIVE LOCATION & HOTSPOTS
            </h3>
            <MapContainer center={[18.5204, 73.8567]} zoom={13} style={{ height: '100%', borderRadius: '8px' }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Marker position={[18.5204, 73.8567]}>
                <Popup>Sentinel-X Node 1</Popup>
              </Marker>
              {/* 🆕 FEATURE 3: Display incident hotspots */}
              {heatmapHotspots.map((hotspot, idx) => {
                const severityColor = hotspot.severity === "SEVERE" ? "#ef4444" : 
                                     hotspot.severity === "MODERATE" ? "#eab308" : "#22c55e";
                const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14" fill="${severityColor}"/></svg>`;
                return (
                  <Marker 
                    key={idx} 
                    position={hotspot.location}
                    icon={new L.Icon({
                      iconUrl: `data:image/svg+xml;base64,${btoa(svgIcon)}`,
                      iconSize: [32, 32],
                      iconAnchor: [16, 32],
                      popupAnchor: [0, -32]
                    })}
                  >
                    <Popup>{hotspot.severity} at {hotspot.time}</Popup>
                  </Marker>
                );
              })}
            </MapContainer>
          </div>

          {/* Data Logs */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-64 overflow-hidden flex flex-col">
            <h3 className="flex items-center gap-2 font-bold mb-4 text-gray-300">
              <Radio size={18} /> SYSTEM LOGS
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 font-mono text-sm">
              {logs.map((log, i) => (
                <div key={i} className="border-l-2 border-blue-500 pl-2 text-gray-400">
                  {log}
                </div>
              ))}
              {logs.length === 0 && <span className="text-gray-600">Waiting for events...</span>}
            </div>
          </div>
          
          {/* Detection Debug List */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
             <h3 className="text-xs font-bold text-gray-400 mb-2">DETECTED OBJECTS</h3>
             <div className="flex flex-wrap gap-2">
               {detections && detections.length > 0 ? (
                 detections.map((d, i) => (
                   <span key={i} className={`px-2 py-1 rounded text-xs font-semibold ${
                     d.conf > 0.7 ? 'bg-red-600 text-white' : d.conf > 0.4 ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-blue-300'
                   }`}>
                     {d.label} ({(d.conf * 100).toFixed(0)}%)
                   </span>
                 ))
               ) : (
                 <span className="text-gray-500 text-xs">No objects detected yet</span>
               )}
             </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mt-4">
            <h3 className="text-xs font-bold text-gray-400 mb-3">📸 EVIDENCE HISTORY</h3>
            {evidenceHistory.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {evidenceHistory.map((evidence, idx) => (
                  <div key={evidence.id} className={`p-3 rounded border-l-4 ${
                    idx === 0 ? 'bg-red-900/30 border-red-500' : 'bg-gray-700/30 border-gray-600'
                  }`}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="text-xs font-bold text-gray-300">
                          {idx === 0 ? '🔴 LATEST' : `#${idx}`} - {evidence.timestamp}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          Objects: {evidence.detections.length > 0 
                            ? evidence.detections.map(d => d.label).join(', ')
                            : 'N/A'
                          }
                        </div>
                        <div className="text-xs text-yellow-400 mt-1">
                          Max Confidence: {(evidence.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                      {idx === 0 && (
                        <div className="ml-2 px-2 py-1 bg-red-600 rounded text-xs font-bold animate-pulse">
                          ACTIVE
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-gray-500 text-xs">No accidents detected yet</span>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

// Simple Helper Component for Badges
const StatusBadge = ({ label, active, color = "green" }) => (
  <div className={`px-3 py-1 rounded-full text-xs font-bold border ${active 
    ? (color === 'purple' ? 'bg-purple-900/50 border-purple-500 text-purple-400' : 'bg-green-900/50 border-green-500 text-green-400') 
    : 'bg-gray-800 border-gray-600 text-gray-500'}`}>
    <span className={`inline-block w-2 h-2 rounded-full mr-2 ${active 
      ? (color === 'purple' ? 'bg-purple-400' : 'bg-green-400') 
      : 'bg-gray-500'}`}></span>
    {label}
  </div>
);

export default App;