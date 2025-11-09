"""
ECHO: The Sentient Workspace
Feature 6: The Vessel - Main unified workspace application
"""

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import threading

class EchoWorkspace(QMainWindow):
    """The main ECHO Workspace - A sentient IDE that adapts to cognitive state"""
    
    state_changed = pyqtSignal(str)
    
    def __init__(self, user_id: str, team_id: str = Config.DEFAULT_TEAM_ID):
        super().__init__()
        self.user_id = user_id
        self.team_id = team_id
        self.current_state = "IDLE"
        
        # Initialize Firebase
        self._init_firebase()
        
        # Setup UI
        self.setup_workspace()
        
        # Start state listener
        self.start_state_listener()
        
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def setup_workspace(self):
        """Setup the main workspace with three panes"""
        self.setWindowTitle("ECHO: The Sentient Workspace")
        self.setGeometry(100, 100, 1600, 900)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Main splitter for three panes
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Pane 1: Context (Left) - Web browser for Notion/Figma/GitHub
        self.context_pane = self.create_context_pane()
        self.main_splitter.addWidget(self.context_pane)
        
        # Pane 2: Canvas (Center) - Living Canvas for design
        self.canvas_pane = self.create_canvas_pane()
        self.main_splitter.addWidget(self.canvas_pane)
        
        # Pane 3: IDE (Right) - Code editor
        self.ide_pane = self.create_ide_pane()
        self.main_splitter.addWidget(self.ide_pane)
        
        # Set initial sizes (equal distribution)
        self.main_splitter.setSizes([400, 600, 600])
        
        main_layout.addWidget(self.main_splitter)
        
        # Create toolbar
        self.create_toolbar()
        
        # Apply initial styling
        self.apply_state_styling("IDLE")
    
    def create_context_pane(self):
        """Create the Context pane with embedded browser"""
        dock = QDockWidget("Context", self)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                        QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        container = QWidget()
        layout = QVBoxLayout()
        
        # URL bar
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL (Notion, Figma, GitHub...)")
        self.url_input.returnPressed.connect(self.load_url)
        
        load_btn = QPushButton("Go")
        load_btn.clicked.connect(self.load_url)
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(load_btn)
        
        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://notion.so"))
        
        layout.addLayout(url_layout)
        layout.addWidget(self.web_view)
        
        container.setLayout(layout)
        dock.setWidget(container)
        
        return dock
    
    def create_canvas_pane(self):
        """Create the Living Canvas pane"""
        dock = QDockWidget("Living Canvas", self)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                        QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        # Import the Living Canvas module
        from living_canvas import LivingCanvas
        self.canvas = LivingCanvas(self.user_id, self.team_id)
        
        dock.setWidget(self.canvas)
        return dock
    
    def create_ide_pane(self):
        """Create the Cognitive IDE pane"""
        dock = QDockWidget("Cognitive IDE", self)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                        QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        # Import the Cognitive IDE module
        from cognitive_ide import CognitiveIDE
        self.ide = CognitiveIDE(self.user_id, self.team_id)
        
        dock.setWidget(self.ide)
        return dock
    
    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Quick access buttons
        notion_action = QAction("📝 Notion", self)
        notion_action.triggered.connect(lambda: self.quick_load("https://notion.so"))
        toolbar.addAction(notion_action)
        
        figma_action = QAction("🎨 Figma", self)
        figma_action.triggered.connect(lambda: self.quick_load("https://figma.com"))
        toolbar.addAction(figma_action)
        
        github_action = QAction("💻 GitHub", self)
        github_action.triggered.connect(lambda: self.quick_load("https://github.com"))
        toolbar.addAction(github_action)
        
        toolbar.addSeparator()
        
        # State indicator
        self.state_indicator = QLabel("State: IDLE")
        self.state_indicator.setStyleSheet("padding: 5px; font-weight: bold;")
        toolbar.addWidget(self.state_indicator)
        
        toolbar.addSeparator()
        
        # Settings
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
    
    def load_url(self):
        """Load URL in context pane"""
        url = self.url_input.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web_view.setUrl(QUrl(url))
    
    def quick_load(self, url: str):
        """Quick load a URL"""
        self.url_input.setText(url)
        self.web_view.setUrl(QUrl(url))
    
    def start_state_listener(self):
        """Listen to cognitive state changes from Firebase"""
        if not self.db:
            return
        
        def listen_to_state():
            try:
                doc_ref = self.db.collection('team_states').document(self.team_id).collection('user_states').document(self.user_id)
                
                def on_state_change(doc_snapshot, changes, read_time):
                    for change in changes:
                        if change.type.name in ['ADDED', 'MODIFIED']:
                            data = change.document.to_dict()
                            if data and 'state' in data:
                                new_state = data['state']
                                QTimer.singleShot(0, lambda: self.handle_state_change(new_state))
                
                doc_ref.on_snapshot(on_state_change)
                
            except Exception as e:
                print(f"State listener error: {e}")
        
        listener_thread = threading.Thread(target=listen_to_state, daemon=True)
        listener_thread.start()
    
    def handle_state_change(self, new_state: str):
        """Handle cognitive state changes"""
        if new_state == self.current_state:
            return
        
        old_state = self.current_state
        self.current_state = new_state
        
        print(f"🧠 State changed: {old_state} → {new_state}")
        
        # Update UI based on state
        self.apply_state_styling(new_state)
        
        # Update state indicator
        self.state_indicator.setText(f"State: {new_state}")
        
        # Emit signal for other components
        self.state_changed.emit(new_state)
    
    def apply_state_styling(self, state: str):
        """Apply UI styling based on cognitive state"""
        
        if state == "FLOWING":
            # Minimize Context and Canvas, maximize IDE
            self.main_splitter.setSizes([100, 100, 1400])
            
            # Fade UI elements
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QDockWidget {
                    border: none;
                }
                QToolBar {
                    background-color: #2d2d2d;
                    border: none;
                    spacing: 5px;
                }
                QLabel {
                    color: #00FF00;
                }
            """)
            
            # Hide toolbars for minimal distraction
            for toolbar in self.findChildren(QToolBar):
                toolbar.setVisible(False)
        
        elif state in ["STUCK", "FRUSTRATED"]:
            # Re-show Context and Canvas
            self.main_splitter.setSizes([400, 600, 600])
            
            # Restore UI elements
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QDockWidget {
                    border: 1px solid #ddd;
                }
                QToolBar {
                    background-color: #ffffff;
                    border-bottom: 1px solid #ddd;
                    spacing: 5px;
                }
                QLabel {
                    color: #4A90E2;
                }
            """)
            
            # Show toolbars
            for toolbar in self.findChildren(QToolBar):
                toolbar.setVisible(True)
        
        else:  # IDLE
            # Balanced layout
            self.main_splitter.setSizes([400, 600, 600])
            
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                }
                QDockWidget {
                    border: 1px solid #ddd;
                }
                QToolBar {
                    background-color: #f8f8f8;
                    border-bottom: 1px solid #ddd;
                }
                QLabel {
                    color: #333;
                }
            """)
    
    def show_settings(self):
        """Show settings dialog"""
        from data_bridge import SettingsDialog
        dialog = SettingsDialog(self.user_id, self)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    workspace = EchoWorkspace("user_001")
    workspace.show()
    
    sys.exit(app.exec())