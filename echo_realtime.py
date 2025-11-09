#!/usr/bin/env python3
"""
ECHO: Real-time Cognitive System
Firebase Realtime Database integration for vibeathon project
"""

import sys
import threading
import time
import json
import requests
from datetime import datetime
from cognitive_sensor import CognitiveSensor

class EchoRealtime:
    def __init__(self, user_id="developer_001", team_id="hackathon_team"):
        self.user_id = user_id
        self.team_id = team_id
        self.cognitive_sensor = None
        self.running = False
        
        # Firebase Realtime Database URL
        self.firebase_url = "https://vibeathon-7b277-default-rtdb.firebaseio.com"
        
    def update_user_state(self, state):
        """Update user state in Firebase Realtime Database"""
        try:
            data = {
                'state': state,
                'timestamp': datetime.now().isoformat(),
                'user_id': self.user_id,
                'team_id': self.team_id
            }
            
            url = f"{self.firebase_url}/team_states/{self.team_id}/users/{self.user_id}.json"
            response = requests.put(url, json=data)
            
            if response.status_code == 200:
                print(f"[OK] State updated: {state}")
                return True
            else:
                print(f"[FAIL] Firebase update failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Firebase error: {e}")
            return False
    
    def get_team_states(self):
        """Get all team member states"""
        try:
            url = f"{self.firebase_url}/team_states/{self.team_id}/users.json"
            response = requests.get(url)
            
            if response.status_code == 200:
                return response.json() or {}
            return {}
            
        except Exception as e:
            print(f"Team state fetch error: {e}")
            return {}
    
    def monitor_team(self):
        """Monitor team states in real-time"""
        def monitor():
            last_states = {}
            
            while self.running:
                try:
                    current_states = self.get_team_states()
                    
                    if current_states != last_states:
                        print(f"\nTeam Update at {datetime.now().strftime('%H:%M:%S')}")
                        print("-" * 40)
                        
                        for user_id, data in current_states.items():
                            if isinstance(data, dict):
                                state = data.get('state', 'UNKNOWN')
                                indicator = {
                                    'FLOWING': '[FLOW]',
                                    'STUCK': '[STUCK]',
                                    'FRUSTRATED': '[FRUST]',
                                    'IDLE': '[IDLE]'
                                }.get(state, '[?]')
                                
                                print(f"  {indicator} {user_id}: {state}")
                                
                                if user_id == self.user_id:
                                    print(f"    ^ That's you!")
                        
                        last_states = current_states.copy()
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    print(f"Monitor error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        print("[OK] Team monitor started")
    
    def simulate_team_activity(self):
        """Simulate team members for demo"""
        def simulate():
            import random
            team_members = ['alice', 'bob', 'carol']
            states = ['FLOWING', 'STUCK', 'FRUSTRATED', 'IDLE']
            
            while self.running:
                try:
                    for member in team_members:
                        if member != self.user_id:
                            state = random.choice(states)
                            data = {
                                'state': state,
                                'timestamp': datetime.now().isoformat(),
                                'user_id': member,
                                'team_id': self.team_id,
                                'simulated': True
                            }
                            
                            url = f"{self.firebase_url}/team_states/{self.team_id}/users/{member}.json"
                            requests.put(url, json=data)
                    
                    time.sleep(8)  # Update every 8 seconds
                    
                except Exception as e:
                    print(f"Simulation error: {e}")
                    time.sleep(5)
        
        sim_thread = threading.Thread(target=simulate, daemon=True)
        sim_thread.start()
        print("[OK] Team simulation started")
    
    def start_cognitive_sensor(self):
        """Start cognitive sensor with Firebase integration"""
        class FirebaseIntegratedSensor(CognitiveSensor):
            def __init__(self, user_id, team_id, firebase_updater):
                self.user_id = user_id
                self.team_id = team_id
                self.firebase_updater = firebase_updater
                self.current_state = "IDLE"
                self.running = False
                
                # Activity tracking
                from collections import deque
                self.typing_events = deque(maxlen=20)
                self.backspace_count = 0
                self.mouse_events = deque(maxlen=10)
                self.last_activity_time = time.time()
                self.audio_levels = deque(maxlen=10)
                
                # Initialize components without Firebase
                self.db = None
                
                try:
                    import cv2
                    self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    self.cap = None
                except:
                    print("OpenCV not available - gaze tracking disabled")
                    self.face_cascade = None
                    self.cap = None
                
                self.keyboard_listener = None
                self.mouse_listener = None
            
            def _update_firebase(self, state):
                """Override to use REST API instead of Admin SDK"""
                self.firebase_updater(state)
        
        try:
            self.cognitive_sensor = FirebaseIntegratedSensor(
                self.user_id, 
                self.team_id, 
                self.update_user_state
            )
            self.cognitive_sensor.start()
            print("[OK] Cognitive sensor started")
            return True
        except Exception as e:
            print(f"[FAIL] Cognitive sensor failed: {e}")
            return False
    
    def run(self):
        """Start the complete ECHO system"""
        print("ECHO: The Omniscient Creative Environment")
        print("=" * 60)
        print("Connecting to Firebase Realtime Database...")
        
        self.running = True
        
        # Test Firebase connection
        firebase_ok = self.update_user_state("IDLE")
        
        # Start cognitive sensor
        sensor_ok = self.start_cognitive_sensor()
        
        if firebase_ok:
            # Start team monitoring
            self.monitor_team()
            
            # Start team simulation
            self.simulate_team_activity()
        
        print(f"\nECHO System Active")
        print(f"   User: {self.user_id}")
        print(f"   Team: {self.team_id}")
        print(f"   Firebase: {'OK' if firebase_ok else 'FAILED'}")
        print(f"   Cognitive Sensor: {'OK' if sensor_ok else 'FAILED'}")
        print(f"   Project: vibeathon-7b277")
        
        if sensor_ok:
            print(f"\nCognitive monitoring active:")
            print("   - FLOWING: High productivity")
            print("   - STUCK: Thinking/reading")
            print("   - FRUSTRATED: High backspacing")
            print("   - IDLE: No activity")
        
        if firebase_ok:
            print(f"\nTeam collaboration features:")
            print("   - Real-time state sharing")
            print("   - Team flow awareness")
            print("   - Intelligent interruption protection")
        
        print(f"\nECHO is monitoring your cognitive state")
        print("Press Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        print("\nShutting down ECHO system...")
        self.running = False
        
        if self.cognitive_sensor:
            self.cognitive_sensor.stop()
            print("[OK] Cognitive sensor stopped")
        
        # Final state update
        self.update_user_state("OFFLINE")
        
        print("[OK] ECHO system shutdown complete")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ECHO: Real-time Cognitive System")
    parser.add_argument("--user-id", default="developer_001", help="Your user ID")
    parser.add_argument("--team-id", default="hackathon_team", help="Your team ID")
    
    args = parser.parse_args()
    
    echo = EchoRealtime(user_id=args.user_id, team_id=args.team_id)
    
    try:
        echo.run()
    except Exception as e:
        print(f"\nSystem error: {e}")
        echo.shutdown()

if __name__ == "__main__":
    main()