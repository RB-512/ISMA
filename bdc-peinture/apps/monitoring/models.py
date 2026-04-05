from django.db import models
from django.utils import timezone


class ErrorReport(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True)
    error_type = models.CharField(max_length=255)
    message = models.TextField()
    traceback = models.TextField()
    url = models.TextField(blank=True)
    method = models.CharField(max_length=10, blank=True)
    user_email = models.CharField(max_length=255, blank=True)
    count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-last_seen"]
        verbose_name = "Rapport d'erreur"
        verbose_name_plural = "Rapports d'erreurs"

    def __str__(self):
        return f"{self.error_type}: {self.message[:80]}"
