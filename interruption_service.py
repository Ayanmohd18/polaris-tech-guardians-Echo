import threading
import time
import re
from typing import Optional, Dict, Any
from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController
import pyautogui
import firebase_admin
from firebase_admin import credentials, firestore
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
from config import Config

class FlowInterruptionDialog(QDialog):
    """Custom dialog for flow state interruption"""
    
    send_anyway = pyqtSignal()
    notify_later = pyqtSignal()
    cancel_action = pyqtSignal()
    
    def __init__(self, recipient_name: str, parent=None):
        super().__init__(parent)
        self.recipient_name = recipient_name
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("ECHO")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(400, 200)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 400) // 2, (screen.height() - 200) // 2)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("ECHO")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #4A90E2;")
        
        # Message
        message_label = QLabel(f"Heads up! <b>{self.recipient_name}</b> is in a flow state. 🧘")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #333; font-size: 14px;")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.send_btn = QPushButton("Send Anyway (Interrupt)")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B35;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E55A2B;
            }
        """)
        self.send_btn.clicked.connect(self.send_anyway.emit)
        
        self.notify_btn = QPushButton("Notify Me When Free 📬")
        self.notify_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A7BC8;
            }
        """)
        self.notify_btn.clicked.connect(self.notify_later.emit)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #CCCCCC;
                color: #333;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #BBBBBB;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_action.emit)
        self.cancel_btn.setDefault(True)
        
        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.notify_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #4A90E2;
                border-radius: 10px;
            }
        """)

class InterruptionService:
    """Intelligent Interruption Service for ECHO"""
    
    def __init__(self, user_id: str, team_id: str = Config.DEFAULT_TEAM_ID):
        self.user_id = user_id
        self.team_id = team_id
        self.running = False
        
        # Keyboard control
        self.keyboard_listener = None
        self.keyboard_controller = KeyboardController()
        
        # Firebase
        self._init_firebase()
        
        # Communication apps patterns
        self.comm_apps = {
            'slack': r'(.+?)\s*[-|]\s*Slack',
            'teams': r'Chat with (.+?)\s*[-|]\s*Microsoft Teams',
            'discord': r'(.+?)\s*[-|]\s*Discord',
            'telegram': r'(.+?)\s*[-|]\s*Telegram',
            'whatsapp': r'(.+?)\s*[-|]\s*WhatsApp'
        }
        
        # User name to ID mapping cache
        self.name_to_id_cache = {}
        
    def _init_firebase(self):
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def start(self):
        """Start the interruption service"""
        if not self.db:
            print("Cannot start InterruptionService: Firebase not initialized")
            return
        
        self.running = True
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            suppress=False  # We'll suppress selectively
        )
        self.keyboard_listener.start()
        
        print("🛡️ Intelligent Interruption Service started")
    
    def stop(self):
        """Stop the interruption service"""
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("🛡️ Interruption Service stopped")
    
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            # Only intercept Enter key
            if key == keyboard.Key.enter:
                return self._handle_enter_key()
        except Exception as e:
            print(f"Key press handler error: {e}")
        
        return True  # Allow key by default
    
    def _handle_enter_key(self) -> bool:
        """Handle Enter key press in communication apps"""
        try:
            # Get active window context
            active_window = pyautogui.getActiveWindow()
            if not active_window:
                return True
            
            window_title = active_window.title
            
            # Check if it's a communication app
            if not self._is_communication_app(window_title):
                return True
            
            # Extract recipient name
            recipient_name = self._get_recipient_from_context(window_title)
            if not recipient_name:
                return True
            
            # Check recipient's flow state
            is_flowing = self._check_recipient_flow(recipient_name)
            if not is_flowing:
                return True
            
            # Recipient is flowing - show interruption dialog
            self._show_interruption_dialog(recipient_name)
            
            # Block the Enter key
            return False
            
        except Exception as e:
            print(f"Enter key handler error: {e}")
            return True
    
    def _is_communication_app(self, window_title: str) -> bool:
        """Check if window is a communication app"""
        title_lower = window_title.lower()
        comm_keywords = ['slack', 'teams', 'discord', 'telegram', 'whatsapp', 'messenger']
        return any(keyword in title_lower for keyword in comm_keywords)
    
    def _get_recipient_from_context(self, window_title: str) -> Optional[str]:
        """Extract recipient name from window title using regex patterns"""
        try:
            # Try each communication app pattern
            for app, pattern in self.comm_apps.items():
                if app in window_title.lower():
                    match = re.search(pattern, window_title, re.IGNORECASE)
                    if match:
                        recipient = match.group(1).strip()
                        
                        # Handle channel names (start with #)
                        if recipient.startswith('#'):
                            return recipient
                        
                        # Clean up recipient name
                        recipient = self._normalize_name(recipient)
                        return recipient
            
            # Fallback: try to extract name from common patterns
            # Pattern: "Name - App" or "App - Name"
            if ' - ' in window_title:
                parts = window_title.split(' - ')
                for part in parts:
                    part = part.strip()
                    # Skip app names
                    if not any(app in part.lower() for app in ['slack', 'teams', 'discord', 'telegram', 'whatsapp']):
                        if self._looks_like_name(part):
                            return self._normalize_name(part)
            
            return None
            
        except Exception as e:
            print(f"Recipient extraction error: {e}")
            return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize recipient name"""
        # Remove common prefixes/suffixes
        name = re.sub(r'^(chat with|dm with|@)\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*(online|offline|away)$', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        return name.title()  # Proper case
    
    def _looks_like_name(self, text: str) -> bool:
        """Heuristic to check if text looks like a person's name"""
        # Basic checks
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Should contain letters
        if not re.search(r'[a-zA-Z]', text):
            return False
        
        # Shouldn't be all caps (likely app name)
        if text.isupper() and len(text) > 3:
            return False
        
        # Common non-name patterns
        non_name_patterns = [
            r'^\d+$',  # Just numbers
            r'^[a-z]+\.(com|org|net)',  # URLs
            r'^(http|https|www)',  # URLs
            r'(notification|alert|system)',  # System messages
        ]
        
        for pattern in non_name_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    def _check_recipient_flow(self, recipient_name: str) -> bool:
        """Check if recipient is in flow state"""
        try:
            # Get recipient's user ID
            recipient_id = self._get_user_id_by_name(recipient_name)
            if not recipient_id:
                return False
            
            # Query Firebase for recipient's state
            doc_ref = self.db.collection('team_states').document(self.team_id).collection('user_states').document(recipient_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                state = data.get('state', 'IDLE')
                return state == 'FLOWING'
            
            return False
            
        except Exception as e:
            print(f"Flow state check error: {e}")
            return False
    
    def _get_user_id_by_name(self, name: str) -> Optional[str]:
        """Get user ID by display name"""
        try:
            # Check cache first
            if name in self.name_to_id_cache:
                return self.name_to_id_cache[name]
            
            # Query Firebase users collection
            users_ref = self.db.collection('users')
            
            # Try exact match first
            query = users_ref.where('display_name', '==', name).limit(1)
            docs = query.stream()
            
            for doc in docs:
                user_id = doc.id
                self.name_to_id_cache[name] = user_id
                return user_id
            
            # Try case-insensitive search
            all_users = users_ref.stream()
            for doc in all_users:
                data = doc.to_dict()
                display_name = data.get('display_name', '')
                if display_name.lower() == name.lower():
                    user_id = doc.id
                    self.name_to_id_cache[name] = user_id
                    return user_id
            
            return None
            
        except Exception as e:
            print(f"User ID lookup error: {e}")
            return None
    
    def _show_interruption_dialog(self, recipient_name: str):
        """Show interruption dialog using Qt"""
        try:
            # Ensure we have a QApplication
            app = QApplication.instance()
            if not app:
                return
            
            # Create and show dialog
            dialog = FlowInterruptionDialog(recipient_name)
            
            # Connect signals
            dialog.send_anyway.connect(lambda: self._handle_send_anyway(dialog))
            dialog.notify_later.connect(lambda: self._handle_notify_later(dialog, recipient_name))
            dialog.cancel_action.connect(lambda: self._handle_cancel(dialog))
            
            # Show dialog modally
            dialog.exec()
            
        except Exception as e:
            print(f"Dialog display error: {e}")
    
    def _handle_send_anyway(self, dialog):
        """Handle 'Send Anyway' button"""
        try:
            dialog.accept()
            
            # Re-send the Enter key after a short delay
            QTimer.singleShot(100, self._resend_enter_key)
            
        except Exception as e:
            print(f"Send anyway error: {e}")
    
    def _handle_notify_later(self, dialog, recipient_name: str):
        """Handle 'Notify Later' button"""
        try:
            dialog.accept()
            
            # Set up flow watcher
            self._create_flow_watcher(recipient_name)
            
            print(f"📬 Will notify when {recipient_name} is available")
            
        except Exception as e:
            print(f"Notify later error: {e}")
    
    def _handle_cancel(self, dialog):
        """Handle 'Cancel' button"""
        try:
            dialog.reject()
            print("Message cancelled")
        except Exception as e:
            print(f"Cancel error: {e}")
    
    def _resend_enter_key(self):
        """Programmatically send Enter key"""
        try:
            self.keyboard_controller.press(keyboard.Key.enter)
            self.keyboard_controller.release(keyboard.Key.enter)
        except Exception as e:
            print(f"Resend key error: {e}")
    
    def _create_flow_watcher(self, recipient_name: str):
        """Create flow watcher in Firebase"""
        try:
            recipient_id = self._get_user_id_by_name(recipient_name)
            if not recipient_id:
                return
            
            # Create watcher document
            watcher_ref = self.db.collection('flow_watchers').document(recipient_id).collection('watchers').document(self.user_id)
            
            watcher_ref.set({
                'notify_at': 'next_idle',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'recipient_name': recipient_name,
                'watcher_id': self.user_id
            })
            
        except Exception as e:
            print(f"Flow watcher creation error: {e}")

class FlowWatcherService:
    """Service to monitor flow watchers and send notifications"""
    
    def __init__(self, user_id: str, team_id: str = Config.DEFAULT_TEAM_ID):
        self.user_id = user_id
        self.team_id = team_id
        self.running = False
        
        # Initialize Firebase
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def start(self):
        """Start monitoring flow watchers"""
        if not self.db:
            return
        
        self.running = True
        
        # Start watcher thread
        watcher_thread = threading.Thread(target=self._monitor_watchers, daemon=True)
        watcher_thread.start()
        
        print("👁️ Flow Watcher Service started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        print("👁️ Flow Watcher Service stopped")
    
    def _monitor_watchers(self):
        """Monitor flow watchers for this user"""
        try:
            # Listen to watchers for this user
            watchers_ref = self.db.collection('flow_watchers').document(self.user_id).collection('watchers')
            
            def on_watcher_change(col_snapshot, changes, read_time):
                # Check current user state
                user_state_ref = self.db.collection('team_states').document(self.team_id).collection('user_states').document(self.user_id)
                user_doc = user_state_ref.get()
                
                if user_doc.exists:
                    current_state = user_doc.to_dict().get('state', 'IDLE')
                    
                    # If user is no longer flowing, notify watchers
                    if current_state in ['STUCK', 'IDLE']:
                        for change in changes:
                            if change.type.name in ['ADDED', 'MODIFIED']:
                                watcher_data = change.document.to_dict()
                                watcher_id = watcher_data.get('watcher_id')
                                
                                if watcher_id:
                                    self._notify_watcher(watcher_id)
                                    
                                    # Remove the watcher
                                    change.document.reference.delete()
            
            watchers_ref.on_snapshot(on_watcher_change)
            
        except Exception as e:
            print(f"Watcher monitoring error: {e}")
    
    def _notify_watcher(self, watcher_id: str):
        """Send notification to watcher"""
        try:
            # In a real implementation, this would integrate with the ECHO Orb
            # For now, we'll create a notification document
            
            notification_ref = self.db.collection('notifications').document(watcher_id).collection('messages')
            
            notification_ref.add({
                'type': 'flow_available',
                'message': f'{self.user_id} is now available. Good time to send that message!',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'read': False
            })
            
            print(f"📬 Notified {watcher_id} that {self.user_id} is available")
            
        except Exception as e:
            print(f"Notification error: {e}")

if __name__ == "__main__":
    # Test the interruption service
    import sys
    
    app = QApplication(sys.argv)
    
    service = InterruptionService("user_001")
    watcher_service = FlowWatcherService("user_001")
    
    service.start()
    watcher_service.start()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        service.stop()
        watcher_service.stop()