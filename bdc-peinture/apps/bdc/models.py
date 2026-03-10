import os
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

# ─── Upload path ──────────────────────────────────────────────────────────────


def pdf_upload_path(instance: "BonDeCommande", filename: str) -> str:
    """Stocke les PDFs dans bdc/<annee>/<mois>/<numero_bdc>_<filename>."""
    today = date.today()
    basename = os.path.basename(filename)
    return f"bdc/{today.year}/{today.month:02d}/{instance.numero_bdc}_{basename}"


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
    zones_masquage = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Zones à masquer sur le PDF",
        help_text="Rectangles de masquage [{x, y, w, h, page, label}]. Coordonnées en points PDF.",
    )
    marqueur_detection = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Marqueur de détection PDF",
        help_text="Texte unique dans les PDF de ce bailleur (ex: 'ICF HABITAT')",
    )
    modele_extraction = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Modèle d'extraction PDF",
        help_text="Mapping champ → label pour extraction automatique",
    )
    pages_a_envoyer = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Pages PDF à envoyer au ST",
        help_text="Liste des numéros de page à inclure (ex: [1]). Vide = toutes les pages.",
    )
    pdf_modele = models.FileField(
        upload_to="bailleurs/modeles/",
        blank=True,
        verbose_name="PDF modèle",
    )

    class Meta:
        verbose_name = "Bailleur"
        verbose_name_plural = "Bailleurs"
        ordering = ["nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.code})"


# ─── ConfigEmail (singleton) ─────────────────────────────────────────────────


class ConfigEmail(models.Model):
    """Template email personnalisable pour les notifications ST. Singleton."""

    sujet = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Sujet du mail",
        help_text="Variables : {numero_bdc}, {adresse}, {ville}, {travaux}, {delai}",
    )
    corps = models.TextField(
        blank=True,
        verbose_name="Corps du mail",
        help_text="Variables : {numero_bdc}, {adresse}, {ville}, {travaux}, {delai}, {commentaire}",
    )

    class Meta:
        verbose_name = "Configuration email"
        verbose_name_plural = "Configuration email"

    def __str__(self):
        return "Configuration email"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ─── PrixForfaitaire (bibliothèque de prix) ────────────────────────────────


class PrixForfaitaire(models.Model):
    """Ligne de la bibliothèque de prix forfaitaires du CDT."""

    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    unite = models.CharField(max_length=20, verbose_name="Unité", help_text="u, m², ml, forfait…")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (€)")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Prix forfaitaire"
        verbose_name_plural = "Prix forfaitaires"
        ordering = ["reference"]

    def __str__(self):
        return f"{self.reference} — {self.designation} ({self.prix_unitaire} €/{self.unite})"


# ─── BonDeCommande ────────────────────────────────────────────────────────────


class StatutChoices(models.TextChoices):
    A_TRAITER = "A_TRAITER", "À contrôler"
    A_FAIRE = "A_FAIRE", "À attribuer"
    EN_COURS = "EN_COURS", "En cours"
    A_FACTURER = "A_FACTURER", "À facturer"
    FACTURE = "FACTURE", "Facturé"


class OccupationChoices(models.TextChoices):
    VACANT = "VACANT", "Vacant"
    OCCUPE = "OCCUPE", "Occupé"


