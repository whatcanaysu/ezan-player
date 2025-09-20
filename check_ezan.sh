#!/bin/bash
# 🕌 Ezan Player Status Checker
# Run this anytime to check if your Ezan Player is working

cd /Users/seymaaysudemir/tmp/ezan-player

echo "🕌 Ezan Player Status Check"
echo "=========================="
echo ""

# Check LaunchAgent service
echo "📋 Service Status:"
SERVICE_CHECK=$(launchctl list | grep ezanplayer)
if [ -n "$SERVICE_CHECK" ]; then
    echo "✅ Service running: $SERVICE_CHECK"
else
    echo "❌ Service not running"
fi
echo ""

# Check Python process
echo "🐍 Python Process:"
PROCESS_CHECK=$(ps aux | grep ezan_player | grep -v grep)
if [ -n "$PROCESS_CHECK" ]; then
    echo "✅ Process active:"
    echo "   $PROCESS_CHECK"
else
    echo "❌ No Python process found"
fi
echo ""

# Show current time
echo "⏰ Current Time: $(date)"
echo ""

# Check recent logs
echo "📝 Recent Activity (last 5 lines):"
if [ -f "ezan_player.log" ]; then
    tail -5 ezan_player.log
elif [ -f "~/Library/Logs/ezanplayer.log" ]; then
    tail -5 ~/Library/Logs/ezanplayer.log
else
    echo "No log files found"
fi
echo ""

# Quick prayer times check
echo "🕰️ Today's Prayer Times:"
python3 -c "
from ezan_player import EzanPlayer
from datetime import datetime
try:
    player = EzanPlayer()
    if player.get_prayer_times():
        current_time = datetime.now().time()
        next_prayer = None
        for prayer, time in player.prayer_times.items():
            prayer_time = datetime.strptime(time, '%H:%M').time()
            status = '✅ NEXT' if prayer_time > current_time else '⏹️ Done'
            print(f'   {prayer.capitalize()}: {time} {status}')
            if prayer_time > current_time and next_prayer is None:
                next_prayer = f'{prayer.capitalize()} at {time}'
        
        if next_prayer:
            print(f'\\n🔔 Next Ezan: {next_prayer}')
            print(f'🔊 Volume will be: {player.audio_settings.get(\"ezan_volume\", 65)}%')
    else:
        print('   Could not fetch prayer times')
except Exception as e:
    print(f'   Error checking prayer times: {e}')
" 2>/dev/null

echo ""
echo "🌐 Web Dashboard:"
DASHBOARD_RUNNING=$(ps aux | grep -c "web_dashboard.py" | grep -v grep || echo "0")
if [ "$DASHBOARD_RUNNING" -gt "1" ]; then
    echo "✅ Dashboard running at http://localhost:8080"
else
    echo "⚠️  Dashboard not running"
fi
echo ""
echo "=========================="
echo "🎮 Control Commands:"
echo "python3 start_dashboard.py  # Start web dashboard"
echo "launchctl unload ~/Library/LaunchAgents/com.ezanplayer.plist"
echo "launchctl load ~/Library/LaunchAgents/com.ezanplayer.plist"
