"""
Management command : affiche les BDC en retard ou proches du délai.
Usage : python manage.py check_delais
"""

from django.core.management.base import BaseCommand

from apps.notifications.alertes import get_bdc_delai_proche, get_bdc_en_retard


class Command(BaseCommand):
    help = "Affiche les BDC dont le délai d'exécution est dépassé ou proche (J-2)."

    def handle(self, *args, **options):
        en_retard = get_bdc_en_retard()
        delai_proche = get_bdc_delai_proche()

        self.stdout.write(self.style.WARNING(f"\n{'=' * 60}"))
        self.stdout.write(self.style.WARNING("  ALERTES DÉLAIS BDC"))
        self.stdout.write(self.style.WARNING(f"{'=' * 60}\n"))

        if en_retard.exists():
            self.stdout.write(self.style.ERROR(f"  {en_retard.count()} BDC en retard :"))
            for bdc in en_retard:
                self.stdout.write(
                    f"    - {bdc.numero_bdc} | {bdc.adresse} | "
                    f"Délai : {bdc.delai_execution.strftime('%d/%m/%Y')} | "
                    f"Statut : {bdc.get_statut_display()}"
                )
            self.stdout.write("")
        else:
            self.stdout.write(self.style.SUCCESS("  Aucun BDC en retard.\n"))

        if delai_proche.exists():
            self.stdout.write(self.style.WARNING(f"  {delai_proche.count()} BDC proches du délai (J-2) :"))
            for bdc in delai_proche:
                self.stdout.write(
                    f"    - {bdc.numero_bdc} | {bdc.adresse} | "
                    f"Délai : {bdc.delai_execution.strftime('%d/%m/%Y')} | "
                    f"Statut : {bdc.get_statut_display()}"
                )
            self.stdout.write("")
        else:
            self.stdout.write(self.style.SUCCESS("  Aucun BDC proche du délai.\n"))
