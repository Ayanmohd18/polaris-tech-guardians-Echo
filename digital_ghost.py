"""
ECHO: The Sentient Workspace
Feature 11: The Digital Ghost - Persona Synthesis
Learns your unique style from your entire digital footprint
"""

import os
import json
from typing import List, Dict, Any, Optional
from git import Repo
import requests
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from notion_client import Client as NotionClient
from config import Config
import chromadb
from datetime import datetime

class DigitalGhost:
    """Synthesizes user's digital persona from their entire footprint"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize services
        openai.api_key = Config.OPENAI_API_KEY
        self._init_firebase()
        self._init_chromadb()
        
        # Persona data
        self.persona_vector = None
        self.style_profile = {}
    
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def _init_chromadb(self):
        """Initialize ChromaDB for persona vectors"""
        self.chroma_client = chromadb.PersistentClient(
            path=f"{Config.CHROMA_PERSIST_DIRECTORY}_persona"
        )
        
        self.persona_collection = self.chroma_client.get_or_create_collection(
            name=f"persona_{self.user_id}",
            metadata={"description": "User's digital persona"}
        )
    
    def index_github_history(self, github_username: str, github_token: Optional[str] = None):
        """Index user's GitHub commit history and code style"""
        print(f"📚 Indexing GitHub history for {github_username}...")
        
        try:
            headers = {}
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            # Get user's repositories
            repos_url = f'https://api.github.com/users/{github_username}/repos'
            response = requests.get(repos_url, headers=headers)
            repos = response.json()
            
            code_samples = []
            commit_messages = []
            
            for repo in repos[:10]:  # Limit to 10 repos
                repo_name = repo['name']
                
                # Get commits
                commits_url = f"https://api.github.com/repos/{github_username}/{repo_name}/commits"
                commits_response = requests.get(commits_url, headers=headers)
                
                if commits_response.status_code == 200:
                    commits = commits_response.json()[:20]  # Last 20 commits
                    
                    for commit in commits:
                        message = commit['commit']['message']
                        commit_messages.append(message)
                        
                        # Get commit diff for code style
                        commit_sha = commit['sha']
                        diff_url = f"https://api.github.com/repos/{github_username}/{repo_name}/commits/{commit_sha}"
                        diff_response = requests.get(diff_url, headers=headers)
                        
                        if diff_response.status_code == 200:
                            files = diff_response.json().get('files', [])
                            for file in files[:3]:  # Sample 3 files
                                if file.get('patch'):
                                    code_samples.append(file['patch'])
            
            # Analyze code style
            self._analyze_code_style(code_samples)
            
            # Analyze commit message style
            self._analyze_commit_style(commit_messages)
            
            # Store in ChromaDB
            self._store_code_samples(code_samples)
            
            print(f"✅ Indexed {len(code_samples)} code samples and {len(commit_messages)} commits")
            
        except Exception as e:
            print(f"GitHub indexing error: {e}")
    
    def index_notion_content(self, notion_token: str):
        """Index user's Notion pages for writing style"""
        print("📝 Indexing Notion content...")
        
        try:
            notion = NotionClient(auth=notion_token)
            
            # Search for pages
            response = notion.search(filter={"property": "object", "value": "page"})
            pages = response.get('results', [])
            
            writing_samples = []
            
            for page in pages[:20]:  # Limit to 20 pages
                page_id = page['id']
                
                # Get page content
                blocks = notion.blocks.children.list(page_id)
                
                for block in blocks.get('results', []):
                    if block['type'] == 'paragraph':
                        text = self._extract_text_from_block(block)
                        if text and len(text) > 50:
                            writing_samples.append(text)
            
            # Analyze writing style
            self._analyze_writing_style(writing_samples)
            
            # Store in ChromaDB
            self._store_writing_samples(writing_samples)
            
            print(f"✅ Indexed {len(writing_samples)} writing samples")
            
        except Exception as e:
            print(f"Notion indexing error: {e}")
    
    def _extract_text_from_block(self, block: dict) -> str:
        """Extract text from Notion block"""
        try:
            if block['type'] == 'paragraph':
                rich_text = block['paragraph'].get('rich_text', [])
                return ' '.join([text['plain_text'] for text in rich_text])
        except:
            pass
        return ""
    
    def _analyze_code_style(self, code_samples: List[str]):
        """Analyze user's coding style using LLM"""
        if not code_samples:
            return
        
        try:
            # Sample code for analysis
            sample_code = '\n\n'.join(code_samples[:5])
            
            prompt = f"""Analyze this developer's coding style and provide a profile:

{sample_code}

Provide JSON with:
- naming_convention: (snake_case, camelCase, etc)
- comment_style: (verbose, minimal, docstring-heavy)
- code_organization: (functional, OOP, mixed)
- preferred_patterns: [list of patterns]
- tone: (technical, casual, formal)"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            self.style_profile['code'] = result
            
            # Store in Firebase
            if self.db:
                self.db.collection('user_personas').document(self.user_id).set({
                    'code_style': result,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }, merge=True)
            
        except Exception as e:
            print(f"Code style analysis error: {e}")
    
    def _analyze_commit_style(self, commit_messages: List[str]):
        """Analyze commit message style"""
        if not commit_messages:
            return
        
        try:
            sample_commits = '\n'.join(commit_messages[:20])
            
            prompt = f"""Analyze this developer's commit message style:

