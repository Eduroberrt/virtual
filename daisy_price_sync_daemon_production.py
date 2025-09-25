"""
DaisySMS Price Sync Daemon for Production (PythonAnywhere)
This script runs continuously and syncs services and prices from DaisySMS API
"""
import os
import sys
import django
import time

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Fixed: only one dirname()
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.core.management import call_command

def main():
    """Main daemon loop for production"""
    # Do an initial sync on startup
    try:
        call_command('sync_daisy_prices')
    except Exception as e:
        pass  # Silent failure
    
    try:
        while True:
            try:
                # Run the sync command silently
                call_command('sync_daisy_prices')
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                pass  # Silent failure
            
            # Wait 30 minutes before next sync (1800 seconds)  
            time.sleep(30 * 60)
    
    except KeyboardInterrupt:
        pass
    
    # Silent shutdown

if __name__ == '__main__':
    main()
