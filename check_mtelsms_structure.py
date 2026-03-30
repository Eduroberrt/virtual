#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from app.mtelsms import get_mtelsms_client
import json

client = get_mtelsms_client()
services = client.get_all_services()

print(f"Total services: {len(services)}")
print(f"\nFirst service structure:")
print(json.dumps(services[0], indent=2))
print(f"\nKeys in first service: {services[0].keys()}")
