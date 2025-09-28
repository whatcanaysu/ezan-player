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
from bs4 import BeautifulSoup
import re
import threading

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
        self.audio_settings = {}
        self.original_volume = None
        self.load_config()
        
    def load_config(self):
        """Load YouTube video URLs and audio settings from configuration file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.youtube_videos = config.get('youtube_videos', {})
                self.audio_settings = config.get('audio_settings', {
                    'ezan_volume': 75,
                    'restore_original_volume': True,
                    'volume_fade_duration': 2
                })
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
                "source": "diyanet_official",
                "diyanet_city_id": "14262",
                "url": "https://namazvakitleri.diyanet.gov.tr/tr-TR/14262/barcelona-icin-namaz-vakti"
            },
            "audio_settings": {
                "ezan_volume": 85,
                "prayer_volumes": {
                    "fajr": 45,
                    "dhuhr": 85,
                    "asr": 85,
                    "maghrib": 85,
                    "isha": 85
                },
                "restore_original_volume": True,
                "volume_fade_duration": 0
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

    def get_current_volume(self):
        """Get current system volume (macOS)."""
        try:
            if sys.platform == "darwin":
                result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], 
                                      capture_output=True, text=True, check=True)
                return int(result.stdout.strip())
            elif sys.platform == "linux":
                result = subprocess.run(['amixer', 'get', 'Master'], 
                                      capture_output=True, text=True, check=True)
                # Parse amixer output to get volume percentage
                import re
                match = re.search(r'\[(\d+)%\]', result.stdout)
                return int(match.group(1)) if match else 50
            elif sys.platform == "win32":
                # Windows volume control would need additional setup
                return 50  # Default fallback
        except (subprocess.CalledProcessError, ValueError) as e:
            logging.error(f"Failed to get current volume: {e}")
            return 50  # Default fallback
        
    def set_volume(self, volume_level):
        """Set system volume level (0-100)."""
        try:
            if sys.platform == "darwin":
                subprocess.run(['osascript', '-e', f'set volume output volume {volume_level}'], 
                             check=True)
                logging.info(f"Volume set to {volume_level}%")
                return True
            elif sys.platform == "linux":
                subprocess.run(['amixer', 'set', 'Master', f'{volume_level}%'], 
                             check=True)
                logging.info(f"Volume set to {volume_level}%")
                return True
            elif sys.platform == "win32":
                # Windows volume control would need additional libraries
                logging.warning("Volume control not implemented for Windows")
                return False
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set volume to {volume_level}%: {e}")
            return False
        
    def restore_volume(self):
        """Restore original volume level."""
        if self.original_volume is not None:
            self.set_volume(self.original_volume)
            logging.info(f"Volume restored to original level: {self.original_volume}%")
            self.original_volume = None
    
    def is_office_mode(self):
        """Check if office mode is enabled via dashboard config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                dashboard_config = config.get('dashboard', {})
                return dashboard_config.get('mode', 'home') == 'office'
        except Exception as e:
            logging.error(f"Error checking office mode: {e}")
            return False  # Default to home mode if error

    def get_prayer_times(self):
        """Fetch prayer times from official Diyanet website for Barcelona."""
        try:
            # Official Diyanet prayer times website for Barcelona
            url = "https://namazvakitleri.diyanet.gov.tr/tr-TR/14262/barcelona-icin-namaz-vakti"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the prayer times table
            table = soup.find('table', class_='table')
            if not table:
                # Try alternative table selectors
                table = soup.find('table')
                
            if not table:
                logging.error("Could not find prayer times table on Diyanet website")
                return False
            
            # Get today's date in Turkish format
            today = datetime.now()
            
            # Turkish month names mapping
            turkish_months = {
                'January': 'Ocak', 'February': 'Şubat', 'March': 'Mart',
                'April': 'Nisan', 'May': 'Mayıs', 'June': 'Haziran',
                'July': 'Temmuz', 'August': 'Ağustos', 'September': 'Eylül',
                'October': 'Ekim', 'November': 'Kasım', 'December': 'Aralık'
            }
            
            english_month = today.strftime('%B')
            turkish_month = turkish_months.get(english_month, english_month)
            today_day = str(today.day)
            today_year = str(today.year)
            
            # Find today's row in the table
            today_row = None
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:  # Should have 8 columns as we discovered
                    date_cell = cells[0].get_text(strip=True)
                    # Check if this row contains today's date
                    if (today_day in date_cell and 
                        turkish_month in date_cell and 
                        today_year in date_cell):
                        today_row = row
                        break
            
            if not today_row:
                expected_date = f"{today_day} {turkish_month} {today_year}"
                logging.error(f"Could not find today's prayer times on Diyanet website for date: {expected_date}")
                return False
            
            # Extract prayer times from the row
            cells = today_row.find_all('td')
            if len(cells) < 8:
                logging.error("Invalid table structure - not enough columns")
                return False
            
            # Column order: Miladi Tarih, Hicri Tarih, İmsak, Güneş, Öğle, İkindi, Akşam, Yatsı
            try:
                self.prayer_times = {
                    'fajr': cells[2].get_text(strip=True),     # İmsak
                    'dhuhr': cells[4].get_text(strip=True),    # Öğle  
                    'asr': cells[5].get_text(strip=True),      # İkindi
                    'maghrib': cells[6].get_text(strip=True),  # Akşam
                    'isha': cells[7].get_text(strip=True)      # Yatsı
                }
                
                # Validate prayer times format (should be HH:MM)
                for prayer, time_str in self.prayer_times.items():
                    if not re.match(r'^\d{2}:\d{2}$', time_str):
                        logging.error(f"Invalid time format for {prayer}: {time_str}")
                        return False
                
                logging.info(f"Diyanet prayer times fetched: {self.prayer_times}")
                return True
                
            except (IndexError, AttributeError) as e:
                logging.error(f"Error parsing prayer times from table: {e}")
                return False
                
        except requests.RequestException as e:
            logging.error(f"Network error fetching Diyanet prayer times: {e}")
            return False
        except Exception as e:
            logging.error(f"Error fetching Diyanet prayer times: {e}")
            return False

    def play_ezan_video(self, prayer_name: str):
        """Play the appropriate ezan video for the given prayer with volume control."""
        try:
            # Check if office mode is enabled
            if self.is_office_mode():
                logging.info(f"🏢 OFFICE MODE: Skipping {prayer_name.upper()} ezan - prayers disabled")
                logging.info(f"🏢 OFFICE MODE: To enable prayers, switch to Home Mode in dashboard")
                return
            
            # Wake up the system first
            self.wake_system()
            
            # Small delay to ensure system is awake
            time.sleep(2)
            
            video_url = self.youtube_videos.get(prayer_name.lower())
            if not video_url or 'YOUR_' in video_url:
                logging.error(f"No valid YouTube URL configured for {prayer_name}")
                return
            
            # Volume control - Prayer-specific volumes for home mode
            prayer_volumes = self.audio_settings.get('prayer_volumes', {})
            ezan_volume = prayer_volumes.get(prayer_name.lower(), self.audio_settings.get('ezan_volume', 85))
            restore_volume = self.audio_settings.get('restore_original_volume', True)
            
            if restore_volume:
                # Save current volume before changing it
                self.original_volume = self.get_current_volume()
                logging.info(f"Current volume: {self.original_volume}%, setting to MAX {ezan_volume}%")
            
            # CONSISTENT VOLUME - Set volume and keep it steady throughout ezan
            logging.info(f"Setting CONSISTENT VOLUME to {ezan_volume}% for {prayer_name} ezan")
            for i in range(5):  # More attempts for instant effect
                self.set_volume(ezan_volume)
                time.sleep(0.1)  # Very short delay - almost instant
            
            # Open YouTube video in default browser
            webbrowser.open(video_url)
            
            # IMMEDIATELY set volume again - no waiting
            self.set_volume(ezan_volume)
            
            # Set volume one more time after a tiny delay to catch browser audio
            time.sleep(0.5)
            self.set_volume(ezan_volume)
            
            logging.info(f"Playing {prayer_name} ezan at CONSISTENT {ezan_volume}% volume: {video_url}")
            
            # NO VOLUME RESTORATION - Keep volume consistent throughout ezan
            # Only restore volume after a longer delay to avoid interrupting the ezan
            if restore_volume and self.original_volume is not None:
                # Wait longer before restoring to avoid volume changes during ezan
                restore_delay = 300  # 5 minutes - well after ezan finishes
                
                # Use threading to restore volume after delay without blocking
                def delayed_restore():
                    time.sleep(restore_delay)
                    self.restore_volume()
                
                restore_thread = threading.Thread(target=delayed_restore)
                restore_thread.daemon = True
                restore_thread.start()
                
                logging.info(f"Volume will be restored to {self.original_volume}% in {restore_delay} seconds (after ezan completes)")
            
            # Optional: You can also use subprocess to open in a specific browser
            # subprocess.run(['open', '-a', 'Safari', video_url])  # macOS with Safari
            # subprocess.run(['google-chrome', video_url])  # Linux with Chrome
            
        except Exception as e:
            logging.error(f"Error playing ezan video for {prayer_name}: {e}")
            # Restore volume on error if we changed it
            if hasattr(self, 'original_volume') and self.original_volume is not None:
                self.restore_volume()

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
