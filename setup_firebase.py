#!/usr/bin/env python3
"""
Firebase Setup Script for ECHO
This script will help you configure Firebase with your credentials
"""

import json
import os

def setup_firebase_config():
    """Interactive Firebase configuration setup"""
    print("ECHO Firebase Configuration Setup")
    print("=" * 40)
    
    print("\nPlease provide your Firebase project details:")
    
    # Get Firebase project details
    project_id = input("Firebase Project ID: ").strip()
    private_key_id = input("Private Key ID: ").strip()
    private_key = input("Private Key (paste the full key): ").strip()
    client_email = input("Client Email: ").strip()
    client_id = input("Client ID: ").strip()
    
    # Create Firebase credentials JSON
    firebase_config = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id,
        "private_key": private_key.replace('\\n', '\n'),  # Fix newlines
        "client_email": client_email,
        "client_id": client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}"
    }
    
    # Save to file
    with open('firebase-credentials.json', 'w') as f:
        json.dump(firebase_config, f, indent=2)
    
    # Update .env file
    env_content = f"""FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
OPENAI_API_KEY=your_openai_key_here
DEFAULT_USER_ID=developer_001
DEFAULT_TEAM_ID=hackathon_team
SENSOR_UPDATE_INTERVAL=3
ACTIVITY_THRESHOLD=60
API_HOST=0.0.0.0
API_PORT=8000"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✓ Firebase credentials saved to firebase-credentials.json")
    print("✓ Environment configuration updated")
    print("\nYou can now run ECHO with:")
    print("python echo_system.py")

def setup_firebase_from_json():
    """Setup Firebase from existing service account JSON"""
    print("ECHO Firebase Configuration from JSON")
    print("=" * 40)
    
    json_path = input("Path to your Firebase service account JSON file: ").strip()
    
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found")
        return
    
    # Copy the file to our expected location
    import shutil
    shutil.copy(json_path, 'firebase-credentials.json')
    
    print("✓ Firebase credentials configured")
    print("\nYou can now run ECHO with:")
    print("python echo_system.py")

def main():
    print("Choose Firebase setup method:")
    print("1. Enter credentials manually")
    print("2. Use existing service account JSON file")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        setup_firebase_config()
    elif choice == "2":
        setup_firebase_from_json()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()