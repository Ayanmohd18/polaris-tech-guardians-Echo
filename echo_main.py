#!/usr/bin/env python3
"""
ECHO: The Omniscient Creative Environment
Main application launcher
"""

import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
import firebase_admin
from firebase_admin import credentials
from config import Config
from cognitive_sensor import CognitiveSensor
from echo_orb import EchoOrb

class EchoSystem:
    def __init__(self, user_id=Config.DEFAULT_USER_ID, team_id=Config.DEFAULT_TEAM_ID):
        self.user_id = user_id
        self.team_id = team_id
        self.cognitive_sensor = None
        self.echo_orb = None
        
    def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                print("✓ Firebase initialized successfully")
                return True
        except Exception as e:
            print(f"✗ Firebase initialization failed: {e}")
            print("  Please check your firebase-credentials.json file")
            return False
            
    def start_cognitive_sensor(self):
        """Start the cognitive sensor in background"""
        try:
            self.cognitive_sensor = CognitiveSensor(self.user_id, self.team_id)
            self.cognitive_sensor.start()
            print("✓ Cognitive sensor started - monitoring flow state")
            return True
        except Exception as e:
            print(f"✗ Cognitive sensor failed to start: {e}")
            return False
            
    def start_echo_orb(self):
        """Start the ECHO Orb UI"""
        try:
            app = QApplication(sys.argv)
            self.echo_orb = EchoOrb(self.user_id, self.team_id)
            self.echo_orb.show()
            print("✓ ECHO Orb activated - your ambient partner is ready")
            return app.exec()
        except Exception as e:
            print(f"✗ ECHO Orb failed to start: {e}")
            return 1
            
    def run(self):
        """Start the complete ECHO system"""
        print("🌟 Initializing ECHO: The Omniscient Creative Environment")
        print("=" * 60)
        
        # Initialize Firebase
        if not self.initialize_firebase():
            print("\n⚠️  Continuing without Firebase - some features will be limited")
            
        # Start cognitive sensor
        if not self.start_cognitive_sensor():
            print("\n⚠️  Continuing without cognitive sensor")
            
        print(f"\n🚀 Starting ECHO for user: {self.user_id}")
        print(f"   Team: {self.team_id}")
        print("\n   Your ambient cognitive partner is now active.")
        print("   The orb will appear in the bottom-right corner.")
        print("   Click it when you need assistance.")
        print("\n   Press Ctrl+C to stop ECHO")
        
        # Start UI (blocking)
        try:
            return self.start_echo_orb()
        except KeyboardInterrupt:
            self.shutdown()
            return 0
            
    def shutdown(self):
        """Clean shutdown of all components"""
        print("\n🛑 Shutting down ECHO system...")
        
        if self.cognitive_sensor:
            self.cognitive_sensor.stop()
            print("✓ Cognitive sensor stopped")
            
        print("✓ ECHO system shutdown complete")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ECHO: The Omniscient Creative Environment")
    parser.add_argument("--user-id", default=Config.DEFAULT_USER_ID, help="User ID")
    parser.add_argument("--team-id", default=Config.DEFAULT_TEAM_ID, help="Team ID")
    
    args = parser.parse_args()
    
    # Create and run ECHO system
    echo = EchoSystem(user_id=args.user_id, team_id=args.team_id)
    
    try:
        sys.exit(echo.run())
    except KeyboardInterrupt:
        echo.shutdown()
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 ECHO system error: {e}")
        echo.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()