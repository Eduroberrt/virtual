#!/usr/bin/env python
"""
Check the API logs to see what parameters are being sent
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import APILog

def check_recent_api_logs():
    """Check recent API logs to see what parameters are being sent"""
    print("🔍 Checking recent API logs...")
    
    # Get the most recent getNumber API calls
    recent_logs = APILog.objects.filter(
        endpoint='getNumber'
    ).order_by('-created_at')[:5]
    
    for log in recent_logs:
        print(f"\n📅 {log.created_at}")
        print(f"📊 Status: {log.status_code}")
        print(f"📝 Request Data: {log.request_data}")
        if log.error_message:
            print(f"❌ Error: {log.error_message}")
        if log.response_data:
            print(f"📤 Response: {log.response_data}")
        print("-" * 50)

if __name__ == "__main__":
    check_recent_api_logs()
