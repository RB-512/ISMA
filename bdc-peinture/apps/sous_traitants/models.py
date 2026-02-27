from django.db import models


class SousTraitant(models.Model):
    """
    Sous-traitant (artisan peintre) qui réalise les travaux.
    Reçoit les BDC terrain par SMS/email. Pas d'accès à l'app en V1.
    """

    nom = models.CharField(max_length=150, verbose_name="Nom / Raison sociale")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Sous-traitant"
        verbose_name_plural = "Sous-traitants"
        ordering = ["nom"]

    def __str__(self) -> str:
        return self.nom
