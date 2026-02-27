"""
Parser PDF pour les BDC ERILIA.
Format : 1 page avec toutes les données et les prix — BDC terrain généré par l'app (SPEC-003).

NOTE: Les patterns regex doivent être calibrés sur des PDFs ERILIA réels.
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
    Extrait les données complètes depuis la page 1 (format tout-en-un avec prix).
    Le BDC terrain sans prix sera généré par l'app (SPEC-003).
    """

    BAILLEUR_CODE = "ERILIA"

    def extraire(self) -> dict[str, Any]:
        """Extrait les données du PDF ERILIA et retourne un dict normalisé."""
        texte_p1 = ""
        tables_p1: list = []

        with pdfplumber.open(self.pdf_path) as pdf:
            if len(pdf.pages) >= 1:
                texte_p1 = pdf.pages[0].extract_text() or ""
                tables_p1 = pdf.pages[0].extract_tables() or []
            # ERILIA PDFs peuvent avoir plusieurs pages — on prend tout le texte
            for page in pdf.pages[1:]:
                texte_p1 += "\n" + (page.extract_text() or "")
                tables_p1 += page.extract_tables() or []

        return {
            "bailleur_code": self.BAILLEUR_CODE,
            "numero_bdc": self._extraire_numero_bdc(texte_p1),
            "numero_marche": self._chercher_champ(
                texte_p1,
                r"N[°o\.]\s*March[eé]\s*[:\s]+(.+?)(?:\n|$)",
                r"March[eé]\s*[:\s]+(.+?)(?:\n|$)",
                r"[Cc]ontrat\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "date_emission": self._extraire_date(
                texte_p1,
                r"(?:Date\s*(?:d[e']?\s*)?(?:[eé]mission|commande|[eé]tablissement)|[Éé]mis\s+le)\s*[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})",
            ),
            "programme_residence": self._chercher_champ(
                texte_p1,
                r"(?:Programme|R[eé]sidence|Ensemble)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "adresse": self._chercher_champ(
                texte_p1,
                r"(?:Adresse\s*(?:des?\s*travaux)?|Lieu\s*des\s*travaux)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "code_postal": self._extraire_code_postal(texte_p1),
            "ville": self._extraire_ville(texte_p1),
            "logement_numero": self._chercher_champ(
                texte_p1,
                r"N[°o\.]\s*(?:logement|appartement|lot)\s*[:\s]+(\S+)",
            ),
            "logement_type": self._chercher_champ(
                texte_p1,
                r"Type\s*(?:de\s*)?logement\s*[:\s]+(\S+)",
                r"\b([TF]\d)\b",
            ),
            "logement_etage": self._chercher_champ(
                texte_p1,
                r"[Ée]tage\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "logement_porte": self._chercher_champ(
                texte_p1,
                r"Porte\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "objet_travaux": self._extraire_objet_travaux(texte_p1),
            "delai_execution": self._extraire_date(
                texte_p1,
                r"(?:D[eé]lai|Date\s*(?:de\s*fin|limite|d['']\s*ex[eé]cution))\s*[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})",
            ),
            "occupant_nom": self._chercher_champ(
                texte_p1,
                r"(?:Occupant|Locataire|Habitant)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "occupant_telephone": self._chercher_champ(
                texte_p1,
                r"T[eé]l\.?\s*(?:occupant|locataire)?\s*[:\s]+(0\d[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2})",
            ),
            "occupant_email": self._chercher_champ(
                texte_p1,
                r"(?:Email|Mail)\s*(?:occupant|locataire)?\s*[:\s]+([\w\.\-]+@[\w\.\-]+\.\w+)",
            ),
            "emetteur_nom": self._chercher_champ(
                texte_p1,
                r"(?:[Éé]metteur|Responsable|Charg[eé]\s*de\s*mission|Gestionnaire)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "emetteur_telephone": self._chercher_champ(
                texte_p1,
                r"T[eé]l\.?\s*[:\s]+(0\d[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2})",
            ),
            "montant_ht": self._extraire_montant(
                texte_p1,
                r"(?:Montant|Total|Prix)\s*H\.?T\.?\s*[:\s]+([\d\s\xa0,\.]+)\s*[€$]?",
            ),
            "montant_tva": self._extraire_montant(
                texte_p1,
                r"T\.?V\.?A\.?\s*(?:\d+\s*%)?\s*[:\s]+([\d\s\xa0,\.]+)\s*[€$]?",
            ),
            "montant_ttc": self._extraire_montant(
                texte_p1,
                r"(?:Montant|Total|Prix)\s*T\.?T\.?C\.?\s*[:\s]+([\d\s\xa0,\.]+)\s*[€$]?",
            ),
            "lignes_prestation": self._extraire_lignes(tables_p1),
        }

    # ── Méthodes privées d'extraction ─────────────────────────────────────────

    def _extraire_numero_bdc(self, texte: str) -> str:
        """Extrait le numéro du bon de commande ERILIA."""
        patterns = [
            r"(?:Bon\s*de\s*[Cc]ommande|BC|BDC|[Cc]ommande)\s*[Nn][°o\.]\s*[:\s]*(\S+)",
            r"[Nn][°o\.]\s*(?:Bon\s*de\s*[Cc]ommande|BC|BDC|[Cc]ommande)\s*[:\s]*(\S+)",
            r"R[eé]f[eé]rence\s*[:\s]+(\S+)",
        ]
        for pattern in patterns:
            result = self._chercher_champ(texte, pattern)
            if result:
                return result
        return ""

    def _extraire_code_postal(self, texte: str) -> str:
        match = re.search(r"\b(\d{5})\b", texte)
        return match.group(1) if match else ""

    def _extraire_ville(self, texte: str) -> str:
        match = re.search(r"\b\d{5}\s+([A-ZÉÈÀÂÙÎÏ][A-ZÉÈÀÂÙÎÏa-zéèàâùîï\s\-]+?)(?:\n|$)", texte)
        if match:
            return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_objet_travaux(self, texte: str) -> str:
        patterns = [
            r"(?:Objet|Nature)\s*(?:des\s*)?travaux\s*[:\s]+(.+?)(?:\n\n|\Z)",
            r"(?:Descriptif|Prestation\(s\)?|D[eé]signation)\s*[:\s]+(.+?)(?:\n\n|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
            if match:
                return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_date(self, texte: str, pattern: str) -> date | None:
        match = re.search(pattern, texte, re.IGNORECASE)
        if not match:
            return None
        valeur = match.group(1).strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(valeur, fmt).date()
            except ValueError:
                continue
        return None

    def _extraire_montant(self, texte: str, pattern: str) -> Decimal | None:
        valeur_str = self._chercher_champ(texte, pattern)
        if not valeur_str:
            return None
        valeur_str = valeur_str.replace("\xa0", "").replace(" ", "").replace(",", ".")
        parts = valeur_str.rsplit(".", 1)
        if len(parts) == 2:
            valeur_str = parts[0].replace(".", "") + "." + parts[1]
        try:
            return Decimal(valeur_str).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    def _chercher_champ(self, texte: str, *patterns: str) -> str:
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_lignes(self, tables: list) -> list[dict]:
        """Extrait les lignes de prestation depuis les tables pdfplumber."""
        lignes = []
        mots_entete = ("DÉSIGNATION", "DESIGNATION", "QUANTITÉ", "QUANTITE", "UNITÉ", "UNITE", "PRIX", "MONTANT")
        mots_total = ("TOTAL", "SOUS-TOTAL", "TVA", "TTC", "HT")

        for table in tables:
            if not table or len(table) < 2:
                continue
            for row in table:
                if row is None:
                    continue
                row_clean = [str(cell or "").strip() for cell in row]
                row_upper = " ".join(row_clean).upper()

                if len(row_clean) < 4:
                    continue
                if any(mot in row_upper for mot in mots_entete):
                    continue
                if any(mot in row_upper for mot in mots_total):
                    continue

                designation = row_clean[0]
                if not designation:
                    continue

                lignes.append({
                    "designation": designation,
                    "quantite": self._parse_decimal(row_clean[1] if len(row_clean) > 1 else ""),
                    "unite": row_clean[2] if len(row_clean) > 2 else "",
                    "prix_unitaire": self._parse_decimal(row_clean[3] if len(row_clean) > 3 else ""),
                    "montant": self._parse_decimal(row_clean[4] if len(row_clean) > 4 else row_clean[-1]),
                })

        return lignes

    def _parse_decimal(self, valeur: str) -> Decimal:
        if not valeur:
            return Decimal("0")
        valeur = valeur.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("€", "").strip()
        try:
            return Decimal(valeur).quantize(Decimal("0.01"))
        except InvalidOperation:
            return Decimal("0")
