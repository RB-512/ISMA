import os
from datetime import date

from django.contrib.auth.models import User
from django.db import models

# ─── Upload path ──────────────────────────────────────────────────────────────

def pdf_upload_path(instance: "BonDeCommande", filename: str) -> str:
    """Stocke les PDFs dans bdc/<annee>/<mois>/<numero_bdc>_<filename>."""
    today = date.today()
    basename = os.path.basename(filename)
    return f"bdc/{today.year}/{today.month:02d}/{instance.numero_bdc}_{basename}"


def pdf_terrain_upload_path(instance: "BonDeCommande", filename: str) -> str:
    """Stocke les PDFs terrain dans bdc_terrain/<annee>/<mois>/<numero_bdc>_terrain.pdf."""
    today = date.today()
    return f"bdc_terrain/{today.year}/{today.month:02d}/{instance.numero_bdc}_terrain.pdf"


# ─── Bailleur ─────────────────────────────────────────────────────────────────

class Bailleur(models.Model):
    """
    Bailleur social émetteur des bons de commande.
    Ex : GDH (Grand Delta Habitat), ERILIA.
    """

    nom = models.CharField(max_length=150, unique=True, verbose_name="Nom")
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Code court utilisé dans l'application. Ex: GDH, ERILIA",
    )

    class Meta:
        verbose_name = "Bailleur"
        verbose_name_plural = "Bailleurs"
        ordering = ["nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.code})"


# ─── BonDeCommande ────────────────────────────────────────────────────────────

class StatutChoices(models.TextChoices):
    A_TRAITER = "A_TRAITER", "À traiter"
    A_FAIRE = "A_FAIRE", "À faire"
    EN_COURS = "EN_COURS", "En cours"
    A_FACTURER = "A_FACTURER", "À facturer"
    FACTURE = "FACTURE", "Facturé"


class OccupationChoices(models.TextChoices):
    VACANT = "VACANT", "Vacant"
    OCCUPE = "OCCUPE", "Occupé"


class BonDeCommande(models.Model):
    """
    Bon de commande émis par un bailleur pour des travaux de peinture.
    Cycle de vie : A_TRAITER → A_FAIRE → EN_COURS → A_FACTURER → FACTURE
    """

    # ── Identification ──────────────────────────────────────────────────────
    numero_bdc = models.CharField(max_length=50, unique=True, verbose_name="N° BDC")
    numero_marche = models.CharField(max_length=100, blank=True, verbose_name="N° Marché")
    bailleur = models.ForeignKey(
        Bailleur,
        on_delete=models.PROTECT,
        related_name="bons_de_commande",
        verbose_name="Bailleur",
    )
    date_emission = models.DateField(null=True, blank=True, verbose_name="Date d'émission")

    # ── Localisation ────────────────────────────────────────────────────────
    programme_residence = models.CharField(max_length=200, blank=True, verbose_name="Programme / Résidence")
    adresse = models.CharField(max_length=255, verbose_name="Adresse")
    code_postal = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    logement_numero = models.CharField(max_length=50, blank=True, verbose_name="N° Logement")
    logement_type = models.CharField(max_length=20, blank=True, verbose_name="Type logement")
    logement_etage = models.CharField(max_length=20, blank=True, verbose_name="Étage")
    logement_porte = models.CharField(max_length=20, blank=True, verbose_name="Porte")

    # ── Travaux ─────────────────────────────────────────────────────────────
    objet_travaux = models.TextField(blank=True, verbose_name="Objet / Nature des travaux")
    delai_execution = models.DateField(null=True, blank=True, verbose_name="Délai d'exécution")

    # ── Contacts ────────────────────────────────────────────────────────────
    occupant_nom = models.CharField(max_length=150, blank=True, verbose_name="Nom occupant")
    occupant_telephone = models.CharField(max_length=20, blank=True, verbose_name="Tél. occupant")
    occupant_email = models.EmailField(blank=True, verbose_name="Email occupant")
    emetteur_nom = models.CharField(max_length=150, blank=True, verbose_name="Émetteur bailleur")
    emetteur_telephone = models.CharField(max_length=20, blank=True, verbose_name="Tél. émetteur")

    # ── Montants (confidentiels — jamais sur le BDC terrain) ────────────────
    montant_ht = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Montant HT (€)"
    )
    montant_tva = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="TVA (€)"
    )
    montant_ttc = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Montant TTC (€)"
    )

    # ── Infos manuelles (saisies par la secrétaire) ──────────────────────────
    occupation = models.CharField(
        max_length=10,
        choices=OccupationChoices.choices,
        blank=True,
        verbose_name="Vacant / Occupé",
        help_text="Obligatoire avant passage en statut 'À faire'",
    )
    modalite_acces = models.TextField(
        blank=True,
        verbose_name="Modalité d'accès",
        help_text="Clés, passes, gardien, agence...",
    )
    rdv_pris = models.BooleanField(default=False, verbose_name="RDV pris")
    rdv_date = models.DateTimeField(null=True, blank=True, verbose_name="Date / heure du RDV")
    notes = models.TextField(blank=True, verbose_name="Notes libres")

    # ── Workflow ─────────────────────────────────────────────────────────────
    statut = models.CharField(
        max_length=20,
        choices=StatutChoices.choices,
        default=StatutChoices.A_TRAITER,
        verbose_name="Statut",
    )
    sous_traitant = models.ForeignKey(
        "sous_traitants.SousTraitant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bons_de_commande",
        verbose_name="Sous-traitant",
    )
    montant_st = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant ST (€)",
        help_text="Montant attribué au sous-traitant",
    )
    pourcentage_st = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="% ST",
        help_text="Pourcentage du BDC attribué au sous-traitant",
    )
    date_realisation = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de réalisation",
        help_text="Date à laquelle les travaux ont été déclarés terminés",
    )

    # ── Fichiers ─────────────────────────────────────────────────────────────
    pdf_original = models.FileField(
        upload_to=pdf_upload_path,
        blank=True,
        verbose_name="PDF original",
        help_text="Fichier PDF du BDC tel que reçu du bailleur",
    )
    pdf_terrain = models.FileField(
        upload_to=pdf_terrain_upload_path,
        blank=True,
        verbose_name="PDF terrain",
        help_text="Version sans prix du BDC, destinée au sous-traitant",
    )

    # ── Métadonnées ──────────────────────────────────────────────────────────
    cree_par = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="bons_de_commande_crees",
        verbose_name="Créé par",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Bon de commande"
        verbose_name_plural = "Bons de commande"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"BDC {self.numero_bdc} — {self.bailleur.code} — {self.get_statut_display()}"

    @property
    def est_pret_pour_attribution(self) -> bool:
        """Vrai si le BDC est en statut À_FAIRE (prêt pour le CDT)."""
        return self.statut == StatutChoices.A_FAIRE

    @property
    def adresse_complete(self) -> str:
        """Adresse formatée pour le SMS/terrain."""
        parts = [self.adresse]
        if self.code_postal or self.ville:
            parts.append(f"{self.code_postal} {self.ville}".strip())
        return ", ".join(filter(None, parts))


