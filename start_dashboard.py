#!/usr/bin/env python3
"""
Ezan Player Dashboard Launcher
Easily start the web dashboard
"""

import sys
import subprocess
import webbrowser
import time
import threading
import os

def start_dashboard():
    """Start the web dashboard server."""
    print("🌐 Starting Ezan Player Web Dashboard...")
    print("=" * 50)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # Start the dashboard server
        process = subprocess.Popen([
            sys.executable, 'web_dashboard.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Try to open the browser
        dashboard_url = "http://localhost:8080"
        print(f"🚀 Opening dashboard at: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        print(f"✅ Dashboard is running!")
        print(f"📱 Access from any device: {dashboard_url}")
        print(f"🛑 Press Ctrl+C to stop the dashboard")
        print("=" * 50)
        
        # Wait for the process to complete (or be interrupted)
        try:
            process.wait()
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping dashboard...")
            process.terminate()
            process.wait()
            print(f"✅ Dashboard stopped!")
            
    except FileNotFoundError:
        print("❌ Error: web_dashboard.py not found!")
        print("Make sure you're in the correct directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_dashboard()




