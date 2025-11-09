#!/usr/bin/env python3
"""
ECHO Firebase Setup
Initialize Firestore collections for the vibeathon project
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from config import Config

def setup_firebase():
    """Initialize Firebase and create collections"""
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://vibeathon-7b277-default-rtdb.firebaseio.com'
            })
        
        db = firestore.client()
        print(f"[OK] Connected to Firebase project: vibeathon-7b277")
        
        # Create demo team
        team_id = "hackathon_team"
        team_ref = db.collection('team_states').document(team_id)
        team_ref.set({
            'created': datetime.now(),
            'team_name': 'ECHO Hackathon Team',
            'project': 'vibeathon-7b277',
            'last_updated': datetime.now()
        })
        
        # Create demo users
        demo_users = ['developer_001', 'alice', 'bob', 'carol']
        for user_id in demo_users:
            user_ref = team_ref.collection('user_states').document(user_id)
            user_ref.set({
                'state': 'IDLE',
                'timestamp': datetime.now(),
                'user_id': user_id,
                'last_seen': datetime.now(),
                'team_id': team_id
            })
            print(f"[OK] Created user: {user_id}")
        
        # Create user preferences collection
        for user_id in demo_users:
            prefs_ref = db.collection('user_preferences').document(user_id)
            prefs_ref.set({
                'preferences': [],
                'created': datetime.now(),
                'user_id': user_id
            })
        
        print(f"[OK] Firebase setup complete!")
        print(f"     Project: vibeathon-7b277")
        print(f"     Team: {team_id}")
        print(f"     Users: {', '.join(demo_users)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Firebase setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_firebase()