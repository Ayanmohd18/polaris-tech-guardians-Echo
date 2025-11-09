"""
Firebase schema setup for ECHO
Run this once to initialize your Firebase collections
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

def setup_firebase_schema():
    """Initialize Firebase collections and indexes"""
    
    # Initialize Firebase (replace with your credentials)
    # cred = credentials.Certificate("path/to/serviceAccountKey.json")
    # firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    # Create team_states collection structure
    team_ref = db.collection('team_states').document('demo_team')
    team_ref.set({
        'created': datetime.now(),
        'team_name': 'Demo Team'
    })
    
    # Create user_states subcollection
    user_ref = team_ref.collection('user_states').document('demo_user')
    user_ref.set({
        'state': 'IDLE',
        'timestamp': datetime.now(),
        'user_id': 'demo_user'
    })
    
    # Create user_preferences collection
    prefs_ref = db.collection('user_preferences').document('demo_user')
    prefs_ref.set({
        'preferences': [],
        'created': datetime.now()
    })
    
    print("Firebase schema initialized successfully!")
    print("Collections created:")
    print("- team_states/{team_id}/user_states/{user_id}")
    print("- user_preferences/{user_id}")

if __name__ == "__main__":
    setup_firebase_schema()