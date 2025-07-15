@echo off
cd "c:\Users\WDN\Desktop\virtual"
python manage.py shell -c "
from app.models import Service

# Fix WhatsApp service
wa_services = Service.objects.filter(code='wa')
print(f'Found {wa_services.count()} services with code wa')

for service in wa_services:
    print(f'  ID {service.id}: {service.name}')
    if 'fallback' in service.name.lower() or 'not listed' in service.name.lower():
        service.name = 'WhatsApp'
        service.save()
        print(f'    Fixed: renamed to {service.name}')

# Create Service Not Listed
snl_service, created = Service.objects.get_or_create(
    code='service_not_listed',
    defaults={
        'name': 'Service Not Listed',
        'price': '2.50',
        'daily_price': '0.00', 
        'profit_margin': '30.00',
        'available_numbers': 999,
        'supports_multiple_sms': True,
        'is_active': True,
    }
)

if created:
    print(f'Created Service Not Listed: {snl_service.name}')
else:
    print(f'Service Not Listed already exists: {snl_service.name}')

print('All services:')
for service in Service.objects.all():
    print(f'  {service.code}: {service.name}')
"
pause
