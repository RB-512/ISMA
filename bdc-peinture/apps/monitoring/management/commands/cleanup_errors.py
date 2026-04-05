from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.monitoring.models import ErrorReport


class Command(BaseCommand):
    help = "Supprime les rapports d'erreur de plus de 30 jours"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=30)
        deleted, _ = ErrorReport.objects.filter(last_seen__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted} rapport(s) supprimé(s)."))
