"""
ECHO Quick Start Script
Automated setup and launch
"""

import os
import sys
import subprocess

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def check_firebase_credentials():
    """Check if Firebase credentials exist"""
    if not os.path.exists("firebase-credentials.json"):
        print("\n⚠️  Firebase credentials not found!")
        print("\n📝 To get your credentials:")
        print("1. Go to: https://console.firebase.google.com/project/vibeathon-7b277/settings/serviceaccounts/adminsdk")
        print("2. Click 'Generate new private key'")
        print("3. Save the file as 'firebase-credentials.json' in this directory")
        print("\nPress Enter after you've added the file...")
        input()
        
        if not os.path.exists("firebase-credentials.json"):
            print("❌ Still not found. Please add the file and run again.")
            return False
    
    print("✅ Firebase credentials found")
    return True

def setup_database():
    """Setup Firebase database"""
    print("\n🔥 Setting up Firebase database...")
    
    try:
        result = subprocess.run([sys.executable, "setup_firebase_database.py"], 
                              capture_output=True, text=True)
        
        if "✅ Firestore schema setup complete!" in result.stdout:
            print("✅ Database setup complete")
            return True
        else:
            print("⚠️  Database setup had issues")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_openai_key():
    """Check if OpenAI API key is configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key or api_key == "your_openai_api_key_here":
        print("\n⚠️  OpenAI API key not configured!")
        print("\n📝 To add your API key:")
        print("1. Get your key from: https://platform.openai.com/api-keys")
        print("2. Open .env file")
        print("3. Replace 'your_openai_api_key_here' with your actual key")
        print("\nPress Enter after you've added the key...")
        input()
        
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "")
        
        if not api_key or api_key == "your_openai_api_key_here":
            print("⚠️  Key still not configured. Some features will be limited.")
            return False
    
    print("✅ OpenAI API key configured")
    return True

def launch_echo():
    """Launch ECHO application"""
    print("\n🚀 Launching ECHO: The Omniscient Creative Environment...")
    print("=" * 60)
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n\n👋 ECHO stopped")
    except Exception as e:
        print(f"\n❌ Launch failed: {e}")

def main():
    """Main quick start function"""
    print("🌟 ECHO Quick Start")
    print("=" * 60)
    
    # Step 1: Check Python
    if not check_python_version():
        return
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependencies")
        return
    
    # Step 3: Check Firebase credentials
    if not check_firebase_credentials():
        print("\n❌ Setup failed at Firebase credentials")
        return
    
    # Step 4: Setup database
    if not setup_database():
        print("\n⚠️  Database setup incomplete, but continuing...")
    
    # Step 5: Check OpenAI key
    check_openai_key()
    
    # Step 6: Launch
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    
    launch_echo()

if __name__ == "__main__":
    main()