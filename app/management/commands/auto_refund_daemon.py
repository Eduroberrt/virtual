from django.core.management.base import BaseCommand
from django.core.management import call_command
import time
from datetime import datetime

class Command(BaseCommand):
    help = 'Development auto-refund daemon - simulates production cron job'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Interval between refund checks in seconds (default: 300)',
        )
        parser.add_argument(
            '--dry-run-only',
            action='store_true',
            help='Only run dry-run, never actually refund',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        dry_run_only = options['dry_run_only']
        
        self.stdout.write(
            self.style.SUCCESS(f'🧪 Starting development auto-refund daemon')
        )
        self.stdout.write(f'   Interval: {interval} seconds')
        self.stdout.write(f'   Dry-run only: {dry_run_only}')
        self.stdout.write('   Press Ctrl+C to stop\n')
        
        try:
            while True:
                self.stdout.write(f'[{datetime.now()}] Checking for expired orders...')
                
                if dry_run_only:
                    # Always dry-run
                    call_command('auto_refund_expired_fivesim', '--dry-run')
                else:
                    # Run actual refunds
                    call_command('auto_refund_expired_fivesim')
                
                self.stdout.write(f'Sleeping for {interval} seconds...\n')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n🛑 Auto-refund daemon stopped by user')
            )
