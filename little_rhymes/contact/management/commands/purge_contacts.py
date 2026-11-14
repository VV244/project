from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from contact.models import ContactMessage

class Command(BaseCommand):
    help = 'Delete resolved adult contact messages older than the configured retention period.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        if options['days'] < 1:
            raise CommandError('--days must be positive.')
        records = ContactMessage.objects.filter(is_resolved=True, created_at__lt=timezone.now() - timedelta(days=options['days']))
        count = records.count()
        if not options['dry_run']:
            records.delete()
        self.stdout.write(f'{"Would delete" if options["dry_run"] else "Deleted"} {count} resolved messages.')
