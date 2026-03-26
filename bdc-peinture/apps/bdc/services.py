"""
Logique métier du workflow BDC.
Toute la logique de transition de statut et d'historique est ici,
jamais dans les vues ni les modèles.
"""

import logging
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction

from apps.sous_traitants.models import SousTraitant

from .models import (
    ActionChoices,
    BonDeCommande,
    ChecklistItem,
    HistoriqueAction,
    LigneForfaitAttribution,
    StatutChoices,
    TransitionChoices,
)

logger = logging.getLogger(__name__)

# ─── Dictionnaire de transitions autorisées ───────────────────────────────────

TRANSITIONS: dict[str, list[str]] = {
    StatutChoices.A_TRAITER: [StatutChoices.A_FAIRE],
    StatutChoices.A_FAIRE: [StatutChoices.A_TRAITER, StatutChoices.EN_COURS],
    StatutChoices.EN_COURS: [StatutChoices.A_FAIRE, StatutChoices.A_FACTURER],
    StatutChoices.A_FACTURER: [StatutChoices.EN_COURS, StatutChoices.FACTURE],
    StatutChoices.FACTURE: [],  # état terminal
}


# ─── Exceptions ───────────────────────────────────────────────────────────────


class TransitionInvalide(Exception):  # noqa: N818
    """Levée quand une transition de statut n'est pas autorisée."""


class BDCIncomplet(Exception):  # noqa: N818
    """Levée quand un BDC ne remplit pas les conditions pour changer de statut."""


def _verifier_checklist_transition(bdc, ancien_statut, nouveau_statut):
    """Vérifie que tous les items de checklist sont cochés pour une transition donnée."""
    transition_key = f"{ancien_statut}__{nouveau_statut}"
    if transition_key not in TransitionChoices.values:
        return
    items_actifs = ChecklistItem.objects.filter(actif=True, transition=transition_key).count()
    if items_actifs > 0:
        items_coches = bdc.checklist_resultats.filter(
            item__actif=True, item__transition=transition_key, coche=True
        ).count()
        if items_coches < items_actifs:
            raise BDCIncomplet("Tous les points de contrôle doivent être cochés.")


# ─── Fonctions de service ─────────────────────────────────────────────────────


def changer_statut(bdc: BonDeCommande, nouveau_statut: str, utilisateur: User) -> BonDeCommande:
    """
    Fait passer un BDC à un nouveau statut après validation des règles métier.

    Args:
        bdc: Le BDC à modifier
        nouveau_statut: La valeur cible (une des constantes StatutChoices)
        utilisateur: L'utilisateur qui effectue l'action

    Returns:
        Le BDC modifié et sauvegardé

    Raises:
        TransitionInvalide: Si la transition n'est pas autorisée depuis le statut actuel
        BDCIncomplet: Si les conditions métier ne sont pas remplies (ex: vacant/occupé manquant)
    """
    ancien_statut = bdc.statut

    # Validation : transition autorisée ?
    transitions_possibles = TRANSITIONS.get(ancien_statut, [])
    if nouveau_statut not in transitions_possibles:
        raise TransitionInvalide(
            f"Transition '{ancien_statut}' → '{nouveau_statut}' non autorisée. "
            f"Transitions possibles depuis '{ancien_statut}' : {transitions_possibles or ['aucune (état terminal)']}"
        )

    # Règles métier : champs obligatoires avant passage en À_FAIRE (À attribuer)
    if nouveau_statut == StatutChoices.A_FAIRE:
        if not bdc.occupation:
            raise BDCIncomplet("Le champ 'Vacant / Occupé' est obligatoire avant passage en 'À attribuer'.")
        if bdc.occupation == "VACANT" and not bdc.type_acces:
            raise BDCIncomplet("Le type d'accès est obligatoire avant passage en 'À attribuer'.")
        if bdc.occupation == "OCCUPE" and not bdc.rdv_date:
            raise BDCIncomplet(
                "La date de RDV est obligatoire pour un logement occupé avant passage en 'À attribuer'."
            )
        _verifier_checklist_transition(bdc, ancien_statut, nouveau_statut)

    with transaction.atomic():
        # Règle métier : retour A_FACTURER → EN_COURS remet date_realisation à null
        if ancien_statut == StatutChoices.A_FACTURER and nouveau_statut == StatutChoices.EN_COURS:
            bdc.date_realisation = None

        # Application du changement
        bdc.statut = nouveau_statut
        bdc.save(update_fields=["statut", "date_realisation", "updated_at"])

        # Traçabilité
        HistoriqueAction.objects.create(
            bdc=bdc,
            utilisateur=utilisateur,
            action=ActionChoices.STATUT_CHANGE,
            details={
                "ancien_statut": ancien_statut,
                "nouveau_statut": nouveau_statut,
            },
        )

    return bdc


