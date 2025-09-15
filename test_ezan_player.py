#!/usr/bin/env python3
"""
Test script for Ezan Player
Use this to verify your setup and configuration.
"""

import json
import sys
from datetime import datetime
from ezan_player import EzanPlayer

def test_config_file():
    """Test if configuration file exists and is valid."""
    print("🔧 Testing configuration file...")
    try:
        with open('ezan_config.json', 'r') as f:
            config = json.load(f)
        
        videos = config.get('youtube_videos', {})
        required_prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        
        missing = [prayer for prayer in required_prayers if prayer not in videos]
        if missing:
            print(f"❌ Missing prayer videos: {missing}")
            return False
        
        placeholder_count = sum(1 for url in videos.values() if 'YOUR_' in url)
        if placeholder_count > 0:
            print(f"⚠️  {placeholder_count} placeholder URLs need to be replaced")
            for prayer, url in videos.items():
                if 'YOUR_' in url:
                    print(f"   {prayer}: {url}")
            return False
        
        print("✅ Configuration file is valid!")
        return True
        
    except FileNotFoundError:
        print("❌ Configuration file (ezan_config.json) not found!")
        return False
    except json.JSONDecodeError:
        print("❌ Configuration file contains invalid JSON!")
        return False

def test_prayer_times_api():
    """Test fetching prayer times from Diyanet API."""
    print("\n🕰️ Testing prayer times API...")
    
    player = EzanPlayer()
    success = player.get_prayer_times()
    
    if success and player.prayer_times:
        print("✅ Prayer times fetched successfully!")
        print("Today's prayer times:")
        for prayer, time in player.prayer_times.items():
            print(f"   {prayer.capitalize()}: {time}")
        return True
    else:
        print("❌ Failed to fetch prayer times!")
        print("Check your internet connection and try again.")
        return False

def test_youtube_integration():
    """Test YouTube video opening (will actually open a test video)."""
    print("\n📺 Testing YouTube integration...")
    
    response = input("This will open a YouTube video in your browser. Continue? (y/N): ")
    if response.lower() != 'y':
        print("⏭️  Skipping YouTube test")
        return True
    
    try:
        import webbrowser
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll as test
        webbrowser.open(test_url)
        print("✅ YouTube integration test successful!")
        print("If a YouTube video opened in your browser, the integration works!")
        return True
    except Exception as e:
        print(f"❌ YouTube integration failed: {e}")
        return False

def test_system_wake():
    """Test system wake functionality."""
    print("\n💤 Testing system wake functionality...")
    
    player = EzanPlayer()
    try:
        player.wake_system()
        print("✅ System wake command executed successfully!")
        print("Note: Actual wake-up from sleep depends on your system settings.")
        return True
    except Exception as e:
        print(f"⚠️  System wake test had issues: {e}")
        print("This may still work when your computer is actually asleep.")
        return False

def test_scheduling():
    """Test prayer time scheduling."""
    print("\n⏰ Testing scheduling functionality...")
    
    player = EzanPlayer()
    if not player.get_prayer_times():
        print("❌ Cannot test scheduling without prayer times")
        return False
    
    try:
        player.schedule_prayers()
        print("✅ Prayer scheduling test successful!")
        
        # Check if any prayers are scheduled for today
        import schedule
        jobs = schedule.jobs
        
        if jobs:
            print(f"📅 {len(jobs)} prayer(s) scheduled for today:")
            for job in jobs:
                print(f"   Next run: {job.next_run}")
        else:
            print("ℹ️  No prayers scheduled (may be because all prayer times have passed today)")
        
        return True
    except Exception as e:
        print(f"❌ Scheduling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🕌 Ezan Player Test Suite")
    print("========================")
    
    tests = [
        ("Configuration", test_config_file),
        ("Prayer Times API", test_prayer_times_api),
        ("YouTube Integration", test_youtube_integration),
        ("System Wake", test_system_wake),
        ("Scheduling", test_scheduling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results Summary")
    print("======================")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your Ezan Player should work correctly.")
        print("You can now run: python3 ezan_player.py")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please fix the issues above.")
        print("Check the README.md for troubleshooting help.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
