"""
Service de masquage PDF : prend le PDF original du bailleur
et masque les valeurs des champs configurés par des étoiles (*****).

Utilise PyMuPDF (fitz) : search_for() + add_redact_annot() + apply_redactions().
"""

import logging
from decimal import Decimal

import fitz  # PyMuPDF

from .models import BonDeCommande

logger = logging.getLogger(__name__)

# Champs BDC accessibles pour le masquage, regroupés par catégorie
CHAMPS_DISPONIBLES = {
    "Identification": [
        ("numero_bdc", "N° BDC"),
        ("numero_marche", "N° Marché"),
        ("date_emission", "Date d'émission"),
    ],
    "Montants": [
        ("montant_ht", "Montant HT"),
        ("montant_tva", "TVA"),
        ("montant_ttc", "Montant TTC"),
    ],
    "Lignes de prestation": [
        ("prix_unitaire", "Prix unitaire"),
        ("montant_ligne", "Montant ligne"),
    ],
    "Contacts": [
        ("occupant_nom", "Nom occupant"),
        ("occupant_telephone", "Tél. occupant"),
        ("occupant_email", "Email occupant"),
        ("emetteur_nom", "Émetteur bailleur"),
        ("emetteur_telephone", "Tél. émetteur"),
    ],
}


def _variantes_montant(valeur: Decimal) -> list[str]:
    """Génère les variantes de formatage d'un montant pour la recherche dans le PDF."""
    if valeur is None:
        return []
    # Normaliser à 2 décimales
    v = valeur.quantize(Decimal("0.01"))
    s = str(v)  # ex: "1234.56"
    partie_entiere, partie_decimale = s.split(".")

    variantes = set()
    # Format point décimal : 1234.56
    variantes.add(s)
    # Format virgule décimale : 1234,56
    variantes.add(f"{partie_entiere},{partie_decimale}")

    # Avec séparateur de milliers si >= 1000
    if len(partie_entiere) > 3:
        # Espace millier + virgule décimale : 1 234,56
        entier_espace = _formater_milliers(partie_entiere, " ")
        variantes.add(f"{entier_espace},{partie_decimale}")
        # Point millier + virgule décimale : 1.234,56
        entier_point = _formater_milliers(partie_entiere, ".")
        variantes.add(f"{entier_point},{partie_decimale}")

    # Sans décimales si .00
    if partie_decimale == "00":
        variantes.add(partie_entiere)
        if len(partie_entiere) > 3:
            variantes.add(_formater_milliers(partie_entiere, " "))
            variantes.add(_formater_milliers(partie_entiere, "."))

    return list(variantes)


def _formater_milliers(entier: str, sep: str) -> str:
    """Formate un entier avec un séparateur de milliers."""
    result = []
    for i, c in enumerate(reversed(entier)):
        if i > 0 and i % 3 == 0:
            result.append(sep)
        result.append(c)
    return "".join(reversed(result))


def _extraire_valeurs_champ(bdc: BonDeCommande, champ: str) -> list[str]:
    """Extrait les valeurs textuelles à chercher dans le PDF pour un champ donné."""
    valeurs = []

    if champ in ("prix_unitaire", "montant_ligne"):
        # Champs des lignes de prestation
        for ligne in bdc.lignes_prestation.all():
            if champ == "prix_unitaire" and ligne.prix_unitaire:
                valeurs.extend(_variantes_montant(ligne.prix_unitaire))
            elif champ == "montant_ligne" and ligne.montant:
                valeurs.extend(_variantes_montant(ligne.montant))
    elif champ in ("montant_ht", "montant_tva", "montant_ttc"):
        val = getattr(bdc, champ, None)
        if val is not None:
            valeurs.extend(_variantes_montant(val))
    elif champ == "date_emission":
        if bdc.date_emission:
            valeurs.append(bdc.date_emission.strftime("%d/%m/%Y"))
            valeurs.append(bdc.date_emission.strftime("%d.%m.%Y"))
            valeurs.append(bdc.date_emission.strftime("%Y-%m-%d"))
    else:
        val = getattr(bdc, champ, None)
        if val:
            valeurs.append(str(val))

    return [v for v in valeurs if v and v.strip()]


def generer_pdf_masque(bdc: BonDeCommande) -> bytes | None:
    """
    Ouvre le PDF original, masque les valeurs des champs configurés,
    retourne les bytes du PDF modifié.

    Returns None si pas de PDF original ou pas de champs à masquer.
    """
    if not bdc.pdf_original or not bdc.pdf_original.name:
        logger.warning("Pas de PDF original pour BDC %s", bdc.numero_bdc)
        return None

    champs_masques = bdc.bailleur.champs_masques if bdc.bailleur else []
    if not champs_masques:
        logger.info("Aucun champ à masquer pour BDC %s (bailleur %s)", bdc.numero_bdc, bdc.bailleur)
        return None

    # Collecter toutes les valeurs à masquer
    valeurs_a_masquer = []
    for champ in champs_masques:
        valeurs_a_masquer.extend(_extraire_valeurs_champ(bdc, champ))

    if not valeurs_a_masquer:
        logger.info("Aucune valeur à masquer trouvée pour BDC %s", bdc.numero_bdc)
        return None

    # Dédupliquer et trier par longueur décroissante (masquer les plus longs d'abord)
    valeurs_a_masquer = sorted(set(valeurs_a_masquer), key=len, reverse=True)

    # Ouvrir le PDF original
    try:
        bdc.pdf_original.open("rb")
        pdf_bytes = bdc.pdf_original.read()
        bdc.pdf_original.close()
    except Exception:
        logger.warning("Impossible de lire le PDF original pour BDC %s", bdc.numero_bdc, exc_info=True)
        return None

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    nb_masques = 0
    for page in doc:
        page_has_redactions = False
        for valeur in valeurs_a_masquer:
            occurrences = page.search_for(valeur)
            for rect in occurrences:
                page.add_redact_annot(rect, text="*****", fill=(1, 1, 1))
                nb_masques += 1
                page_has_redactions = True
        if page_has_redactions:
            page.apply_redactions()

    logger.info("PDF masqué généré pour BDC %s : %d occurrences masquées", bdc.numero_bdc, nb_masques)

    result = doc.tobytes()
    doc.close()
    return result
