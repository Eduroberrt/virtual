"""
Django management command to recalculate profit margins based on corrected wholesale prices
This fixes the issue where margins were calculated using incorrect USD-based pricing
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from app.models import SMSService

class Command(BaseCommand):
    help = 'Recalculate profit margins based on corrected wholesale prices (RUB-based)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--percentage',
            type=int,
            default=40,
            help='Profit margin percentage to apply (default: 40%)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        percentage = options['percentage']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(f'Recalculating profit margins with {percentage}% markup...')
        
        services = SMSService.objects.all()
        updated_count = 0
        
        for service in services:
            try:
                # Get current corrected wholesale price
                old_margin = float(service.profit_margin_naira)
                old_final_price = service.get_final_price_ngn()
                
                # Calculate new wholesale price (using RUB conversion)
                wholesale_ngn = service.get_wholesale_price_ngn()
                
                # Calculate new profit margin based on percentage
                new_margin_ngn = round(wholesale_ngn * percentage / 100, 2)
                new_final_price = wholesale_ngn + new_margin_ngn
                
                # Show the comparison
                self.stdout.write(
                    f'  {service.service_name}:'
                )
                self.stdout.write(
                    f'    Wholesale: ₦{wholesale_ngn:,.2f}'
                )
                self.stdout.write(
                    f'    Margin: ₦{old_margin:,.2f} → ₦{new_margin_ngn:,.2f}'
                )
                self.stdout.write(
                    f'    Final: ₦{old_final_price:,.2f} → ₦{new_final_price:,.2f}'
                )
                
                # Update if not dry run
                if not dry_run:
                    service.profit_margin_naira = new_margin_ngn
                    service.save()
                    updated_count += 1
                
                self.stdout.write('')  # Empty line for readability
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error updating {service.service_code}: {str(e)}')
                )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would update {services.count()} services')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Updated profit margins for {updated_count} services')
            )
