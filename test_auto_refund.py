"""
Development Auto-Refund Test Runner
Simulates production cron job for testing
"""
import time
import subprocess
import sys
from datetime import datetime

def run_auto_refund():
    """Run the auto-refund command"""
    try:
        print(f"[{datetime.now()}] Running auto-refund...")
        
        # Run with dry-run first to see what would happen
        result = subprocess.run([
            sys.executable, 'manage.py', 'auto_refund_expired_fivesim', '--dry-run'
        ], capture_output=True, text=True, cwd='c:/Users/WDN/Desktop/virtual')
        
        if result.stdout:
            print("DRY RUN OUTPUT:")
            print(result.stdout)
        
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
            
        # Uncomment this to actually run refunds (not just dry-run)
        # result = subprocess.run([
        #     sys.executable, 'manage.py', 'auto_refund_expired_fivesim'
        # ], capture_output=True, text=True, cwd='c:/Users/WDN/Desktop/virtual')
        
    except Exception as e:
        print(f"Error running auto-refund: {e}")

def main():
    """Main testing loop"""
    print("🧪 Development Auto-Refund Tester")
    print("This simulates the PythonAnywhere always-on task")
    print("Press Ctrl+C to stop\n")
    
    interval = 5 * 60  # 5 minutes (same as production)
    
    try:
        while True:
            run_auto_refund()
            print(f"Waiting {interval} seconds until next check...\n")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Test runner stopped by user")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")

if __name__ == "__main__":
    main()