{sample_commits}

Provide JSON with:
- format: (conventional, descriptive, brief)
- tone: (professional, casual, technical)
- detail_level: (high, medium, low)"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            self.style_profile['commits'] = result
            
        except Exception as e:
            print(f"Commit style analysis error: {e}")
    
    def _analyze_writing_style(self, writing_samples: List[str]):
        """Analyze user's writing style"""
        if not writing_samples:
            return
        
        try:
            sample_text = '\n\n'.join(writing_samples[:5])
            
            prompt = f"""Analyze this person's writing style:

{sample_text}

Provide JSON with:
- tone: (confident, humble, technical, approachable)
- sentence_structure: (complex, simple, varied)
- vocabulary_level: (technical, accessible, mixed)
- personality_traits: [list]"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            self.style_profile['writing'] = result
            
            # Store in Firebase
            if self.db:
                self.db.collection('user_personas').document(self.user_id).set({
                    'writing_style': result,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }, merge=True)
            
        except Exception as e:
            print(f"Writing style analysis error: {e}")
    
    def _store_code_samples(self, samples: List[str]):
        """Store code samples in ChromaDB"""
        for i, sample in enumerate(samples):
            self.persona_collection.add(
                documents=[sample],
                metadatas=[{'type': 'code', 'index': i}],
                ids=[f'code_{i}']
            )
    
    def _store_writing_samples(self, samples: List[str]):
        """Store writing samples in ChromaDB"""
        for i, sample in enumerate(samples):
            self.persona_collection.add(
                documents=[sample],
                metadatas=[{'type': 'writing', 'index': i}],
                ids=[f'writing_{i}']
            )
    
    def generate_in_user_voice(self, prompt: str, content_type: str = 'writing') -> str:
        """Generate content in user's unique voice"""
        try:
            # Get style profile
            style = self.style_profile.get(content_type, {})
            
            # Get similar samples from ChromaDB
            results = self.persona_collection.query(
                query_texts=[prompt],
                n_results=3,
                where={'type': content_type}
            )
            
            examples = results['documents'][0] if results['documents'] else []
            
            # Build persona-aware prompt
            persona_prompt = f"""You are writing as this person. Match their style exactly.

Style Profile:
{json.dumps(style, indent=2)}

Example of their {content_type}:
{chr(10).join(examples[:2])}

Now write: {prompt}

Write in THEIR voice, not yours."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": persona_prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Voice generation error: {e}")
            return ""
    
    def generate_code_in_user_style(self, task_description: str, context: str = "") -> str:
        """Generate code matching user's exact coding style"""
        try:
            # Get code style profile
            code_style = self.style_profile.get('code', {})
            
            # Get similar code samples
            results = self.persona_collection.query(
                query_texts=[task_description],
                n_results=5,
                where={'type': 'code'}
            )
            
            code_examples = results['documents'][0] if results['documents'] else []
            
            # Build style-aware prompt
            style_prompt = f"""Generate code for this task, matching the user's EXACT style.

User's Code Style:
- Naming: {code_style.get('naming_convention', 'snake_case')}
- Comments: {code_style.get('comment_style', 'minimal')}
- Organization: {code_style.get('code_organization', 'functional')}
- Patterns: {', '.join(code_style.get('preferred_patterns', []))}

Examples of their code:
```
{chr(10).join(code_examples[:2])}
```

Task: {task_description}

{f'Context: {context}' if context else ''}

Generate code that looks like THEY wrote it, not generic code."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": style_prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            code = response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if code.startswith('```'):
                code = '\n'.join(code.split('\n')[1:-1])
            
            return code
            
        except Exception as e:
            print(f"Code generation error: {e}")
            return ""
    
    def get_persona_summary(self) -> Dict[str, Any]:
        """Get summary of user's digital persona"""
        return {
            'user_id': self.user_id,
            'style_profile': self.style_profile,
            'indexed_samples': self.persona_collection.count(),
            'last_updated': datetime.now().isoformat()
        }

