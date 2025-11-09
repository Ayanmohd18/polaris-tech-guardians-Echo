import chromadb
from chromadb.config import Settings
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openai
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import json
from config import Config

class MemoryEngine:
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=Config.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collections
        self.conversations_collection = self.chroma_client.get_or_create_collection(
            name="conversations",
            metadata={"description": "User conversation history"}
        )
        
        self.preferences_collection = self.chroma_client.get_or_create_collection(
            name="preferences", 
            metadata={"description": "User preferences and memories"}
        )
        
        # Initialize Firebase
        self._init_firebase()
        
        # Initialize OpenAI
        openai.api_key = Config.OPENAI_API_KEY
    
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def store_conversation(self, user_id: str, query: str, response: str, context: Dict[str, Any] = None):
        """Store a conversation in vector database for semantic retrieval"""
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create conversation document
        conversation_text = f"User: {query}\nECHO: {response}"
        
        # Store in ChromaDB
        self.conversations_collection.add(
            documents=[conversation_text],
            metadatas=[{
                "user_id": user_id,
                "timestamp": timestamp,
                "query": query,
                "response": response,
                "context": json.dumps(context or {})
            }],
            ids=[conversation_id]
        )
        
        return conversation_id
    
    def store_preference(self, user_id: str, preference_text: str, category: str = "general"):
        """Store user preference with @ECHO command"""
        preference_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Store in ChromaDB for semantic search
        self.preferences_collection.add(
            documents=[preference_text],
            metadatas=[{
                "user_id": user_id,
                "timestamp": timestamp,
                "category": category
            }],
            ids=[preference_id]
        )
        
        # Store in Firebase for explicit retrieval
        if self.db:
            try:
                self.db.collection('user_preferences').document(user_id).collection('preferences').add({
                    'text': preference_text,
                    'category': category,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'preference_id': preference_id
                })
            except Exception as e:
                print(f"Firebase preference storage failed: {e}")
        
        return preference_id
    
    def get_relevant_conversations(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve semantically similar conversations"""
        try:
            results = self.conversations_collection.query(
                query_texts=[query],
                n_results=limit,
                where={"user_id": user_id}
            )
            
            conversations = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    conversations.append({
                        'text': doc,
                        'query': metadata.get('query', ''),
                        'response': metadata.get('response', ''),
                        'timestamp': metadata.get('timestamp', ''),
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return conversations
        except Exception as e:
            print(f"Conversation retrieval failed: {e}")
            return []
    
    def get_relevant_preferences(self, user_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve semantically similar preferences"""
        try:
            results = self.preferences_collection.query(
                query_texts=[query],
                n_results=limit,
                where={"user_id": user_id}
            )
            
            preferences = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    preferences.append({
                        'text': doc,
                        'category': metadata.get('category', 'general'),
                        'timestamp': metadata.get('timestamp', ''),
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return preferences
        except Exception as e:
            print(f"Preference retrieval failed: {e}")
            return []
    
    def get_explicit_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all explicit preferences from Firebase"""
        if not self.db:
            return []
        
        try:
            preferences_ref = self.db.collection('user_preferences').document(user_id).collection('preferences')
            docs = preferences_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
            
            preferences = []
            for doc in docs:
                data = doc.to_dict()
                preferences.append({
                    'text': data.get('text', ''),
                    'category': data.get('category', 'general'),
                    'timestamp': data.get('timestamp', ''),
                    'id': doc.id
                })
            
            return preferences
        except Exception as e:
            print(f"Explicit preference retrieval failed: {e}")
            return []
    
    def build_context_prompt(self, user_id: str, query: str) -> str:
        """Build enhanced prompt with user context"""
        
        # Get relevant conversations
        conversations = self.get_relevant_conversations(user_id, query, limit=3)
        
        # Get relevant preferences
        preferences = self.get_relevant_preferences(user_id, query, limit=3)
        
        # Get explicit preferences
        explicit_prefs = self.get_explicit_preferences(user_id)
        
        # Build context sections
        context_parts = []
        
        if explicit_prefs:
            context_parts.append("## User Preferences:")
            for pref in explicit_prefs[:5]:
                context_parts.append(f"- {pref['text']}")
        
        if preferences:
            context_parts.append("\n## Relevant User Context:")
            for pref in preferences:
                if pref['distance'] < 0.7:  # Only include close matches
                    context_parts.append(f"- {pref['text']}")
        
        if conversations:
            context_parts.append("\n## Recent Relevant Conversations:")
            for conv in conversations:
                if conv['distance'] < 0.6:  # Only include close matches
                    context_parts.append(f"User asked: {conv['query']}")
                    context_parts.append(f"ECHO responded: {conv['response'][:200]}...")
        
        # Build final prompt
        base_prompt = f"""You are ECHO, an Ambient Cognitive Partner. You provide contextual, proactive assistance based on the user's cognitive state and preferences.

Current user query: {query}

{chr(10).join(context_parts) if context_parts else "No specific user context available."}

Respond naturally and helpfully, incorporating the user's preferences and past context where relevant. Be concise but thorough."""
        
        return base_prompt

# FastAPI Backend
app = FastAPI(title="ECHO Memory Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory engine instance
memory_engine = MemoryEngine()

@app.post("/ask_echo")
async def ask_echo(request: Dict[str, Any]):
    """Main endpoint for ECHO queries with memory integration"""
    try:
        user_id = request.get("user_id")
        query = request.get("query")
        
        if not user_id or not query:
            raise HTTPException(status_code=400, detail="user_id and query are required")
        
        # Build context-aware prompt
        enhanced_prompt = memory_engine.build_context_prompt(user_id, query)
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Store conversation for future context
        conversation_id = memory_engine.store_conversation(
            user_id=user_id,
            query=query,
            response=ai_response,
            context=request.get("context", {})
        )
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memorize")
async def memorize(request: Dict[str, Any]):
    """Endpoint for @ECHO memory commands"""
    try:
        user_id = request.get("user_id")
        text = request.get("text")
        category = request.get("category", "general")
        
        if not user_id or not text:
            raise HTTPException(status_code=400, detail="user_id and text are required")
        
        # Store preference
        preference_id = memory_engine.store_preference(user_id, text, category)
        
        return {
            "message": f"Remembered: {text}",
            "preference_id": preference_id,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user_context/{user_id}")
async def get_user_context(user_id: str):
    """Get user's stored preferences and recent conversations"""
    try:
        explicit_prefs = memory_engine.get_explicit_preferences(user_id)
        
        return {
            "user_id": user_id,
            "preferences": explicit_prefs,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)