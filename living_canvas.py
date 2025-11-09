"""
ECHO: The Sentient Workspace
Feature 8: The Living Canvas - Figma-like design canvas with task spawning
"""

import os
import base64
from io import BytesIO
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import requests
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

class CanvasNode(QGraphicsItem):
    """Base class for canvas nodes"""
    
    def __init__(self, x, y, width, height):
        super().__init__()
        self.setPos(x, y)
        self.width = width
        self.height = height
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

class RectangleNode(CanvasNode):
    """Rectangle shape node"""
    
    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(QColor(74, 144, 226, 100)))
        painter.setPen(QPen(QColor(74, 144, 226), 2))
        painter.drawRect(0, 0, self.width, self.height)

class TextNode(CanvasNode):
    """Text node with task detection"""
    
    def __init__(self, x, y, text=""):
        super().__init__(x, y, 200, 100)
        self.text = text
        self.is_task = self.detect_task()
    
    def detect_task(self):
        """Detect if text is a task"""
        return self.text.strip().upper().startswith(('TASK:', 'TODO:'))
    
    def paint(self, painter, option, widget):
        # Background
        if self.is_task:
            painter.setBrush(QBrush(QColor(255, 107, 53, 50)))
            painter.setPen(QPen(QColor(255, 107, 53), 2))
        else:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        painter.drawRect(0, 0, self.width, self.height)
        
        # Text
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(QRectF(10, 10, self.width - 20, self.height - 20), 
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                        self.text)
        
        # Task indicator
        if self.is_task:
            painter.setBrush(QBrush(QColor(255, 107, 53)))
            painter.drawEllipse(self.width - 30, 10, 20, 20)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QRectF(self.width - 30, 10, 20, 20), 
                           Qt.AlignmentFlag.AlignCenter, "▶")

class ImageNode(CanvasNode):
    """Image node for Figma imports"""
    
    def __init__(self, x, y, pixmap):
        self.pixmap = pixmap
        super().__init__(x, y, pixmap.width(), pixmap.height())
    
    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.pixmap)
        painter.setPen(QPen(QColor(74, 144, 226), 2))
        painter.drawRect(0, 0, self.width, self.height)

