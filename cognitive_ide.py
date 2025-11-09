"""
ECHO: The Sentient Workspace
Feature 7: The Cognitive IDE - AI-powered code editor with GitHub integration
"""

import os
import threading
import time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from git import Repo
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

class CognitiveIDE(QWidget):
    """Cognitive IDE with GitHub import and AI pair programming"""
    
    def __init__(self, user_id: str, team_id: str):
        super().__init__()
        self.user_id = user_id
        self.team_id = team_id
        self.current_state = "IDLE"
        self.current_file = None
        self.workspace_dir = "./workspace"
        
        # Initialize OpenAI
        openai.api_key = Config.OPENAI_API_KEY
        
        # Initialize Firebase
        self._init_firebase()
        
        # Setup UI
        self.setup_ui()
        
        # Start cognitive trigger
        self.start_cognitive_trigger()
        
        # Listen for tasks from Canvas
        self.start_task_listener()
    
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
        """Setup the IDE interface"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # GitHub import
        self.github_input = QLineEdit()
        self.github_input.setPlaceholderText("GitHub URL (e.g., https://github.com/user/repo)")
        
        import_btn = QPushButton("📥 Import from GitHub")
        import_btn.clicked.connect(self.import_from_github)
        
        toolbar.addWidget(QLabel("GitHub:"))
        toolbar.addWidget(self.github_input)
        toolbar.addWidget(import_btn)
        
        # File tree and editor splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Files")
        self.file_tree.itemClicked.connect(self.open_file)
        self.file_tree.setMaximumWidth(250)
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        self.code_editor.textChanged.connect(self.on_code_changed)
        
        content_splitter.addWidget(self.file_tree)
        content_splitter.addWidget(self.code_editor)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background: #2d2d2d; color: #00FF00;")
        
        layout.addLayout(toolbar)
        layout.addWidget(content_splitter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Create workspace directory
        os.makedirs(self.workspace_dir, exist_ok=True)
        self.refresh_file_tree()
    
    def import_from_github(self):
        """Import repository from GitHub"""
        github_url = self.github_input.text().strip()
        
        if not github_url:
            QMessageBox.warning(self, "Error", "Please enter a GitHub URL")
            return
        
        try:
            self.status_label.setText("Cloning repository...")
            QApplication.processEvents()
            
            # Extract repo name
            repo_name = github_url.rstrip('/').split('/')[-1].replace('.git', '')
            target_dir = os.path.join(self.workspace_dir, repo_name)
            
            # Clone repository
            if os.path.exists(target_dir):
                QMessageBox.warning(self, "Error", f"Directory {repo_name} already exists")
                return
            
            Repo.clone_from(github_url, target_dir)
            
            self.status_label.setText(f"✅ Cloned {repo_name}")
            self.refresh_file_tree()
            
            QMessageBox.information(self, "Success", f"Repository cloned to {target_dir}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Clone failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to clone repository:\n{str(e)}")
    
    def refresh_file_tree(self):
        """Refresh the file tree"""
        self.file_tree.clear()
        
        if not os.path.exists(self.workspace_dir):
            return
        
        root_item = QTreeWidgetItem(self.file_tree, [self.workspace_dir])
        self.populate_tree(root_item, self.workspace_dir)
        self.file_tree.expandAll()
    
    def populate_tree(self, parent_item, path):
        """Recursively populate file tree"""
        try:
            items = os.listdir(path)
            items.sort()
            
            for item in items:
                if item.startswith('.'):
                    continue
                
                item_path = os.path.join(path, item)
                tree_item = QTreeWidgetItem(parent_item, [item])
                tree_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                
                if os.path.isdir(item_path):
                    tree_item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    self.populate_tree(tree_item, item_path)
                else:
                    tree_item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        except PermissionError:
            pass
    
    def open_file(self, item, column):
        """Open file in editor"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not file_path or os.path.isdir(file_path):
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.code_editor.setPlainText(content)
            self.current_file = file_path
            self.status_label.setText(f"Opened: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
    
    def on_code_changed(self):
        """Handle code changes"""
        if self.current_file:
            self.status_label.setText(f"Modified: {os.path.basename(self.current_file)}")
    
    def save_current_file(self):
        """Save current file"""
        if not self.current_file:
            return
        
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.code_editor.toPlainText())
            
            self.status_label.setText(f"✅ Saved: {os.path.basename(self.current_file)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def start_cognitive_trigger(self):
        """Start monitoring cognitive state for AI assistance"""
        def monitor_state():
            last_activity = time.time()
            stuck_triggered = False
            
            while True:
                try:
                    # Check if user is stuck
                    if self.current_state == "STUCK" and not stuck_triggered:
                        idle_time = time.time() - last_activity
                        
                        if idle_time > 60 and self.current_file:  # 60 seconds idle
                            self.trigger_socratic_question()
                            stuck_triggered = True
                    
                    elif self.current_state != "STUCK":
                        stuck_triggered = False
                        last_activity = time.time()
                    
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"Cognitive trigger error: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=monitor_state, daemon=True)
        thread.start()
    
    def trigger_socratic_question(self):
        """Generate Socratic question when user is stuck"""
        try:
            code = self.code_editor.toPlainText()
            cursor = self.code_editor.textCursor()
            cursor_position = cursor.position()
            
            # Get context around cursor
            lines = code.split('\n')
            current_line = code[:cursor_position].count('\n')
            context_start = max(0, current_line - 5)
            context_end = min(len(lines), current_line + 5)
            context = '\n'.join(lines[context_start:context_end])
            
            # Generate Socratic question
            prompt = f"""Act as an expert pair programmer. The user is stuck on this code:

```
{context}
```

The cursor is at line {current_line + 1}.

Do not solve it. Ask a single, Socratic question to un-block them. 
Format: # ECHO: [your question]"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            question = response.choices[0].message.content.strip()
            
            # Insert question as comment
            QTimer.singleShot(0, lambda: self.insert_ai_comment(question, current_line))
            
        except Exception as e:
            print(f"Socratic question error: {e}")
    
    def insert_ai_comment(self, comment: str, line_number: int):
        """Insert AI comment at specific line"""
        cursor = self.code_editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_number)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText(f"\n{comment}\n")
        
        self.status_label.setText("💡 ECHO has a question for you")
    
    def start_task_listener(self):
        """Listen for tasks from Living Canvas"""
        if not self.db:
            return
        
        def listen_to_tasks():
            try:
                tasks_ref = self.db.collection('tasks').where('assigned_to', '==', 'ide').where('status', '==', 'pending')
                
                def on_task_change(col_snapshot, changes, read_time):
                    for change in changes:
                        if change.type.name == 'ADDED':
                            task_data = change.document.to_dict()
                            QTimer.singleShot(0, lambda: self.execute_task(task_data, change.document.id))
                
                tasks_ref.on_snapshot(on_task_change)
                
            except Exception as e:
                print(f"Task listener error: {e}")
        
        thread = threading.Thread(target=listen_to_tasks, daemon=True)
        thread.start()
    
    def execute_task(self, task_data: dict, task_id: str):
        """Execute task from Living Canvas (Bolt.new style)"""
        try:
            description = task_data.get('description', '')
            
            self.status_label.setText(f"🤖 Building: {description[:50]}...")
            QApplication.processEvents()
            
            # Generate filename
            filename = description.lower().replace(' ', '_')[:30] + '.py'
            file_path = os.path.join(self.workspace_dir, filename)
            
            # Generate code using LLM
            prompt = f"""Build the complete, production-ready code for this task:

Task: {description}

Requirements:
- Write clean, well-documented Python code
- Include error handling
- Add type hints
- Follow best practices

Generate only the code, no explanations."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if generated_code.startswith('```'):
                generated_code = '\n'.join(generated_code.split('\n')[1:-1])
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            
            # Update task status
            if self.db:
                self.db.collection('tasks').document(task_id).update({
                    'status': 'completed',
                    'file_path': file_path
                })
            
            # Refresh UI
            self.refresh_file_tree()
            self.status_label.setText(f"✅ Built: {filename}")
            
            QMessageBox.information(self, "Task Complete", f"Generated {filename}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Task failed: {str(e)}")
            print(f"Task execution error: {e}")
    
    def update_state(self, new_state: str):
        """Update cognitive state"""
        self.current_state = new_state