class PersonaIndexingDialog:
    """Dialog for indexing user's digital footprint"""
    
    @staticmethod
    def show_indexing_dialog(user_id: str):
        """Show dialog to configure persona indexing"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QProgressBar, QMessageBox
        
        dialog = QDialog()
        dialog.setWindowTitle("ECHO - Build Your Digital Ghost")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("👻 Build Your Digital Ghost")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        
        description = QLabel(
            "ECHO will analyze your digital footprint to learn your unique style.\n"
            "This enables AI to write code and content that sounds like YOU."
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 10px; color: #666;")
        
        # Input fields
        form = QFormLayout()
        
        github_username = QLineEdit()
        github_username.setPlaceholderText("your-username")
        
        github_token = QLineEdit()
        github_token.setPlaceholderText("ghp_xxxxx (optional, for private repos)")
        github_token.setEchoMode(QLineEdit.EchoMode.Password)
        
        notion_token = QLineEdit()
        notion_token.setPlaceholderText("secret_xxxxx (optional)")
        notion_token.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("GitHub Username:", github_username)
        form.addRow("GitHub Token:", github_token)
        form.addRow("Notion API Token:", notion_token)
        
        # Progress bar
        progress = QProgressBar()
        progress.setVisible(False)
        
        # Buttons
        index_btn = QPushButton("🚀 Build My Digital Ghost")
        index_btn.clicked.connect(lambda: PersonaIndexingDialog._start_indexing(
            user_id, github_username.text(), github_token.text(), 
            notion_token.text(), progress, dialog
        ))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(form)
        layout.addWidget(progress)
        layout.addWidget(index_btn)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    @staticmethod
    def _start_indexing(user_id, github_username, github_token, notion_token, progress, dialog):
        """Start the indexing process"""
        from PyQt6.QtWidgets import QMessageBox
        import threading
        
        if not github_username and not notion_token:
            QMessageBox.warning(dialog, "Error", "Please provide at least GitHub username or Notion token")
            return
        
        progress.setVisible(True)
        progress.setRange(0, 0)  # Indeterminate
        
        def index_thread():
            ghost = DigitalGhost(user_id)
            
            if github_username:
                ghost.index_github_history(github_username, github_token or None)
            
            if notion_token:
                ghost.index_notion_content(notion_token)
            
            # Show summary
            summary = ghost.get_persona_summary()
            
            QMessageBox.information(
                dialog,
                "Success",
                f"✅ Digital Ghost built!\n\n"
                f"Indexed {summary['indexed_samples']} samples\n"
                f"Code style: {summary['style_profile'].get('code', {}).get('naming_convention', 'N/A')}\n"
                f"Writing tone: {summary['style_profile'].get('writing', {}).get('tone', 'N/A')}\n\n"
                f"ECHO will now generate content in YOUR voice!"
            )
            
            progress.setVisible(False)
        
        thread = threading.Thread(target=index_thread, daemon=True)
        thread.start()

if __name__ == "__main__":
    # Test the digital ghost
    ghost = DigitalGhost("user_001")
    
    # Example: Generate in user's voice
    headline = ghost.generate_in_user_voice(
        "Write a headline for a developer productivity tool",
        content_type='writing'
    )
    
    print(f"Generated headline: {headline}")