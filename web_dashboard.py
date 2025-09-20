#!/usr/bin/env python3
"""
Ezan Player Web Dashboard
A beautiful web interface to control your Ezan Player
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import subprocess
import sys
import os
from datetime import datetime, timedelta
import threading
import time
import logging
from ezan_player import EzanPlayer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global ezan player instance
ezan_player = None
dashboard_config = {
    'mode': 'home',  # 'home' or 'office'
    'port': 8080,
    'auto_refresh': True
}

def load_dashboard_config():
    """Load dashboard configuration."""
    global dashboard_config
    try:
        with open('ezan_config.json', 'r') as f:
            config = json.load(f)
            dashboard_config.update(config.get('dashboard', {}))
    except:
        pass

def save_dashboard_config():
    """Save dashboard configuration."""
    try:
        with open('ezan_config.json', 'r') as f:
            config = json.load(f)
        
        config['dashboard'] = dashboard_config
        
        with open('ezan_config.json', 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save dashboard config: {e}")

def get_system_status():
    """Get current system status."""
    try:
        # Check if service is running
        result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
        service_running = 'com.ezanplayer' in result.stdout
        
        # Get process info
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        process_lines = [line for line in result.stdout.split('\n') if 'ezan_player.py' in line]
        
        process_info = None
        if process_lines:
            parts = process_lines[0].split()
            process_info = {
                'pid': parts[1],
                'cpu': parts[2],
                'memory': parts[3],
                'start_time': parts[8]
            }
        
        return {
            'service_running': service_running,
            'process_info': process_info,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {'error': str(e)}

def get_current_wifi():
    """Get current WiFi network name."""
    try:
        if sys.platform == "darwin":
            result = subprocess.run([
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', 
                '-I'
            ], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'SSID' in line and 'BSSID' not in line:
                    return line.split(':')[1].strip()
        return "Unknown"
    except:
        return "Unknown"

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get current status."""
    global ezan_player, dashboard_config
    
    if not ezan_player:
        ezan_player = EzanPlayer()
    
    # Get prayer times
    prayer_times = {}
    next_prayer = None
    if ezan_player.get_prayer_times():
        prayer_times = ezan_player.prayer_times
        
        # Find next prayer
        current_time = datetime.now().time()
        for prayer, time_str in prayer_times.items():
            prayer_time = datetime.strptime(time_str, '%H:%M').time()
            if prayer_time > current_time:
                next_prayer = {
                    'name': prayer.capitalize(),
                    'time': time_str,
                    'countdown': str(datetime.combine(datetime.now().date(), prayer_time) - datetime.now()).split('.')[0]
                }
                break
    
    return jsonify({
        'mode': dashboard_config['mode'],
        'volume': ezan_player.audio_settings.get('ezan_volume', 75),
        'prayer_times': prayer_times,
        'next_prayer': next_prayer,
        'system_status': get_system_status(),
        'wifi_network': get_current_wifi(),
        'current_time': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/toggle_mode', methods=['POST'])
def toggle_mode():
    """Toggle between home and office mode."""
    global dashboard_config
    
    data = request.get_json()
    new_mode = data.get('mode', 'home')
    old_mode = dashboard_config.get('mode', 'home')
    
    dashboard_config['mode'] = new_mode
    save_dashboard_config()
    
    # Enhanced logging for visibility
    mode_emoji = "🏠" if new_mode == 'home' else "🏢"
    status_msg = "Ezan ENABLED" if new_mode == 'home' else "Ezan DISABLED"
    
    logger.info(f"🎮 DASHBOARD: Mode switched from {old_mode.upper()} to {new_mode.upper()} {mode_emoji}")
    logger.info(f"🎮 DASHBOARD: {status_msg} - prayers will {'play normally' if new_mode == 'home' else 'be skipped'}")
    
    # Also write to ezan player log for visibility
    try:
        with open('ezan_player.log', 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
            f.write(f"{timestamp} - INFO - 🎮 DASHBOARD: Mode changed to {new_mode.upper()} {mode_emoji} ({status_msg})\n")
    except:
        pass
    
    return jsonify({'success': True, 'mode': new_mode})

@app.route('/api/set_volume', methods=['POST'])
def set_volume():
    """Set ezan volume."""
    global ezan_player
    
    if not ezan_player:
        ezan_player = EzanPlayer()
    
    data = request.get_json()
    volume = int(data.get('volume', 75))
    
    # Update config file
    try:
        with open('ezan_config.json', 'r') as f:
            config = json.load(f)
        
        config['audio_settings']['ezan_volume'] = volume
        
        with open('ezan_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        # Update in-memory settings
        ezan_player.audio_settings['ezan_volume'] = volume
        
        # Enhanced logging for visibility
        logger.info(f"🔊 DASHBOARD: Ezan volume changed to {volume}%")
        
        # Also write to ezan player log for visibility
        try:
            with open('ezan_player.log', 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                f.write(f"{timestamp} - INFO - 🔊 DASHBOARD: Ezan volume set to {volume}%\n")
        except:
            pass
        
        return jsonify({'success': True, 'volume': volume})
    
    except Exception as e:
        logger.error(f"Failed to set volume: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/play_test', methods=['POST'])
def play_test():
    """Play test ezan."""
    global ezan_player, dashboard_config
    
    # Don't play if in office mode
    if dashboard_config['mode'] == 'office':
        return jsonify({'success': False, 'message': 'Office mode active - ezan disabled'})
    
    if not ezan_player:
        ezan_player = EzanPlayer()
    
    data = request.get_json()
    prayer = data.get('prayer', 'fajr')
    
    try:
        ezan_player.play_ezan_video(prayer)
        
        # Enhanced logging for visibility  
        logger.info(f"🎵 DASHBOARD: Manual test - {prayer.upper()} ezan played")
        
        # Also write to ezan player log for visibility
        try:
            with open('ezan_player.log', 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                f.write(f"{timestamp} - INFO - 🎵 DASHBOARD: Manual test - {prayer.upper()} ezan played\n")
        except:
            pass
            
        return jsonify({'success': True, 'message': f'{prayer.capitalize()} ezan played'})
    except Exception as e:
        logger.error(f"Failed to play test ezan: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/restart_service', methods=['POST'])
def restart_service():
    """Restart the ezan service."""
    try:
        subprocess.run(['launchctl', 'unload', os.path.expanduser('~/Library/LaunchAgents/com.ezanplayer.plist')], 
                      check=False)
        time.sleep(1)
        subprocess.run(['launchctl', 'load', os.path.expanduser('~/Library/LaunchAgents/com.ezanplayer.plist')], 
                      check=True)
        
        logger.info("Service restarted successfully")
        return jsonify({'success': True, 'message': 'Service restarted'})
    except Exception as e:
        logger.error(f"Failed to restart service: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logs')
def get_logs():
    """Get recent logs."""
    try:
        logs = []
        log_files = ['ezan_player.log', os.path.expanduser('~/Library/Logs/ezanplayer.log')]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    logs.extend(lines[-20:])  # Get last 20 lines
                break
        
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'logs': [f'Error reading logs: {e}']})

if __name__ == '__main__':
    load_dashboard_config()
    
    # Override ezan playback based on mode
    original_play_ezan_video = None
    
    def mode_aware_play_ezan_video(self, prayer_name):
        """Play ezan only if in home mode."""
        global dashboard_config
        
        if dashboard_config['mode'] == 'office':
            logger.info(f"Office mode active - skipping {prayer_name} ezan")
            return
        
        # Call original method
        return original_play_ezan_video(self, prayer_name)
    
    # Monkey patch the EzanPlayer class
    if 'ezan_player' in sys.modules:
        original_play_ezan_video = sys.modules['ezan_player'].EzanPlayer.play_ezan_video
        sys.modules['ezan_player'].EzanPlayer.play_ezan_video = mode_aware_play_ezan_video
    
    port = dashboard_config.get('port', 8080)
    print(f"🌐 Ezan Player Dashboard starting on http://localhost:{port}")
    print(f"🎯 Open your browser to control your ezan player!")
    
    app.run(host='0.0.0.0', port=port, debug=False)
