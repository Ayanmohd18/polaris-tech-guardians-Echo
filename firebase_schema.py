"""
Firebase Schema Setup for ECHO
Creates the necessary collections and documents for the interruption service
"""

import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import time

class FirebaseSchemaSetup:
    def __init__(self):
        self._init_firebase()
    
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def setup_schema(self):
        """Set up the complete Firebase schema for ECHO"""
        if not self.db:
            print("Cannot setup schema: Firebase not initialized")
            return
        
        print("🔧 Setting up Firebase schema...")
        
        # Create sample users
        self._create_sample_users()
        
        # Create team structure
        self._create_team_structure()
        
        # Create collections
        self._create_collections()
        
        print("✅ Firebase schema setup complete")
    
    def _create_sample_users(self):
        """Create sample users for testing"""
        sample_users = [
            {
                'user_id': 'user_001',
                'display_name': 'Alex Chen',
                'email': 'alex.chen@company.com',
                'team_id': 'default_team'
            },
            {
                'user_id': 'user_002', 
                'display_name': 'Sarah Johnson',
                'email': 'sarah.johnson@company.com',
                'team_id': 'default_team'
            },
            {
                'user_id': 'user_003',
                'display_name': 'Mike Rodriguez',
                'email': 'mike.rodriguez@company.com', 
                'team_id': 'default_team'
            }
        ]
        
        for user in sample_users:
            user_ref = self.db.collection('users').document(user['user_id'])
            user_ref.set(user)
            print(f"Created user: {user['display_name']}")
    
    def _create_team_structure(self):
        """Create team structure and initial states"""
        team_id = 'default_team'
        
        # Create team document
        team_ref = self.db.collection('teams').document(team_id)
        team_ref.set({
            'name': 'Default Team',
            'created_at': firestore.SERVER_TIMESTAMP,
            'members': ['user_001', 'user_002', 'user_003']
        })
        
        # Create initial user states
        initial_states = [
            {'user_id': 'user_001', 'state': 'IDLE'},
            {'user_id': 'user_002', 'state': 'FLOWING'},  # Sarah is flowing
            {'user_id': 'user_003', 'state': 'STUCK'}
        ]
        
        for state_data in initial_states:
            state_ref = self.db.collection('team_states').document(team_id).collection('user_states').document(state_data['user_id'])
            state_ref.set({
                'state': state_data['state'],
                'timestamp': firestore.SERVER_TIMESTAMP,
                'user_id': state_data['user_id']
            })
            print(f"Set {state_data['user_id']} state to {state_data['state']}")
    
    def _create_collections(self):
        """Create necessary collections with sample data"""
        
        # Flow watchers collection (empty initially)
        watchers_ref = self.db.collection('flow_watchers')
        # Create a placeholder document to ensure collection exists
        watchers_ref.document('_placeholder').set({'created': firestore.SERVER_TIMESTAMP})
        
        # Notifications collection (empty initially)  
        notifications_ref = self.db.collection('notifications')
        notifications_ref.document('_placeholder').set({'created': firestore.SERVER_TIMESTAMP})
        
        # User preferences collection
        prefs_ref = self.db.collection('user_preferences')
        prefs_ref.document('_placeholder').set({'created': firestore.SERVER_TIMESTAMP})
        
        print("Created collections: flow_watchers, notifications, user_preferences")
    
    def simulate_flow_state_change(self, user_id: str, new_state: str):
        """Simulate a user's flow state change"""
        try:
            state_ref = self.db.collection('team_states').document('default_team').collection('user_states').document(user_id)
            state_ref.update({
                'state': new_state,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            print(f"Updated {user_id} state to {new_state}")
        except Exception as e:
            print(f"Error updating state: {e}")
    
    def get_user_by_name(self, display_name: str):
        """Get user by display name"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('display_name', '==', display_name).limit(1)
            docs = query.stream()
            
            for doc in docs:
                return doc.to_dict()
            
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

def main():
    """Setup Firebase schema"""
    setup = FirebaseSchemaSetup()
    setup.setup_schema()
    
    # Demo: Show how to change states
    print("\n🎭 Demo: Changing user states...")
    time.sleep(2)
    
    setup.simulate_flow_state_change('user_002', 'STUCK')  # Sarah exits flow
    time.sleep(1)
    setup.simulate_flow_state_change('user_001', 'FLOWING')  # Alex enters flow
    time.sleep(1)
    setup.simulate_flow_state_change('user_003', 'IDLE')  # Mike goes idle
    
    print("\n✅ Schema setup and demo complete!")

if __name__ == "__main__":
    main()