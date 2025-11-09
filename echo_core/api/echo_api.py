from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from echo_core.memory.memory_engine import MemoryEngine
from echo_core.sensors.contextual_synthesizer import ContextualSynthesizer
import asyncio
import json

app = FastAPI(title="ECHO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
memory_engines = {}
synthesizers = {}

class QueryRequest(BaseModel):
    user_id: str
    query: str
    openai_key: str

class MemorizeRequest(BaseModel):
    user_id: str
    text: str
    openai_key: str

@app.post("/ask_echo")
async def ask_echo(request: QueryRequest):
    """Main ECHO query endpoint with context awareness"""
    try:
        # Get or create memory engine
        if request.user_id not in memory_engines:
            memory_engines[request.user_id] = MemoryEngine(request.user_id, request.openai_key)
        
        memory = memory_engines[request.user_id]
        
        # Build enhanced prompt with context
        enhanced_prompt = memory.build_enhanced_prompt(request.query)
        
        # Query OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": enhanced_prompt}],
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Store conversation for future context
        memory.store_conversation(request.query, ai_response)
        
        return {"response": ai_response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memorize")
async def memorize(request: MemorizeRequest):
    """Store explicit user preferences"""
    try:
        if request.user_id not in memory_engines:
            memory_engines[request.user_id] = MemoryEngine(request.user_id, request.openai_key)
        
        memory = memory_engines[request.user_id]
        memory.memorize_explicit(request.text)
        
        return {"status": "memorized"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthesize")
async def synthesize(user_id: str, contexts: list):
    """Proactive synthesis endpoint"""
    try:
        if user_id not in synthesizers:
            synthesizers[user_id] = ContextualSynthesizer(user_id)
        
        synthesizer = synthesizers[user_id]
        suggestion = await synthesizer.analyze_contexts(contexts)
        
        return {"suggestion": suggestion}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time state updates"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back for now - extend for real-time features
            await websocket.send_text(json.dumps({
                "type": "state_update",
                "user_id": user_id,
                "data": message
            }))
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)