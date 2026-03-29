"""Local Development Scheduler.

This script runs the marketing agent pipeline every 5 minutes locally.
It uses 'uv' to ensure it runs in the correct environment with all dependencies.
"""

import time
import subprocess
import datetime
import sys

def main():
    interval_minutes = 720  # 12 hours (Run twice a day)
    interval_seconds = interval_minutes * 60
    
    print("=" * 60)
    print(f"🚀 Marketing Agent — Local Python Scheduler")
    print(f"Interval: Every {interval_minutes} minutes")
    print("=" * 60)
    
    while True:
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[🕒 {now}] Triggering scheduled run...")
            
            # Run the same command GitHub Actions uses
            result = subprocess.run(["uv", "run", "python", "scripts/run_and_report.py"])
            
            if result.returncode == 0:
                print(f"[✅ {datetime.datetime.now().strftime('%H:%M:%S')}] Run completed successfully.")
            else:
                print(f"[❌ {datetime.datetime.now().strftime('%H:%M:%S')}] Run failed with exit code {result.returncode}.")
                
        except Exception as e:
            print(f"[⚠️ Error] Exception while running pipeline: {e}")
            
        next_run = (datetime.datetime.now() + datetime.timedelta(seconds=interval_seconds)).strftime("%H:%M:%S")
        print("-" * 60)
        print(f"💤 Sleeping for {interval_minutes} minutes. Next run at: {next_run}")
        print("Press Ctrl+C to stop the scheduler.")
        print("-" * 60)
        
        # Sleep for the interval
        time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped manually.")
        sys.exit(0)
