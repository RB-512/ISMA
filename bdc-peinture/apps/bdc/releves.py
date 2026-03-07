"""
Service de gestion des relevés de facturation sous-traitant.
Logique métier : création, validation, anti-doublon.
"""

from django.contrib.auth.models import User
from django.db.models import Max
from django.utils import timezone

from apps.sous_traitants.models import SousTraitant

from .models import BonDeCommande, ReleveFacturation, ReleveStatutChoices, StatutChoices


class ReleveError(Exception):  # noqa: N818
    """Levée quand une opération sur un relevé est invalide."""


def _bdc_eligibles(sous_traitant: SousTraitant):
    """
    Retourne les BDC éligibles pour un nouveau relevé :
    - Attribués à ce ST
    - En statut A_FACTURER ou FACTURE
    - Non rattachés à un relevé validé
    """
    bdc_dans_releve_valide = BonDeCommande.objects.filter(
        releves_facturation__statut=ReleveStatutChoices.VALIDE,
    )
    return BonDeCommande.objects.filter(
        sous_traitant=sous_traitant,
        statut__in=[StatutChoices.A_FACTURER, StatutChoices.FACTURE],
    ).exclude(pk__in=bdc_dans_releve_valide)


def _prochain_numero(sous_traitant: SousTraitant) -> int:
    """Retourne le prochain numéro de relevé pour ce ST."""
    max_num = ReleveFacturation.objects.filter(
        sous_traitant=sous_traitant,
    ).aggregate(max_num=Max("numero"))["max_num"]
    return (max_num or 0) + 1


def creer_releve(sous_traitant: SousTraitant, utilisateur: User) -> ReleveFacturation:
    """
    Crée un relevé brouillon pour un ST avec tous les BDC éligibles.

    Raises:
        ReleveError: Si aucun BDC éligible.
    """
    eligibles = list(_bdc_eligibles(sous_traitant))
    if not eligibles:
        raise ReleveError(
            f"Aucun BDC éligible pour {sous_traitant.nom}. "
            "Tous les BDC sont déjà dans un relevé validé ou aucun BDC à facturer."
        )

    releve = ReleveFacturation.objects.create(
        numero=_prochain_numero(sous_traitant),
        sous_traitant=sous_traitant,
        cree_par=utilisateur,
    )
    releve.bdc.set(eligibles)
    return releve


def retirer_bdc_du_releve(releve: ReleveFacturation, bdc: BonDeCommande) -> None:
    """
    Retire un BDC d'un relevé brouillon.

    Raises:
        ReleveError: Si le relevé est validé.
    """
    if releve.statut == ReleveStatutChoices.VALIDE:
        raise ReleveError("Impossible de modifier un relevé déjà validé.")
    releve.bdc.remove(bdc)


def valider_releve(releve: ReleveFacturation, utilisateur: User) -> ReleveFacturation:
    """
    Valide un relevé brouillon. Les BDC sont verrouillés.

    Raises:
        ReleveError: Si le relevé est déjà validé ou vide.
    """
    if releve.statut == ReleveStatutChoices.VALIDE:
        raise ReleveError("Ce relevé est déjà validé.")

    if releve.bdc.count() == 0:
        raise ReleveError("Impossible de valider un relevé vide.")

    releve.statut = ReleveStatutChoices.VALIDE
    releve.date_validation = timezone.now()
    releve.save(update_fields=["statut", "date_validation"])
    return releve
