from django.core.management.base import BaseCommand, CommandError
from token_auth.models import ApiToken


class Command(BaseCommand):
    help = 'Create a new API token'

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            type=str,
            help='Name for the API token'
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Create token as inactive',
        )

    def handle(self, *args, **options):
        name = options['name']
        is_active = not options['inactive']

        try:
            # Check if token with this name already exists
            if ApiToken.objects.filter(name=name).exists():
                raise CommandError(f'Token with name "{name}" already exists')

            # Create the token
            token = ApiToken.objects.create(
                name=name,
                is_active=is_active
            )

            # Print success message with token
            self.stdout.write(
                self.style.SUCCESS('Successfully created API token')
            )
            self.stdout.write(f'Name: {token.name}')
            self.stdout.write(f'Token: {token.token}')
            self.stdout.write(f'Active: {token.is_active}')
            self.stdout.write(f'Created: {token.created_at}')
            
            if not is_active:
                self.stdout.write(
                    self.style.WARNING('Token is inactive. Activate it in Django admin or create without --inactive flag.')
                )

        except Exception as e:
            raise CommandError(f'Error creating token: {str(e)}')