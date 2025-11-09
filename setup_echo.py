#!/usr/bin/env python3
"""
ECHO Setup Script
Automated setup for the complete ECHO system
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class EchoSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        
    def run_setup(self):
        """Run complete ECHO setup"""
        print("🌟 ECHO - Ambient Cognitive Partner Setup")
        print("=" * 50)
        
        try:
            self.check_python()
            self.create_virtual_environment()
            self.install_dependencies()
            self.setup_environment_files()
            self.setup_firebase_schema()
            self.create_desktop_shortcuts()
            
            print("\n✅ ECHO setup complete!")
            print("\n🚀 To start ECHO:")
            print("   Windows: run_echo.bat")
            print("   Manual:  python main.py")
            print("\n🧪 To test interruption service:")
            print("   python test_interruption.py")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)
    
    def check_python(self):
        """Check Python version"""
        print("🐍 Checking Python version...")
        
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8+ required")
        
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    def create_virtual_environment(self):
        """Create virtual environment"""
        print("📦 Creating virtual environment...")
        
        if self.venv_path.exists():
            print("   ✅ Virtual environment already exists")
            return
        
        subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
        print("   ✅ Virtual environment created")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("📚 Installing dependencies...")
        
        # Get pip path
        if os.name == 'nt':  # Windows
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            pip_path = self.venv_path / "bin" / "pip"
        
        # Install requirements
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("   ✅ Dependencies installed")
    
    def setup_environment_files(self):
        """Setup environment configuration"""
        print("⚙️ Setting up environment files...")
        
        # Check if .env exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            print("   ✅ .env file already exists")
        else:
            print("   ⚠️ Please update .env with your API keys")
        
        # Check Firebase credentials
        firebase_file = self.project_root / "firebase-credentials.json"
        if firebase_file.exists():
            print("   ✅ Firebase credentials found")
        else:
            print("   ⚠️ Please add your Firebase credentials to firebase-credentials.json")
            self.create_firebase_template()
    
    def create_firebase_template(self):
        """Create Firebase credentials template"""
        template = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        with open("firebase-credentials-template.json", "w") as f:
            json.dump(template, f, indent=2)
        
        print("   📝 Created firebase-credentials-template.json")
    
    def setup_firebase_schema(self):
        """Setup Firebase schema"""
        print("🔥 Setting up Firebase schema...")
        
        try:
            # Import and run schema setup
            from firebase_schema import FirebaseSchemaSetup
            
            setup = FirebaseSchemaSetup()
            setup.setup_schema()
            
            print("   ✅ Firebase schema created")
            
        except Exception as e:
            print(f"   ⚠️ Firebase setup skipped: {e}")
            print("   Please run 'python firebase_schema.py' after configuring Firebase")
    
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts"""
        print("🖥️ Creating shortcuts...")
        
        if os.name == 'nt':  # Windows
            self.create_windows_shortcuts()
        else:
            print("   ⚠️ Desktop shortcuts only supported on Windows")
    
    def create_windows_shortcuts(self):
        """Create Windows desktop shortcuts"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            
            # ECHO shortcut
            shortcut_path = os.path.join(desktop, "ECHO.lnk")
            target = str(self.project_root / "run_echo.bat")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = str(self.project_root)
            shortcut.IconLocation = target
            shortcut.save()
            
            print("   ✅ Desktop shortcut created")
            
        except ImportError:
            print("   ⚠️ Desktop shortcut creation requires: pip install winshell pywin32")
        except Exception as e:
            print(f"   ⚠️ Shortcut creation failed: {e}")

def main():
    """Main setup function"""
    setup = EchoSetup()
    setup.run_setup()

if __name__ == "__main__":
    main()