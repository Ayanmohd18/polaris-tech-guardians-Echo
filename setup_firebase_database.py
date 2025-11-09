"""
Setup Firebase Database Schema for ECHO
Creates all necessary collections and initial data
"""

from firebase_config import FirebaseConfig
from datetime import datetime

def setup_firestore_schema():
    """Setup Firestore collections and indexes"""
    
    db = FirebaseConfig.get_firestore()
    
    if not db:
        print("❌ Cannot setup schema: Firebase not initialized")
        print("   Please add your service account key to firebase-credentials.json")
        return False
    
    print("🔧 Setting up Firestore schema...")
    
    # 1. Users Collection
    print("   Creating users collection...")
    users_ref = db.collection('users')
    users_ref.document('demo_user').set({
        'user_id': 'demo_user',
        'display_name': 'Demo User',
        'email': 'demo@echo.ai',
        'created_at': datetime.now(),
        'team_id': 'default_team'
    })
    
    # 2. Team States Collection
    print("   Creating team_states collection...")
    team_states_ref = db.collection('team_states').document('default_team')
    team_states_ref.set({
        'team_id': 'default_team',
        'name': 'Default Team',
        'created_at': datetime.now()
    })
    
    # User states subcollection
    user_states_ref = team_states_ref.collection('user_states')
    user_states_ref.document('demo_user').set({
        'user_id': 'demo_user',
        'state': 'IDLE',
        'timestamp': datetime.now()
    })
    
    # 3. Captured Intents Collection (Feature 10)
    print("   Creating captured_intents collection...")
    db.collection('captured_intents').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 4. User Personas Collection (Feature 11)
    print("   Creating user_personas collection...")
    db.collection('user_personas').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 5. A/B Tests Collection (Feature 12)
    print("   Creating ab_tests collection...")
    db.collection('ab_tests').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 6. Biometric Data Collection (Feature 13)
    print("   Creating biometric_data collection...")
    db.collection('biometric_data').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 7. Project Sonars Collection (Feature 14)
    print("   Creating project_sonars collection...")
    db.collection('project_sonars').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 8. Tasks Collection (Canvas → IDE)
    print("   Creating tasks collection...")
    db.collection('tasks').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 9. Flow Watchers Collection (Team Flow)
    print("   Creating flow_watchers collection...")
    db.collection('flow_watchers').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 10. Notifications Collection
    print("   Creating notifications collection...")
    db.collection('notifications').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 11. User Secrets Collection (Data Bridge)
    print("   Creating user_secrets collection...")
    db.collection('user_secrets').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 12. Harmonizer Events Collection
    print("   Creating harmonizer_events collection...")
    db.collection('harmonizer_events').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 13. Orb Events Collection
    print("   Creating orb_events collection...")
    db.collection('orb_events').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    # 14. Sonar Notifications Collection
    print("   Creating sonar_notifications collection...")
    db.collection('sonar_notifications').document('_init').set({
        'initialized': True,
        'timestamp': datetime.now()
    })
    
    print("✅ Firestore schema setup complete!")
    return True

def setup_realtime_database():
    """Setup Realtime Database structure"""
    
    rtdb = FirebaseConfig.get_realtime_db()
    
    if not rtdb:
        print("⚠️  Realtime Database not available")
        return False
    
    print("🔧 Setting up Realtime Database...")
    
    # Create initial structure
    rtdb.child('echo').set({
        'initialized': True,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })
    
    # Real-time cognitive states
    rtdb.child('cognitive_states').child('demo_user').set({
        'state': 'IDLE',
        'timestamp': datetime.now().isoformat()
    })
    
    print("✅ Realtime Database setup complete!")
    return True

def verify_setup():
    """Verify database setup"""
    
    print("\n🔍 Verifying setup...")
    
    db = FirebaseConfig.get_firestore()
    
    if not db:
        print("❌ Verification failed: Firebase not initialized")
        return False
    
    # Check collections
    collections = [
        'users', 'team_states', 'captured_intents', 'user_personas',
        'ab_tests', 'biometric_data', 'project_sonars', 'tasks',
        'flow_watchers', 'notifications', 'user_secrets',
        'harmonizer_events', 'orb_events', 'sonar_notifications'
    ]
    
    for collection_name in collections:
        try:
            docs = db.collection(collection_name).limit(1).stream()
            count = sum(1 for _ in docs)
            status = "✅" if count > 0 else "⚠️"
            print(f"   {status} {collection_name}: {count} document(s)")
        except Exception as e:
            print(f"   ❌ {collection_name}: Error - {e}")
    
    print("\n✅ Verification complete!")
    return True

def main():
    """Main setup function"""
    
    print("🌟 ECHO Firebase Database Setup")
    print("=" * 50)
    print(f"Project: {FirebaseConfig.PROJECT_ID}")
    print(f"Database: {FirebaseConfig.DATABASE_URL}")
    print()
    
    # Setup Firestore
    if not setup_firestore_schema():
        print("\n❌ Setup failed!")
        print("\n📝 Next steps:")
        print("1. Go to: https://console.firebase.google.com/project/vibeathon-7b277/settings/serviceaccounts/adminsdk")
        print("2. Click 'Generate new private key'")
        print("3. Save the JSON file as 'firebase-credentials.json'")
        print("4. Run this script again")
        return
    
    # Setup Realtime Database
    setup_realtime_database()
    
    # Verify
    verify_setup()
    
    print("\n🚀 Database ready! You can now run:")
    print("   python main.py")

if __name__ == "__main__":
    main()