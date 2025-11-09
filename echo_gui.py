#!/usr/bin/env python3
"""
ECHO GUI Client
Desktop application with real-time cognitive monitoring
"""

import sys
import threading
import time
import json
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QBrush, QColor, QFont
from cognitive_sensor import CognitiveSensor

class CognitiveSensorThread(QThread):
    state_changed = pyqtSignal(str)
    
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.sensor = None
        self.running = False
        
    def run(self):
        class GUICognitiveSensor(CognitiveSensor):
            def __init__(self, user_id, state_callback):
                self.user_id = user_id
                self.state_callback = state_callback
                self.current_state = "IDLE"
                self.running = False
                
                # Simplified initialization
                from collections import deque
                self.typing_events = deque(maxlen=20)
                self.backspace_count = 0
                self.mouse_events = deque(maxlen=10)
                self.last_activity_time = time.time()
                
                self.keyboard_listener = None
                self.mouse_listener = None
                self.db = None
            
            def _update_firebase(self, state):
                """Override to emit signal instead"""
                self.state_callback.emit(state)
        
        self.sensor = GUICognitiveSensor(self.user_id, self.state_changed)
        self.sensor.start()
        self.running = True
        
        while self.running:
            time.sleep(1)
    
    def stop(self):
        self.running = False
        if self.sensor:
            self.sensor.stop()

class EchoOrb(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "IDLE"
        self.setFixedSize(120, 120)
        
    def set_state(self, state):
        self.state = state
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # State colors
        colors = {
            'FLOWING': QColor(76, 175, 80),    # Green
            'STUCK': QColor(33, 150, 243),     # Blue
            'FRUSTRATED': QColor(255, 152, 0), # Orange
            'IDLE': QColor(158, 158, 158)      # Gray
        }
        
        color = colors.get(self.state, colors['IDLE'])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw orb
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = 40
        
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

class EchoMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_id = "developer_001"
        self.team_id = "hackathon_team"
        self.sensor_thread = None
        self.session_start = datetime.now()
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        self.setWindowTitle("ECHO: Cognitive Monitoring Dashboard")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("ECHO: The Omniscient Creative Environment")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #2196F3; margin: 20px;")
        layout.addWidget(header)
        
        # User info
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel(f"User: {self.user_id}"))
        user_layout.addWidget(QLabel(f"Team: {self.team_id}"))
        layout.addLayout(user_layout)
        
        # Orb and state display
        orb_layout = QHBoxLayout()
        
        # Orb
        self.orb = EchoOrb()
        orb_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # State info
        state_widget = QWidget()
        state_layout = QVBoxLayout(state_widget)
        
        self.state_label = QLabel("IDLE")
        self.state_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_layout.addWidget(self.state_label)
        
        self.last_update_label = QLabel("Last Update: --")
        self.last_update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_layout.addWidget(self.last_update_label)
        
        self.session_time_label = QLabel("Session: 00:00:00")
        self.session_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_layout.addWidget(self.session_time_label)
        
        orb_layout.addWidget(state_widget)
        layout.addLayout(orb_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        self.start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-size: 14px; }")
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; font-size: 14px; }")
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # State descriptions
        desc_widget = QWidget()
        desc_layout = QGridLayout(desc_widget)
        
        states = [
            ("FLOWING", "High productivity, minimal interruptions", "#4CAF50"),
            ("STUCK", "Thinking/reading, low activity", "#2196F3"),
            ("FRUSTRATED", "High backspacing, audio spikes", "#FF9800"),
            ("IDLE", "No activity detected", "#9E9E9E")
        ]
        
        for i, (state, desc, color) in enumerate(states):
            state_label = QLabel(state)
            state_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            desc_label = QLabel(desc)
            
            desc_layout.addWidget(state_label, i, 0)
            desc_layout.addWidget(desc_label, i, 1)
        
        layout.addWidget(desc_widget)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        layout.addWidget(QLabel("Activity Log:"))
        layout.addWidget(self.log_area)
        
        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
    def setup_timer(self):
        # Timer for session time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_session_time)
        self.timer.start(1000)  # Update every second
        
    def update_session_time(self):
        elapsed = datetime.now() - self.session_start
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        seconds = elapsed.seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.session_time_label.setText(f"Session: {time_str}")
        
    def start_monitoring(self):
        if not self.sensor_thread or not self.sensor_thread.isRunning():
            self.sensor_thread = CognitiveSensorThread(self.user_id)
            self.sensor_thread.state_changed.connect(self.update_state)
            self.sensor_thread.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            self.log_message("Cognitive monitoring started")
            
    def stop_monitoring(self):
        if self.sensor_thread and self.sensor_thread.isRunning():
            self.sensor_thread.stop()
            self.sensor_thread.wait()
            
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            self.log_message("Cognitive monitoring stopped")
            
    def update_state(self, state):
        self.orb.set_state(state)
        self.state_label.setText(state)
        self.last_update_label.setText(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Set state label color
        colors = {
            'FLOWING': "#4CAF50",
            'STUCK': "#2196F3", 
            'FRUSTRATED': "#FF9800",
            'IDLE': "#9E9E9E"
        }
        
        color = colors.get(state, "#9E9E9E")
        self.state_label.setStyleSheet(f"color: {color};")
        
        self.log_message(f"State changed to: {state}")
        
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        if self.sensor_thread and self.sensor_thread.isRunning():
            self.sensor_thread.stop()
            self.sensor_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ECHO Cognitive Monitor")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = EchoMainWindow()
    window.show()
    
    print("ECHO GUI Client Started")
    print("=" * 30)
    print("- Click 'Start Monitoring' to begin cognitive state tracking")
    print("- The orb will change color based on your cognitive state")
    print("- Close the window to stop the application")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()