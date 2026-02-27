"""
Parser PDF pour les BDC Grand Delta Habitat (GDH).
Format : 2 pages — page 1 = BDC complet avec prix, page 2 = bon d'intervention sans prix.

NOTE: Les patterns regex doivent être calibrés sur des PDFs GDH réels (plateforme IKOS).
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pdfplumber

from .base import PDFParser


class GDHParser(PDFParser):
    """
    Parser pour les BDC GDH issus de la plateforme IKOS.
    Extrait les données de la page 1 du PDF.
    La page 2 (bon d'intervention sans prix) est conservée telle quelle pour le BDC terrain.
    """

    BAILLEUR_CODE = "GDH"

    def extraire(self) -> dict[str, Any]:
        """Extrait les données du PDF GDH et retourne un dict normalisé."""
        texte_p1 = ""
        texte_p2 = ""
        tables_p1: list = []

        with pdfplumber.open(self.pdf_path) as pdf:
            if len(pdf.pages) >= 1:
                texte_p1 = pdf.pages[0].extract_text() or ""
                tables_p1 = pdf.pages[0].extract_tables() or []
            if len(pdf.pages) >= 2:
                texte_p2 = pdf.pages[1].extract_text() or ""

        return {
            "bailleur_code": self.BAILLEUR_CODE,
            "numero_bdc": self._extraire_numero_bdc(texte_p1),
            "numero_marche": self._chercher_champ(
                texte_p1,
                r"N[°o\.]\s*March[eé]\s*[:\s]+(.+?)(?:\n|$)",
                r"March[eé]\s*N[°o\.]\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "date_emission": self._extraire_date(
                texte_p1,
                r"(?:Date|[Éé]mis\s+le|Le)\s*[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})",
            ),
            "programme_residence": self._chercher_champ(
                texte_p1,
                r"(?:Programme|R[eé]sidence)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "adresse": self._chercher_champ(
                texte_p1,
                r"(?:Adresse|Situ[eé][eé]?\s*au?)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "code_postal": self._extraire_code_postal(texte_p1),
            "ville": self._extraire_ville(texte_p1),
            "logement_numero": self._chercher_champ(
                texte_p1,
                r"N[°o\.]\s*(?:logement|appart\.?|appartement)\s*[:\s]+(\S+)",
                r"Logement\s*[:\s]+(\S+)",
            ),
            "logement_type": self._chercher_champ(
                texte_p1,
                r"Type\s+(?:logement|de\s+logement)\s*[:\s]+(\S+)",
                r"Type\s*[:\s]+([TF]\d)\b",
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
                r"(?:D[eé]lai|Fin\s*des?\s*travaux|Date\s*de\s*fin)\s*[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})",
            ),
            "occupant_nom": self._chercher_champ(
                texte_p2 or texte_p1,
                r"(?:Occupant|Locataire|Nom\s+occupant)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "occupant_telephone": self._chercher_champ(
                texte_p2 or texte_p1,
                r"T[eé]l\.?\s*(?:occupant)?\s*[:\s]+(0\d[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2})",
            ),
            "occupant_email": self._chercher_champ(
                texte_p2 or texte_p1,
                r"(?:Email|Mail)\s*(?:occupant)?\s*[:\s]+([\w\.\-]+@[\w\.\-]+\.\w+)",
            ),
            "emetteur_nom": self._chercher_champ(
                texte_p1,
                r"(?:[Éé]metteur|Responsable|Gestionnaire|Contact\s+bailleur)\s*[:\s]+(.+?)(?:\n|$)",
            ),
            "emetteur_telephone": self._chercher_champ(
                texte_p1,
                r"T[eé]l\.?\s*[:\s]+(0\d[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2})",
            ),
            "montant_ht": self._extraire_montant(
                texte_p1,
                r"(?:Montant|Total)\s*H\.?T\.?\s*[:\s]+([\d\s\xa0,\.]+)\s*[€$]?",
            ),
            "montant_tva": self._extraire_montant(
                texte_p1,
                r"T\.?V\.?A\.?\s*[:\s]+([\d\s\xa0,\.]+)\s*[€$]?",
            ),
            "montant_ttc": self._extraire_montant(
                texte_p1,
                r"(?:Montant|Total)\s*T\.?T\.?C\.?\s*[:\s]+([\d\s\xa0,\.]+)\s*[€$]?",
            ),
            "lignes_prestation": self._extraire_lignes(tables_p1),
        }

    # ── Méthodes privées d'extraction ─────────────────────────────────────────

    def _extraire_numero_bdc(self, texte: str) -> str:
        """Extrait le numéro du bon de commande depuis plusieurs patterns possibles."""
        patterns = [
            r"(?:Bon\s*de\s*[Cc]ommande|BC|BDC)\s*[Nn][°o\.]\s*[:\s]*(\S+)",
            r"[Nn][°o\.]\s*(?:Bon\s*de\s*[Cc]ommande|BC|BDC)\s*[:\s]*(\S+)",
            r"[Cc]ommande\s*[Nn][°o\.]\s*[:\s]*(\S+)",
        ]
        for pattern in patterns:
            result = self._chercher_champ(texte, pattern)
            if result:
                return result
        return ""

    def _extraire_code_postal(self, texte: str) -> str:
        """Extrait le code postal français (5 chiffres)."""
        match = re.search(r"\b(\d{5})\b", texte)
        return match.group(1) if match else ""

    def _extraire_ville(self, texte: str) -> str:
        """Extrait la ville depuis la ligne contenant le code postal."""
        match = re.search(r"\b\d{5}\s+([A-ZÉÈÀÂÙÎÏ][A-ZÉÈÀÂÙÎÏa-zéèàâùîï\s\-]+?)(?:\n|$)", texte)
        if match:
            return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_objet_travaux(self, texte: str) -> str:
        """Extrait la désignation des travaux (potentiellement multi-lignes)."""
        patterns = [
            r"(?:Objet|Nature)\s*(?:des\s*)?travaux\s*[:\s]+(.+?)(?:\n\n|\Z)",
            r"(?:Descriptif|Prestation\(s\)?)\s*[:\s]+(.+?)(?:\n\n|\Z)",
            r"Libell[eé]\s*[:\s]+(.+?)(?:\n\n|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
            if match:
                return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_date(self, texte: str, pattern: str) -> date | None:
        """Extrait une date depuis le texte selon le pattern donné."""
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
        """Extrait un montant et le convertit en Decimal (format français)."""
        valeur_str = self._chercher_champ(texte, pattern)
        if not valeur_str:
            return None
        # Normalise : "1 234,56" ou "1\xa0234,56" → "1234.56"
        valeur_str = valeur_str.replace("\xa0", "").replace(" ", "").replace(",", ".")
        # Si plusieurs points, garde seulement le dernier comme séparateur décimal
        parts = valeur_str.rsplit(".", 1)
        if len(parts) == 2:
            valeur_str = parts[0].replace(".", "") + "." + parts[1]
        try:
            return Decimal(valeur_str).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    def _chercher_champ(self, texte: str, *patterns: str) -> str:
        """Cherche le premier pattern qui matche et retourne le groupe capturé nettoyé."""
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_lignes(self, tables: list) -> list[dict]:
        """
        Extrait les lignes de prestation depuis les tables pdfplumber.

        Chaque table est une liste de lignes, chaque ligne est une liste de cellules.
        Colonnes attendues : Désignation | Qté | Unité | P.U. | Montant
        """
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
        """Parse une cellule numérique en Decimal (format français)."""
        if not valeur:
            return Decimal("0")
        valeur = valeur.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("€", "").strip()
        try:
            return Decimal(valeur).quantize(Decimal("0.01"))
        except InvalidOperation:
            return Decimal("0")
