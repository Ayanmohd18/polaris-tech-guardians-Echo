#!/usr/bin/env python3
"""
ECHO: The Omniscient Creative Environment
Main application entry point
"""

import sys
import asyncio
import threading
from PyQt6.QtWidgets import QApplication
import firebase_admin
from firebase_admin import credentials
from echo_core.sensors.cognitive_sensor import CognitiveSensor
from echo_core.ui.echo_orb import EchoOrb
from echo_core.sensors.contextual_synthesizer import ContextualSynthesizer
import uvicorn
from echo_core.api.echo_api import app

class EchoSystem:
    def __init__(self, user_id="user123", team_id="team456", openai_key=None):
        self.user_id = user_id
        self.team_id = team_id
        self.openai_key = openai_key
        
        # Core components
        self.cognitive_sensor = None
        self.echo_orb = None
        self.synthesizer = None
        self.api_server = None
        
    def initialize_firebase(self, credentials_path=None):
        """Initialize Firebase - replace with your credentials"""
        try:
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                # For demo - you'll need actual Firebase credentials
                print("Warning: Using demo mode - Firebase features limited")
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            
    def start_api_server(self):
        """Start FastAPI server in background thread"""
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
            
        self.api_server = threading.Thread(target=run_server, daemon=True)
        self.api_server.start()
        print("ECHO API server started on http://localhost:8000")
        
    def start_cognitive_sensor(self):
        """Start the multimodal cognitive sensor"""
        self.cognitive_sensor = CognitiveSensor(self.user_id, self.team_id)
        self.cognitive_sensor.start()
        print("Cognitive sensor started - monitoring flow state")
        
    def start_synthesizer(self):
        """Start the contextual synthesizer"""
        self.synthesizer = ContextualSynthesizer(self.user_id)
        self.synthesizer.start()
        print("Contextual synthesizer started - watching for connections")
        
    def start_ui(self):
        """Start the ECHO Orb UI"""
        app = QApplication(sys.argv)
        self.echo_orb = EchoOrb(self.user_id, self.team_id)
        self.echo_orb.show()
        print("ECHO Orb activated - ambient partner ready")
        return app.exec()
        
    def run(self, firebase_credentials=None):
        """Start the complete ECHO system"""
        print("🌟 Initializing ECHO: The Omniscient Creative Environment")
        
        # Initialize Firebase
        self.initialize_firebase(firebase_credentials)
        
        # Start background services
        self.start_api_server()
        self.start_cognitive_sensor()
        self.start_synthesizer()
        
        # Start UI (blocking)
        print("🚀 ECHO is now active - your ambient cognitive partner")
        return self.start_ui()
        
    def shutdown(self):
        """Clean shutdown of all components"""
        if self.cognitive_sensor:
            self.cognitive_sensor.stop()
        if self.synthesizer:
            self.synthesizer.stop()
        print("ECHO system shutdown complete")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ECHO: The Omniscient Creative Environment")
    parser.add_argument("--user-id", default="user123", help="User ID")
    parser.add_argument("--team-id", default="team456", help="Team ID")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--firebase-creds", help="Path to Firebase credentials JSON")
    
    args = parser.parse_args()
    
    # Create and run ECHO system
    echo = EchoSystem(
        user_id=args.user_id,
        team_id=args.team_id,
        openai_key=args.openai_key
    )
    
    try:
        echo.run(args.firebase_creds)
    except KeyboardInterrupt:
        echo.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()