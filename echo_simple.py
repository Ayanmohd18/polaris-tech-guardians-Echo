#!/usr/bin/env python3
"""
ECHO Simple Server
Minimal Bio-Cognitive HUD on port 8000
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
import threading
import time
from datetime import datetime
from cognitive_sensor import CognitiveSensor

app = FastAPI(title="ECHO Bio-Cognitive System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
user_states = {}
connections = {}
sensors = {}

class APICognitiveSensor(CognitiveSensor):
    def __init__(self, user_id, team_id="hackathon_team"):
        self.user_id = user_id
        self.team_id = team_id
        self.current_state = "IDLE"
        self.running = False
        
        from collections import deque
        self.typing_events = deque(maxlen=20)
        self.backspace_count = 0
        self.mouse_events = deque(maxlen=10)
        self.last_activity_time = time.time()
        
        self.keyboard_listener = None
        self.mouse_listener = None
        self.db = None
        self.cap = None
        self.face_cascade = None
    
    def _track_gaze(self):
        return {'focused': True, 'confidence': 0.8}
    
    def _track_audio(self):
        return {'rms': 0.01, 'spike_detected': False}
    
    def _update_firebase(self, state):
        user_states[self.user_id] = {
            'state': state,
            'timestamp': datetime.now().isoformat(),
            'user_id': self.user_id,
            'team_id': self.team_id
        }
        asyncio.create_task(broadcast_state_update(self.user_id, state))

async def broadcast_state_update(user_id, state):
    if user_id in connections:
        try:
            await connections[user_id].send_text(json.dumps({
                'type': 'state_update',
                'user_id': user_id,
                'state': state,
                'timestamp': datetime.now().isoformat(),
                'team_states': user_states
            }))
        except:
            pass

@app.get("/")
async def get_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>ECHO: Bio-Cognitive HUD</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at center, #0a0a0a 0%, #000000 100%);
            color: #fff;
            overflow: hidden;
            height: 100vh;
        }
        
        .bio-hud {
            position: relative;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .ndot57-title {
            font-family: 'Courier New', monospace;
            font-size: 4rem;
            letter-spacing: 0.3em;
            text-transform: uppercase;
            font-weight: bold;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.8);
            animation: emissiveGlow 3s ease-in-out infinite alternate;
            margin-bottom: 20px;
        }
        
        .subtitle {
            font-size: 1.2rem;
            letter-spacing: 0.2em;
            opacity: 0.8;
            margin-bottom: 40px;
        }
        
        .orb {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: #9E9E9E;
            margin: 30px;
            transition: all 0.8s ease;
            box-shadow: 0 0 50px rgba(158, 158, 158, 0.6);
            animation: pulse 2s infinite;
        }
        
        .orb.flowing {
            background: #4CAF50;
            box-shadow: 0 0 60px rgba(76, 175, 80, 0.8);
        }
        
        .orb.stuck {
            background: #2196F3;
            box-shadow: 0 0 60px rgba(33, 150, 243, 0.8);
        }
        
        .orb.frustrated {
            background: #FF9800;
            box-shadow: 0 0 60px rgba(255, 152, 0, 0.8);
            animation: shake 0.5s infinite;
        }
        
        .orb.idle {
            background: #9E9E9E;
            box-shadow: 0 0 40px rgba(158, 158, 158, 0.4);
        }
        
        .state-display {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .state-desc {
            font-size: 1rem;
            opacity: 0.8;
            margin-bottom: 30px;
        }
        
        .controls {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .bio-button {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            padding: 15px 30px;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        
        .bio-button:hover {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .bio-button.primary {
            background: linear-gradient(135deg, #4CAF50, #45a049);
        }
        
        .bio-button.danger {
            background: linear-gradient(135deg, #f44336, #da190b);
        }
        
        .status-panel {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 20px;
            min-width: 300px;
        }
        
        .team-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 20px;
            min-width: 250px;
        }
        
        .team-member {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
        }
        
        .state-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        
        .logs {
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 15px;
            max-height: 150px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        @keyframes emissiveGlow {
            0% { text-shadow: 0 0 30px rgba(255, 255, 255, 0.5); }
            100% { text-shadow: 0 0 50px rgba(255, 255, 255, 0.9); }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-3px); }
            75% { transform: translateX(3px); }
        }
        
        .glitch-effect {
            animation: glitchShake 0.2s ease-in-out;
        }
        
        @keyframes glitchShake {
            0%, 100% { transform: translateX(0); }
            10% { transform: translateX(-2px) translateY(1px); }
            20% { transform: translateX(2px) translateY(-1px); }
            30% { transform: translateX(-1px) translateY(2px); }
            40% { transform: translateX(1px) translateY(-2px); }
            50% { transform: translateX(-2px) translateY(1px); }
            60% { transform: translateX(2px) translateY(-1px); }
            70% { transform: translateX(-1px) translateY(2px); }
            80% { transform: translateX(1px) translateY(-2px); }
            90% { transform: translateX(-2px) translateY(1px); }
        }
    </style>
</head>
<body>
    <div class="bio-hud">
        <h1 class="ndot57-title">ECHO</h1>
        <p class="subtitle">OMNISCIENT CREATIVE ENVIRONMENT</p>
        
        <div id="orb" class="orb idle"></div>
        
        <div id="state-display" class="state-display">IDLE</div>
        <div id="state-desc" class="state-desc">Baseline monitoring • Ready for engagement</div>
        
        <div class="controls">
            <button id="start-btn" class="bio-button primary" onclick="startMonitoring()">
                INITIATE NEURAL LINK
            </button>
            <button id="stop-btn" class="bio-button danger" onclick="stopMonitoring()">
                TERMINATE LINK
            </button>
        </div>
        
        <div class="status-panel">
            <h3 style="margin-bottom: 15px; font-family: 'Courier New', monospace; letter-spacing: 0.1em;">COGNITIVE STATUS</h3>
            <div>USER: developer_001</div>
            <div>SESSION: <span id="session-time">00:00:00</span></div>
            <div>LAST UPDATE: <span id="last-update">--</span></div>
        </div>
        
        <div class="team-panel">
            <h3 style="margin-bottom: 15px; font-family: 'Courier New', monospace; letter-spacing: 0.1em;">TEAM NEURAL NETWORK</h3>
            <div id="team-members"></div>
        </div>
        
        <div class="logs" id="logs">
            <div>[00:00:00] ECHO Bio-Cognitive HUD initialized</div>
        </div>
    </div>

    <script>
        let ws = null;
        let sessionStart = new Date();
        let isMonitoring = false;
        
        function updateSessionTime() {
            const now = new Date();
            const diff = Math.floor((now - sessionStart) / 1000);
            const hours = Math.floor(diff / 3600);
            const minutes = Math.floor((diff % 3600) / 60);
            const seconds = diff % 60;
            
            document.getElementById('session-time').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/developer_001`);
            
            ws.onopen = function() {
                addLog('Neural link established');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'state_update') {
                    updateCognitiveState(data.state);
                    updateTeamStates(data.team_states);
                    
                    if (data.state === 'FRUSTRATED') {
                        document.body.classList.add('glitch-effect');
                        setTimeout(() => {
                            document.body.classList.remove('glitch-effect');
                        }, 200);
                    }
                }
            };
            
            ws.onclose = function() {
                addLog('Neural link disconnected - reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        function updateCognitiveState(state) {
            const orb = document.getElementById('orb');
            const stateDisplay = document.getElementById('state-display');
            const stateDesc = document.getElementById('state-desc');
            const lastUpdate = document.getElementById('last-update');
            
            orb.className = `orb ${state.toLowerCase()}`;
            stateDisplay.textContent = state;
            lastUpdate.textContent = new Date().toLocaleTimeString();
            
            const descriptions = {
                FLOWING: 'Neural pathways optimized • Deep focus achieved',
                STUCK: 'Cognitive processing • Seeking new perspectives',
                FRUSTRATED: 'Stress patterns detected • Recalibrating approach',
                IDLE: 'Baseline monitoring • Ready for engagement',
                OFFLINE: 'Neural link terminated • Standby mode'
            };
            
            stateDesc.textContent = descriptions[state] || 'Unknown cognitive pattern';
            addLog(`Cognitive state: ${state}`);
        }
        
        function updateTeamStates(teamStates) {
            const teamContainer = document.getElementById('team-members');
            teamContainer.innerHTML = '';
            
            Object.entries(teamStates).forEach(([userId, userData]) => {
                if (userId !== 'developer_001') {
                    const memberDiv = document.createElement('div');
                    memberDiv.className = 'team-member';
                    
                    const indicator = document.createElement('div');
                    indicator.className = 'state-indicator';
                    indicator.style.backgroundColor = getStateColor(userData.state);
                    
                    const info = document.createElement('div');
                    info.innerHTML = `
                        <div style="font-weight: bold; font-family: 'Courier New', monospace;">${userId.toUpperCase()}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">${userData.state} • ${userData.simulated ? 'SIM' : 'LIVE'}</div>
                    `;
                    
                    memberDiv.appendChild(indicator);
                    memberDiv.appendChild(info);
                    teamContainer.appendChild(memberDiv);
                }
            });
        }
        
        function getStateColor(state) {
            const colors = {
                FLOWING: '#4CAF50',
                STUCK: '#2196F3',
                FRUSTRATED: '#FF9800',
                IDLE: '#9E9E9E',
                OFFLINE: '#424242'
            };
            return colors[state] || '#9E9E9E';
        }
        
        function addLog(message) {
            const logs = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] ${message}`;
            logs.appendChild(logEntry);
            logs.scrollTop = logs.scrollHeight;
            
            // Keep only last 10 logs
            while (logs.children.length > 10) {
                logs.removeChild(logs.firstChild);
            }
        }
        
        async function startMonitoring() {
            try {
                const response = await fetch('/api/start/developer_001', { method: 'POST' });
                const data = await response.json();
                if (data.status === 'started' || data.status === 'already_running') {
                    isMonitoring = true;
                    document.getElementById('start-btn').textContent = 'NEURAL LINK ACTIVE';
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                    addLog('Bio-cognitive monitoring initiated');
                }
            } catch (error) {
                addLog('Neural link failed to establish');
            }
        }
        
        async function stopMonitoring() {
            try {
                const response = await fetch('/api/stop/developer_001', { method: 'POST' });
                const data = await response.json();
                if (data.status === 'stopped' || data.status === 'not_running') {
                    isMonitoring = false;
                    document.getElementById('start-btn').textContent = 'INITIATE NEURAL LINK';
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    updateCognitiveState('OFFLINE');
                    addLog('Bio-cognitive monitoring terminated');
                }
            } catch (error) {
                addLog('Neural link termination failed');
            }
        }
        
        // Initialize
        connectWebSocket();
        setInterval(updateSessionTime, 1000);
        document.getElementById('stop-btn').disabled = true;
    </script>
</body>
</html>
    """)

