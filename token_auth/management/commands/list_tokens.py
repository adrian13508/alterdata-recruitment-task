from django.core.management.base import BaseCommand
from token_auth.models import ApiToken


class Command(BaseCommand):
    help = 'List all API tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active tokens',
        )
        parser.add_argument(
            '--show-tokens',
            action='store_true',
            help='Show full token values (security warning)',
        )

    def handle(self, *args, **options):
        queryset = ApiToken.objects.all().order_by('-created_at')
        
        if options['active_only']:
            queryset = queryset.filter(is_active=True)

        if not queryset.exists():
            self.stdout.write(
                self.style.WARNING('No API tokens found')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {queryset.count()} API token(s):')
        )
        self.stdout.write('')

        for token in queryset:
            status = self.style.SUCCESS('ACTIVE') if token.is_active else self.style.ERROR('INACTIVE')
            
            self.stdout.write(f'Name: {token.name}')
            self.stdout.write(f'Status: {status}')
            
            if options['show_tokens']:
                self.stdout.write(f'Token: {token.token}')
            else:
                self.stdout.write(f'Token: {token.token[:8]}...{token.token[-4:]}')
            
            self.stdout.write(f'Created: {token.created_at}')
            self.stdout.write(f'Last Used: {token.last_used_at or "Never"}')
            self.stdout.write('-' * 50)