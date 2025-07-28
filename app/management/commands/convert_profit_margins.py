from django.core.management.base import BaseCommand
from app.models import Service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Convert existing percentage-based profit margins to absolute Naira amounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--default-margin',
            type=float,
            default=100.0,
            help='Default profit margin in Naira for services with 0 margin (default: 100.0)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        default_margin = Decimal(str(options['default_margin']))
        
        self.stdout.write(
            self.style.SUCCESS('Converting profit margins from percentage to absolute Naira amounts')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be saved')
            )
        
        services = Service.objects.all()
        
        for service in services:
            old_margin = service.profit_margin
            
            # If it's already a reasonable Naira amount (> 10), skip
            if old_margin > 10:
                self.stdout.write(f'Skipping {service.name}: Already appears to be in Naira (₦{old_margin})')
                continue
            
            # Calculate base price in Naira
            if service.price < 100:
                base_price_naira = service.price * Decimal('1650')
            else:
                base_price_naira = service.price
            
            # Convert percentage to absolute amount
            if old_margin > 0:
                # Convert percentage to absolute Naira amount
                new_margin = base_price_naira * (old_margin / Decimal('100'))
            else:
                # Use default margin for services with 0% margin
                new_margin = default_margin
            
            self.stdout.write(
                f'{service.name}: {old_margin}% → ₦{new_margin} '
                f'(base: ₦{base_price_naira}, final: ₦{base_price_naira + new_margin})'
            )
            
            if not dry_run:
                service.profit_margin = new_margin
                service.save()
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('Successfully converted all profit margins to Naira amounts!')
            )
            self.stdout.write('')
            self.stdout.write('You can now set profit margins in the admin as absolute Naira amounts:')
            self.stdout.write('  - 100.00 for ₦100 profit')
            self.stdout.write('  - 250.00 for ₦250 profit') 
            self.stdout.write('  - 75.50 for ₦75.50 profit')
        else:
            self.stdout.write('')
            self.stdout.write('To apply these changes, run the command without --dry-run')
