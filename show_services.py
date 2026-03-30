#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.models import Service

print('=' * 80)
print('YOUR CURRENT SERVICES IN DATABASE:')
print('=' * 80)

services = Service.objects.all()[:10]
for s in services:
    mtelsms_id = s.mtelsms_service_id if s.mtelsms_service_id else "❌ NOT SET"
    print(f'Code: {s.code:15} | Name: {s.name:35} | MTelSMS ID: {mtelsms_id}')

print('\n' + '=' * 80)
print('WHAT "MAPPING" MEANS:')
print('=' * 80)
print("""
Your Django database has services like:
  - Code: "wa"        Name: "WhatsApp"
  - Code: "tg"        Name: "Telegram"
  - Code: "fb"        Name: "Facebook"
  
MTelSMS API uses NUMERIC service IDs like:
  - Service ID: "1"   Name: "WhatsApp"
  - Service ID: "5"   Name: "Telegram"  
  - Service ID: "12"  Name: "Facebook"

You need to MATCH them! This means:
  1. Get list of services from MTelSMS API
  2. Find which MTelSMS service matches your Django service by NAME
  3. Store MTelSMS's numeric ID in your Django service's mtelsms_service_id field

Example:
  Your Django service: code="wa", name="WhatsApp", mtelsms_service_id=NULL
  MTelSMS service:     id="1", name="WhatsApp"
  
  After mapping: code="wa", name="WhatsApp", mtelsms_service_id="1" ✅
  
Now when a user purchases WhatsApp verification, your code will:
  - Look up Service with code "wa"
  - Read mtelsms_service_id field → gets "1"
  - Call MTelSMS API with service_id="1"
  - MTelSMS knows "1" means WhatsApp!

Without mapping, the API call will fail because MTelSMS doesn't know what "wa" means.
""")

print('=' * 80)
print('Total services in database:', services.count())
print('Services without MTelSMS ID:', Service.objects.filter(mtelsms_service_id__isnull=True).count())
print('=' * 80)
