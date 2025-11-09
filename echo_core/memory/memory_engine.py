import chromadb
import openai
from firebase_admin import firestore
from datetime import datetime
import json

class MemoryEngine:
    def __init__(self, user_id, openai_api_key):
        self.user_id = user_id
        openai.api_key = openai_api_key
        
        # Vector DB for implicit context
        self.chroma_client = chromadb.PersistentClient(path=f"./memory/{user_id}")
        self.context_collection = self.chroma_client.get_or_create_collection("conversations")
        
        # Firebase for explicit preferences
        self.db = firestore.client()
        
    def memorize_explicit(self, text):
        """Store explicit user preference/instruction"""
        # Store in Firebase
        doc_ref = self.db.collection('user_preferences').document(self.user_id)
        doc_ref.update({
            'preferences': firestore.ArrayUnion([{
                'text': text,
                'timestamp': datetime.now()
            }])
        })
        
        # Also embed in vector DB for semantic search
        self.context_collection.add(
            documents=[text],
            metadatas=[{"type": "explicit", "timestamp": str(datetime.now())}],
            ids=[f"explicit_{datetime.now().timestamp()}"]
        )
        
    def get_context(self, query, limit=5):
        """Retrieve relevant context for a query"""
        # Get semantic context from vector DB
        results = self.context_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        implicit_context = results['documents'][0] if results['documents'] else []
        
        # Get explicit preferences from Firebase
        doc_ref = self.db.collection('user_preferences').document(self.user_id)
        doc = doc_ref.get()
        explicit_prefs = doc.to_dict().get('preferences', []) if doc.exists else []
        
        return {
            'implicit_context': implicit_context,
            'explicit_preferences': [p['text'] for p in explicit_prefs[-3:]]  # Last 3
        }
        
    def store_conversation(self, user_message, ai_response):
        """Store conversation for future context"""
        conversation = f"User: {user_message}\nECHO: {ai_response}"
        
        self.context_collection.add(
            documents=[conversation],
            metadatas=[{"type": "conversation", "timestamp": str(datetime.now())}],
            ids=[f"conv_{datetime.now().timestamp()}"]
        )
        
    def build_enhanced_prompt(self, user_query, base_prompt="You are ECHO, an ambient cognitive partner."):
        """Build context-aware prompt for LLM"""
        context = self.get_context(user_query)
        
        enhanced_prompt = f"""{base_prompt}

EXPLICIT USER PREFERENCES:
{chr(10).join(context['explicit_preferences'])}

RELEVANT CONTEXT:
{chr(10).join(context['implicit_context'])}

USER QUERY: {user_query}

Respond as ECHO, considering the user's preferences and conversation history."""
        
        return enhanced_prompt