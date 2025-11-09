"""
ECHO: The Sentient Workspace
Feature 13: The Bio-Cognitive Harmonizer - The Ultimate Sensor
Integrates biometric data for holistic cognitive state awareness
"""

import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import requests
import json

class BioCognitiveHarmonizer:
    """Integrates biometric data with cognitive state for holistic awareness"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.running = False
        
        # Biometric data
        self.current_hrv = None
        self.current_heart_rate = None
        self.sleep_quality = None
        self.stress_level = 0
        
        # Cognitive state
        self.cognitive_state = "IDLE"
        
        # Thresholds
        self.stress_threshold = 70  # Heart rate threshold
        self.low_hrv_threshold = 30  # Low HRV indicates stress
        self.poor_sleep_threshold = 5.0  # Hours
        
        # Initialize Firebase
        self._init_firebase()
        
        # Wearable integrations
        self.apple_health_token = None
        self.oura_token = None
    
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
        """Start bio-cognitive monitoring"""
        self.running = True
        
        # Start biometric monitoring thread
        bio_thread = threading.Thread(target=self._biometric_loop, daemon=True)
        bio_thread.start()
        
        # Start harmonization thread
        harmony_thread = threading.Thread(target=self._harmonization_loop, daemon=True)
        harmony_thread.start()
        
        print("💓 Bio-Cognitive Harmonizer started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        print("💓 Bio-Cognitive Harmonizer stopped")
    
    def configure_apple_health(self, token: str):
        """Configure Apple HealthKit integration"""
        self.apple_health_token = token
        print("✅ Apple Health configured")
    
    def configure_oura_ring(self, token: str):
        """Configure Oura Ring integration"""
        self.oura_token = token
        print("✅ Oura Ring configured")
    
    def _biometric_loop(self):
        """Continuously fetch biometric data"""
        while self.running:
            try:
                # Fetch from Apple Health
                if self.apple_health_token:
                    self._fetch_apple_health_data()
                
                # Fetch from Oura Ring
                if self.oura_token:
                    self._fetch_oura_data()
                
                # Calculate stress level
                self._calculate_stress_level()
                
                # Store in Firebase
                self._store_biometric_data()
                
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                print(f"Biometric loop error: {e}")
                time.sleep(10)
    
    def _fetch_apple_health_data(self):
        """Fetch data from Apple HealthKit"""
        try:
            # Simulated Apple Health API call
            # In production, use HealthKit API via iOS app
            
            # Simulate HRV data
            self.current_hrv = np.random.randint(20, 80)
            
            # Simulate heart rate
            self.current_heart_rate = np.random.randint(60, 100)
            
            # Simulate sleep data
            self.sleep_quality = np.random.uniform(4.0, 8.0)
            
        except Exception as e:
            print(f"Apple Health fetch error: {e}")
    
    def _fetch_oura_data(self):
        """Fetch data from Oura Ring API"""
        try:
            # Real Oura API integration
            headers = {'Authorization': f'Bearer {self.oura_token}'}
            
            # Get sleep data
            today = datetime.now().strftime('%Y-%m-%d')
            sleep_url = f'https://api.ouraring.com/v2/usercollection/sleep?start_date={today}&end_date={today}'
            
            response = requests.get(sleep_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    sleep_data = data['data'][0]
                    self.sleep_quality = sleep_data.get('total_sleep_duration', 0) / 3600  # Convert to hours
            
            # Get readiness data (includes HRV)
            readiness_url = f'https://api.ouraring.com/v2/usercollection/daily_readiness?start_date={today}&end_date={today}'
            
            response = requests.get(readiness_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    readiness_data = data['data'][0]
                    # Oura provides readiness score, we can infer HRV from it
                    readiness_score = readiness_data.get('score', 50)
                    self.current_hrv = readiness_score  # Simplified mapping
            
        except Exception as e:
            print(f"Oura fetch error: {e}")
    
    def _calculate_stress_level(self):
        """Calculate overall stress level from biometrics"""
        stress_factors = []
        
        # Heart rate factor
        if self.current_heart_rate:
            if self.current_heart_rate > self.stress_threshold:
                stress_factors.append(0.4)  # High stress
            elif self.current_heart_rate > 70:
                stress_factors.append(0.2)  # Moderate stress
            else:
                stress_factors.append(0.0)  # Low stress
        
        # HRV factor (lower HRV = higher stress)
        if self.current_hrv:
            if self.current_hrv < self.low_hrv_threshold:
                stress_factors.append(0.4)
            elif self.current_hrv < 50:
                stress_factors.append(0.2)
            else:
                stress_factors.append(0.0)
        
        # Sleep factor
        if self.sleep_quality:
            if self.sleep_quality < self.poor_sleep_threshold:
                stress_factors.append(0.3)
            elif self.sleep_quality < 6.5:
                stress_factors.append(0.15)
            else:
                stress_factors.append(0.0)
        
        # Calculate overall stress (0-100)
        if stress_factors:
            self.stress_level = int(sum(stress_factors) / len(stress_factors) * 100)
        else:
            self.stress_level = 0
    
    def _store_biometric_data(self):
        """Store biometric data in Firebase"""
        if not self.db:
            return
        
        try:
            self.db.collection('biometric_data').add({
                'user_id': self.user_id,
                'hrv': self.current_hrv,
                'heart_rate': self.current_heart_rate,
                'sleep_quality': self.sleep_quality,
                'stress_level': self.stress_level,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print(f"Biometric storage error: {e}")
    
    def _harmonization_loop(self):
        """Main harmonization logic"""
        while self.running:
            try:
                # Get current cognitive state
                self._fetch_cognitive_state()
                
                # Analyze holistic state
                recommendation = self._analyze_holistic_state()
                
                if recommendation:
                    self._execute_recommendation(recommendation)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Harmonization loop error: {e}")
                time.sleep(10)
    
    def _fetch_cognitive_state(self):
        """Fetch current cognitive state from sensor"""
        if not self.db:
            return
        
        try:
            doc = self.db.collection('team_states')\
                .document(Config.DEFAULT_TEAM_ID)\
                .collection('user_states')\
                .document(self.user_id)\
                .get()
            
            if doc.exists:
                data = doc.to_dict()
                self.cognitive_state = data.get('state', 'IDLE')
        except:
            pass
    
    def _analyze_holistic_state(self) -> Optional[Dict[str, Any]]:
        """Analyze combined bio-cognitive state"""
        
        # Morning check: Low sleep quality
        if self.sleep_quality and self.sleep_quality < self.poor_sleep_threshold:
            return {
                'type': 'low_energy_day',
                'message': f"You only got {self.sleep_quality:.1f} hours of sleep. "
                          "Your cognitive resources are limited today.",
                'recommendation': 'postpone_complex_tasks',
                'alternative_tasks': ['refactoring', 'documentation', 'bug_fixes']
            }
        
        # Real-time stress detection
        if self.stress_level > 70:
            if self.cognitive_state == "FRUSTRATED":
                return {
                    'type': 'high_stress_intervention',
                    'message': "Your physiological stress is high. Let's regulate.",
                    'recommendation': 'breathing_exercise',
                    'duration': 60  # seconds
                }
        
        # Moderate stress with low HRV
        if self.stress_level > 50 and self.current_hrv and self.current_hrv < 40:
            return {
                'type': 'stress_warning',
                'message': "Your HRV is low. Consider taking a short break.",
                'recommendation': 'suggest_break',
                'duration': 300  # 5 minutes
            }
        
        return None
    
    def _execute_recommendation(self, recommendation: Dict[str, Any]):
        """Execute harmonization recommendation"""
        
        rec_type = recommendation['type']
        
        if rec_type == 'low_energy_day':
            self._show_low_energy_dialog(recommendation)
        
        elif rec_type == 'high_stress_intervention':
            self._trigger_breathing_exercise(recommendation)
        
        elif rec_type == 'stress_warning':
            self._suggest_break(recommendation)
    
    def _show_low_energy_dialog(self, recommendation: Dict[str, Any]):
        """Show morning energy assessment dialog"""
        if not self.db:
            return
        
        try:
            # Store recommendation for UI to display
            self.db.collection('harmonizer_events').add({
                'user_id': self.user_id,
                'type': 'low_energy_day',
                'message': recommendation['message'],
                'alternative_tasks': recommendation['alternative_tasks'],
                'timestamp': firestore.SERVER_TIMESTAMP,
                'status': 'pending'
            })
            
            print(f"💤 {recommendation['message']}")
            print(f"   Recommended: {', '.join(recommendation['alternative_tasks'])}")
            
        except Exception as e:
            print(f"Low energy dialog error: {e}")
    
    def _trigger_breathing_exercise(self, recommendation: Dict[str, Any]):
        """Trigger breathing exercise overlay"""
        if not self.db:
            return
        
        try:
            # Store event for UI to display breathing overlay
            self.db.collection('harmonizer_events').add({
                'user_id': self.user_id,
                'type': 'breathing_exercise',
                'message': recommendation['message'],
                'duration': recommendation['duration'],
                'timestamp': firestore.SERVER_TIMESTAMP,
                'status': 'pending'
            })
            
            print(f"🧘 {recommendation['message']}")
            print(f"   Starting {recommendation['duration']}s breathing exercise...")
            
        except Exception as e:
            print(f"Breathing exercise error: {e}")
    
    def _suggest_break(self, recommendation: Dict[str, Any]):
        """Suggest taking a break"""
        if not self.db:
            return
        
        try:
            self.db.collection('harmonizer_events').add({
                'user_id': self.user_id,
                'type': 'break_suggestion',
                'message': recommendation['message'],
                'duration': recommendation['duration'],
                'timestamp': firestore.SERVER_TIMESTAMP,
                'status': 'pending'
            })
            
            print(f"☕ {recommendation['message']}")
            
        except Exception as e:
            print(f"Break suggestion error: {e}")
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily biometric summary"""
        return {
            'user_id': self.user_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'sleep_quality': self.sleep_quality,
            'average_hrv': self.current_hrv,
            'average_heart_rate': self.current_heart_rate,
            'stress_level': self.stress_level,
            'cognitive_state': self.cognitive_state,
            'recommendation': self._get_daily_recommendation()
        }
    
    def _get_daily_recommendation(self) -> str:
        """Get daily recommendation based on biometrics"""
        if self.sleep_quality and self.sleep_quality < 5:
            return "Prioritize rest today. Focus on low-cognitive-load tasks."
        elif self.stress_level > 60:
            return "Stress levels elevated. Take regular breaks and practice breathing exercises."
        elif self.current_hrv and self.current_hrv > 60:
            return "Great recovery! You're in optimal condition for complex problem-solving."
        else:
            return "Balanced state. Maintain your current rhythm."

