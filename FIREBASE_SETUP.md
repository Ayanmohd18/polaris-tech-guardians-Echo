# Firebase Setup Guide for ECHO

## 🔥 Your Firebase Project

**Project ID:** `vibeathon-7b277`  
**Database URL:** `https://vibeathon-7b277-default-rtdb.firebaseio.com`  
**Console:** https://console.firebase.google.com/project/vibeathon-7b277

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Service Account Key

1. Go to Firebase Console:
   ```
   https://console.firebase.google.com/project/vibeathon-7b277/settings/serviceaccounts/adminsdk
   ```

2. Click **"Generate new private key"**

3. Save the downloaded JSON file as `firebase-credentials.json` in the project root

### Step 2: Initialize Database

```bash
python setup_firebase_database.py
```

This will create all necessary collections:
- ✅ users
- ✅ team_states
- ✅ captured_intents (Feature 10: Passive Intent-Casting)
- ✅ user_personas (Feature 11: Digital Ghost)
- ✅ ab_tests (Feature 12: Market Validation)
- ✅ biometric_data (Feature 13: Bio-Harmonizer)
- ✅ project_sonars (Feature 14: Project Sonar)
- ✅ tasks (Canvas → IDE communication)
- ✅ flow_watchers (Team Flow)
- ✅ notifications
- ✅ user_secrets (Data Bridge)
- ✅ harmonizer_events
- ✅ orb_events
- ✅ sonar_notifications

### Step 3: Verify Setup

```bash
python -c "from firebase_config import FirebaseConfig; FirebaseConfig.initialize()"
```

You should see:
```
✅ Firebase initialized: vibeathon-7b277
```

---

## 📊 Database Structure

### Firestore Collections

```
vibeathon-7b277 (Firestore)
│
├── users/
│   └── {user_id}
│       ├── user_id: string
│       ├── display_name: string
│       ├── email: string
│       ├── team_id: string
│       └── created_at: timestamp
│
├── team_states/
│   └── {team_id}/
│       └── user_states/
│           └── {user_id}
│               ├── state: "FLOWING" | "STUCK" | "FRUSTRATED" | "IDLE"
│               └── timestamp: timestamp
│
├── captured_intents/
│   └── {intent_id}
│       ├── user_id: string
│       ├── type: string
│       ├── text: string
│       ├── task: string
│       ├── status: "pending" | "converted_to_task"
│       └── timestamp: timestamp
│
├── user_personas/
│   └── {user_id}
│       ├── code_style: object
│       ├── writing_style: object
│       └── updated_at: timestamp
│
├── ab_tests/
│   └── {test_id}
│       ├── user_id: string
│       ├── variants: array
│       ├── results: object
│       ├── status: "running" | "completed"
│       └── timestamp: timestamp
│
├── biometric_data/
│   └── {data_id}
│       ├── user_id: string
│       ├── hrv: number
│       ├── heart_rate: number
│       ├── sleep_quality: number
│       ├── stress_level: number
│       └── timestamp: timestamp
│
├── project_sonars/
│   └── {sonar_id}
│       ├── user_id: string
│       ├── problem: string
│       ├── status: "active" | "completed"
│       ├── solution: object
│       ├── simulations_run: number
│       └── timestamp: timestamp
│
├── tasks/
│   └── {task_id}
│       ├── description: string
│       ├── assigned_to: "ide" | "canvas"
│       ├── status: "pending" | "completed"
│       ├── created_by: string
│       └── timestamp: timestamp
│
└── flow_watchers/
    └── {recipient_id}/
        └── watchers/
            └── {watcher_id}
                ├── notify_at: "next_idle"
                └── timestamp: timestamp
```

### Realtime Database

```
vibeathon-7b277-default-rtdb (Realtime Database)
│
├── echo/
│   ├── initialized: true
│   └── version: "1.0.0"
│
└── cognitive_states/
    └── {user_id}
        ├── state: string
        └── timestamp: string
```

---

## 🔒 Security Rules

### Firestore Rules

Add these rules in Firebase Console → Firestore → Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Team states readable by team members
    match /team_states/{teamId}/user_states/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // User-specific collections
    match /captured_intents/{intentId} {
      allow read, write: if request.auth != null;
    }
    
    match /user_personas/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    match /biometric_data/{dataId} {
      allow read, write: if request.auth != null;
    }
    
    match /project_sonars/{sonarId} {
      allow read, write: if request.auth != null;
    }
    
    // Tasks readable by all team members
    match /tasks/{taskId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
    
    // User secrets - highly restricted
    match /user_secrets/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### Realtime Database Rules

Add these rules in Firebase Console → Realtime Database → Rules:

```json
{
  "rules": {
    "echo": {
      ".read": true,
      ".write": true
    },
    "cognitive_states": {
      "$userId": {
        ".read": true,
        ".write": true
      }
    }
  }
}
```

---

## 🧪 Testing the Setup

### Test 1: Firestore Connection

```python
from firebase_config import FirebaseConfig

db = FirebaseConfig.get_firestore()
users = db.collection('users').limit(1).stream()
print(f"✅ Found {sum(1 for _ in users)} user(s)")
```

### Test 2: Realtime Database

```python
from firebase_config import FirebaseConfig

rtdb = FirebaseConfig.get_realtime_db()
data = rtdb.child('echo').get()
print(f"✅ ECHO initialized: {data.get('initialized')}")
```

### Test 3: Write Test

```python
from firebase_config import FirebaseConfig
from datetime import datetime

db = FirebaseConfig.get_firestore()
db.collection('test').document('test_doc').set({
    'message': 'Hello from ECHO!',
    'timestamp': datetime.now()
})
print("✅ Write successful!")
```

---

## 🔧 Troubleshooting

### Error: "Firebase not initialized"

**Solution:** Download service account key from Firebase Console

```bash
# Go to:
https://console.firebase.google.com/project/vibeathon-7b277/settings/serviceaccounts/adminsdk

# Click "Generate new private key"
# Save as firebase-credentials.json
```

### Error: "Permission denied"

**Solution:** Update Firestore security rules (see above)

### Error: "Module not found"

**Solution:** Install dependencies

```bash
pip install firebase-admin python-dotenv
```

---

## 📚 Next Steps

1. ✅ Setup complete
2. Run ECHO: `python main.py`
3. Test features:
   - Deploy Project Sonar
   - Create tasks on Canvas
   - Test team flow protection

---

## 🌐 Firebase Console Links

- **Overview:** https://console.firebase.google.com/project/vibeathon-7b277
- **Firestore:** https://console.firebase.google.com/project/vibeathon-7b277/firestore
- **Realtime DB:** https://console.firebase.google.com/project/vibeathon-7b277/database
- **Authentication:** https://console.firebase.google.com/project/vibeathon-7b277/authentication
- **Settings:** https://console.firebase.google.com/project/vibeathon-7b277/settings/general

---

**Your Firebase project is ready for ECHO! 🚀**