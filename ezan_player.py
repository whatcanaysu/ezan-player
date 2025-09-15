#!/usr/bin/env python3
"""
Automated Ezan Player
Plays different YouTube ezan videos at prayer times according to Diyanet Başkanlığı for Barcelona, Spain.
"""

import requests
import schedule
import time
import webbrowser
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import subprocess
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ezan_player.log'),
        logging.StreamHandler()
    ]
)

class EzanPlayer:
    def __init__(self):
        self.config_file = 'ezan_config.json'
        self.prayer_times = {}
        self.youtube_videos = {}
        self.load_config()
        
    def load_config(self):
        """Load YouTube video URLs from configuration file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.youtube_videos = config.get('youtube_videos', {})
                logging.info("Configuration loaded successfully")
        except FileNotFoundError:
            logging.warning("Configuration file not found. Creating default config...")
            self.create_default_config()
            
    def create_default_config(self):
        """Create default configuration file with placeholder YouTube URLs."""
        default_config = {
            "youtube_videos": {
                "fajr": "https://youtube.com/watch?v=YOUR_FAJR_VIDEO_ID",
                "dhuhr": "https://youtube.com/watch?v=YOUR_DHUHR_VIDEO_ID", 
                "asr": "https://youtube.com/watch?v=YOUR_ASR_VIDEO_ID",
                "maghrib": "https://youtube.com/watch?v=YOUR_MAGHRIB_VIDEO_ID",
                "isha": "https://youtube.com/watch?v=YOUR_ISHA_VIDEO_ID"
            },
            "location": {
                "city": "Barcelona",
                "country": "Spain",
                "diyanet_city_id": "9541"  # Barcelona's Diyanet city ID
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Created default config file: {self.config_file}")
        logging.info("Please update the YouTube video URLs in the config file!")
        
    def wake_system(self):
        """Wake up the system from sleep mode."""
        try:
            # On macOS, we can use caffeinate to prevent sleep and wake the system
            if sys.platform == "darwin":
                # This command will wake the system and keep it awake briefly
                subprocess.run(['caffeinate', '-u', '-t', '10'], check=True)
                logging.info("System wake command executed (macOS)")
            elif sys.platform == "linux":
                # On Linux, you might need different approaches depending on your setup
                subprocess.run(['xset', 'dpms', 'force', 'on'], check=True)
                logging.info("System wake command executed (Linux)")
            elif sys.platform == "win32":
                # On Windows, we can use powercfg
                subprocess.run(['powercfg', '/WAKE'], check=True, shell=True)
                logging.info("System wake command executed (Windows)")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to wake system: {e}")
        except Exception as e:
            logging.error(f"Error waking system: {e}")

    def get_prayer_times(self):
        """Fetch prayer times from Aladhan API for Barcelona."""
        try:
            # Aladhan API endpoint for prayer times (more reliable than Diyanet)
            url = "https://api.aladhan.com/v1/timingsByCity"
            
            # Parameters for Barcelona, Spain
            params = {
                'city': 'Barcelona',
                'country': 'Spain',
                'method': '13',  # Method 13 is close to Diyanet calculations
                'date': datetime.now().strftime('%d-%m-%Y')
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and data.get('code') == 200:
                timings = data['data']['timings']
                self.prayer_times = {
                    'fajr': timings.get('Fajr', ''),
                    'dhuhr': timings.get('Dhuhr', ''), 
                    'asr': timings.get('Asr', ''),
                    'maghrib': timings.get('Maghrib', ''),
                    'isha': timings.get('Isha', '')
                }
                logging.info(f"Prayer times fetched: {self.prayer_times}")
                return True
            else:
                logging.error("No prayer times data received from API")
                return False
                
        except requests.RequestException as e:
            logging.error(f"Network error fetching prayer times: {e}")
            return False
        except Exception as e:
            logging.error(f"Error fetching prayer times: {e}")
            return False

    def play_ezan_video(self, prayer_name: str):
        """Play the appropriate ezan video for the given prayer."""
        try:
            # Wake up the system first
            self.wake_system()
            
            # Small delay to ensure system is awake
            time.sleep(2)
            
            video_url = self.youtube_videos.get(prayer_name.lower())
            if not video_url or 'YOUR_' in video_url:
                logging.error(f"No valid YouTube URL configured for {prayer_name}")
                return
            
            logging.info(f"Playing {prayer_name} ezan video: {video_url}")
            
            # Open YouTube video in default browser
            webbrowser.open(video_url)
            
            # Optional: You can also use subprocess to open in a specific browser
            # subprocess.run(['open', '-a', 'Safari', video_url])  # macOS with Safari
            # subprocess.run(['google-chrome', video_url])  # Linux with Chrome
            
        except Exception as e:
            logging.error(f"Error playing ezan video for {prayer_name}: {e}")

    def schedule_prayers(self):
        """Schedule ezan videos for today's prayer times."""
        if not self.prayer_times:
            logging.error("No prayer times available for scheduling")
            return
            
        # Clear existing scheduled jobs
        schedule.clear()
        
        for prayer_name, prayer_time in self.prayer_times.items():
            if prayer_time and prayer_time != '':
                try:
                    # Convert prayer time to datetime
                    today = datetime.now().date()
                    prayer_datetime = datetime.strptime(f"{today} {prayer_time}", "%Y-%m-%d %H:%M")
                    
                    # Only schedule if the prayer time hasn't passed today
                    if prayer_datetime > datetime.now():
                        schedule.every().day.at(prayer_time).do(self.play_ezan_video, prayer_name)
                        logging.info(f"Scheduled {prayer_name} ezan at {prayer_time}")
                    else:
                        logging.info(f"Skipped {prayer_name} at {prayer_time} (already passed today)")
                        
                except ValueError as e:
                    logging.error(f"Error parsing time for {prayer_name}: {prayer_time} - {e}")

    def run_daily_update(self):
        """Daily task to fetch new prayer times and reschedule."""
        logging.info("Running daily prayer times update...")
        if self.get_prayer_times():
            self.schedule_prayers()
        else:
            logging.error("Failed to update prayer times, keeping existing schedule")

    def run(self):
        """Main application loop."""
        logging.info("Starting Ezan Player...")
        
        # Initial setup
        if not self.get_prayer_times():
            logging.error("Failed to fetch initial prayer times. Exiting...")
            return
            
        self.schedule_prayers()
        
        # Schedule daily updates at midnight
        schedule.every().day.at("00:01").do(self.run_daily_update)
        
        logging.info("Ezan Player is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logging.info("Ezan Player stopped by user")
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")

def main():
    """Entry point of the application."""
    player = EzanPlayer()
    player.run()

if __name__ == "__main__":
    main()
