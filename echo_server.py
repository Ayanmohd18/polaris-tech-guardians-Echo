#!/usr/bin/env python3
"""
ECHO Local Server
FastAPI server with WebSocket support for real-time cognitive monitoring
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
import asyncio
from datetime import datetime
from cognitive_sensor import CognitiveSensor
import threading

app = FastAPI(title="ECHO Cognitive System")

# Store active connections and states
connections = {}
user_states = {}

@app.get("/")
async def get_dashboard():
    """Serve the ECHO dashboard"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>ECHO: Cognitive Dashboard</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0; padding: 20px; color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .orb { 
            width: 100px; height: 100px; border-radius: 50%;
            margin: 20px auto; transition: all 0.3s ease;
            box-shadow: 0 0 30px rgba(255,255,255,0.3);
        }
        .flowing { background: #4CAF50; animation: pulse 2s infinite; }
        .stuck { background: #2196F3; animation: pulse 1s infinite; }
        .frustrated { background: #FF9800; animation: shake 0.5s infinite; }
        .idle { background: #9E9E9E; }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .team-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-top: 30px;
        }
        .user-card {
            background: rgba(255,255,255,0.1); border-radius: 10px;
            padding: 20px; text-align: center; backdrop-filter: blur(10px);
        }
        .state-indicator {
            width: 20px; height: 20px; border-radius: 50%;
            display: inline-block; margin-right: 10px;
        }
        .stats { margin-top: 20px; }
        .stat { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 ECHO: The Omniscient Creative Environment</h1>
            <p>Real-time Cognitive State Monitoring</p>
        </div>
        
        <div class="user-card">
            <h2 id="current-user">developer_001</h2>
            <div id="user-orb" class="orb idle"></div>
            <h3 id="current-state">IDLE</h3>
            <div class="stats">
                <div class="stat">Last Update: <span id="last-update">--</span></div>
                <div class="stat">Session Time: <span id="session-time">00:00</span></div>
            </div>
        </div>
        
        <div class="team-grid" id="team-grid">
            <!-- Team members will be populated here -->
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <button onclick="startMonitoring()" style="padding: 10px 20px; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Start Cognitive Monitoring
            </button>
        </div>
    </div>

    <script>
        let ws = null;
        let sessionStart = new Date();
        
        function updateSessionTime() {
            const now = new Date();
            const diff = Math.floor((now - sessionStart) / 1000);
            const minutes = Math.floor(diff / 60);
            const seconds = diff % 60;
            document.getElementById('session-time').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://localhost:8000/ws/developer_001`);
            
            ws.onopen = function(event) {
                console.log('Connected to ECHO system');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateUserState(data);
            };
            
            ws.onclose = function(event) {
                console.log('Disconnected from ECHO system');
                setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
            };
        }
        
        function updateUserState(data) {
            if (data.type === 'state_update') {
                const state = data.state;
                const orb = document.getElementById('user-orb');
                const stateText = document.getElementById('current-state');
                const lastUpdate = document.getElementById('last-update');
                
                // Update orb appearance
                orb.className = `orb ${state.toLowerCase()}`;
                stateText.textContent = state;
                lastUpdate.textContent = new Date().toLocaleTimeString();
                
                // Update team grid if team data is available
                if (data.team_states) {
                    updateTeamGrid(data.team_states);
                }
            }
        }
        
        function updateTeamGrid(teamStates) {
            const grid = document.getElementById('team-grid');
            grid.innerHTML = '';
            
            Object.entries(teamStates).forEach(([userId, userData]) => {
                if (userId !== 'developer_001') {
                    const card = document.createElement('div');
                    card.className = 'user-card';
                    card.innerHTML = `
                        <h3>${userId}</h3>
                        <div class="state-indicator ${userData.state.toLowerCase()}" style="background: ${getStateColor(userData.state)};"></div>
                        <span>${userData.state}</span>
                        <div class="stat">Last seen: ${new Date(userData.timestamp).toLocaleTimeString()}</div>
                    `;
                    grid.appendChild(card);
                }
            });
        }
        
        function getStateColor(state) {
            const colors = {
                'FLOWING': '#4CAF50',
                'STUCK': '#2196F3',
                'FRUSTRATED': '#FF9800',
                'IDLE': '#9E9E9E'
            };
            return colors[state] || '#9E9E9E';
        }
        
        function startMonitoring() {
            fetch('/start_monitoring', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Monitoring started:', data);
                });
        }
        
        // Initialize
        connectWebSocket();
        setInterval(updateSessionTime, 1000);
    </script>
</body>
</html>
    """)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    connections[user_id] = websocket
    
    try:
        while True:
            # Send current state if available
            if user_id in user_states:
                await websocket.send_text(json.dumps({
                    "type": "state_update",
                    "user_id": user_id,
                    "state": user_states[user_id]["state"],
                    "timestamp": user_states[user_id]["timestamp"],
                    "team_states": user_states
                }))
            
            await asyncio.sleep(2)  # Send updates every 2 seconds
            
    except WebSocketDisconnect:
        del connections[user_id]

@app.post("/start_monitoring")
async def start_monitoring():
    """Start cognitive monitoring"""
    def run_sensor():
        class LocalCognitiveSensor(CognitiveSensor):
            def __init__(self, user_id):
                self.user_id = user_id
                self.current_state = "IDLE"
                self.running = False
                
                # Simplified initialization
                from collections import deque
                self.typing_events = deque(maxlen=20)
                self.backspace_count = 0
                self.mouse_events = deque(maxlen=10)
                self.last_activity_time = time.time()
                
                self.keyboard_listener = None
                self.mouse_listener = None
                self.db = None  # No Firebase needed
            
            def _update_firebase(self, state):
                """Override to update local state instead"""
                user_states[self.user_id] = {
                    "state": state,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": self.user_id
                }
                print(f"State updated: {self.user_id} -> {state}")
        
        sensor = LocalCognitiveSensor("developer_001")
        sensor.start()
        
        # Keep sensor running
        try:
            while True:
                time.sleep(1)
        except:
            sensor.stop()
    
    # Start sensor in background thread
    sensor_thread = threading.Thread(target=run_sensor, daemon=True)
    sensor_thread.start()
    
    return {"status": "monitoring_started", "user_id": "developer_001"}

@app.get("/api/states")
async def get_states():
    """Get current user states"""
    return user_states

if __name__ == "__main__":
    print("Starting ECHO Local Server")
    print("=" * 40)
    print("Dashboard: http://localhost:8000")
    print("API: http://localhost:8000/api/states")
    print("WebSocket: ws://localhost:8000/ws/{user_id}")
    print("\nPress Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)