from django.db import models
from django.db.models import Q, UniqueConstraint


class SousTraitant(models.Model):
    """
    Sous-traitant (artisan peintre) qui réalise les travaux.
    Reçoit les BDC terrain par SMS/email. Pas d'accès à l'app en V1.
    """

    nom = models.CharField(max_length=150, unique=True, verbose_name="Nom / Raison sociale")
    siret = models.CharField(max_length=14, blank=True, verbose_name="SIRET")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    adresse = models.CharField(max_length=255, blank=True, verbose_name="Adresse")
    code_postal = models.CharField(max_length=5, blank=True, verbose_name="Code postal")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Sous-traitant"
        verbose_name_plural = "Sous-traitants"
        ordering = ["nom"]
        constraints = [
            UniqueConstraint(
                fields=["siret"],
                name="unique_siret_non_vide",
                condition=~Q(siret=""),
            ),
        ]

    def __str__(self) -> str:
        return self.nom