def enregistrer_action(
    bdc: BonDeCommande,
    utilisateur: User,
    action: str,
    details: dict | None = None,
) -> HistoriqueAction:
    """
    Enregistre une action dans l'historique sans changer le statut.

    Args:
        bdc: Le BDC concerné
        utilisateur: L'utilisateur qui effectue l'action
        action: Une des constantes ActionChoices
        details: Données complémentaires en JSON (optionnel)

    Returns:
        L'entrée HistoriqueAction créée
    """
    return HistoriqueAction.objects.create(
        bdc=bdc,
        utilisateur=utilisateur,
        action=action,
        details=details,
    )


# ─── Validation réalisation / Facturation ────────────────────────────────────


def valider_realisation(bdc: BonDeCommande, utilisateur: User) -> BonDeCommande:
    """
    Marque un BDC EN_COURS comme réalisé → A_FACTURER.
    Remplit date_realisation et trace l'action VALIDATION.
    """
    if bdc.statut != StatutChoices.EN_COURS:
        raise TransitionInvalide(
            f"Validation impossible : le BDC est en '{bdc.get_statut_display()}', il doit être en 'En cours'."
        )

    _verifier_checklist_transition(bdc, StatutChoices.EN_COURS, StatutChoices.A_FACTURER)

    with transaction.atomic():
        bdc.statut = StatutChoices.A_FACTURER
        bdc.date_realisation = date.today()
        bdc.save(update_fields=["statut", "date_realisation", "updated_at"])

        HistoriqueAction.objects.create(
            bdc=bdc,
            utilisateur=utilisateur,
            action=ActionChoices.VALIDATION,
            details={"date_realisation": str(bdc.date_realisation)},
        )

    return bdc


def valider_facturation(bdc: BonDeCommande, utilisateur: User) -> BonDeCommande:
    """
    Passe un BDC A_FACTURER au statut FACTURE.
    Trace l'action FACTURATION.
    """
    if bdc.statut != StatutChoices.A_FACTURER:
        raise TransitionInvalide(
            f"Facturation impossible : le BDC est en '{bdc.get_statut_display()}', il doit être en 'À facturer'."
        )

    _verifier_checklist_transition(bdc, StatutChoices.A_FACTURER, StatutChoices.FACTURE)

    with transaction.atomic():
        bdc.statut = StatutChoices.FACTURE
        bdc.save(update_fields=["statut", "updated_at"])

        HistoriqueAction.objects.create(
            bdc=bdc,
            utilisateur=utilisateur,
            action=ActionChoices.FACTURATION,
        )

    return bdc


