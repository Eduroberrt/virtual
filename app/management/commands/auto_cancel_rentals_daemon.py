"""
Always-on daemon for Dashboard-2 (MTelSMS) that:
1. Auto-cancels rentals after 5 minutes if no SMS received
2. Checks for expired rentals and processes refunds

This is the Dashboard-2 equivalent of auto_refund_daemon.py
Run as an always-on task on PythonAnywhere
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from datetime import datetime
import time


class Command(BaseCommand):
    help = 'Always-on daemon for MTelSMS rental management (5-min cancel + expired refunds)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=120,  # Default 2 minutes (faster than Dashboard-1 since MTelSMS is faster)
            help='Seconds to wait between cycles (default: 120 = 2 minutes)',
        )
        parser.add_argument(
            '--dry-run-only',
            action='store_true',
            help='Run all commands in dry-run mode (no actual changes)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        dry_run_only = options['dry_run_only']
        
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('🚀 MTelSMS Rental Auto-Cancel Daemon Starting'))
        self.stdout.write('='*60)
        self.stdout.write(f'Mode: {"DRY RUN ONLY" if dry_run_only else "PRODUCTION"}')
        self.stdout.write(f'Interval: {interval} seconds ({interval/60:.1f} minutes)')
        self.stdout.write('Process:')
        self.stdout.write('  STEP 1: Auto-cancel rentals waiting > 5 minutes')
        self.stdout.write('  STEP 2: Check for expired rentals and refund')
        self.stdout.write('='*60)
        self.stdout.write('')
        
        if dry_run_only:
            self.stdout.write(
                self.style.WARNING('⚠ DRY RUN MODE - No actual changes will be made')
            )
            self.stdout.write('')
        
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                self.stdout.write(f'[{datetime.now()}] Starting cycle #{cycle_count}...')
                
                # STEP 1: Auto-cancel rentals waiting > 5 minutes without SMS
                self.stdout.write('   → Auto-cancelling rentals waiting > 5 minutes...')
                try:
                    if dry_run_only:
                        call_command('auto_cancel_5min_rentals', '--dry-run')
                    else:
                        call_command('auto_cancel_5min_rentals')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ✗ 5-minute auto-cancel failed: {str(e)}')
                    )
                
                # STEP 2: Check for expired rentals and process refunds
                self.stdout.write('   → Checking for expired rentals to refund...')
                try:
                    if dry_run_only:
                        call_command('check_expired_rentals', '--dry-run')
                    else:
                        call_command('check_expired_rentals')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ✗ Expired rental check failed: {str(e)}')
                    )
                
                self.stdout.write(f'✓ Cycle #{cycle_count} complete. Sleeping for {interval} seconds...\n')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠ Daemon stopped by user (Ctrl+C)'))
            self.stdout.write(f'Completed {cycle_count} cycles')
