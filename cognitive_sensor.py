import threading
import time
import cv2
import numpy as np
import sounddevice as sd
from pynput import keyboard, mouse
from collections import deque
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import pyautogui

class CognitiveSensor:
    def __init__(self, user_id: str, team_id: str = Config.DEFAULT_TEAM_ID):
        self.user_id = user_id
        self.team_id = team_id
        self.current_state = "IDLE"
        self.running = False
        
        # Activity tracking
        self.typing_events = deque(maxlen=20)
        self.backspace_count = 0
        self.mouse_events = deque(maxlen=10)
        self.last_activity_time = time.time()
        self.audio_levels = deque(maxlen=10)
        
        # Initialize Firebase
        self._init_firebase()
        
        # Initialize face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.cap = None
        
        # Listeners
        self.keyboard_listener = None
        self.mouse_listener = None
        
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
        
        # Start input listeners
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Start camera
        try:
            self.cap = cv2.VideoCapture(0)
        except:
            print("Camera not available")
        
        # Start main sensor thread
        sensor_thread = threading.Thread(target=self._sensor_loop, daemon=True)
        sensor_thread.start()
        
    def stop(self):
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.cap:
            self.cap.release()
    
    def _on_key_press(self, key):
        current_time = time.time()
        self.typing_events.append(current_time)
        self.last_activity_time = current_time
        
        if key == keyboard.Key.backspace:
            self.backspace_count += 1
    
    def _on_key_release(self, key):
        pass
    
    def _on_mouse_move(self, x, y):
        current_time = time.time()
        self.mouse_events.append((x, y, current_time))
        self.last_activity_time = current_time
    
    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.last_activity_time = time.time()
    
    def _track_activity(self):
        current_time = time.time()
        
        # Calculate typing cadence (events per minute)
        recent_typing = [t for t in self.typing_events if current_time - t < 60]
        typing_cadence = len(recent_typing)
        
        # Calculate backspace frequency
        backspace_frequency = self.backspace_count / max(1, len(recent_typing))
        self.backspace_count = 0  # Reset counter
        
        # Calculate mouse activity
        recent_mouse = [event for event in self.mouse_events if current_time - event[2] < 30]
        mouse_activity = len(recent_mouse)
        
        # Time since last activity
        idle_time = current_time - self.last_activity_time
        
        return {
            'typing_cadence': typing_cadence,
            'backspace_frequency': backspace_frequency,
            'mouse_activity': mouse_activity,
            'idle_time': idle_time
        }
    
    def _track_gaze(self):
        if not self.cap or not self.cap.isOpened():
            return {'focused': False, 'confidence': 0}
        
        ret, frame = self.cap.read()
        if not ret:
            return {'focused': False, 'confidence': 0}
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            # Simple heuristic: if face is detected and centered, user is focused
            face = faces[0]
            frame_center_x = frame.shape[1] // 2
            face_center_x = face[0] + face[2] // 2
            
            # Calculate how centered the face is
            center_offset = abs(face_center_x - frame_center_x) / frame_center_x
            focused = center_offset < 0.3  # Within 30% of center
            
            return {'focused': focused, 'confidence': 1 - center_offset}
        
        return {'focused': False, 'confidence': 0}
    
    def _track_audio(self):
        try:
            # Record a short audio sample
            duration = 0.1  # 100ms
            sample_rate = 44100
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, blocking=True)
            
            # Calculate RMS volume
            rms = np.sqrt(np.mean(audio_data**2))
            self.audio_levels.append(rms)
            
            # Detect sudden spikes (potential frustration sounds)
            if len(self.audio_levels) > 5:
                avg_level = np.mean(list(self.audio_levels)[:-1])
                spike_detected = rms > avg_level * 3  # 3x average
                return {'rms': rms, 'spike_detected': spike_detected}
            
            return {'rms': rms, 'spike_detected': False}
        except:
            return {'rms': 0, 'spike_detected': False}
    
    def _get_active_app(self):
        try:
            active_window = pyautogui.getActiveWindow()
            return active_window.title if active_window else "Unknown"
        except:
            return "Unknown"
    
    def _calculate_cognitive_state(self):
        activity = self._track_activity()
        gaze = self._track_gaze()
        audio = self._track_audio()
        active_app = self._get_active_app()
        
        # State determination logic
        if activity['idle_time'] > Config.ACTIVITY_THRESHOLD:
            if gaze['focused'] and any(keyword in active_app.lower() for keyword in ['code', 'visual studio', 'pycharm', 'sublime', 'atom', 'notepad']):
                return "STUCK"
            else:
                return "IDLE"
        
        # Check for frustration indicators
        if (activity['backspace_frequency'] > 0.3 or 
            audio['spike_detected'] or 
            not gaze['focused']):
            return "FRUSTRATED"
        
        # Check for flow state
        if (activity['typing_cadence'] > 10 and 
            activity['backspace_frequency'] < 0.1 and 
            gaze['focused'] and 
            activity['mouse_activity'] > 2):
            return "FLOWING"
        
        # Default to stuck if there's some activity but not flowing
        if activity['typing_cadence'] > 0 or activity['mouse_activity'] > 0:
            return "STUCK"
        
        return "IDLE"
    
    def _update_firebase(self, state: str):
        if not self.db:
            return
        
        try:
            doc_ref = self.db.collection('team_states').document(self.team_id).collection('user_states').document(self.user_id)
            doc_ref.set({
                'state': state,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'user_id': self.user_id
            })
        except Exception as e:
            print(f"Firebase update failed: {e}")
    
    def _sensor_loop(self):
        while self.running:
            try:
                new_state = self._calculate_cognitive_state()
                
                if new_state != self.current_state:
                    self.current_state = new_state
                    self._update_firebase(new_state)
                    print(f"State changed to: {new_state}")
                
                time.sleep(Config.SENSOR_UPDATE_INTERVAL)
            except Exception as e:
                print(f"Sensor loop error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    sensor = CognitiveSensor("user_001")
    sensor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sensor.stop()
        print("Sensor stopped")