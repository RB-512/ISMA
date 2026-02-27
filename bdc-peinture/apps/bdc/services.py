"""
Logique métier du workflow BDC.
Toute la logique de transition de statut et d'historique est ici,
jamais dans les vues ni les modèles.
"""
from django.contrib.auth.models import User

from .models import ActionChoices, BonDeCommande, HistoriqueAction, StatutChoices

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

    # Règle métier : occupation obligatoire avant passage en À_FAIRE
    if nouveau_statut == StatutChoices.A_FAIRE and not bdc.occupation:
        raise BDCIncomplet(
            "Le champ 'Vacant / Occupé' est obligatoire avant d'enregistrer le BDC en 'À faire'."
        )

    # Application du changement
    bdc.statut = nouveau_statut
    bdc.save(update_fields=["statut", "updated_at"])

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
