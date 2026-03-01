"""
Classe abstraite de base pour les parsers PDF.
Chaque bailleur a son propre parser héritant de cette classe.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class PDFParser(ABC):
    """Parser PDF abstrait. Un parser par type de bailleur."""

    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)

    @abstractmethod
    def extraire(self) -> dict[str, Any]:
        """
        Extrait toutes les données structurées du PDF.

        Returns:
            dict avec les clés correspondant aux champs de BonDeCommande :
            - bailleur_code: str
            - numero_bdc: str
            - numero_marche: str
            - date_emission: date | None
            - objet_travaux: str
            - delai_execution: date | None
            - programme_residence: str
            - adresse: str
            - code_postal: str
            - ville: str
            - logement_numero: str
            - logement_type: str
            - logement_etage: str
            - logement_porte: str
            - occupant_nom: str
            - occupant_telephone: str
            - occupant_email: str
            - emetteur_nom: str
            - emetteur_telephone: str
            - montant_ht: Decimal | None
            - montant_tva: Decimal | None
            - montant_ttc: Decimal | None
            - lignes_prestation: list[dict]
        """
        raise NotImplementedError

    def _nettoyer_texte(self, texte: str | None) -> str:
        """Nettoie et normalise un texte extrait du PDF."""
        if not texte:
            return ""
        return " ".join(texte.strip().split())
