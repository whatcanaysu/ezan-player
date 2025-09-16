# 🕌 Automated Ezan Player

Automatically plays YouTube ezan videos at prayer times according to Diyanet Başkanlığı for Barcelona, Spain.

## Features

- 🕰️ Fetches official prayer times directly from Diyanet Başkanlığı website
- 📺 Automatically opens YouTube videos at prayer times
- 💤 Wakes up your computer from sleep mode when prayer time arrives
- ⚙️ Configurable YouTube video URLs for each prayer (5 prayers)
- 📅 Daily automatic updates of prayer times
- 🔄 Runs as a background service
- 📝 Comprehensive logging

## Prayer Times Covered

1. **Fajr** (İmsak) - Dawn prayer
2. **Dhuhr** (Öğle) - Noon prayer  
3. **Asr** (İkindi) - Afternoon prayer
4. **Maghrib** (Akşam) - Sunset prayer
5. **Isha** (Yatsı) - Night prayer

## Prerequisites

- Python 3.7 or higher
- Internet connection
- macOS, Linux, or Windows

## Quick Setup

1. **Clone or download the project files**
2. **Run the setup script:**
   ```bash
   python3 setup.py
   ```
3. **Configure your YouTube videos** (see Configuration section)
4. **Test the application:**
   ```bash
   python3 ezan_player.py
   ```

## Configuration

### YouTube Videos

Edit `ezan_config.json` and replace the placeholder URLs with your actual YouTube ezan videos:

```json
{
  "youtube_videos": {
    "fajr": "https://youtube.com/watch?v=YOUR_ACTUAL_FAJR_VIDEO_ID",
    "dhuhr": "https://youtube.com/watch?v=YOUR_ACTUAL_DHUHR_VIDEO_ID",
    "asr": "https://youtube.com/watch?v=YOUR_ACTUAL_ASR_VIDEO_ID",
    "maghrib": "https://youtube.com/watch?v=YOUR_ACTUAL_MAGHRIB_VIDEO_ID",
    "isha": "https://youtube.com/watch?v=YOUR_ACTUAL_ISHA_VIDEO_ID"
  },
  "location": {
    "city": "Barcelona",
    "country": "Spain",
    "diyanet_city_id": "9541"
  }
}
```

### Finding YouTube Video IDs

1. Go to your desired ezan video on YouTube
2. Copy the URL (e.g., `https://youtube.com/watch?v=dQw4w9WgXcQ`)
3. The video ID is the part after `v=` (in this example: `dQw4w9WgXcQ`)

## Installation and Running

### Manual Installation

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Make the script executable
chmod +x ezan_player.py

# Run manually
python3 ezan_player.py
```

### Automatic Startup (macOS)

```bash
# Create Launch Agent
python3 setup.py

# Start the service
launchctl load ~/Library/LaunchAgents/com.ezanplayer.plist

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.ezanplayer.plist
```

### Automatic Startup (Linux)

```bash
# Create systemd service
python3 setup.py

# Install and start service (requires sudo)
sudo cp ezanplayer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ezanplayer
sudo systemctl start ezanplayer

# Check status
sudo systemctl status ezanplayer
```

## Sleep Mode Handling

The application includes functionality to wake your computer from sleep mode:

- **macOS**: Uses `caffeinate` command to wake the system
- **Linux**: Uses `xset` command to wake the display
- **Windows**: Uses `powercfg` command

**Note**: Some sleep modes may require additional system configuration to allow wake-up events.

## Logging

The application creates detailed logs in:
- `ezan_player.log` - Application logs
- Console output for real-time monitoring

Log levels include:
- INFO: Normal operation events
- WARNING: Non-critical issues
- ERROR: Failed operations

## Troubleshooting

### Common Issues

1. **"Failed to fetch prayer times"**
   - Check internet connection
   - Verify Diyanet API is accessible
   - Check firewall settings

2. **YouTube videos don't open**
   - Verify YouTube URLs in config file
   - Check default browser settings
   - Ensure browser is installed

3. **Computer doesn't wake up**
   - Check power management settings
   - Verify wake-up permissions
   - Test with shorter sleep periods

4. **Service doesn't start automatically**
   - Check service installation
   - Verify file permissions
   - Review system logs

### Testing

Test individual components:

```python
# Test prayer times API
from ezan_player import EzanPlayer
player = EzanPlayer()
player.get_prayer_times()
print(player.prayer_times)

# Test YouTube opening
player.play_ezan_video('fajr')
```

## File Structure

```
ezan_player/
├── ezan_player.py          # Main application
├── setup.py               # Setup and service installation
├── requirements.txt       # Python dependencies
├── ezan_config.json       # Configuration file
├── README.md             # This file
├── ezan_player.log       # Application logs (created at runtime)
└── ezanplayer.service    # Linux systemd service (created by setup.py)
```

## Data Source Information

This application uses:
- **Official Diyanet Başkanlığı Website**: `https://namazvakitleri.diyanet.gov.tr/tr-TR/14262/barcelona-icin-namaz-vakti`
- **Barcelona City ID**: 14262 (in Diyanet system)
- **Method**: Web scraping from official Diyanet prayer times website
- **Accuracy**: Official prayer times calculated by Turkish Presidency of Religious Affairs

## Security and Privacy

- No personal data is collected or stored
- Only prayer times are fetched from Diyanet API
- YouTube videos are opened in your default browser
- All processing happens locally on your computer

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

---

**May this application help you maintain your prayer schedule! 🤲**