class LivingCanvas(QWidget):
    """Living Canvas for design and planning"""
    
    def __init__(self, user_id: str, team_id: str):
        super().__init__()
        self.user_id = user_id
        self.team_id = team_id
        self.current_tool = "select"
        
        # Initialize OpenAI
        openai.api_key = Config.OPENAI_API_KEY
        
        # Initialize Firebase
        self._init_firebase()
        
        # Setup UI
        self.setup_ui()
    
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def setup_ui(self):
        """Setup the canvas interface"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Tools
        select_btn = QPushButton("🖱️ Select")
        select_btn.clicked.connect(lambda: self.set_tool("select"))
        
        rect_btn = QPushButton("⬜ Rectangle")
        rect_btn.clicked.connect(lambda: self.set_tool("rectangle"))
        
        text_btn = QPushButton("📝 Text")
        text_btn.clicked.connect(lambda: self.set_tool("text"))
        
        toolbar.addWidget(select_btn)
        toolbar.addWidget(rect_btn)
        toolbar.addWidget(text_btn)
        toolbar.addStretch()
        
        # Figma import
        self.figma_input = QLineEdit()
        self.figma_input.setPlaceholderText("Figma File URL")
        
        figma_btn = QPushButton("🎨 Import from Figma")
        figma_btn.clicked.connect(self.import_from_figma)
        
        toolbar.addWidget(self.figma_input)
        toolbar.addWidget(figma_btn)
        
        # Graphics view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 2000)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Grid background
        self.view.setBackgroundBrush(QBrush(QColor(250, 250, 250)))
        
        layout.addLayout(toolbar)
        layout.addWidget(self.view)
        
        self.setLayout(layout)
        
        # Mouse tracking
        self.view.viewport().installEventFilter(self)
        self.drawing_start = None
    
    def set_tool(self, tool: str):
        """Set current drawing tool"""
        self.current_tool = tool
        
        if tool == "select":
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
    
    def eventFilter(self, obj, event):
        """Handle mouse events for drawing"""
        if obj == self.view.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                if self.current_tool != "select":
                    self.drawing_start = self.view.mapToScene(event.pos())
                    return True
            
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self.drawing_start and self.current_tool != "select":
                    end_pos = self.view.mapToScene(event.pos())
                    self.create_node(self.drawing_start, end_pos)
                    self.drawing_start = None
                    return True
        
        return super().eventFilter(obj, event)
    
    def create_node(self, start_pos, end_pos):
        """Create node based on current tool"""
        x = min(start_pos.x(), end_pos.x())
        y = min(start_pos.y(), end_pos.y())
        width = abs(end_pos.x() - start_pos.x())
        height = abs(end_pos.y() - start_pos.y())
        
        if self.current_tool == "rectangle":
            node = RectangleNode(x, y, max(width, 50), max(height, 50))
            self.scene.addItem(node)
        
        elif self.current_tool == "text":
            text, ok = QInputDialog.getText(self, "Text Node", "Enter text:")
            if ok and text:
                node = TextNode(x, y, text)
                self.scene.addItem(node)
                
                # Check if it's a task
                if node.is_task:
                    self.handle_task_node(node)
    
    def handle_task_node(self, node: TextNode):
        """Handle task node creation"""
        reply = QMessageBox.question(
            self,
            "Task Detected",
            f"Build this task?\n\n{node.text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.spawn_task(node.text)
    
    def spawn_task(self, task_text: str):
        """Spawn task to Firebase for IDE to execute"""
        try:
            # Extract task description
            description = task_text.split(':', 1)[1].strip() if ':' in task_text else task_text
            
            # Save to Firebase
            if self.db:
                self.db.collection('tasks').add({
                    'description': description,
                    'assigned_to': 'ide',
                    'status': 'pending',
                    'created_by': self.user_id,
                    'timestamp': firestore.SERVER_TIMESTAMP
                })
                
                QMessageBox.information(self, "Task Spawned", f"Task sent to Cognitive IDE:\n{description}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to spawn task:\n{str(e)}")
    
    def import_from_figma(self):
        """Import design from Figma"""
        figma_url = self.figma_input.text().strip()
        
        if not figma_url:
            QMessageBox.warning(self, "Error", "Please enter a Figma URL")
            return
        
        try:
            # Extract file key from URL
            # Format: https://www.figma.com/file/{file_key}/...
            parts = figma_url.split('/')
            if 'file' in parts:
                file_key = parts[parts.index('file') + 1]
            else:
                QMessageBox.warning(self, "Error", "Invalid Figma URL format")
                return
            
            # Get Figma API token from settings
            figma_token = os.getenv('FIGMA_API_TOKEN', '')
            
            if not figma_token:
                QMessageBox.warning(self, "Error", "Figma API token not configured. Please add to .env file.")
                return
            
            # Fetch file from Figma API
            headers = {'X-Figma-Token': figma_token}
            response = requests.get(f'https://api.figma.com/v1/files/{file_key}', headers=headers)
            
            if response.status_code != 200:
                QMessageBox.critical(self, "Error", f"Figma API error: {response.status_code}")
                return
            
            file_data = response.json()
            
            # Get images
            node_ids = []
            self.extract_node_ids(file_data['document'], node_ids)
            
            if node_ids:
                # Get image URLs
                images_response = requests.get(
                    f'https://api.figma.com/v1/images/{file_key}',
                    headers=headers,
                    params={'ids': ','.join(node_ids[:5]), 'format': 'png'}  # Limit to 5 frames
                )
                
                if images_response.status_code == 200:
                    images_data = images_response.json()
                    self.process_figma_images(images_data.get('images', {}))
            
            QMessageBox.information(self, "Success", "Figma design imported!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import from Figma:\n{str(e)}")
    
    def extract_node_ids(self, node, node_ids):
        """Recursively extract node IDs from Figma document"""
        if node.get('type') == 'FRAME':
            node_ids.append(node['id'])
        
        for child in node.get('children', []):
            self.extract_node_ids(child, node_ids)
    
    def process_figma_images(self, images: dict):
        """Process and place Figma images on canvas"""
        x_offset = 100
        y_offset = 100
        
        for node_id, image_url in images.items():
            try:
                # Download image
                response = requests.get(image_url)
                if response.status_code == 200:
                    # Create pixmap
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    
                    # Scale down if too large
                    if pixmap.width() > 400:
                        pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                    
                    # Add to canvas
                    image_node = ImageNode(x_offset, y_offset, pixmap)
                    self.scene.addItem(image_node)
                    
                    # Analyze with GPT-4 Vision
                    self.analyze_design_with_ai(pixmap, x_offset + pixmap.width() + 20, y_offset)
                    
                    y_offset += pixmap.height() + 50
                    
            except Exception as e:
                print(f"Error processing image: {e}")
    
    def analyze_design_with_ai(self, pixmap: QPixmap, x: int, y: int):
        """Analyze design with GPT-4 Vision"""
        try:
            # Convert pixmap to base64
            buffer = BytesIO()
            pixmap.save(buffer, "PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Call GPT-4 Vision
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this UI design as a component tree. What are the key elements and layout? Be concise."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }],
                max_tokens=300
            )
            
            description = response.choices[0].message.content
            
            # Add description as text node
            text_node = TextNode(x, y, f"AI Analysis:\n\n{description}")
            self.scene.addItem(text_node)
            
        except Exception as e:
            print(f"AI analysis error: {e}")