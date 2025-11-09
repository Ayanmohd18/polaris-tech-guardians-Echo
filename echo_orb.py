import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QBrush, QColor
import firebase_admin
from firebase_admin import firestore
from config import Config

class FirebaseListener(QThread):
    state_changed = pyqtSignal(str, dict)
    
    def __init__(self, team_id, user_id):
        super().__init__()
        self.team_id = team_id
        self.user_id = user_id
        self.db = firestore.client()
        
    def run(self):
        try:
            doc_ref = self.db.collection('team_states').document(self.team_id).collection('user_states')
            
            def on_snapshot(doc_snapshot, changes, read_time):
                team_states = {}
                user_state = "IDLE"
                
                for doc in doc_snapshot:
                    data = doc.to_dict()
                    if doc.id == self.user_id:
                        user_state = data.get('state', 'IDLE')
                    else:
                        team_states[doc.id] = data.get('state', 'IDLE')
                
                self.state_changed.emit(user_state, team_states)
            
            doc_ref.on_snapshot(on_snapshot)
        except Exception as e:
            print(f"Firebase listener error: {e}")

class CommandBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(40, 40, 40, 200);
                border: 2px solid #4A90E2;
                border-radius: 25px;
                padding: 15px 20px;
                font-size: 16px;
                color: white;
            }
        """)
        self.input_field.returnPressed.connect(self.handle_input)
        layout.addWidget(self.input_field)
        self.setLayout(layout)
        
        self.resize(500, 60)
        self.hide()
        
    def show_centered(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())
        self.show()
        self.input_field.setFocus()
        
    def handle_input(self):
        text = self.input_field.text()
        if text:
            print(f"ECHO Command: {text}")
            self.input_field.clear()
        self.hide()

class EchoOrb(QWidget):
    def __init__(self, user_id=Config.DEFAULT_USER_ID, team_id=Config.DEFAULT_TEAM_ID):
        super().__init__()
        self.user_id = user_id
        self.team_id = team_id
        self.current_state = "IDLE"
        self.team_states = {}
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Orb properties
        self.orb_size = 30
        self.orb_opacity = 0.3
        self.orb_color = QColor(100, 149, 237)
        
        # Command bar
        self.command_bar = CommandBar()
        
        # Firebase listener
        self.firebase_listener = FirebaseListener(team_id, user_id)
        self.firebase_listener.state_changed.connect(self.update_states)
        self.firebase_listener.start()
        
        # Animation timer
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_animation)
        
        self.resize(100, 100)
        self.position_orb()
        
    def position_orb(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 120, screen.height() - 120)
        
    def update_states(self, user_state, team_states):
        self.current_state = user_state
        self.team_states = team_states
        self.adapt_to_state()
        self.update()
        
    def adapt_to_state(self):
        if self.current_state == "FLOWING":
            self.orb_size = 10
            self.orb_opacity = 0.1
            self.orb_color = QColor(100, 149, 237)
            self.pulse_timer.stop()
            
        elif self.current_state == "STUCK":
            self.orb_size = 30
            self.orb_opacity = 0.6
            self.orb_color = QColor(100, 149, 237)
            self.pulse_timer.start(1000)
            
        elif self.current_state == "FRUSTRATED":
            self.orb_size = 35
            self.orb_opacity = 0.8
            self.orb_color = QColor(255, 165, 0)
            QTimer.singleShot(2000, lambda: self.update_states("STUCK", self.team_states))
            
        else:  # IDLE
            self.orb_size = 20
            self.orb_opacity = 0.4
            self.orb_color = QColor(128, 128, 128)
            self.pulse_timer.stop()
            
    def pulse_animation(self):
        current_size = self.orb_size
        self.orb_size = current_size + 5 if current_size < 35 else 30
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw main orb
        brush = QBrush(self.orb_color)
        painter.setBrush(brush)
        painter.setOpacity(self.orb_opacity)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        painter.drawEllipse(center_x - self.orb_size//2, center_y - self.orb_size//2, 
                          self.orb_size, self.orb_size)
        
        # Draw team satellites
        if self.team_states:
            angle_step = 360 / len(self.team_states)
            radius = 40
            
            for i, (teammate_id, state) in enumerate(self.team_states.items()):
                angle = i * angle_step
                satellite_x = center_x + radius * np.cos(np.radians(angle))
                satellite_y = center_y + radius * np.sin(np.radians(angle))
                
                satellite_color = QColor(100, 149, 237) if state == "FLOWING" else QColor(128, 128, 128)
                painter.setBrush(QBrush(satellite_color))
                painter.setOpacity(0.7)
                painter.drawEllipse(int(satellite_x-2), int(satellite_y-2), 5, 5)
                
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_state != "FLOWING":
            if self.current_state == "STUCK":
                self.command_bar.input_field.setPlaceholderText("Need a different perspective on this?")
            else:
                self.command_bar.input_field.setPlaceholderText("How can I help?")
                
            self.command_bar.show_centered()

def main():
    app = QApplication(sys.argv)
    
    try:
        if not firebase_admin._apps:
            from firebase_admin import credentials
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        print("Running in offline mode...")
    
    orb = EchoOrb()
    orb.show()
    
    print("ECHO Orb started - Click the orb to interact")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()