class BreathingExerciseOverlay:
    """Breathing exercise overlay for stress regulation"""
    
    @staticmethod
    def show_breathing_exercise(duration: int = 60):
        """Show breathing exercise overlay"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtCore import QTimer, Qt
        from PyQt6.QtGui import QFont
        
        dialog = QDialog()
        dialog.setWindowTitle("ECHO - Breathe")
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        dialog.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        dialog.showFullScreen()
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Instruction label
        instruction = QLabel("Breathe with me")
        instruction.setStyleSheet("color: white; font-size: 48px; font-weight: bold;")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Phase label
        phase_label = QLabel("Inhale")
        phase_label.setStyleSheet("color: #4A90E2; font-size: 72px; font-weight: bold;")
        phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Counter label
        counter_label = QLabel("4")
        counter_label.setStyleSheet("color: white; font-size: 120px; font-weight: bold;")
        counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(instruction)
        layout.addWidget(phase_label)
        layout.addWidget(counter_label)
        
        dialog.setLayout(layout)
        
        # Breathing cycle: Inhale 4s, Hold 4s, Exhale 4s, Hold 4s
        cycle = [
            ('Inhale', '#4A90E2', 4),
            ('Hold', '#00AA00', 4),
            ('Exhale', '#FF6B35', 4),
            ('Hold', '#00AA00', 4)
        ]
        
        current_phase = [0]
        current_count = [4]
        cycles_completed = [0]
        total_cycles = duration // 16  # 16 seconds per cycle
        
        def update_breathing():
            if cycles_completed[0] >= total_cycles:
                dialog.accept()
                return
            
            current_count[0] -= 1
            
            if current_count[0] <= 0:
                current_phase[0] = (current_phase[0] + 1) % 4
                if current_phase[0] == 0:
                    cycles_completed[0] += 1
                
                phase_name, color, duration = cycle[current_phase[0]]
                phase_label.setText(phase_name)
                phase_label.setStyleSheet(f"color: {color}; font-size: 72px; font-weight: bold;")
                current_count[0] = duration
            
            counter_label.setText(str(current_count[0]))
        
        timer = QTimer()
        timer.timeout.connect(update_breathing)
        timer.start(1000)  # Update every second
        
        dialog.exec()

if __name__ == "__main__":
    # Test bio-cognitive harmonizer
    harmonizer = BioCognitiveHarmonizer("user_001")
    
    # Simulate Oura Ring token (get from https://cloud.ouraring.com/personal-access-tokens)
    # harmonizer.configure_oura_ring("YOUR_OURA_TOKEN")
    
    harmonizer.start()
    
    try:
        print("💓 Monitoring biometric data...")
        print("   Press Ctrl+C to stop")
        
        while True:
            time.sleep(5)
            summary = harmonizer.get_daily_summary()
            print(f"\n📊 Current State:")
            print(f"   Sleep: {summary['sleep_quality']:.1f}h")
            print(f"   HRV: {summary['average_hrv']}")
            print(f"   HR: {summary['average_heart_rate']} bpm")
            print(f"   Stress: {summary['stress_level']}%")
            print(f"   Cognitive: {summary['cognitive_state']}")
            print(f"   💡 {summary['recommendation']}")
            
    except KeyboardInterrupt:
        harmonizer.stop()