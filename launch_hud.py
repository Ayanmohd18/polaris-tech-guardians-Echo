"""Simplified launcher for Bio-Cognitive HUD"""
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

def serve_ui():
    os.chdir('ui/build')
    server = HTTPServer(('localhost', 3000), SimpleHTTPRequestHandler)
    print("🌟 ECHO Bio-Cognitive HUD running at http://localhost:3000")
    print("Press Ctrl+C to stop")
    server.serve_forever()

if __name__ == "__main__":
    thread = threading.Thread(target=serve_ui, daemon=True)
    thread.start()
    webbrowser.open('http://localhost:3000')
    try:
        thread.join()
    except KeyboardInterrupt:
        print("\n✨ ECHO shutting down...")
