# ECHO Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Setup Firebase (Optional for demo)
```bash
python config/firebase_setup.py
```

### 4. Run ECHO
```bash
# Full system
python main.py --user-id your_id --openai-key your_key

# Demo mode
python demo_script.py
```

## Core Components

### 🧠 Cognitive Sensor
- Tracks typing, gaze, audio, mouse
- Calculates flow states: FLOWING, STUCK, FRUSTRATED, IDLE
- Real-time Firebase sync

### 🎨 ECHO Orb
- State-aware UI that adapts to cognitive state
- Team collaboration satellites
- Proactive command interface

### 🗂️ Memory Engine
- ChromaDB for semantic memory
- Firebase for explicit preferences
- Context-aware LLM prompts

### ✨ Contextual Synthesizer
- Watches application context
- Finds hidden connections
- Proactive suggestions

## API Endpoints

- `POST /ask_echo` - Context-aware queries
- `POST /memorize` - Store preferences
- `POST /synthesize` - Proactive analysis
- `WebSocket /ws/{user_id}` - Real-time updates

## Demo Script

Run the winning demo:
```bash
python demo_script.py
```

This showcases all features in a 15-minute presentation format perfect for hackathons.

## Architecture

```
ECHO System
├── Cognitive Sensor (Background)
├── ECHO Orb (UI)
├── Memory Engine (Context)
├── Synthesizer (Proactive)
└── API Server (Integration)
```

**You now have a complete, hackathon-winning AI system.**