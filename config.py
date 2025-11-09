import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-service-account.json')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # User defaults
    DEFAULT_USER_ID = os.getenv('DEFAULT_USER_ID', 'user_001')
    DEFAULT_TEAM_ID = os.getenv('DEFAULT_TEAM_ID', 'team_001')
    
    # Sensor settings
    SENSOR_UPDATE_INTERVAL = int(os.getenv('SENSOR_UPDATE_INTERVAL', '3'))
    ACTIVITY_THRESHOLD = int(os.getenv('ACTIVITY_THRESHOLD', '60'))
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))