import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

NUMERO_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}(-\d+)?$")


def valider_numero_calver(value):
    if not NUMERO_RE.match(value):
        raise ValidationError("Le numéro doit suivre le format AAAA.MM.JJ ou AAAA.MM.JJ-N.")


class Version(models.Model):
    numero = models.CharField(max_length=20, unique=True, validators=[valider_numero_calver])
    date_mise_en_ligne = models.DateField()
    resume = models.TextField()
    changements = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_mise_en_ligne", "-created_at"]
        verbose_name = "Version"
        verbose_name_plural = "Versions"

    def __str__(self):
        return self.numero