class TypeAccesChoices(models.TextChoices):
    BADGE_CODE = "BADGE_CODE", "Badge / Code"
    CLE = "CLE", "Clé à récupérer"


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
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="TVA (€)")
    montant_ttc = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Montant TTC (€)"
    )

    # ── Infos manuelles (saisies par la secrétaire) ──────────────────────────
    occupation = models.CharField(
        max_length=10,
        choices=OccupationChoices.choices,
        blank=True,
        verbose_name="Vacant / Occupé",
        help_text="Obligatoire avant passage en statut 'À attribuer'",
    )
    modalite_acces = models.TextField(
        blank=True,
        verbose_name="Modalité d'accès",
        help_text="Clés, passes, gardien, agence...",
    )
    type_acces = models.CharField(
        max_length=15,
        choices=TypeAccesChoices.choices,
        blank=True,
        verbose_name="Type d'accès",
    )
    acces_complement = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Détail accès",
        help_text="Code/badge ou lieu de récupération de la clé",
    )
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
    mode_attribution = models.CharField(
        max_length=15,
        choices=[("pourcentage", "Pourcentage"), ("forfait", "Forfait")],
        blank=True,
        verbose_name="Mode d'attribution",
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
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (€)")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Ligne de prestation"
        verbose_name_plural = "Lignes de prestation"
        ordering = ["ordre"]

    def __str__(self) -> str:
        return f"{self.designation} — {self.quantite} {self.unite} — {self.montant} €"


# ─── LigneForfaitAttribution ────────────────────────────────────────────────


class LigneForfaitAttribution(models.Model):
    """Ligne de devis forfaitaire attribuée à un BDC (mode forfait)."""

    bdc = models.ForeignKey(
        BonDeCommande,
        on_delete=models.CASCADE,
        related_name="lignes_forfait",
        verbose_name="BDC",
    )
    prix_forfaitaire = models.ForeignKey(
        PrixForfaitaire,
        on_delete=models.PROTECT,
        verbose_name="Prix forfaitaire",
    )
    quantite = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix unitaire (€)",
        help_text="Pré-rempli depuis la bibliothèque, modifiable",
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")

    class Meta:
        verbose_name = "Ligne forfait attribution"
        verbose_name_plural = "Lignes forfait attribution"

    def __str__(self):
        return f"{self.prix_forfaitaire.reference} × {self.quantite} = {self.montant} €"


# ─── ChecklistItem / ChecklistResultat ────────────────────────────────────────


class TransitionChoices(models.TextChoices):
    CONTROLE = "A_TRAITER__A_FAIRE", "Contrôle → À attribuer"
    ATTRIBUTION = "A_FAIRE__EN_COURS", "Attribution → En cours"
    REALISATION = "EN_COURS__A_FACTURER", "Réalisation → À facturer"
    FACTURATION = "A_FACTURER__FACTURE", "Facturation → Facturé"


class ChecklistItem(models.Model):
    """
    Item de checklist de contrôle configurable.
    Associé à une transition spécifique du workflow.
    """

    libelle = models.CharField(max_length=200)
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)
    transition = models.CharField(
        max_length=30,
        choices=TransitionChoices.choices,
        default=TransitionChoices.CONTROLE,
    )

    class Meta:
        ordering = ["transition", "ordre"]
        verbose_name = "Item de checklist"
        verbose_name_plural = "Items de checklist"

    def __str__(self):
        return self.libelle


class ChecklistResultat(models.Model):
    """Résultat d'un item de checklist pour un BDC donné."""

    bdc = models.ForeignKey(BonDeCommande, on_delete=models.CASCADE, related_name="checklist_resultats")
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    coche = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ("bdc", "item")
        verbose_name = "Résultat checklist"

    def __str__(self):
        return f"{self.item.libelle} — {'Oui' if self.coche else 'Non'}"


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
    RENVOI = "RENVOI", "Renvoi au contrôle"


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


# ─── ReleveFacturation ───────────────────────────────────────────────────────


class ReleveStatutChoices(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    VALIDE = "VALIDE", "Validé"


class ReleveFacturation(models.Model):
    """
    Relevé de facturation regroupant les BDC réalisés par un sous-traitant.
    Workflow : BROUILLON → VALIDE.
    Un BDC ne peut appartenir qu'à un seul relevé validé (anti-doublon).
    """

    numero = models.PositiveIntegerField(verbose_name="N° Relevé")
    sous_traitant = models.ForeignKey(
        "sous_traitants.SousTraitant",
        on_delete=models.PROTECT,
        related_name="releves_facturation",
        verbose_name="Sous-traitant",
    )
    statut = models.CharField(
        max_length=10,
        choices=ReleveStatutChoices.choices,
        default=ReleveStatutChoices.BROUILLON,
        verbose_name="Statut",
    )
    bdc = models.ManyToManyField(
        BonDeCommande,
        blank=True,
        related_name="releves_facturation",
        verbose_name="Bons de commande",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    cree_par = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="releves_crees",
        verbose_name="Créé par",
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Validé le")

    class Meta:
        verbose_name = "Relevé de facturation"
        verbose_name_plural = "Relevés de facturation"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Relevé n°{self.numero} — {self.sous_traitant.nom}"

    @property
    def montant_total(self):
        result = self.bdc.aggregate(total=models.Sum("montant_st"))["total"]
        return result or Decimal("0")

    @property
    def nb_bdc(self):
        return self.bdc.count()

    @property
    def periode(self):
        agg = self.bdc.aggregate(
            debut=models.Min("date_realisation"),
            fin=models.Max("date_realisation"),
        )
        return agg["debut"], agg["fin"]
