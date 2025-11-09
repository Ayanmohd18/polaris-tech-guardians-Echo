import threading
import time
import pyautogui
from collections import deque
import openai
import requests
from typing import List, Dict, Any, Optional
from config import Config
import json

class ContextualSynthesizer:
    def __init__(self, user_id: str, api_base_url: str = "http://localhost:8000"):
        self.user_id = user_id
        self.api_base_url = api_base_url
        self.running = False
        
        # Activity tracking
        self.activity_stream = deque(maxlen=10)
        self.last_synthesis_time = 0
        self.synthesis_cooldown = 30  # seconds between synthesis attempts
        
        # OpenAI setup
        openai.api_key = Config.OPENAI_API_KEY
        
        # Synthesis thread
        self.synthesis_thread = None
    
    def start(self):
        """Start the contextual synthesizer"""
        self.running = True
        self.synthesis_thread = threading.Thread(target=self._synthesis_loop, daemon=True)
        self.synthesis_thread.start()
        print("Contextual Synthesizer started")
    
    def stop(self):
        """Stop the contextual synthesizer"""
        self.running = False
        print("Contextual Synthesizer stopped")
    
    def _get_active_window_info(self) -> Dict[str, str]:
        """Get information about the currently active window"""
        try:
            active_window = pyautogui.getActiveWindow()
            if active_window:
                title = active_window.title
                
                # Extract application name and context
                app_name = "Unknown"
                context = title
                
                # Parse common application patterns
                if "Chrome" in title or "Firefox" in title or "Edge" in title:
                    app_name = "Browser"
                    # Extract page title from browser window
                    if " - " in title:
                        context = title.split(" - ")[0]
                elif "Visual Studio Code" in title or "VSCode" in title:
                    app_name = "Code Editor"
                    if " - " in title:
                        context = title.split(" - ")[0]
                elif "Word" in title or "Excel" in title or "PowerPoint" in title:
                    app_name = "Office"
                    context = title
                elif "Slack" in title:
                    app_name = "Communication"
                    context = "Slack"
                elif "Zoom" in title or "Teams" in title:
                    app_name = "Video Call"
                    context = title
                else:
                    # Try to extract app name from window title
                    parts = title.split(" - ")
                    if len(parts) > 1:
                        app_name = parts[-1]
                        context = " - ".join(parts[:-1])
                
                return {
                    "app_name": app_name,
                    "context": context,
                    "full_title": title,
                    "timestamp": time.time()
                }
        except Exception as e:
            print(f"Error getting active window: {e}")
        
        return {
            "app_name": "Unknown",
            "context": "Unknown",
            "full_title": "Unknown",
            "timestamp": time.time()
        }
    
    def _update_activity_stream(self):
        """Update the activity stream with current window info"""
        window_info = self._get_active_window_info()
        
        # Only add if it's different from the last entry
        if not self.activity_stream or self.activity_stream[-1]["full_title"] != window_info["full_title"]:
            self.activity_stream.append(window_info)
    
    def _analyze_activity_patterns(self) -> Dict[str, Any]:
        """Analyze the activity stream for patterns"""
        if len(self.activity_stream) < 3:
            return {"pattern": "insufficient_data"}
        
        # Convert to list for easier analysis
        activities = list(self.activity_stream)
        
        # Analyze patterns
        app_sequence = [activity["app_name"] for activity in activities]
        context_sequence = [activity["context"] for activity in activities]
        
        # Detect common patterns
        patterns = {
            "research_to_writing": self._detect_research_writing_pattern(app_sequence, context_sequence),
            "code_to_documentation": self._detect_code_docs_pattern(app_sequence, context_sequence),
            "meeting_to_action": self._detect_meeting_action_pattern(app_sequence, context_sequence),
            "learning_to_application": self._detect_learning_application_pattern(app_sequence, context_sequence)
        }
        
        # Find the strongest pattern
        active_patterns = [k for k, v in patterns.items() if v["detected"]]
        
        return {
            "pattern": active_patterns[0] if active_patterns else "no_pattern",
            "details": patterns,
            "activity_summary": self._summarize_activities(activities)
        }
    
    def _detect_research_writing_pattern(self, apps: List[str], contexts: List[str]) -> Dict[str, Any]:
        """Detect research -> writing workflow"""
        browser_count = apps.count("Browser")
        office_count = apps.count("Office")
        
        # Look for browser followed by office apps
        transitions = []
        for i in range(len(apps) - 1):
            if apps[i] == "Browser" and apps[i + 1] == "Office":
                transitions.append((contexts[i], contexts[i + 1]))
        
        return {
            "detected": len(transitions) > 0 and browser_count >= 2,
            "confidence": min(0.9, len(transitions) * 0.3 + browser_count * 0.1),
            "transitions": transitions
        }
    
    def _detect_code_docs_pattern(self, apps: List[str], contexts: List[str]) -> Dict[str, Any]:
        """Detect coding -> documentation workflow"""
        code_count = apps.count("Code Editor")
        browser_count = apps.count("Browser")
        
        # Look for code editor followed by browser (documentation lookup)
        doc_lookups = []
        for i in range(len(apps) - 1):
            if apps[i] == "Code Editor" and apps[i + 1] == "Browser":
                if any(term in contexts[i + 1].lower() for term in ["docs", "documentation", "api", "tutorial", "stackoverflow"]):
                    doc_lookups.append((contexts[i], contexts[i + 1]))
        
        return {
            "detected": len(doc_lookups) > 0,
            "confidence": min(0.8, len(doc_lookups) * 0.4),
            "lookups": doc_lookups
        }
    
    def _detect_meeting_action_pattern(self, apps: List[str], contexts: List[str]) -> Dict[str, Any]:
        """Detect meeting -> action items workflow"""
        meeting_count = apps.count("Video Call")
        
        # Look for meeting followed by productivity apps
        action_transitions = []
        for i in range(len(apps) - 1):
            if apps[i] == "Video Call" and apps[i + 1] in ["Office", "Code Editor", "Communication"]:
                action_transitions.append((contexts[i], contexts[i + 1]))
        
        return {
            "detected": len(action_transitions) > 0,
            "confidence": min(0.7, len(action_transitions) * 0.5),
            "transitions": action_transitions
        }
    
    def _detect_learning_application_pattern(self, apps: List[str], contexts: List[str]) -> Dict[str, Any]:
        """Detect learning -> application workflow"""
        browser_contexts = [ctx for i, ctx in enumerate(contexts) if apps[i] == "Browser"]
        
        # Look for educational content followed by practical application
        learning_indicators = ["tutorial", "course", "learn", "how to", "guide", "documentation"]
        learning_sessions = []
        
        for i, ctx in enumerate(browser_contexts):
            if any(indicator in ctx.lower() for indicator in learning_indicators):
                learning_sessions.append(ctx)
        
        return {
            "detected": len(learning_sessions) > 0 and len(apps) > len(learning_sessions),
            "confidence": min(0.6, len(learning_sessions) * 0.3),
            "learning_content": learning_sessions
        }
    
    def _summarize_activities(self, activities: List[Dict[str, Any]]) -> str:
        """Create a human-readable summary of recent activities"""
        if not activities:
            return "No recent activity"
        
        summary_parts = []
        for activity in activities[-5:]:  # Last 5 activities
            app = activity["app_name"]
            context = activity["context"][:50] + "..." if len(activity["context"]) > 50 else activity["context"]
            summary_parts.append(f"{app}: {context}")
        
        return " → ".join(summary_parts)
    
    def _generate_synthesis(self, pattern_analysis: Dict[str, Any]) -> Optional[str]:
        """Generate proactive synthesis using LLM"""
        try:
            pattern = pattern_analysis["pattern"]
            activity_summary = pattern_analysis["activity_summary"]
            
            if pattern == "no_pattern" or pattern == "insufficient_data":
                return None
            
            # Create synthesis prompt
            synthesis_prompt = f"""You are ECHO, a proactive AI assistant. Analyze this user activity pattern and provide a helpful, actionable suggestion.

Activity Pattern: {pattern}
Recent Activity: {activity_summary}
Pattern Details: {json.dumps(pattern_analysis['details'], indent=2)}

Provide a concise, actionable suggestion (max 100 words) that would help the user based on this pattern. If no strong suggestion emerges, respond with "N/A".

Examples of good suggestions:
- "I noticed you're researching pricing models and working on a proposal. Would you like me to help draft a pricing section?"
- "You've been looking up API documentation while coding. Should I summarize the key endpoints for your current project?"
- "After your meeting, you switched to coding. Want me to help organize any action items from the discussion?"

Your suggestion:"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": synthesis_prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            suggestion = response.choices[0].message.content.strip()
            
            # Filter out non-actionable responses
            if suggestion.lower() in ["n/a", "no suggestion", "none"] or len(suggestion) < 20:
                return None
            
            return suggestion
            
        except Exception as e:
            print(f"Synthesis generation error: {e}")
            return None
    
    def _send_synthesis_to_orb(self, synthesis: str):
        """Send synthesis suggestion to the ECHO Orb"""
        try:
            # This would typically send to the orb via WebSocket or API
            # For now, we'll print and could integrate with the orb's notification system
            print(f"🔮 PROACTIVE SYNTHESIS: {synthesis}")
            
            # TODO: Integrate with orb notification system
            # Could send via WebSocket, file system, or direct API call
            
        except Exception as e:
            print(f"Error sending synthesis to orb: {e}")
    
    def _synthesis_loop(self):
        """Main synthesis loop"""
        while self.running:
            try:
                # Update activity stream
                self._update_activity_stream()
                
                # Check if enough time has passed since last synthesis
                current_time = time.time()
                if current_time - self.last_synthesis_time < self.synthesis_cooldown:
                    time.sleep(5)
                    continue
                
                # Analyze patterns
                pattern_analysis = self._analyze_activity_patterns()
                
                # Generate synthesis if pattern detected
                if pattern_analysis["pattern"] not in ["no_pattern", "insufficient_data"]:
                    synthesis = self._generate_synthesis(pattern_analysis)
                    
                    if synthesis:
                        self._send_synthesis_to_orb(synthesis)
                        self.last_synthesis_time = current_time
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Synthesis loop error: {e}")
                time.sleep(5)

# Synthesis API endpoint (to be added to the main FastAPI app)
def add_synthesis_endpoints(app):
    """Add synthesis endpoints to the FastAPI app"""
    
    @app.post("/synthesize")
    async def synthesize_context(request: Dict[str, Any]):
        """Endpoint for manual synthesis requests"""
        try:
            user_id = request.get("user_id")
            context_list = request.get("context_list", [])
            
            if not user_id or not context_list:
                raise HTTPException(status_code=400, detail="user_id and context_list are required")
            
            # Create a temporary synthesizer for this request
            synthesizer = ContextualSynthesizer(user_id)
            
            # Simulate activity stream from provided context
            for i, context in enumerate(context_list):
                synthesizer.activity_stream.append({
                    "app_name": context.get("app_name", "Unknown"),
                    "context": context.get("context", ""),
                    "full_title": context.get("full_title", ""),
                    "timestamp": time.time() - (len(context_list) - i) * 60
                })
            
            # Analyze and generate synthesis
            pattern_analysis = synthesizer._analyze_activity_patterns()
            synthesis = synthesizer._generate_synthesis(pattern_analysis)
            
            return {
                "synthesis": synthesis or "N/A",
                "pattern": pattern_analysis["pattern"],
                "confidence": pattern_analysis.get("details", {}).get(pattern_analysis["pattern"], {}).get("confidence", 0),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Test the synthesizer
    synthesizer = ContextualSynthesizer("user_001")
    synthesizer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        synthesizer.stop()
        print("Synthesizer stopped")