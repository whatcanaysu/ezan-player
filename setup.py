#!/usr/bin/env python3
"""
Setup script for Ezan Player
This script helps set up the application and create necessary system services.
"""

import os
import sys
import subprocess
import json
import platform

def install_requirements():
    """Install required Python packages."""
    print("Installing required packages...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements. Please install them manually:")
        print("pip install -r requirements.txt")
        return False

def setup_macos_launch_agent():
    """Create macOS Launch Agent for automatic startup."""
    launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
    plist_path = os.path.join(launch_agents_dir, "com.ezanplayer.plist")
    
    # Create Launch Agents directory if it doesn't exist
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    # Get absolute path to the Python script
    script_path = os.path.abspath("ezan_player.py")
    python_path = sys.executable
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ezanplayer</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{os.path.expanduser('~/Library/Logs/ezanplayer.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser('~/Library/Logs/ezanplayer_error.log')}</string>
    <key>WorkingDirectory</key>
    <string>{os.path.dirname(script_path)}</string>
</dict>
</plist>"""
    
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    print(f"✅ Launch Agent created at: {plist_path}")
    print("To start the service, run:")
    print(f"launchctl load {plist_path}")
    print("To stop the service, run:")
    print(f"launchctl unload {plist_path}")
    
    return plist_path

def setup_linux_systemd():
    """Create systemd service for Linux."""
    service_content = f"""[Unit]
Description=Ezan Player - Automated Prayer Time YouTube Player
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.abspath('ezan_player.py')}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
    
    service_path = f"/etc/systemd/system/ezanplayer.service"
    local_service_path = "ezanplayer.service"
    
    # Write to local file first
    with open(local_service_path, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Service file created: {local_service_path}")
    print("To install the service, run as root:")
    print(f"sudo cp {local_service_path} {service_path}")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl enable ezanplayer")
    print("sudo systemctl start ezanplayer")
    
    return local_service_path

def check_youtube_urls():
    """Check if YouTube URLs are configured."""
    try:
        with open('ezan_config.json', 'r') as f:
            config = json.load(f)
            videos = config.get('youtube_videos', {})
            
            has_placeholders = any('YOUR_' in url for url in videos.values())
            
            if has_placeholders:
                print("⚠️  Please update the YouTube video URLs in ezan_config.json")
                print("Replace the placeholder URLs with your actual ezan video links:")
                for prayer, url in videos.items():
                    if 'YOUR_' in url:
                        print(f"  {prayer}: {url}")
                return False
            else:
                print("✅ YouTube URLs are configured!")
                return True
                
    except FileNotFoundError:
        print("❌ Configuration file not found. It will be created when you run the application.")
        return False

def main():
    """Main setup function."""
    print("🕌 Ezan Player Setup")
    print("==================")
    
    # Install requirements
    if not install_requirements():
        return
    
    # Check configuration
    check_youtube_urls()
    
    # Create service based on OS
    system = platform.system().lower()
    
    if system == "darwin":
        setup_macos_launch_agent()
        print("\n📋 macOS Setup Complete!")
        print("To test the application manually, run:")
        print("python3 ezan_player.py")
        
    elif system == "linux":
        setup_linux_systemd()
        print("\n📋 Linux Setup Complete!")
        print("To test the application manually, run:")
        print("python3 ezan_player.py")
        
    else:
        print(f"⚠️  Automatic service setup not available for {system}")
        print("You can still run the application manually:")
        print("python ezan_player.py")
    
    print("\n📚 Next Steps:")
    print("1. Update YouTube URLs in ezan_config.json")
    print("2. Test the application manually first")
    print("3. Set up the system service if desired")
    print("4. Check the logs: ezan_player.log")

if __name__ == "__main__":
    main()
