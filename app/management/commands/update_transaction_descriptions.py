"""
Django management command to update existing transaction descriptions
This updates all historical transaction records to use the new naming conventions
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import Transaction
import re

class Command(BaseCommand):
    help = 'Update existing transaction descriptions to use new naming conventions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all transactions that need updating using Q objects
        from django.db.models import Q
        
        transactions_to_update = Transaction.objects.filter(
            Q(description__icontains='5sim') | 
            Q(description__icontains='(Daisy SMS') |
            Q(description__icontains='(Daisy sms') |
            Q(description__icontains='(daisy sms') |
            Q(description__icontains='(daisy SMS')
        )
        
        if not transactions_to_update.exists():
            self.stdout.write(
                self.style.SUCCESS('No transaction descriptions need updating!')
            )
            return
        
        total_count = transactions_to_update.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {total_count} transaction descriptions')
            )
            
            # Show examples of what would be changed
            for tx in transactions_to_update[:10]:
                old_desc = tx.description
                new_desc = self.update_description(old_desc)
                if old_desc != new_desc:
                    self.stdout.write(f'  OLD: {old_desc}')
                    self.stdout.write(f'  NEW: {new_desc}')
                    self.stdout.write('')
            
            if total_count > 10:
                self.stdout.write(f'  ... and {total_count - 10} more')
            
            return
        
        # Update the descriptions
        updated_count = 0
        error_count = 0
        
        self.stdout.write(f'Updating {total_count} transaction descriptions...')
        
        with transaction.atomic():
            for tx in transactions_to_update:
                try:
                    old_description = tx.description
                    new_description = self.update_description(old_description)
                    
                    if old_description != new_description:
                        tx.description = new_description
                        tx.save(update_fields=['description'])
                        updated_count += 1
                        
                        if updated_count % 100 == 0:
                            self.stdout.write(f'  Updated {updated_count} records...')
                            
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error updating transaction {tx.id}: {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} transaction descriptions '
                f'({error_count} errors)'
            )
        )

    def update_description(self, description):
        """Update a single description string"""
        if not description:
            return description
        
        # Replace "5sim" with "Dashboard 1" (case insensitive)
        updated = re.sub(r'\b5sim\b', 'Dashboard 1', description, flags=re.IGNORECASE)
        
        # Remove various forms of Daisy SMS brackets (case insensitive)
        updated = re.sub(r'\s*\([Dd]aisy\s+[Ss][Mm][Ss]\s+expired\)', '', updated)
        updated = re.sub(r'\s*\([Dd]aisy\s+[Ss][Mm][Ss]\s+cancelled\)', '', updated)
        updated = re.sub(r'\s*\([Dd]aisy\s+sms\s+expired\)', '', updated)
        updated = re.sub(r'\s*\([Dd]aisy\s+sms\s+cancelled\)', '', updated)
        
        # Clean up any double spaces
        updated = re.sub(r'\s+', ' ', updated).strip()
        
        return updated