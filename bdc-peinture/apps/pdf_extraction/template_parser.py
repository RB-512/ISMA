"""
Parser PDF configurable par template label→champ.
Utilise le modele_extraction du Bailleur pour extraire les donnees.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pdfplumber

from .base import PDFParser

# Champs standard extractibles via template
CHAMPS_STANDARD = [
    "numero_bdc",
    "numero_marche",
    "date_emission",
    "programme_residence",
    "adresse",
    "code_postal",
    "ville",
    "logement_numero",
    "logement_type",
    "logement_etage",
    "logement_porte",
    "objet_travaux",
    "delai_execution",
    "occupant_nom",
    "occupant_telephone",
    "occupant_email",
    "emetteur_nom",
    "emetteur_telephone",
    "montant_ht",
    "montant_tva",
    "montant_ttc",
]

# Champs qui doivent etre convertis en Decimal
CHAMPS_MONTANT = {"montant_ht", "montant_tva", "montant_ttc"}

# Champs qui doivent etre convertis en date
CHAMPS_DATE = {"date_emission", "delai_execution"}


def _convertir_montant(valeur_str: str) -> Decimal | None:
    """Convertit une chaine en Decimal, gerant virgule et point."""
    if not valeur_str:
        return None
    # Nettoyer : espaces, euro, nbsp
    v = valeur_str.strip().replace("\xa0", "").replace(" ", "").replace("€", "").strip()
    if not v:
        return None
    # Si virgule et point presents : point = millier, virgule = decimal
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        v = v.replace(",", ".")
    # Supprimer separateurs milliers restants
    parts = v.rsplit(".", 1)
    if len(parts) == 2:
        v = parts[0].replace(".", "") + "." + parts[1]
    try:
        return Decimal(v).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _convertir_date(valeur_str: str):
    """Convertit une chaine en date, essayant plusieurs formats."""
    if not valeur_str:
        return None
    valeur_str = valeur_str.strip()
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(valeur_str, fmt).date()
        except ValueError:
            continue
    return None


def extraire_valeur_par_label(texte: str, label: str) -> str:
    """Cherche un label dans le texte et extrait la valeur qui suit."""
    if not label:
        return ""
    label_escaped = re.escape(label)
    # Chercher le label suivi optionnellement de : puis la valeur jusqu'a fin de ligne
    pattern = label_escaped + r"\s*:?\s*(.+?)(?:\n|$)"
    match = re.search(pattern, texte, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


class TemplateParser(PDFParser):
    """
    Parser PDF configurable via les labels definis dans Bailleur.modele_extraction.
    Pour chaque champ, cherche le label dans le texte et extrait la valeur suivante.
    """

    def __init__(self, pdf_path, bailleur):
        super().__init__(pdf_path)
        self.bailleur = bailleur
        self.modele = bailleur.modele_extraction or {}

    def extraire(self) -> dict[str, Any]:
        """Extrait les donnees du PDF en utilisant les labels configures."""
        texte_complet = self._extraire_texte_complet()

        result = {
            "bailleur_code": self.bailleur.code,
            "lignes_prestation": [],
        }

        for champ in CHAMPS_STANDARD:
            config = self.modele.get(champ, {})
            label = config.get("label", "") if isinstance(config, dict) else ""
            if not label:
                result[champ] = None if champ in CHAMPS_MONTANT | CHAMPS_DATE else ""
                continue

            valeur_brute = extraire_valeur_par_label(texte_complet, label)

            if champ in CHAMPS_MONTANT:
                result[champ] = _convertir_montant(valeur_brute)
            elif champ in CHAMPS_DATE:
                result[champ] = _convertir_date(valeur_brute)
            else:
                result[champ] = self._nettoyer_texte(valeur_brute)

        return result

    def _extraire_texte_complet(self) -> str:
        """Extrait le texte de toutes les pages du PDF."""
        pages_texte = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                texte = page.extract_text() or ""
                pages_texte.append(texte)
        return "\n".join(pages_texte)
