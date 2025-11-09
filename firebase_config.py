"""
Firebase Configuration and Initialization for ECHO
Integrates with vibeathon-7b277 Firebase project
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirebaseConfig:
    """Centralized Firebase configuration"""
    
    # Your Firebase Web Config
    WEB_CONFIG = {
        "apiKey": "AIzaSyBvwGY2uIVOc9B7mHYiPIvFnebhdsfB2ak",
        "authDomain": "vibeathon-7b277.firebaseapp.com",
        "databaseURL": "https://vibeathon-7b277-default-rtdb.firebaseio.com",
        "projectId": "vibeathon-7b277",
        "storageBucket": "vibeathon-7b277.firebasestorage.app",
        "messagingSenderId": "909432426012",
        "appId": "1:909432426012:web:2bfa2c148e52c44a1d99d9",
        "measurementId": "G-WZD4Y3S8XZ"
    }
    
    # Admin SDK Config
    PROJECT_ID = "vibeathon-7b277"
    DATABASE_URL = "https://vibeathon-7b277-default-rtdb.firebaseio.com"
    CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    _initialized = False
    _app = None
    _firestore_client = None
    _realtime_db = None
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if cls._initialized:
            return cls._app
        
        try:
            # Check if credentials file exists
            if not os.path.exists(cls.CREDENTIALS_PATH):
                print(f"⚠️  Firebase credentials not found at {cls.CREDENTIALS_PATH}")
                print("   Creating template. Please add your service account key.")
                cls._create_credentials_template()
                return None
            
            # Initialize with credentials
            cred = credentials.Certificate(cls.CREDENTIALS_PATH)
            cls._app = firebase_admin.initialize_app(cred, {
                'databaseURL': cls.DATABASE_URL,
                'projectId': cls.PROJECT_ID
            })
            
            cls._initialized = True
            print(f"✅ Firebase initialized: {cls.PROJECT_ID}")
            
            return cls._app
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            print("   Please download service account key from Firebase Console:")
            print("   https://console.firebase.google.com/project/vibeathon-7b277/settings/serviceaccounts/adminsdk")
            return None
    
    @classmethod
    def get_firestore(cls):
        """Get Firestore client"""
        if not cls._initialized:
            cls.initialize()
        
        if not cls._firestore_client:
            cls._firestore_client = firestore.client()
        
        return cls._firestore_client
    
    @classmethod
    def get_realtime_db(cls):
        """Get Realtime Database reference"""
        if not cls._initialized:
            cls.initialize()
        
        if not cls._realtime_db:
            cls._realtime_db = db.reference()
        
        return cls._realtime_db
    
    @classmethod
    def _create_credentials_template(cls):
        """Create credentials template file"""
        template = {
            "type": "service_account",
            "project_id": cls.PROJECT_ID,
            "private_key_id": "DOWNLOAD_FROM_FIREBASE_CONSOLE",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nDOWNLOAD_FROM_FIREBASE_CONSOLE\\n-----END PRIVATE KEY-----\\n",
            "client_email": f"firebase-adminsdk@{cls.PROJECT_ID}.iam.gserviceaccount.com",
            "client_id": "DOWNLOAD_FROM_FIREBASE_CONSOLE",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/v1/metadata/x509/firebase-adminsdk%40{cls.PROJECT_ID}.iam.gserviceaccount.com"
        }
        
        import json
        with open(cls.CREDENTIALS_PATH, 'w') as f:
            json.dump(template, f, indent=2)

# Initialize on import
FirebaseConfig.initialize()