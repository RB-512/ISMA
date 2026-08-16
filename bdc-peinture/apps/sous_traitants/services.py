"""
Service de fusion de sous-traitants en double.

Cas réel : le même sous-traitant a été saisi deux fois avec des orthographes
différentes, et des BDC ont été attribués aux deux fiches. La charge d'un ST se
retrouve alors scindée entre deux identités.
"""

import re
import unicodedata
from collections import defaultdict

from django.db import transaction
from django.db.models import Max

from .models import SousTraitant


class FusionError(Exception):  # noqa: N818
    """Levée quand une fusion de sous-traitants est invalide."""


def nom_normalise(nom: str) -> str:
    """
    Normalise un nom pour la détection de doublons.

    « DUPONT Peinture », « dupont  peinture » et « Dupont-Péinture » donnent tous
    « dupont peinture ». Nécessaire car SousTraitant.nom est unique : un doublon ne
    peut être qu'une variante d'écriture, jamais une égalité stricte.
    """
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", nom) if unicodedata.category(c) != "Mn")
    sans_ponctuation = re.sub(r"[^\w\s]", " ", sans_accents)
    return re.sub(r"\s+", " ", sans_ponctuation).strip().casefold()


def detecter_doublons() -> list[list[SousTraitant]]:
    """Retourne les groupes de sous-traitants partageant un même nom normalisé."""
    groupes: dict[str, list[SousTraitant]] = defaultdict(list)
    for st in SousTraitant.objects.all().order_by("nom"):
        groupes[nom_normalise(st.nom)].append(st)
    return [sts for sts in groupes.values() if len(sts) > 1]


def fusionner_sous_traitants(garde: SousTraitant, doublon: SousTraitant) -> dict:
    """
    Fusionne deux fiches : tout ce qui pointe vers `doublon` est réaffecté à `garde`,
    puis `doublon` est désactivé (jamais supprimé automatiquement).

    L'ordre est essentiel. `BonDeCommande.sous_traitant` est en SET_NULL : supprimer
    ou vider la fiche avant réaffectation orphelinerait silencieusement ses BDC.
    `ReleveFacturation.sous_traitant` est en PROTECT. Une fois la réaffectation faite,
    plus rien ne pointe vers le doublon : sa suppression devient sûre, et peut donc
    être proposée à l'utilisateur.

    Returns:
        dict avec le nombre de BDC et de relevés réaffectés.

    Raises:
        FusionError: Si les deux fiches sont identiques.
    """
    from apps.bdc.models import BonDeCommande, ReleveFacturation

    if garde.pk == doublon.pk:
        raise FusionError("Impossible de fusionner un sous-traitant avec lui-même.")

    with transaction.atomic():
        nb_bdc = BonDeCommande.objects.filter(sous_traitant=doublon).update(sous_traitant=garde)

        # Les relevés sont renumérotés à la suite de ceux de la fiche conservée :
        # ReleveFacturation impose unique_together (sous_traitant, numero), donc un
        # simple update() collisionnerait si les deux fiches ont un relevé n°1.
        prochain = (ReleveFacturation.objects.filter(sous_traitant=garde).aggregate(m=Max("numero"))["m"] or 0) + 1
        releves = list(ReleveFacturation.objects.filter(sous_traitant=doublon).order_by("numero"))
        for releve in releves:
            releve.sous_traitant = garde
            releve.numero = prochain
            releve.save(update_fields=["sous_traitant", "numero"])
            prochain += 1

        doublon.actif = False
        doublon.save(update_fields=["actif"])

    return {"bdc": nb_bdc, "releves": len(releves)}
