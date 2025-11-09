#!/usr/bin/env python3
"""
ECHO: The Omniscient Creative Environment
Complete system with Firebase integration
"""

import sys
import threading
import time
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
from cognitive_sensor import CognitiveSensor

class EchoSystem:
    def __init__(self, user_id=Config.DEFAULT_USER_ID, team_id=Config.DEFAULT_TEAM_ID):
        self.user_id = user_id
        self.team_id = team_id
        self.cognitive_sensor = None
        self.db = None
        self.running = False
        
    def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            
            # Test connection by creating initial documents
            self._setup_firebase_collections()
            
            print("[OK] Firebase initialized successfully")
            return True
        except Exception as e:
            print(f"[FAIL] Firebase initialization failed: {e}")
            print("  Note: Using demo credentials - replace with real Firebase project")
            return False
            
    def _setup_firebase_collections(self):
        """Setup initial Firebase collections"""
        try:
            # Create team document
            team_ref = self.db.collection('team_states').document(self.team_id)
            team_ref.set({
                'created': datetime.now(),
                'team_name': f'Team {self.team_id}',
                'last_updated': datetime.now()
            }, merge=True)
            
            # Create user state document
            user_ref = team_ref.collection('user_states').document(self.user_id)
            user_ref.set({
                'state': 'IDLE',
                'timestamp': datetime.now(),
                'user_id': self.user_id,
                'last_seen': datetime.now()
            })
            
            print(f"[OK] Firebase collections setup for team: {self.team_id}, user: {self.user_id}")
            
        except Exception as e:
            print(f"Firebase setup error: {e}")
            
    def start_cognitive_sensor(self):
        """Start the cognitive sensor"""
        try:
            self.cognitive_sensor = CognitiveSensor(self.user_id, self.team_id)
            self.cognitive_sensor.start()
            print("[OK] Cognitive sensor started - monitoring your flow state")
            return True
        except Exception as e:
            print(f"[FAIL] Cognitive sensor failed: {e}")
            return False
            
    def start_team_monitor(self):
        """Start monitoring team states"""
        def monitor_team():
            if not self.db:
                return
                
            try:
                team_ref = self.db.collection('team_states').document(self.team_id).collection('user_states')
                
                def on_snapshot(doc_snapshot, changes, read_time):
                    print(f"\nTeam State Update at {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 40)
                    
                    for doc in doc_snapshot:
                        data = doc.to_dict()
                        user_id = doc.id
                        state = data.get('state', 'UNKNOWN')
                        timestamp = data.get('timestamp')
                        
                        # State indicators
                        indicator = {
                            'FLOWING': '[FLOW]',
                            'STUCK': '[STUCK]', 
                            'FRUSTRATED': '[FRUST]',
                            'IDLE': '[IDLE]'
                        }.get(state, '[?]')
                        
                        print(f"  {indicator} {user_id}: {state}")
                        
                        if user_id == self.user_id:
                            print(f"    ^ That's you! Current state: {state}")
                    
                    print()
                
                team_ref.on_snapshot(on_snapshot)
                print("[OK] Team monitor started - watching team flow states")
                
            except Exception as e:
                print(f"Team monitor error: {e}")
                
        monitor_thread = threading.Thread(target=monitor_team, daemon=True)
        monitor_thread.start()
        
    def simulate_team_activity(self):
        """Simulate other team members for demo"""
        if not self.db:
            return
            
        def simulate():
            team_members = ['alice', 'bob', 'carol']
            states = ['FLOWING', 'STUCK', 'FRUSTRATED', 'IDLE']
            
            while self.running:
                try:
                    for member in team_members:
                        if member != self.user_id:  # Don't override real user
                            import random
                            state = random.choice(states)
                            
                            user_ref = self.db.collection('team_states').document(self.team_id).collection('user_states').document(member)
                            user_ref.set({
                                'state': state,
                                'timestamp': datetime.now(),
                                'user_id': member,
                                'simulated': True
                            })
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    print(f"Simulation error: {e}")
                    
        sim_thread = threading.Thread(target=simulate, daemon=True)
        sim_thread.start()
        print("[OK] Team simulation started - generating demo team activity")
        
    def run(self):
        """Start the complete ECHO system"""
        print("ECHO: The Omniscient Creative Environment")
        print("=" * 60)
        print("Initializing ambient cognitive partner...")
        
        self.running = True
        
        # Initialize Firebase
        firebase_ok = self.initialize_firebase()
        
        # Start cognitive sensor
        sensor_ok = self.start_cognitive_sensor()
        
        if firebase_ok:
            # Start team monitoring
            self.start_team_monitor()
            
            # Start team simulation for demo
            self.simulate_team_activity()
        
        print(f"\nECHO System Active")
        print(f"   User: {self.user_id}")
        print(f"   Team: {self.team_id}")
        print(f"   Firebase: {'OK' if firebase_ok else 'FAILED'}")
        print(f"   Cognitive Sensor: {'OK' if sensor_ok else 'FAILED'}")
        
        if sensor_ok:
            print(f"\nYour cognitive state is being monitored:")
            print("   - FLOWING: High productivity, minimal interruptions")
            print("   - STUCK: Thinking/reading, low activity") 
            print("   - FRUSTRATED: High backspacing, audio spikes")
            print("   - IDLE: No activity detected")
        
        if firebase_ok:
            print(f"\nTeam collaboration features active:")
            print("   - Real-time team state sharing")
            print("   - Intelligent interruption protection")
            print("   - Collective flow awareness")
        
        print(f"\nECHO is now your ambient cognitive partner")
        print("   Press Ctrl+C to stop the system")
        
        try:
            # Keep system running
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
            
        print("[OK] ECHO system shutdown complete")
        print("Thank you for using ECHO - your ambient cognitive partner")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ECHO: The Omniscient Creative Environment")
    parser.add_argument("--user-id", default=Config.DEFAULT_USER_ID, help="Your user ID")
    parser.add_argument("--team-id", default=Config.DEFAULT_TEAM_ID, help="Your team ID")
    
    args = parser.parse_args()
    
    echo = EchoSystem(user_id=args.user_id, team_id=args.team_id)
    
    try:
        echo.run()
    except Exception as e:
        print(f"\nSystem error: {e}")
        echo.shutdown()

if __name__ == "__main__":
    main()