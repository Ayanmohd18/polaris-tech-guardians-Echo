"""Bio-Cognitive HUD - The Sentient Glass Interface"""
import sys
from PyQt6.QtCore import Qt, QUrl, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from firebase_config import FirebaseConfig
import json

class CognitiveStateBridge:
    """Bridge between Python cognitive state and React UI"""
    def __init__(self, web_view):
        self.web_view = web_view
        self.db = FirebaseConfig.get_firestore()
        self.current_state = "IDLE"
        
    def start_listening(self):
        """Listen to Firebase cognitive state changes"""
        def on_snapshot(doc_snapshot, changes, read_time):
            for doc in doc_snapshot:
                data = doc.to_dict()
                new_state = data.get('current_state', 'IDLE')
                if new_state != self.current_state:
                    self.current_state = new_state
                    self.send_to_ui(new_state, data)
        
        self.db.collection('users').document('demo_user').collection('cognitive_states').on_snapshot(on_snapshot)
    
    def send_to_ui(self, state, data):
        """Send cognitive state to React UI"""
        js_code = f"window.updateCognitiveState('{state}', {json.dumps(data)})"
        self.web_view.page().runJavaScript(js_code)

class BioHUD(QMainWindow):
    """Main Bio-Cognitive HUD Window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECHO - Bio-Cognitive HUD")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 1600, 900)
        
        # Web engine for React UI
        self.web_view = QWebEngineView()
        import os
        build_path = os.path.abspath("ui/build/index.html")
        self.web_view.setUrl(QUrl.fromLocalFile(build_path))
        self.setCentralWidget(self.web_view)
        
        # Bridge for cognitive state
        self.bridge = CognitiveStateBridge(self.web_view)
        self.bridge.start_listening()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = BioHUD()
    hud.show()
    sys.exit(app.exec())
