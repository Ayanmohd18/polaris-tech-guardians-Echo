import threading
import time
import pyautogui
from pynput import keyboard
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
from typing import Dict, Any, List
import json

class TeamFlowManager:
    def __init__(self, user_id: str, team_id: str = Config.DEFAULT_TEAM_ID):
        self.user_id = user_id
        self.team_id = team_id
        self.team_states = {}
        self.running = False
        
        # Message interception
        self.pending_messages = {}
        self.keyboard_listener = None
        
        # Initialize Firebase
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
    
    def start(self):
        self.running = True
        
        # Start team state listener
        self._start_team_listener()
        
        # Start message interception
        self._start_message_interception()
        
        print(f"Team Flow Manager started for team: {self.team_id}")
    
    def stop(self):
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("Team Flow Manager stopped")
    
    def _start_team_listener(self):
        """Listen to team state changes in Firebase"""
        if not self.db:
            return
        
        def listen_to_team():
            try:
                team_ref = self.db.collection('team_states').document(self.team_id).collection('user_states')
                
                def on_team_change(col_snapshot, changes, read_time):
                    for change in changes:
                        if change.type.name in ['ADDED', 'MODIFIED']:
                            user_id = change.document.id
                            data = change.document.to_dict()
                            if data and 'state' in data:
                                self.team_states[user_id] = {
                                    'state': data['state'],
                                    'timestamp': data.get('timestamp'),
                                    'last_updated': time.time()
                                }
                
                team_ref.on_snapshot(on_team_change)
                
            except Exception as e:
                print(f"Team listener error: {e}")
        
        listener_thread = threading.Thread(target=listen_to_team, daemon=True)
        listener_thread.start()
    
    def _start_message_interception(self):
        """Start intercepting potential message sending"""
        def on_key_combination(key):
            try:
                # Detect Ctrl+Enter (common send shortcut)
                if hasattr(key, 'vk') and key.vk == 13:  # Enter key
                    active_window = pyautogui.getActiveWindow()
                    if active_window and self._is_communication_app(active_window.title):
                        self._handle_message_attempt(active_window.title)
            except:
                pass
        
        self.keyboard_listener = keyboard.Listener(on_press=on_key_combination)
        self.keyboard_listener.start()
    
    def _is_communication_app(self, window_title: str) -> bool:
        """Check if current window is a communication app"""
        comm_apps = ['slack', 'teams', 'discord', 'telegram', 'whatsapp', 'messenger']
        return any(app in window_title.lower() for app in comm_apps)
    
    def _handle_message_attempt(self, window_title: str):
        """Handle potential message sending attempt"""
        # Extract potential recipient from window title
        recipient = self._extract_recipient(window_title)
        
        if recipient and recipient in self.team_states:
            recipient_state = self.team_states[recipient]['state']
            
            if recipient_state == 'FLOWING':
                self._show_flow_interruption_dialog(recipient, recipient_state)
    
    def _extract_recipient(self, window_title: str) -> str:
        """Extract recipient name from communication app window"""
        # Simple heuristic - in real implementation, this would be more sophisticated
        # Could integrate with specific app APIs or use OCR
        
        # For Slack: "Slack | #channel-name" or "Slack | @username"
        if 'slack' in window_title.lower():
            parts = window_title.split('|')
            if len(parts) > 1:
                recipient = parts[1].strip()
                if recipient.startswith('@'):
                    return recipient[1:]  # Remove @ symbol
        
        return None
    
    def _show_flow_interruption_dialog(self, recipient: str, state: str):
        """Show dialog asking about interrupting team member's flow"""
        from PyQt6.QtWidgets import QMessageBox, QApplication
        
        if not QApplication.instance():
            return
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("ECHO - Flow State Alert")
        msg_box.setText(f"{recipient} is currently in a {state.lower()} state.")
        msg_box.setInformativeText("Do you want to send this message now, or have ECHO deliver it when they're available?")
        
        send_now_btn = msg_box.addButton("Send Now", QMessageBox.ButtonRole.AcceptRole)
        delay_btn = msg_box.addButton("Deliver Later", QMessageBox.ButtonRole.RejectRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.DestructiveRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == delay_btn:
            self._schedule_delayed_message(recipient)
        elif msg_box.clickedButton() == cancel_btn:
            # User cancelled, could clear clipboard or undo typing
            pass
    
    def _schedule_delayed_message(self, recipient: str):
        """Schedule message for delayed delivery"""
        if not self.db:
            return
        
        try:
            # Store pending message in Firebase
            self.db.collection('pending_messages').add({
                'sender': self.user_id,
                'recipient': recipient,
                'team_id': self.team_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'status': 'pending'
            })
            
            print(f"Message to {recipient} scheduled for later delivery")
            
        except Exception as e:
            print(f"Failed to schedule message: {e}")
    
    def check_pending_messages(self):
        """Check and deliver pending messages when recipients are available"""
        if not self.db:
            return
        
        try:
            # Get pending messages for this user
            pending_ref = self.db.collection('pending_messages').where('recipient', '==', self.user_id).where('status', '==', 'pending')
            pending_docs = pending_ref.stream()
            
            current_state = self.team_states.get(self.user_id, {}).get('state', 'IDLE')
            
            if current_state in ['STUCK', 'IDLE']:  # Available states
                for doc in pending_docs:
                    data = doc.to_dict()
                    sender = data.get('sender', 'Unknown')
                    
                    # Notify user of pending message
                    self._notify_pending_message(sender)
                    
                    # Mark as delivered
                    doc.reference.update({'status': 'delivered'})
        
        except Exception as e:
            print(f"Error checking pending messages: {e}")
    
    def _notify_pending_message(self, sender: str):
        """Notify user of pending message"""
        print(f"📨 You have a pending message from {sender}")
        # Could integrate with orb notification system
    
    def get_team_flow_summary(self) -> Dict[str, Any]:
        """Get current team flow state summary"""
        summary = {
            'team_id': self.team_id,
            'total_members': len(self.team_states),
            'states': {},
            'flow_score': 0
        }
        
        if not self.team_states:
            return summary
        
        # Count states
        for user_id, user_data in self.team_states.items():
            state = user_data['state']
            summary['states'][state] = summary['states'].get(state, 0) + 1
        
        # Calculate team flow score (0-100)
        flowing_count = summary['states'].get('FLOWING', 0)
        total_count = len(self.team_states)
        summary['flow_score'] = int((flowing_count / total_count) * 100) if total_count > 0 else 0
        
        return summary

class TeamFlowOrb:
    """Enhanced orb with team flow visualization"""
    
    def __init__(self, base_orb):
        self.base_orb = base_orb
        self.team_manager = TeamFlowManager(base_orb.user_id, base_orb.team_id)
    
    def start_team_features(self):
        """Start team flow features"""
        self.team_manager.start()
        
        # Start periodic pending message checks
        def check_messages_periodically():
            while self.team_manager.running:
                self.team_manager.check_pending_messages()
                time.sleep(30)  # Check every 30 seconds
        
        message_thread = threading.Thread(target=check_messages_periodically, daemon=True)
        message_thread.start()
    
    def get_team_satellites_data(self) -> List[Dict[str, Any]]:
        """Get data for team member satellites"""
        satellites = []
        
        for user_id, user_data in self.team_manager.team_states.items():
            if user_id != self.base_orb.user_id:  # Exclude self
                satellites.append({
                    'user_id': user_id,
                    'state': user_data['state'],
                    'last_updated': user_data.get('last_updated', 0)
                })
        
        return satellites

if __name__ == "__main__":
    # Test team flow manager
    manager = TeamFlowManager("user_001", "test_team")
    manager.start()
    
    try:
        while True:
            summary = manager.get_team_flow_summary()
            print(f"Team Flow: {summary}")
            time.sleep(10)
    except KeyboardInterrupt:
        manager.stop()