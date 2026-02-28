"""
Parser PDF pour les BDC ERILIA.
Format : 2 pages — page 1 = BDC avec prestations et prix, page 2 = récapitulatif avec date d'édition.

Patterns calibrés sur le PDF modèle réel (docs/Modèle_bdc_ERILIA.pdf).
Texte pdfplumber réel :
  - Numéro : "ERILIA N° 2026 20205"
  - Marché : "Marché n° 2025 356 4 1" (espaces dans le numéro)
  - Adresse : "ADRESSE 5 RUE DE LA PETITE VITESSE"
  - Programme : "Programme 1398 LES TERRASSES DE MERCURE"
  - Émetteur : "ÉMETTEUR ARCQ GWENAEL Tél 0432743295"
  - Montants : "TOTAL H.T. 1.071,40" (virgule décimale, point milliers)
  - Date : "Édité le\n06-02-2026" (page 2)
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pdfplumber

from .base import PDFParser


class ERILIAParser(PDFParser):
    """
    Parser pour les BDC ERILIA reçus par email.
    Extrait les données depuis un PDF 2 pages (page 1 = détail, page 2 = récapitulatif + date).
    """

    BAILLEUR_CODE = "ERILIA"

    def extraire(self) -> dict[str, Any]:
        """Extrait les données du PDF ERILIA et retourne un dict normalisé."""
        texte_complet = ""

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                texte_complet += (page.extract_text() or "") + "\n"

        return {
            "bailleur_code": self.BAILLEUR_CODE,
            "numero_bdc": self._extraire_numero_bdc(texte_complet),
            "numero_marche": self._extraire_numero_marche(texte_complet),
            "date_emission": self._extraire_date_emission(texte_complet),
            "programme_residence": self._extraire_programme(texte_complet),
            "adresse": self._extraire_adresse(texte_complet),
            "code_postal": self._extraire_code_postal_apres_adresse(texte_complet),
            "ville": self._extraire_ville_apres_adresse(texte_complet),
            "logement_numero": self._extraire_champ(texte_complet, r"Logement\s+(\d+)"),
            "logement_type": "",
            "logement_etage": self._extraire_champ(
                texte_complet, r"[eé]tage\s+(\S+)"
            ),
            "logement_porte": "",
            "objet_travaux": self._extraire_objet(texte_complet),
            "delai_execution": self._extraire_delai(texte_complet),
            "occupant_nom": "",
            "occupant_telephone": "",
            "occupant_email": "",
            "emetteur_nom": self._extraire_emetteur_nom(texte_complet),
            "emetteur_telephone": self._extraire_emetteur_telephone(texte_complet),
            "montant_ht": self._extraire_montant(
                texte_complet, r"TOTAL\s+H\.T\.\s+([\d.,\s]+?)(?:\n|$)"
            ),
            "montant_tva": self._extraire_montant(
                texte_complet, r"T\.V\.A\.\s+[\d,]+\s*%\s+([\d.,\s]+?)(?:\n|$)"
            ),
            "montant_ttc": self._extraire_montant(
                texte_complet, r"TOTAL\s+T\.T\.C\.\s+([\d.,\s]+?)(?:\n|$)"
            ),
            "lignes_prestation": [],
        }

    # ── Méthodes privées d'extraction ─────────────────────────────────────────

    def _extraire_champ(self, texte: str, pattern: str) -> str:
        """Recherche un pattern et retourne le premier groupe capturé."""
        match = re.search(pattern, texte, re.IGNORECASE)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_numero_bdc(self, texte: str) -> str:
        """Extrait le numéro depuis 'ERILIA N° 2026 20205'."""
        match = re.search(r"ERILIA\s+N[°o]\s+(\d+\s+\d+)", texte)
        return match.group(1).strip() if match else ""

    def _extraire_numero_marche(self, texte: str) -> str:
        """Extrait le marché depuis 'Marché n° 2025 356 4 1'."""
        match = re.search(r"March[eé]\s+n[°o]\s+([\d\s]+\d)(?:\s+\d{5}|\s*\n)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_date_emission(self, texte: str) -> date | None:
        """Extrait la date depuis 'Édité le\\n06-02-2026' (page 2)."""
        match = re.search(r"[ÉéE]dit[eé]\s+le\s*\n?\s*(\d{2}-\d{2}-\d{4})", texte)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d-%m-%Y").date()
        except ValueError:
            return None

    def _extraire_objet(self, texte: str) -> str:
        """Extrait l'objet depuis 'Objet Récl. Tech. n° 2026/15635'."""
        match = re.search(r"Objet\s+(.+?)(?:\n|$)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_adresse(self, texte: str) -> str:
        """Extrait l'adresse depuis 'LOCALISATION ADRESSE 5 RUE DE LA PETITE VITESSE'."""
        match = re.search(r"LOCALISATION\s+ADRESSE\s+(.+?)(?:\n|$)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_code_postal_apres_adresse(self, texte: str) -> str:
        """Extrait le code postal après la ligne LOCALISATION ADRESSE."""
        idx = texte.find("LOCALISATION")
        if idx < 0:
            return ""
        remaining = texte[idx:]
        match = re.search(r"\b(\d{5})\s+[A-ZÉÈÀÂÙÎÏ]", remaining)
        return match.group(1) if match else ""

    def _extraire_ville_apres_adresse(self, texte: str) -> str:
        """Extrait la ville après la ligne LOCALISATION ADRESSE."""
        idx = texte.find("LOCALISATION")
        if idx < 0:
            return ""
        remaining = texte[idx:]
        match = re.search(
            r"\b\d{5}\s+([A-ZÉÈÀÂÙÎÏ][A-ZÉÈÀÂÙÎÏ\s\-]+?)(?:\n|$)", remaining
        )
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_programme(self, texte: str) -> str:
        """Extrait le programme depuis 'Programme 1398 LES TERRASSES DE MERCURE'."""
        match = re.search(r"Programme\s+(.+?)(?:\s+\d{5}\s+[A-Z]|\n|$)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_emetteur_nom(self, texte: str) -> str:
        """Extrait le nom émetteur depuis 'ÉMETTEUR ARCQ GWENAEL Tél 0432743295'."""
        match = re.search(r"[ÉéE]METTEUR\s+(.+?)\s+T[eé]l\s", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_emetteur_telephone(self, texte: str) -> str:
        """Extrait le téléphone émetteur depuis 'ÉMETTEUR ... Tél 0432743295'."""
        match = re.search(r"[ÉéE]METTEUR\s+.+?\s+T[eé]l\s+(\d+)", texte)
        return match.group(1).strip() if match else ""

    def _extraire_delai(self, texte: str) -> date | None:
        """Extrait la date de fin depuis 'PÉRIODE DU ... AU 15-02-2026'."""
        match = re.search(
            r"P[ÉéE]RIODE\s+DU\s+\d{2}-\d{2}-\d{4}\s+AU\s+(\d{2}-\d{2}-\d{4})",
            texte,
        )
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d-%m-%Y").date()
        except ValueError:
            return None

    def _extraire_montant(self, texte: str, pattern: str) -> Decimal | None:
        """Extrait un montant et le convertit en Decimal (format français)."""
        match = re.search(pattern, texte)
        if not match:
            return None
        valeur_str = match.group(1).strip()
        # Normalise : "1.071,40" → "1071.40"
        valeur_str = valeur_str.replace("\xa0", "").replace(" ", "").replace(",", ".")
        parts = valeur_str.rsplit(".", 1)
        if len(parts) == 2:
            valeur_str = parts[0].replace(".", "") + "." + parts[1]
        try:
            return Decimal(valeur_str).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None
