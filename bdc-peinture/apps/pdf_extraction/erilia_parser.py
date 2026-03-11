"""
Parser PDF pour les BDC ERILIA.
Format multi-pages : prestations sur N pages, récapitulatif + date d'édition en dernière page.

Patterns calibrés sur le PDF modèle réel (docs/Modèle_bdc_ERILIA.pdf).
Texte pdfplumber réel :
  - Numéro : "ERILIA N° 2026 20205"
  - Marché : "Marché n° 2025 356 4 1" (espaces dans le numéro)
  - Adresse : "ADRESSE 5 RUE DE LA PETITE VITESSE"
  - Programme : "Programme 1398 LES TERRASSES DE MERCURE"
  - Émetteur : "ÉMETTEUR ARCQ GWENAEL Tél 0432743295"
  - Montants : "TOTAL H.T. 1.071,40" (virgule décimale, point milliers)
  - Date : "Édité le\n06-02-2026" (dernière page)
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
    Extrait les données depuis un PDF multi-pages (prestations pouvant s'étaler sur N pages).
    """

    BAILLEUR_CODE = "ERILIA"

    def extraire(self) -> dict[str, Any]:
        """Extrait les données du PDF ERILIA et retourne un dict normalisé."""
        texte_complet = ""
        all_tables: list = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                texte_complet += (page.extract_text() or "") + "\n"
                all_tables.extend(page.extract_tables() or [])

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
            "logement_etage": self._extraire_champ(texte_complet, r"[eé]tage\s+(\S+)"),
            "logement_porte": "",
            "objet_travaux": self._extraire_objet(texte_complet),
            "delai_execution": self._extraire_delai(texte_complet),
            "occupant_nom": "",
            "occupant_telephone": "",
            "occupant_email": "",
            "emetteur_nom": self._extraire_emetteur_nom(texte_complet),
            "emetteur_telephone": self._extraire_emetteur_telephone(texte_complet),
            "montant_ht": self._extraire_montant(texte_complet, r"TOTAL\s+H\.T\.\s+([\d.,\s]+?)(?:\n|$)"),
            "montant_tva": self._extraire_montant(texte_complet, r"T\.V\.A\.\s+[\d,]+\s*%\s+([\d.,\s]+?)(?:\n|$)"),
            "montant_ttc": self._extraire_montant(texte_complet, r"TOTAL\s+T\.T\.C\.\s+([\d.,\s]+?)(?:\n|$)"),
            "lignes_prestation": self._extraire_lignes_prestation(all_tables),
        }

    # ── Extraction lignes de prestation ────────────────────────────────────────

    def _extraire_lignes_prestation(self, tables: list) -> list[dict]:
        """Extrait les lignes de prestation depuis la table ERILIA page 1.

        Format réel pdfplumber (cellule unique multi-lignes dans table 1) :
            Row 0: ['ARTICLE DÉSIGNATION UNITÉ QUANTITÉ PRIX UNITAIRE H.T. TOTAL T.T.C.']
            Row 1: ['PP4-31 Peinture finition A sur murs, plafond, FOR 1,00 180,27 198,30\\n
                     boiseries et métalleries - WC\\nEDL : ...\\n
                     PP4-33 Peinture finition A ...']
        """
        lignes: list[dict] = []
        cellule = self._trouver_cellule_prestations_erilia(tables)
        if not cellule:
            return lignes

        # Pattern ERILIA : code  désignation  unité  quantité  prix_ht  montant_ttc
        pattern = re.compile(
            r"^(\S+)\s+(.+?)\s+(FOR|M2|ML|U|ENS|H|F)\s+"
            r"([\d]+(?:[.,]\d+)?)\s+"
            r"([\d]+(?:[.,]\d+)?)\s+"
            r"([\d]+(?:[.,]\d+)?)$"
        )

        ligne_courante: dict | None = None
        for raw_line in cellule.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            # Ignorer les lignes EDL
            if line.startswith("EDL"):
                continue
            match = pattern.match(line)
            if match:
                if ligne_courante is not None:
                    lignes.append(ligne_courante)
                prix_unitaire = self._convertir_montant_fr(match.group(5))
                quantite = self._convertir_montant_fr(match.group(4))
                montant_ht = (prix_unitaire * quantite).quantize(Decimal("0.01"))
                ligne_courante = {
                    "code": match.group(1),
                    "designation": self._nettoyer_texte(match.group(2)),
                    "unite": match.group(3),
                    "quantite": quantite,
                    "prix_unitaire": prix_unitaire,
                    "montant_ht": montant_ht,
                    "ordre": len(lignes),
                }
            elif ligne_courante is not None:
                # Ligne de continuation de désignation
                ligne_courante["designation"] = self._nettoyer_texte(ligne_courante["designation"] + " " + line)

        if ligne_courante is not None:
            lignes.append(ligne_courante)

        return lignes

    def _trouver_cellule_prestations_erilia(self, tables: list) -> str:
        """Trouve la cellule contenant les lignes de prestation dans la table ERILIA."""
        for table in tables:
            for ri, row in enumerate(table):
                if not row:
                    continue
                cell0 = str(row[0] or "")
                if "ARTICLE" in cell0 and "SIGNATION" in cell0:
                    # La cellule suivante contient les prestations
                    if ri + 1 < len(table) and table[ri + 1]:
                        return str(table[ri + 1][0] or "")
        return ""

    def _convertir_montant_fr(self, valeur: str) -> Decimal:
        """Convertit un montant au format français (virgule) en Decimal."""
        return Decimal(valeur.replace(",", ".")).quantize(Decimal("0.01"))

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
        match = re.search(r"\b\d{5}\s+([A-ZÉÈÀÂÙÎÏ][A-ZÉÈÀÂÙÎÏ\s\-]+?)(?:\n|$)", remaining)
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
