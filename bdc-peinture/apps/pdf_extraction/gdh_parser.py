"""
Parser PDF pour les BDC Grand Delta Habitat (GDH).
Format : 2 pages — page 1 = BDC complet avec prix, page 2 = bon d'intervention sans prix.

Patterns calibrés sur le PDF modèle réel (docs/Modèle_bdc_GDH.pdf).
Texte pdfplumber réel :
  - En-tête : "Bon de commande\n<objet>\nn° <num> du <date>"
  - Marché : "Marché n° 026322-CPP-003"
  - Habitation dans table[0] row contenant "Habitation" (cellule gauche)
  - Occupant dans table[0] même row (cellule droite)
  - Montants : "Total HT 167.85 €" (point décimal, pas virgule)
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
    Extrait les données de la page 1 (BDC avec prix).
    La page 2 (bon d'intervention sans prix) fournit les infos occupant.
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

        texte_complet = texte_p1 + "\n" + texte_p2

        # Extraire le bloc logement/occupant depuis la table
        bloc_logement, bloc_occupant = self._extraire_blocs_table(tables_p1)

        # Extraction habitation (un seul regex multi-groupes)
        hab = self._extraire_habitation(bloc_logement or texte_complet)

        return {
            "bailleur_code": self.BAILLEUR_CODE,
            "numero_bdc": self._extraire_numero_bdc(texte_p1),
            "numero_marche": self._extraire_numero_marche(texte_p1),
            "date_emission": self._extraire_date_emission(texte_p1),
            "programme_residence": self._extraire_programme(bloc_logement or texte_complet),
            "adresse": self._extraire_adresse(bloc_logement or texte_complet),
            "code_postal": self._extraire_code_postal(bloc_logement or texte_complet),
            "ville": self._extraire_ville(bloc_logement or texte_complet),
            "logement_numero": hab["numero"],
            "logement_type": hab["type"],
            "logement_etage": hab["etage"],
            "logement_porte": hab["porte"],
            "objet_travaux": self._extraire_objet_travaux(texte_p1),
            "delai_execution": self._extraire_delai(texte_p1),
            "occupant_nom": self._extraire_occupant_nom(bloc_occupant or texte_complet),
            "occupant_telephone": self._extraire_telephone(bloc_occupant or texte_complet),
            "occupant_email": self._extraire_email(bloc_occupant or texte_complet),
            "emetteur_nom": self._extraire_emetteur_nom(texte_p1),
            "emetteur_telephone": self._extraire_emetteur_telephone(texte_p1),
            "montant_ht": self._extraire_montant(
                texte_p1, r"Total\s+HT\s+([\d.,]+)\s*[€]?"
            ),
            "montant_tva": self._extraire_montant(
                texte_p1, r"Total\s+TVA\s+[\d.,]+\s*%\s+([\d.,]+)\s*[€]?"
            ),
            "montant_ttc": self._extraire_montant(
                texte_p1, r"Total\s+TTC\s+([\d.,]+)\s*[€]?"
            ),
            "lignes_prestation": [],
        }

    # ── Extraction depuis la table ────────────────────────────────────────────

    def _extraire_blocs_table(self, tables: list) -> tuple[str, str]:
        """Extrait les cellules logement (gauche) et occupant (droite) depuis la table."""
        for table in tables:
            for row in table:
                if row and len(row) >= 2:
                    cell0 = str(row[0] or "")
                    if "Habitation" in cell0:
                        return cell0, str(row[1] or "")
        return "", ""

    # ── Extraction en-tête ────────────────────────────────────────────────────

    def _extraire_numero_bdc(self, texte: str) -> str:
        """Extrait le numéro BDC depuis 'n° 450056 du 09/02/2026'."""
        match = re.search(r"n[°o]\s+(\d+)\s+du\s+", texte)
        return match.group(1).strip() if match else ""

    def _extraire_date_emission(self, texte: str) -> date | None:
        """Extrait la date depuis 'n° 450056 du 09/02/2026'."""
        match = re.search(r"n[°o]\s+\d+\s+du\s+(\d{2}/\d{2}/\d{4})", texte)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date()
        except ValueError:
            return None

    def _extraire_numero_marche(self, texte: str) -> str:
        """Extrait le numéro de marché depuis 'Marché n° 026322-CPP-003'."""
        match = re.search(r"March[eé]\s+n[°o]\s+(.+?)(?:\n|$)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_objet_travaux(self, texte: str) -> str:
        """Extrait l'objet travaux depuis l'en-tête entre 'Bon de commande' et 'n°'."""
        match = re.search(r"Bon de commande\n(.+?)\nn[°o]", texte, re.DOTALL)
        if match:
            return self._nettoyer_texte(match.group(1))
        return ""

    def _extraire_delai(self, texte: str) -> date | None:
        """Extrait la date de délai depuis 'Prestation à réaliser pour le 20/02/2026'."""
        match = re.search(
            r"[Pp]restation\s+[àa]\s+r[eé]aliser\s+pour\s+le\s+(\d{2}/\d{2}/\d{4})",
            texte,
        )
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date()
        except ValueError:
            return None

    def _extraire_emetteur_nom(self, texte: str) -> str:
        """Extrait le nom émetteur depuis 'Emetteur : Joseph LONEGRO'."""
        match = re.search(r"Emetteur\s*:\s*(.+?)(?:\s+Mail\s*:|\n|$)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_emetteur_telephone(self, texte: str) -> str:
        """Extrait le téléphone émetteur (première ligne Tél après Emetteur)."""
        match = re.search(r"Emetteur\s*:.*\nT[eé]l\s*:\s*(\d+)", texte)
        return match.group(1).strip() if match else ""

    # ── Extraction bloc logement (table cellule gauche) ──────────────────────

    def _extraire_habitation(self, texte: str) -> dict[str, str]:
        """Parse 'Habitation n° 000756 de type Type 3, Etage 1, porte 107'."""
        result = {"numero": "", "type": "", "etage": "", "porte": ""}
        match = re.search(
            r"Habitation\s+n[°o]\s+(\d+).*?de\s+type\s+(Type\s+\d+).*?Etage\s+(\d+).*?porte\s+(\d+)",
            texte,
            re.IGNORECASE,
        )
        if match:
            result["numero"] = match.group(1)
            result["type"] = match.group(2)
            result["etage"] = match.group(3)
            result["porte"] = match.group(4)
        return result

    def _extraire_programme(self, texte: str) -> str:
        """Extrait le programme/résidence (ligne après Habitation, avant l'adresse)."""
        lines = texte.strip().split("\n")
        for i, line in enumerate(lines):
            if "Habitation" in line:
                if i + 1 < len(lines):
                    prog = lines[i + 1].strip()
                    # Retirer le code en parenthèses à la fin
                    prog = re.sub(r"\s*\([^)]+\)\s*$", "", prog)
                    return self._nettoyer_texte(prog)
        return ""

    def _extraire_adresse(self, texte: str) -> str:
        """Extrait l'adresse (ligne avant le code postal dans le bloc logement)."""
        lines = texte.strip().split("\n")
        for i, line in enumerate(lines):
            if re.match(r"\d{5}\s+[A-ZÉÈÀÂÙÎÏ]", line.strip()):
                if i > 0:
                    return self._nettoyer_texte(lines[i - 1])
        return ""

    def _extraire_code_postal(self, texte: str) -> str:
        """Extrait le code postal (5 chiffres suivi d'une ville en majuscules)."""
        match = re.search(r"\b(\d{5})\s+[A-ZÉÈÀÂÙÎÏ]", texte)
        return match.group(1) if match else ""

    def _extraire_ville(self, texte: str) -> str:
        """Extrait la ville (mot en majuscules après le code postal)."""
        match = re.search(
            r"\b\d{5}\s+([A-ZÉÈÀÂÙÎÏ][A-ZÉÈÀÂÙÎÏ\s\-]+?)(?:\n|$)", texte
        )
        if match:
            return self._nettoyer_texte(match.group(1))
        return ""

    # ── Extraction occupant (table cellule droite) ───────────────────────────

    def _extraire_occupant_nom(self, texte: str) -> str:
        """Extrait le nom occupant depuis 'Occupant actuel : MUSELLA CHRISTIANE (074143/35)'."""
        match = re.search(r"Occupant\s+actuel\s*:\s*(.+?)(?:\s*\(|\s*\n|\s*$)", texte)
        return self._nettoyer_texte(match.group(1)) if match else ""

    def _extraire_telephone(self, texte: str) -> str:
        """Extrait le téléphone occupant (Portable ou Tél)."""
        match = re.search(r"(?:Portable|T[eé]l)\s*:\s*(\d+)", texte)
        return match.group(1).strip() if match else ""

    def _extraire_email(self, texte: str) -> str:
        """Extrait l'email occupant."""
        match = re.search(r"Mail\s*:\s*([\w.\-]+@[\w.\-]+\.\w+)", texte)
        return match.group(1).strip() if match else ""

    # ── Montants ─────────────────────────────────────────────────────────────

    def _extraire_montant(self, texte: str, pattern: str) -> Decimal | None:
        """Extrait un montant et le convertit en Decimal."""
        match = re.search(pattern, texte, re.IGNORECASE)
        if not match:
            return None
        valeur_str = match.group(1).strip()
        # Normalise : "1 234,56" ou "1.234,56" → "1234.56", "167.85" → "167.85"
        valeur_str = valeur_str.replace("\xa0", "").replace(" ", "").replace(",", ".")
        parts = valeur_str.rsplit(".", 1)
        if len(parts) == 2:
            valeur_str = parts[0].replace(".", "") + "." + parts[1]
        try:
            return Decimal(valeur_str).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None