def renvoyer_controle(bdc: BonDeCommande, commentaire: str, utilisateur: User) -> BonDeCommande:
    """
    Renvoie un BDC A_FAIRE au contrôle (A_TRAITER) avec un commentaire du CDT.
    """
    if bdc.statut != StatutChoices.A_FAIRE:
        raise TransitionInvalide(
            f"Renvoi impossible : le BDC est en '{bdc.get_statut_display()}', il doit être en 'À attribuer'."
        )

    with transaction.atomic():
        bdc.statut = StatutChoices.A_TRAITER
        bdc.save(update_fields=["statut", "updated_at"])

        HistoriqueAction.objects.create(
            bdc=bdc,
            utilisateur=utilisateur,
            action=ActionChoices.RENVOI,
            details={"commentaire": commentaire},
        )

    return bdc


# ─── Attribution / Réattribution ─────────────────────────────────────────────


def _calculer_montant_st(bdc: BonDeCommande, pourcentage: Decimal) -> Decimal | None:
    if bdc.montant_ht is None:
        return None
    return (bdc.montant_ht * pourcentage / Decimal("100")).quantize(Decimal("0.01"))


def attribuer_st(
    bdc: BonDeCommande,
    sous_traitant: SousTraitant,
    pourcentage: Decimal | None,
    utilisateur: User,
    commentaire: str = "",
    mode: str = "pourcentage",
    lignes_forfait: list[dict] | None = None,
    joindre_bdc: bool = True,
) -> BonDeCommande:
    """
    Attribue un BDC à un sous-traitant. Le BDC doit être en statut A_FAIRE.
    Passe le statut en EN_COURS et trace l'attribution.
    """
    if bdc.statut != StatutChoices.A_FAIRE:
        raise TransitionInvalide(
            f"Attribution impossible : le BDC est en '{bdc.get_statut_display()}', il doit être en 'À attribuer'."
        )

    _verifier_checklist_transition(bdc, StatutChoices.A_FAIRE, StatutChoices.EN_COURS)

    with transaction.atomic():
        bdc.sous_traitant = sous_traitant
        bdc.mode_attribution = mode

        if mode == "forfait" and lignes_forfait:
            bdc.lignes_forfait.all().delete()
            total = Decimal("0")
            for ligne in lignes_forfait:
                montant_ligne = (ligne["quantite"] * ligne["prix_unitaire"]).quantize(Decimal("0.01"))
                LigneForfaitAttribution.objects.create(
                    bdc=bdc,
                    prix_forfaitaire_id=ligne["prix_id"],
                    quantite=ligne["quantite"],
                    prix_unitaire=ligne["prix_unitaire"],
                    montant=montant_ligne,
                )
                total += montant_ligne
            bdc.montant_st = total
            if bdc.montant_ht and bdc.montant_ht > 0:
                bdc.pourcentage_st = (total / bdc.montant_ht * Decimal("100")).quantize(Decimal("0.01"))
            else:
                bdc.pourcentage_st = None
        else:
            bdc.pourcentage_st = pourcentage
            bdc.montant_st = _calculer_montant_st(bdc, pourcentage)

        bdc.statut = StatutChoices.EN_COURS
        bdc.save(
            update_fields=[
                "sous_traitant",
                "pourcentage_st",
                "montant_st",
                "mode_attribution",
                "statut",
                "updated_at",
            ]
        )

        HistoriqueAction.objects.create(
            bdc=bdc,
            utilisateur=utilisateur,
            action=ActionChoices.ATTRIBUTION,
            details={
                "sous_traitant": str(sous_traitant),
                "pourcentage": str(pourcentage),
                "montant_st": str(bdc.montant_st) if bdc.montant_st else None,
            },
        )

    _notifier_st_si_possible(bdc, commentaire=commentaire, joindre_bdc=joindre_bdc)

    return bdc


