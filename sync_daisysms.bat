@echo off
echo Starting DaisySMS Service Sync...
cd /d "c:\Users\WDN\Desktop\virtual"

echo.
echo Step 1: Clearing existing sample services...
python manage.py shell -c "from app.models import Service; Service.objects.all().delete(); print('Sample services cleared')"

echo.
echo Step 2: Testing DaisySMS API connection...
python manage.py shell -c "from app.daisysms import DaisySMSClient; from django.conf import settings; client = DaisySMSClient(settings.DAISYSMS_API_KEY); balance = client.get_balance(); print(f'DaisySMS Balance: ${balance}')"

echo.
echo Step 3: Syncing real services from DaisySMS...
python manage.py shell -c "from app.daisysms import DaisySMSClient; from django.conf import settings; from app.models import Service; client = DaisySMSClient(settings.DAISYSMS_API_KEY); count = client.sync_services(); print(f'Synced {count} services'); print(f'Total services: {Service.objects.count()}')"

echo.
echo Done! You can now view the real DaisySMS services at http://127.0.0.1:8000/service/
pause
