"""
ECHO: The Sentient Workspace
Feature 10: Passive Intent-Casting - The Unspoken Word
Real-time audio transcription and intent detection without wake words
"""

import threading
import time
import queue
import numpy as np
import sounddevice as sd
from typing import Optional, List, Dict, Any
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import re
from datetime import datetime

class PassiveIntentCaster:
    """Listens to ambient speech and captures unspoken intents"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.running = False
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_duration = 3  # seconds
        self.audio_queue = queue.Queue()
        
        # Intent detection
        self.intent_buffer = []
        self.detected_intents = []
        
        # OpenAI
        openai.api_key = Config.OPENAI_API_KEY
        
        # Firebase
        self._init_firebase()
        
        # Intent patterns
        self.intent_patterns = {
            'refactor': r'(should|need to|gotta|have to).*(refactor|break out|split|separate|extract)',
            'todo': r'(later|tomorrow|eventually|remind me|don\'t forget)',
            'bug': r'(bug|broken|not working|issue|problem|error)',
            'feature': r'(add|build|create|implement|need).*(feature|functionality)',
            'optimize': r'(slow|optimize|performance|faster|speed up)',
            'document': r'(document|comment|explain|write docs)',
            'test': r'(test|testing|unit test|integration test)'
        }
    
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
        """Start passive listening"""
        self.running = True
        
        # Start audio capture thread
        audio_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        audio_thread.start()
        
        # Start transcription thread
        transcription_thread = threading.Thread(target=self._transcription_loop, daemon=True)
        transcription_thread.start()
        
        # Start intent analysis thread
        intent_thread = threading.Thread(target=self._intent_analysis_loop, daemon=True)
        intent_thread.start()
        
        print("🎤 Passive Intent-Casting started (listening for unspoken thoughts...)")
    
    def stop(self):
        """Stop passive listening"""
        self.running = False
        print("🎤 Passive Intent-Casting stopped")
    
    def _audio_capture_loop(self):
        """Continuously capture audio chunks"""
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio status: {status}")
            
            # Calculate RMS to detect speech
            rms = np.sqrt(np.mean(indata**2))
            
            # Only process if there's significant audio (speech detection)
            if rms > 0.01:  # Threshold for speech
                self.audio_queue.put(indata.copy())
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=audio_callback,
                blocksize=int(self.sample_rate * self.chunk_duration)
            ):
                while self.running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Audio capture error: {e}")
    
    def _transcription_loop(self):
        """Transcribe audio chunks using Whisper"""
        while self.running:
            try:
                # Get audio chunk (with timeout)
                try:
                    audio_data = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Transcribe using OpenAI Whisper
                transcription = self._transcribe_audio(audio_data)
                
                if transcription:
                    self.intent_buffer.append({
                        'text': transcription,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Keep buffer size manageable
                    if len(self.intent_buffer) > 20:
                        self.intent_buffer.pop(0)
                    
                    print(f"🎤 Heard: {transcription}")
                
            except Exception as e:
                print(f"Transcription error: {e}")
                time.sleep(1)
    
    def _transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            # Convert numpy array to WAV format
            import io
            import wave
            
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            buffer.seek(0)
            buffer.name = "audio.wav"
            
            # Transcribe with Whisper
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=buffer,
                language="en"
            )
            
            text = response.get('text', '').strip()
            return text if len(text) > 5 else None  # Filter out noise
            
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return None
    
    def _intent_analysis_loop(self):
        """Analyze transcriptions for intents"""
        while self.running:
            try:
                if len(self.intent_buffer) < 2:
                    time.sleep(2)
                    continue
                
                # Get recent transcriptions
                recent_text = ' '.join([item['text'] for item in self.intent_buffer[-5:]])
                
                # Check for intent patterns
                detected_intent = self._detect_intent(recent_text)
                
                if detected_intent:
                    self._handle_detected_intent(detected_intent)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Intent analysis error: {e}")
                time.sleep(2)
    
    def _detect_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect intent from text using patterns and LLM"""
        text_lower = text.lower()
        
        # First pass: Pattern matching
        for intent_type, pattern in self.intent_patterns.items():
            if re.search(pattern, text_lower):
                return {
                    'type': intent_type,
                    'text': text,
                    'confidence': 'pattern_match'
                }
        
        # Second pass: LLM-based intent detection
        if len(text) > 20:  # Only for substantial text
            return self._llm_intent_detection(text)
        
        return None
    
    def _llm_intent_detection(self, text: str) -> Optional[Dict[str, Any]]:
        """Use LLM to detect subtle intents"""
        try:
            prompt = f"""Analyze this developer's muttering for actionable intent:

"{text}"

Is there an unspoken TODO, refactor need, or concern? Respond in JSON:
{{"has_intent": true/false, "type": "refactor/todo/bug/feature/none", "task": "brief description", "urgency": "low/medium/high"}}

Only detect genuine intents, not casual remarks."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            if result.get('has_intent'):
                return {
                    'type': result.get('type', 'todo'),
                    'text': text,
                    'task': result.get('task', ''),
                    'urgency': result.get('urgency', 'low'),
                    'confidence': 'llm_detected'
                }
            
        except Exception as e:
            print(f"LLM intent detection error: {e}")
        
        return None
    
    def _handle_detected_intent(self, intent: Dict[str, Any]):
        """Handle detected intent"""
        try:
            # Check if already processed
            intent_signature = f"{intent['type']}:{intent.get('task', intent['text'][:50])}"
            
            if any(d.get('signature') == intent_signature for d in self.detected_intents):
                return  # Already processed
            
            # Add to detected intents
            intent['signature'] = intent_signature
            intent['timestamp'] = datetime.now().isoformat()
            self.detected_intents.append(intent)
            
            # Pulse the orb
            self._pulse_orb()
            
            # Store intent for later action
            self._store_intent(intent)
            
            print(f"💡 Intent detected: {intent['type']} - {intent.get('task', intent['text'][:50])}")
            
        except Exception as e:
            print(f"Intent handling error: {e}")
    
    def _pulse_orb(self):
        """Pulse the ECHO orb to acknowledge intent capture"""
        if self.db:
            try:
                self.db.collection('orb_events').add({
                    'user_id': self.user_id,
                    'event': 'intent_captured',
                    'timestamp': firestore.SERVER_TIMESTAMP
                })
            except:
                pass
    
    def _store_intent(self, intent: Dict[str, Any]):
        """Store intent in Firebase for later retrieval"""
        if not self.db:
            return
        
        try:
            self.db.collection('captured_intents').add({
                'user_id': self.user_id,
                'type': intent['type'],
                'text': intent['text'],
                'task': intent.get('task', ''),
                'urgency': intent.get('urgency', 'low'),
                'confidence': intent['confidence'],
                'status': 'pending',
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print(f"Intent storage error: {e}")
    
    def get_pending_intents(self) -> List[Dict[str, Any]]:
        """Get pending intents for user review"""
        if not self.db:
            return []
        
        try:
            docs = self.db.collection('captured_intents')\
                .where('user_id', '==', self.user_id)\
                .where('status', '==', 'pending')\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(10)\
                .stream()
            
            intents = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                intents.append(data)
            
            return intents
            
        except Exception as e:
            print(f"Get intents error: {e}")
            return []
    
    def create_task_from_intent(self, intent_id: str) -> bool:
        """Convert captured intent into actionable task"""
        if not self.db:
            return False
        
        try:
            # Get intent
            intent_doc = self.db.collection('captured_intents').document(intent_id).get()
            
            if not intent_doc.exists:
                return False
            
            intent_data = intent_doc.to_dict()
            
            # Create task on Living Canvas
            task_description = intent_data.get('task') or intent_data.get('text')
            
            self.db.collection('tasks').add({
                'description': f"[From Intent] {task_description}",
                'type': intent_data.get('type', 'todo'),
                'urgency': intent_data.get('urgency', 'low'),
                'assigned_to': 'canvas',
                'status': 'pending',
                'created_by': self.user_id,
                'source': 'passive_intent',
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            # Mark intent as processed
            self.db.collection('captured_intents').document(intent_id).update({
                'status': 'converted_to_task'
            })
            
            return True
            
        except Exception as e:
            print(f"Task creation error: {e}")
            return False

class IntentReviewDialog:
    """Dialog to review captured intents before commit"""
    
    @staticmethod
    def show_pre_commit_review(intent_caster: PassiveIntentCaster):
        """Show dialog before git commit"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, QHBoxLayout, QMessageBox
        
        pending_intents = intent_caster.get_pending_intents()
        
        if not pending_intents:
            return True  # No intents, proceed with commit
        
        dialog = QDialog()
        dialog.setWindowTitle("ECHO - Captured Intents")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"💡 I captured {len(pending_intents)} unspoken thought(s) while you were coding:")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        
        # Intent list
        intent_list = QListWidget()
        for intent in pending_intents:
            task = intent.get('task') or intent.get('text', '')[:100]
            intent_list.addItem(f"[{intent['type'].upper()}] {task}")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_tasks_btn = QPushButton("✅ Create Tasks on Canvas")
        create_tasks_btn.clicked.connect(lambda: IntentReviewDialog._create_all_tasks(intent_caster, pending_intents, dialog))
        
        ignore_btn = QPushButton("❌ Ignore")
        ignore_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(create_tasks_btn)
        button_layout.addWidget(ignore_btn)
        
        layout.addWidget(title)
        layout.addWidget(intent_list)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        return dialog.exec()
    
    @staticmethod
    def _create_all_tasks(intent_caster, intents, dialog):
        """Create tasks from all intents"""
        from PyQt6.QtWidgets import QMessageBox
        
        for intent in intents:
            intent_caster.create_task_from_intent(intent['id'])
        
        QMessageBox.information(dialog, "Success", f"Created {len(intents)} task(s) on your Living Canvas!")
        dialog.accept()

if __name__ == "__main__":
    # Test the intent caster
    caster = PassiveIntentCaster("user_001")
    caster.start()
    
    try:
        print("Speak naturally while coding. Say things like:")
        print("  'I should refactor this later'")
        print("  'This is getting complicated'")
        print("  'Need to add error handling'")
        print()
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        caster.stop()
        
        # Show captured intents
        intents = caster.get_pending_intents()
        print(f"\n💡 Captured {len(intents)} intents:")
        for intent in intents:
            print(f"  - [{intent['type']}] {intent.get('task', intent['text'][:50])}")