def reattribuer_st(
    bdc: BonDeCommande,
    nouveau_st: SousTraitant,
    pourcentage: Decimal | None,
    utilisateur: User,
    commentaire: str = "",
    mode: str = "pourcentage",
    lignes_forfait: list[dict] | None = None,
    joindre_bdc: bool = True,
) -> BonDeCommande:
    """
    Réattribue un BDC en cours à un autre sous-traitant.
    Le statut reste EN_COURS. Trace l'ancien et le nouveau ST.
    """
    if bdc.statut != StatutChoices.EN_COURS:
        raise TransitionInvalide(
            f"Réattribution impossible : le BDC est en '{bdc.get_statut_display()}', il doit être en 'En cours'."
        )

    ancien_st = str(bdc.sous_traitant) if bdc.sous_traitant else ""
    ancien_st_telephone = bdc.sous_traitant.telephone if bdc.sous_traitant else ""
    ancien_st_email = bdc.sous_traitant.email if bdc.sous_traitant else ""

    with transaction.atomic():
        bdc.sous_traitant = nouveau_st
        bdc.mode_attribution = mode

        if mode == "forfait" and lignes_forfait:
            bdc.lignes_forfait.all().delete()
            total = Decimal("0")
            for ligne in lignes_forfait:
                montant_ligne = (ligne["quantite"] * ligne["prix_unitaire"]).quantize(Decimal("0.01"))
                LigneForfaitAttribution.objects.create(
                    bdc=bdc,
                    prix_forfaitaire_id=ligne["prix_id"],
                    quantite=ligne["quantite"],
                    prix_unitaire=ligne["prix_unitaire"],
                    montant=montant_ligne,
                )
                total += montant_ligne
            bdc.montant_st = total
            if bdc.montant_ht and bdc.montant_ht > 0:
                bdc.pourcentage_st = (total / bdc.montant_ht * Decimal("100")).quantize(Decimal("0.01"))
            else:
                bdc.pourcentage_st = None
        else:
            bdc.pourcentage_st = pourcentage
            bdc.montant_st = _calculer_montant_st(bdc, pourcentage)

        bdc.save(
            update_fields=[
                "sous_traitant",
                "pourcentage_st",
                "montant_st",
                "mode_attribution",
                "updated_at",
            ]
        )

        HistoriqueAction.objects.create(
            bdc=bdc,
            utilisateur=utilisateur,
            action=ActionChoices.REATTRIBUTION,
            details={
                "ancien_st": ancien_st,
                "nouveau_st": str(nouveau_st),
                "pourcentage": str(pourcentage),
            },
        )

    _notifier_reattribution_si_possible(bdc, ancien_st_telephone, ancien_st_email, commentaire=commentaire, joindre_bdc=joindre_bdc)

    return bdc


def _notifier_st_si_possible(bdc: BonDeCommande, commentaire: str = "", joindre_bdc: bool = True) -> None:
    """Envoie les notifications SMS et email au ST, non-bloquant."""
    try:
        from apps.notifications.sms import envoyer_sms_attribution

        envoyer_sms_attribution(bdc)
    except Exception:
        logger.warning("Échec SMS attribution BDC %s", bdc.numero_bdc, exc_info=True)

    try:
        from apps.notifications.email import envoyer_email_attribution

        envoyer_email_attribution(bdc, commentaire=commentaire, joindre_bdc=joindre_bdc)
    except Exception:
        logger.warning("Échec email attribution BDC %s", bdc.numero_bdc, exc_info=True)


def _notifier_reattribution_si_possible(
    bdc: BonDeCommande, ancien_st_telephone: str, ancien_st_email: str, commentaire: str = "", joindre_bdc: bool = True
) -> None:
    """Envoie les notifications de réattribution, non-bloquant."""
    try:
        from apps.notifications.sms import envoyer_sms_reattribution

        envoyer_sms_reattribution(bdc, ancien_st_telephone)
    except Exception:
        logger.warning("Échec SMS réattribution BDC %s", bdc.numero_bdc, exc_info=True)

    try:
        from apps.notifications.email import envoyer_email_reattribution

        envoyer_email_reattribution(bdc, ancien_st_email, commentaire=commentaire, joindre_bdc=joindre_bdc)
    except Exception:
        logger.warning("Échec email réattribution BDC %s", bdc.numero_bdc, exc_info=True)
