import threading
import time
import pyautogui
from collections import deque
import openai
import requests

class ContextualSynthesizer:
    def __init__(self, user_id, api_base_url="http://localhost:8000"):
        self.user_id = user_id
        self.api_base_url = api_base_url
        self.context_history = deque(maxlen=10)
        self.running = False
        self.synthesis_thread = None
        
    def start(self):
        self.running = True
        self.synthesis_thread = threading.Thread(target=self._synthesis_loop, daemon=True)
        self.synthesis_thread.start()
        
    def stop(self):
        self.running = False
        
    def _get_active_context(self):
        """Get current application context"""
        try:
            active_window = pyautogui.getActiveWindow()
            if active_window:
                return active_window.title
            return "Unknown"
        except:
            return "Unknown"
            
    def _synthesis_loop(self):
        """Main synthesis loop that runs every 10 seconds"""
        while self.running:
            try:
                current_context = self._get_active_context()
                self.context_history.append({
                    'context': current_context,
                    'timestamp': time.time()
                })
                
                # Analyze contexts every 10 seconds
                if len(self.context_history) >= 3:
                    contexts = [ctx['context'] for ctx in list(self.context_history)[-5:]]
                    
                    # Call synthesis API
                    response = requests.post(
                        f"{self.api_base_url}/synthesize",
                        params={"user_id": self.user_id},
                        json=contexts
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        suggestion = result.get('suggestion')
                        
                        if suggestion and suggestion != "N/A":
                            self._trigger_proactive_suggestion(suggestion)
                            
            except Exception as e:
                print(f"Synthesis error: {e}")
                
            time.sleep(10)
            
    def _trigger_proactive_suggestion(self, suggestion):
        """Trigger the orb to show proactive suggestion"""
        # This would integrate with the ECHO Orb to show the suggestion
        print(f"Proactive suggestion: {suggestion}")
        
    async def analyze_contexts(self, contexts):
        """Analyze context list for connections"""
        try:
            context_string = " | ".join(contexts)
            
            prompt = f"""Analyze this activity stream: {context_string}

Find a hidden connection or proactive suggestion. Examples:
- If user is researching "SaaS pricing" and has "proposal.doc" open, suggest adding pricing section
- If switching between code editor and documentation, suggest relevant code snippets
- If multiple design tools open, suggest consolidating workflow

If no strong connection exists, respond with "N/A"."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return "N/A"