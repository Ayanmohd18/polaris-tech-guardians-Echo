"""
ECHO: The Sentient Workspace
Feature 9: The Data Bridge - Secure database schema introspection
"""

from fastapi import FastAPI, HTTPException
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import firebase_admin
from firebase_admin import credentials, firestore
from supabase import create_client, Client
from notion_client import Client as NotionClient
from cryptography.fernet import Fernet
import json
import os
from config import Config

class DataBridge:
    """Secure bridge to user's databases"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize Firebase
        self._init_firebase()
        
        # Encryption key (in production, use proper key management)
        self.cipher_key = self._get_or_create_cipher_key()
        self.cipher = Fernet(self.cipher_key)
    
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def _get_or_create_cipher_key(self):
        """Get or create encryption key"""
        key_file = ".cipher_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def store_credentials(self, service_name: str, credentials_data: dict):
        """Store encrypted credentials in Firebase"""
        if not self.db:
            raise Exception("Firebase not initialized")
        
        try:
            # Encrypt credentials
            encrypted_data = self.cipher.encrypt(json.dumps(credentials_data).encode())
            
            # Store in Firebase
            doc_ref = self.db.collection('user_secrets').document(self.user_id).collection('keys').document(service_name)
            doc_ref.set({
                'encrypted_data': encrypted_data.decode(),
                'service': service_name,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to store credentials: {str(e)}")
    
    def get_credentials(self, service_name: str) -> dict:
        """Retrieve and decrypt credentials from Firebase"""
        if not self.db:
            raise Exception("Firebase not initialized")
        
        try:
            doc_ref = self.db.collection('user_secrets').document(self.user_id).collection('keys').document(service_name)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise Exception(f"No credentials found for {service_name}")
            
            data = doc.to_dict()
            encrypted_data = data['encrypted_data'].encode()
            
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            raise Exception(f"Failed to retrieve credentials: {str(e)}")
    
    def introspect_supabase(self, query: str) -> dict:
        """Introspect Supabase database schema"""
        try:
            creds = self.get_credentials('supabase')
            
            supabase: Client = create_client(
                creds['url'],
                creds['api_key']
            )
            
            if query == 'list_tables':
                # Query information_schema
                response = supabase.rpc('get_tables').execute()
                return {'tables': response.data}
            
            elif query.startswith('get_schema:'):
                table_name = query.split(':')[1]
                response = supabase.rpc('get_table_schema', {'table_name': table_name}).execute()
                return {'schema': response.data}
            
            else:
                raise Exception(f"Unknown query: {query}")
                
        except Exception as e:
            raise Exception(f"Supabase introspection failed: {str(e)}")
    
    def introspect_firebase(self, query: str) -> dict:
        """Introspect Firebase Firestore schema"""
        try:
            creds = self.get_credentials('firebase')
            
            # Initialize separate Firebase app for user's project
            user_cred = credentials.Certificate(creds)
            user_app = firebase_admin.initialize_app(user_cred, name=f'user_{self.user_id}')
            user_db = firestore.client(user_app)
            
            if query == 'list_collections':
                collections = user_db.collections()
                collection_names = [col.id for col in collections]
                return {'collections': collection_names}
            
            elif query.startswith('get_schema:'):
                collection_name = query.split(':')[1]
                # Sample first document to infer schema
                docs = user_db.collection(collection_name).limit(1).stream()
                
                schema = {}
                for doc in docs:
                    data = doc.to_dict()
                    schema = {key: type(value).__name__ for key, value in data.items()}
                
                return {'schema': schema}
            
            else:
                raise Exception(f"Unknown query: {query}")
                
        except Exception as e:
            raise Exception(f"Firebase introspection failed: {str(e)}")
    
    def introspect_notion(self, query: str) -> dict:
        """Introspect Notion database schema"""
        try:
            creds = self.get_credentials('notion')
            
            notion = NotionClient(auth=creds['api_token'])
            
            if query == 'list_databases':
                response = notion.search(filter={"property": "object", "value": "database"})
                databases = [{'id': db['id'], 'title': db.get('title', [{}])[0].get('plain_text', 'Untitled')} 
                           for db in response.get('results', [])]
                return {'databases': databases}
            
            elif query.startswith('get_schema:'):
                database_id = query.split(':')[1]
                database = notion.databases.retrieve(database_id)
                
                schema = {}
                for prop_name, prop_data in database.get('properties', {}).items():
                    schema[prop_name] = prop_data.get('type', 'unknown')
                
                return {'schema': schema}
            
            else:
                raise Exception(f"Unknown query: {query}")
                
        except Exception as e:
            raise Exception(f"Notion introspection failed: {str(e)}")

# FastAPI endpoints
app = FastAPI(title="ECHO Data Bridge", version="1.0.0")

data_bridges = {}  # Cache of DataBridge instances

@app.post("/introspect_schema")
async def introspect_schema(request: dict):
    """Introspect database schema"""
    try:
        user_id = request.get('user_id')
        service_name = request.get('service_name')
        query = request.get('query')
        
        if not all([user_id, service_name, query]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Get or create DataBridge instance
        if user_id not in data_bridges:
            data_bridges[user_id] = DataBridge(user_id)
        
        bridge = data_bridges[user_id]
        
        # Route to appropriate introspection method
        if service_name == 'supabase':
            result = bridge.introspect_supabase(query)
        elif service_name == 'firebase':
            result = bridge.introspect_firebase(query)
        elif service_name == 'notion':
            result = bridge.introspect_notion(query)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
        
        return {
            'status': 'success',
            'service': service_name,
            'query': query,
            'result': result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_credentials")
async def store_credentials(request: dict):
    """Store user credentials"""
    try:
        user_id = request.get('user_id')
        service_name = request.get('service_name')
        credentials_data = request.get('credentials')
        
        if not all([user_id, service_name, credentials_data]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Get or create DataBridge instance
        if user_id not in data_bridges:
            data_bridges[user_id] = DataBridge(user_id)
        
        bridge = data_bridges[user_id]
        bridge.store_credentials(service_name, credentials_data)
        
        return {
            'status': 'success',
            'message': f'Credentials stored for {service_name}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Settings Dialog for PyQt6
class SettingsDialog(QDialog):
    """Settings dialog for configuring database credentials"""
    
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.bridge = DataBridge(user_id)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup settings UI"""
        self.setWindowTitle("ECHO Settings - Data Bridge")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔐 Secure Database Credentials")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        
        # Tabs for different services
        tabs = QTabWidget()
        
        # Supabase tab
        supabase_tab = self.create_supabase_tab()
        tabs.addTab(supabase_tab, "Supabase")
        
        # Firebase tab
        firebase_tab = self.create_firebase_tab()
        tabs.addTab(firebase_tab, "Firebase")
        
        # Notion tab
        notion_tab = self.create_notion_tab()
        tabs.addTab(notion_tab, "Notion")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save All")
        save_btn.clicked.connect(self.save_all_credentials)
        
        test_btn = QPushButton("🧪 Test Connection")
        test_btn.clicked.connect(self.test_connections)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(test_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addWidget(title)
        layout.addWidget(tabs)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_supabase_tab(self):
        """Create Supabase credentials tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.supabase_url = QLineEdit()
        self.supabase_url.setPlaceholderText("https://xxxxx.supabase.co")
        
        self.supabase_key = QLineEdit()
        self.supabase_key.setPlaceholderText("Your Supabase API key")
        self.supabase_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Supabase URL:", self.supabase_url)
        layout.addRow("API Key:", self.supabase_key)
        
        widget.setLayout(layout)
        return widget
    
    def create_firebase_tab(self):
        """Create Firebase credentials tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("Upload Firebase service account JSON:")
        
        self.firebase_path = QLineEdit()
        self.firebase_path.setPlaceholderText("Path to service account JSON")
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_firebase_file)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.firebase_path)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(label)
        layout.addLayout(path_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_notion_tab(self):
        """Create Notion credentials tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.notion_token = QLineEdit()
        self.notion_token.setPlaceholderText("secret_xxxxx")
        self.notion_token.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Notion API Token:", self.notion_token)
        
        widget.setLayout(layout)
        return widget
    
    def browse_firebase_file(self):
        """Browse for Firebase credentials file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firebase Service Account JSON",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.firebase_path.setText(file_path)
    
    def save_all_credentials(self):
        """Save all credentials"""
        try:
            # Save Supabase
            if self.supabase_url.text() and self.supabase_key.text():
                self.bridge.store_credentials('supabase', {
                    'url': self.supabase_url.text(),
                    'api_key': self.supabase_key.text()
                })
            
            # Save Firebase
            if self.firebase_path.text():
                with open(self.firebase_path.text(), 'r') as f:
                    firebase_creds = json.load(f)
                self.bridge.store_credentials('firebase', firebase_creds)
            
            # Save Notion
            if self.notion_token.text():
                self.bridge.store_credentials('notion', {
                    'api_token': self.notion_token.text()
                })
            
            QMessageBox.information(self, "Success", "Credentials saved securely!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save credentials:\n{str(e)}")
    
    def test_connections(self):
        """Test database connections"""
        results = []
        
        # Test Supabase
        try:
            result = self.bridge.introspect_supabase('list_tables')
            results.append("✅ Supabase: Connected")
        except:
            results.append("❌ Supabase: Failed")
        
        # Test Firebase
        try:
            result = self.bridge.introspect_firebase('list_collections')
            results.append("✅ Firebase: Connected")
        except:
            results.append("❌ Firebase: Failed")
        
        # Test Notion
        try:
            result = self.bridge.introspect_notion('list_databases')
            results.append("✅ Notion: Connected")
        except:
            results.append("❌ Notion: Failed")
        
        QMessageBox.information(self, "Connection Test", "\n".join(results))