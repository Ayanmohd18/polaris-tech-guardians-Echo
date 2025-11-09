#!/usr/bin/env python3
"""
ECHO FastAPI Backend
Real-time cognitive monitoring API with WebSocket support
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import asyncio
import threading
import time
from datetime import datetime
from cognitive_sensor import CognitiveSensor
from collections import defaultdict

app = FastAPI(title="ECHO Cognitive API")

# Enable CORS for React frontend
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
        
        # Simplified initialization without Firebase
        from collections import deque
        self.typing_events = deque(maxlen=20)
        self.backspace_count = 0
        self.mouse_events = deque(maxlen=10)
        self.last_activity_time = time.time()
        self.audio_levels = deque(maxlen=10)
        
        self.keyboard_listener = None
        self.mouse_listener = None
        self.db = None
        
        # Skip camera and audio for API version
        self.cap = None
        self.face_cascade = None
    
    def _track_gaze(self):
        return {'focused': True, 'confidence': 0.8}
    
    def _track_audio(self):
        return {'rms': 0.01, 'spike_detected': False}
    
    def _update_firebase(self, state):
        """Override to update API state"""
        user_states[self.user_id] = {
            'state': state,
            'timestamp': datetime.now().isoformat(),
            'user_id': self.user_id,
            'team_id': self.team_id
        }
        
        # Broadcast to WebSocket connections
        asyncio.create_task(broadcast_state_update(self.user_id, state))

async def broadcast_state_update(user_id, state):
    """Broadcast state updates to connected WebSocket clients"""
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/states")
async def get_all_states():
    """Get all user states"""
    return user_states

@app.get("/api/states/{user_id}")
async def get_user_state(user_id: str):
    """Get specific user state"""
    return user_states.get(user_id, {"state": "UNKNOWN", "user_id": user_id})

@app.post("/api/start/{user_id}")
async def start_monitoring(user_id: str):
    """Start cognitive monitoring for a user"""
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
    """Stop cognitive monitoring for a user"""
    if user_id in sensors:
        sensors[user_id].stop()
        del sensors[user_id]
        
        # Update state to offline
        user_states[user_id] = {
            'state': 'OFFLINE',
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        }
        
        return {"status": "stopped", "user_id": user_id}
    
    return {"status": "not_running", "user_id": user_id}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    connections[user_id] = websocket
    
    try:
        # Send initial state
        if user_id in user_states:
            await websocket.send_text(json.dumps({
                'type': 'state_update',
                'user_id': user_id,
                'state': user_states[user_id]['state'],
                'timestamp': user_states[user_id]['timestamp'],
                'team_states': user_states
            }))
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        if user_id in connections:
            del connections[user_id]

# Simulate team activity for demo
async def simulate_team():
    """Simulate team members for demo purposes"""
    import random
    team_members = ['alice', 'bob', 'carol']
    states = ['FLOWING', 'STUCK', 'FRUSTRATED', 'IDLE']
    
    while True:
        for member in team_members:
            if member not in sensors:  # Only simulate if not real user
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
    """Start background tasks"""
    asyncio.create_task(simulate_team())

if __name__ == "__main__":
    print("Starting ECHO API Server")
    print("=" * 30)
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("WebSocket: ws://localhost:8000/ws/{user_id}")
    print("\nPress Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)