@app.post("/api/start/{user_id}")
async def start_monitoring(user_id: str):
    if user_id in sensors:
        return {"status": "already_running", "user_id": user_id}
    
    def run_sensor():
        sensor = APICognitiveSensor(user_id)
        sensors[user_id] = sensor
        sensor.start()
        
        try:
            while sensor.running:
                time.sleep(1)
        except:
            pass
    
    sensor_thread = threading.Thread(target=run_sensor, daemon=True)
    sensor_thread.start()
    
    return {"status": "started", "user_id": user_id}

@app.post("/api/stop/{user_id}")
async def stop_monitoring(user_id: str):
    if user_id in sensors:
        sensors[user_id].stop()
        del sensors[user_id]
        
        user_states[user_id] = {
            'state': 'OFFLINE',
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        }
        
        return {"status": "stopped", "user_id": user_id}
    
    return {"status": "not_running", "user_id": user_id}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connections[user_id] = websocket
    
    try:
        if user_id in user_states:
            await websocket.send_text(json.dumps({
                'type': 'state_update',
                'user_id': user_id,
                'state': user_states[user_id]['state'],
                'timestamp': user_states[user_id]['timestamp'],
                'team_states': user_states
            }))
        
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        if user_id in connections:
            del connections[user_id]

async def simulate_team():
    import random
    team_members = ['alice', 'bob', 'carol']
    states = ['FLOWING', 'STUCK', 'FRUSTRATED', 'IDLE']
    
    while True:
        for member in team_members:
            if member not in sensors:
                state = random.choice(states)
                user_states[member] = {
                    'state': state,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': member,
                    'team_id': 'hackathon_team',
                    'simulated': True
                }
        
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulate_team())

if __name__ == "__main__":
    print("ECHO: Bio-Cognitive HUD System")
    print("=" * 40)
    print("Dashboard: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)