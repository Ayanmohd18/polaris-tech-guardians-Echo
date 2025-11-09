#!/usr/bin/env python3
"""
Test script for the Intelligent Interruption Service
Demonstrates the complete flow protection workflow
"""

import sys
import time
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal
from interruption_service import InterruptionService, FlowWatcherService
from firebase_schema import FirebaseSchemaSetup
from cognitive_sensor import CognitiveSensor

class InterruptionTestApp(QMainWindow):
    """Test application for interruption service"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Initialize services
        self.setup = FirebaseSchemaSetup()
        self.interruption_service = InterruptionService("user_001")
        self.flow_watcher = FlowWatcherService("user_002")  # Sarah
        
        # Setup Firebase schema
        self.setup.setup_schema()
        
        # Start services
        self.interruption_service.start()
        self.flow_watcher.start()
        
    def setup_ui(self):
        """Setup the test UI"""
        self.setWindowTitle("ECHO Interruption Service Test")
        self.setGeometry(100, 100, 600, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🛡️ ECHO Interruption Service Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A90E2; margin: 10px;")
        
        # Instructions
        instructions = QLabel("""
        Test Instructions:
        1. Click 'Simulate Sarah Flowing' to put Sarah in flow state
        2. Open Slack/Teams and try to message 'Sarah Johnson'
        3. Press Enter - ECHO should intercept and show dialog
        4. Test different dialog options
        """)
        instructions.setStyleSheet("margin: 10px; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        
        # Control buttons
        self.flow_btn = QPushButton("Simulate Sarah Flowing")
        self.flow_btn.clicked.connect(self.set_sarah_flowing)
        self.flow_btn.setStyleSheet("padding: 10px; font-size: 14px; background: #4A90E2; color: white; border-radius: 5px;")
        
        self.idle_btn = QPushButton("Simulate Sarah Available")
        self.idle_btn.clicked.connect(self.set_sarah_idle)
        self.idle_btn.setStyleSheet("padding: 10px; font-size: 14px; background: #00AA00; color: white; border-radius: 5px;")
        
        self.test_btn = QPushButton("Test Recipient Detection")
        self.test_btn.clicked.connect(self.test_recipient_detection)
        self.test_btn.setStyleSheet("padding: 10px; font-size: 14px; background: #FF6B35; color: white; border-radius: 5px;")
        
        # Status display
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold; margin: 10px;")
        
        # Log display
        log_label = QLabel("Service Log:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("background: #f8f8f8; border: 1px solid #ddd; border-radius: 5px;")
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(self.flow_btn)
        layout.addWidget(self.idle_btn)
        layout.addWidget(self.test_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(log_label)
        layout.addWidget(self.log_display)
        
        central_widget.setLayout(layout)
        
        # Setup log timer
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.update_log)
        self.log_timer.start(1000)  # Update every second
        
    def set_sarah_flowing(self):
        """Set Sarah to flowing state"""
        self.setup.simulate_flow_state_change('user_002', 'FLOWING')
        self.status_label.setText("Status: Sarah is now FLOWING 🧘")
        self.log("Sarah Johnson entered FLOWING state")
        
    def set_sarah_idle(self):
        """Set Sarah to idle state"""
        self.setup.simulate_flow_state_change('user_002', 'IDLE')
        self.status_label.setText("Status: Sarah is now IDLE 💤")
        self.log("Sarah Johnson is now available (IDLE)")
        
    def test_recipient_detection(self):
        """Test recipient name detection"""
        test_titles = [
            "Sarah Johnson - Slack",
            "Chat with Sarah Johnson - Microsoft Teams",
            "Sarah Johnson - Discord",
            "#development - Slack",
            "DM with @sarah.johnson - Slack"
        ]
        
        self.log("Testing recipient detection:")
        for title in test_titles:
            recipient = self.interruption_service._get_recipient_from_context(title)
            self.log(f"  '{title}' → '{recipient}'")
    
    def log(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_display.append(log_entry)
        print(log_entry)  # Also print to console
    
    def update_log(self):
        """Update log display periodically"""
        # This could fetch real-time logs from the services
        pass
    
    def closeEvent(self, event):
        """Clean up when closing"""
        self.interruption_service.stop()
        self.flow_watcher.stop()
        event.accept()

class InterruptionDemo:
    """Comprehensive demo of the interruption service"""
    
    def __init__(self):
        self.setup = FirebaseSchemaSetup()
        
    def run_demo(self):
        """Run the complete demo"""
        print("🎭 ECHO Interruption Service Demo")
        print("=" * 50)
        
        # Setup Firebase
        print("1. Setting up Firebase schema...")
        self.setup.setup_schema()
        time.sleep(1)
        
        # Demo scenarios
        print("\n2. Demo Scenarios:")
        self.demo_recipient_detection()
        self.demo_flow_state_checking()
        self.demo_watcher_system()
        
        print("\n✅ Demo complete!")
    
    def demo_recipient_detection(self):
        """Demo recipient name detection"""
        print("\n📝 Testing Recipient Detection:")
        
        service = InterruptionService("user_001")
        
        test_cases = [
            ("Sarah Johnson - Slack", "Sarah Johnson"),
            ("Chat with Mike Rodriguez - Microsoft Teams", "Mike Rodriguez"),
            ("#development - Slack", "#development"),
            ("Alex Chen - Discord", "Alex Chen"),
            ("Random App Window", None)
        ]
        
        for window_title, expected in test_cases:
            result = service._get_recipient_from_context(window_title)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{window_title}' → '{result}' (expected: '{expected}')")
    
    def demo_flow_state_checking(self):
        """Demo flow state checking"""
        print("\n🧘 Testing Flow State Checking:")
        
        service = InterruptionService("user_001")
        
        # Test with known users
        test_users = ["Sarah Johnson", "Mike Rodriguez", "Unknown User"]
        
        for user in test_users:
            is_flowing = service._check_recipient_flow(user)
            status = "🧘 FLOWING" if is_flowing else "💤 AVAILABLE"
            print(f"  {user}: {status}")
    
    def demo_watcher_system(self):
        """Demo the flow watcher system"""
        print("\n👁️ Testing Flow Watcher System:")
        
        service = InterruptionService("user_001")
        
        # Create a watcher
        print("  Creating flow watcher for Sarah Johnson...")
        service._create_flow_watcher("Sarah Johnson")
        
        # Simulate state change
        print("  Simulating Sarah's state change to IDLE...")
        self.setup.simulate_flow_state_change('user_002', 'IDLE')
        
        print("  ✅ Watcher system test complete")

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run command-line demo
        demo = InterruptionDemo()
        demo.run_demo()
    else:
        # Run GUI test app
        app = QApplication(sys.argv)
        
        test_app = InterruptionTestApp()
        test_app.show()
        
        print("🚀 Interruption Service Test App started")
        print("Try messaging 'Sarah Johnson' in Slack/Teams while she's flowing!")
        
        sys.exit(app.exec())

if __name__ == "__main__":
    main()