# ─── LignePrestation ──────────────────────────────────────────────────────────

class LignePrestation(models.Model):
    """
    Ligne de prestation d'un BDC.
    Ex : « M-P préparation et mise en peinture — 15 m² — 11,19 €/m² — 167,85 € »
    Les prix sont confidentiels et ne doivent jamais apparaître sur le BDC terrain.
    """

    bdc = models.ForeignKey(
        BonDeCommande,
        on_delete=models.CASCADE,
        related_name="lignes_prestation",
        verbose_name="BDC",
    )
    designation = models.TextField(verbose_name="Désignation")
    quantite = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité")
    unite = models.CharField(max_length=20, blank=True, verbose_name="Unité")
    prix_unitaire = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix unitaire (€)"
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Ligne de prestation"
        verbose_name_plural = "Lignes de prestation"
        ordering = ["ordre"]

    def __str__(self) -> str:
        return f"{self.designation} — {self.quantite} {self.unite} — {self.montant} €"


# ─── HistoriqueAction ─────────────────────────────────────────────────────────

class ActionChoices(models.TextChoices):
    CREATION = "CREATION", "Création"
    MODIFICATION = "MODIFICATION", "Modification"
    STATUT_CHANGE = "STATUT_CHANGE", "Changement de statut"
    ATTRIBUTION = "ATTRIBUTION", "Attribution"
    REATTRIBUTION = "REATTRIBUTION", "Réattribution"
    NOTIFICATION_SMS = "NOTIFICATION_SMS", "SMS envoyé"
    VALIDATION = "VALIDATION", "Validation réalisation"
    FACTURATION = "FACTURATION", "Passage en facturation"


class HistoriqueAction(models.Model):
    """
    Journal d'audit de toutes les actions sur un BDC.
    Traçabilité complète : qui a fait quoi et quand.
    """

    bdc = models.ForeignKey(
        BonDeCommande,
        on_delete=models.CASCADE,
        related_name="historique",
        verbose_name="BDC",
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="actions_bdc",
        verbose_name="Utilisateur",
    )
    action = models.CharField(
        max_length=30,
        choices=ActionChoices.choices,
        verbose_name="Action",
    )
    details = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Détails",
        help_text="Informations complémentaires en JSON (ex: ancien/nouveau statut)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date / heure")

    class Meta:
        verbose_name = "Action historisée"
        verbose_name_plural = "Historique des actions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.bdc.numero_bdc} — {self.get_action_display()} par {self.utilisateur} le {self.created_at:%d/%m/%Y %H:%M}"
