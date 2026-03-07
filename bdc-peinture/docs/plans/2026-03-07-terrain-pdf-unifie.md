# Processus unifie PDF terrain — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remplacer les deux strategies terrain (GDH extraction page 2 / ERILIA WeasyPrint) par un processus unique qui genere le PDF terrain depuis les donnees en base avec PyMuPDF.

**Architecture:** Une seule fonction `_generer_pdf_terrain_pymupdf(bdc)` construit un PDF propre avec PyMuPDF : en-tete bailleur, sections localisation/travaux/occupant/prestations, mention "SANS PRIX". Plus de dispatch par bailleur, plus de WeasyPrint, plus de regex d'anonymisation.

**Tech Stack:** PyMuPDF (fitz), pytest, Django ORM

---

### Task 1: Ecrire les tests pour le nouveau generateur unifie

**Files:**
- Modify: `tests/test_bdc/test_terrain.py`

**Step 1: Ecrire les tests RED**

Remplacer les classes `TestGenererTerrainGDH`, `TestAnonymisationTerrainGDH`, `TestGenererTerrainERILIA` par une classe unique `TestGenererPdfTerrainUnifie` qui teste le nouveau comportement.

```python
# Dans test_terrain.py, remplacer les helpers et classes 7.1/7.1b/7.2 par :

def _extraire_texte_terrain(bdc) -> str:
    """Helper : genere le terrain et retourne le texte du PDF."""
    from apps.bdc.terrain import generer_pdf_terrain
    bdc = generer_pdf_terrain(bdc)
    doc = fitz.open(stream=bdc.pdf_terrain.read(), filetype="pdf")
    texte = doc[0].get_text()
    doc.close()
    return texte


class TestGenererPdfTerrainUnifie:
    """Tests du generateur unifie PyMuPDF (remplace GDH + ERILIA)."""

    def test_pdf_genere_et_stocke(self, bdc_a_faire):
        """Le PDF terrain est genere et stocke sur le BDC."""
        from apps.bdc.terrain import generer_pdf_terrain
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_pdf_une_seule_page(self, bdc_a_faire):
        """Le PDF terrain fait une seule page."""
        from apps.bdc.terrain import generer_pdf_terrain
        bdc = generer_pdf_terrain(bdc_a_faire)
        doc = fitz.open(stream=bdc.pdf_terrain.read(), filetype="pdf")
        assert len(doc) == 1
        doc.close()

    def test_nom_bailleur_en_entete(self, bdc_a_faire):
        """Le nom du bailleur apparait en en-tete."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "Grand Delta Habitat" in texte or "GRAND DELTA HABITAT" in texte

    def test_numero_bdc_present(self, bdc_a_faire):
        """Le numero BDC apparait dans le PDF."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert bdc_a_faire.numero_bdc in texte

    def test_adresse_presente(self, bdc_a_faire):
        """L'adresse du chantier apparait."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert bdc_a_faire.adresse in texte
        assert bdc_a_faire.ville in texte

    def test_objet_travaux_present(self, bdc_a_faire):
        """L'objet des travaux apparait."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert bdc_a_faire.objet_travaux in texte

    def test_occupant_present(self, bdc_a_faire):
        """Le contact occupant (nom + tel) apparait."""
        bdc_a_faire.occupant_nom = "MUSELLA CHRISTIANE"
        bdc_a_faire.occupant_telephone = "0612345678"
        bdc_a_faire.save(update_fields=["occupant_nom", "occupant_telephone"])
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "MUSELLA" in texte
        assert "0612345678" in texte

    def test_prestations_sans_prix(self, bdc_a_faire):
        """Les prestations apparaissent (designation, quantite, unite) SANS prix."""
        LignePrestation.objects.create(
            bdc=bdc_a_faire,
            designation="Peinture SDB",
            quantite=Decimal("15"),
            unite="m2",
            prix_unitaire=Decimal("11.19"),
            montant=Decimal("167.85"),
            ordre=0,
        )
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "Peinture SDB" in texte
        assert "15" in texte
        assert "11.19" not in texte
        assert "167.85" not in texte

    def test_montants_bdc_absents(self, bdc_a_faire):
        """Les montants globaux du BDC n'apparaissent pas."""
        bdc_a_faire.montant_ht = Decimal("1071.40")
        bdc_a_faire.montant_tva = Decimal("107.14")
        bdc_a_faire.montant_ttc = Decimal("1178.54")
        bdc_a_faire.save(update_fields=["montant_ht", "montant_tva", "montant_ttc"])
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "1071" not in texte
        assert "1178" not in texte

    def test_contact_emetteur_absent(self, bdc_a_faire):
        """Le telephone et email de l'emetteur n'apparaissent pas."""
        bdc_a_faire.emetteur_nom = "Joseph LONEGRO"
        bdc_a_faire.emetteur_telephone = "0490272800"
        bdc_a_faire.save(update_fields=["emetteur_nom", "emetteur_telephone"])
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "0490272800" not in texte

    def test_mention_sans_prix(self, bdc_a_faire):
        """La mention DOCUMENT TERRAIN SANS PRIX apparait."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "SANS PRIX" in texte

    def test_fonctionne_bailleur_gdh(self, bdc_a_faire):
        """Fonctionne pour un BDC GDH (plus besoin de pdf_original)."""
        from apps.bdc.terrain import generer_pdf_terrain
        assert bdc_a_faire.bailleur.code == "GDH"
        assert not bdc_a_faire.pdf_original  # pas de PDF original necessaire
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain

    def test_fonctionne_bailleur_erilia(self, bdc_a_faire, bailleur_erilia):
        """Fonctionne pour un BDC ERILIA."""
        from apps.bdc.terrain import generer_pdf_terrain
        bdc_a_faire.bailleur = bailleur_erilia
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain

    def test_fonctionne_bailleur_inconnu(self, bdc_a_faire):
        """Fonctionne pour n'importe quel bailleur."""
        from apps.bdc.models import Bailleur
        from apps.bdc.terrain import generer_pdf_terrain
        autre = Bailleur.objects.create(nom="Nouveau Bailleur", code="NB")
        bdc_a_faire.bailleur = autre
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "Nouveau Bailleur" in texte
```

**Step 2: Lancer les tests pour verifier qu'ils echouent**

Run: `uv run pytest tests/test_bdc/test_terrain.py::TestGenererPdfTerrainUnifie -v --tb=short`
Expected: FAIL (les anciens generateurs ne produisent pas le bon format)

---

### Task 2: Reecrire terrain.py avec le generateur unifie

**Files:**
- Modify: `apps/bdc/terrain.py`

**Step 3: Implementer le generateur unifie**

Remplacer tout le contenu de `terrain.py` par :

```python
"""
Generation du PDF terrain (sans prix) pour les sous-traitants.

Strategie unique : generation PyMuPDF depuis les donnees en base.
Fonctionne pour tous les bailleurs sans configuration specifique.
"""

import logging

import fitz  # PyMuPDF
from django.core.files.base import ContentFile

from .models import BonDeCommande

logger = logging.getLogger(__name__)


class GenerationTerrainError(Exception):
    """Levee quand la generation du PDF terrain echoue."""


# ─── Constantes mise en page ────────────────────────────────────────────────

_MARGE_G = 50       # marge gauche
_MARGE_D = 50       # marge droite
_Y_START = 60       # debut du contenu
_INTERLIGNE = 16    # espacement entre lignes
_SECTION_GAP = 12   # espace supplementaire entre sections


def _draw_section_title(page: fitz.Page, y: float, titre: str, width: float) -> float:
    """Dessine un titre de section avec une ligne de separation. Retourne le nouveau y."""
    y += _SECTION_GAP
    page.insert_text((_MARGE_G, y), titre.upper(), fontsize=9, fontname="helv", color=(0.33, 0.33, 0.33))
    y += 4
    page.draw_line(
        fitz.Point(_MARGE_G, y),
        fitz.Point(width - _MARGE_D, y),
        color=(0.8, 0.8, 0.8),
        width=0.5,
    )
    y += _INTERLIGNE
    return y


def _draw_field(page: fitz.Page, y: float, label: str, valeur: str) -> float:
    """Dessine un champ label: valeur. Retourne le nouveau y."""
    if not valeur:
        return y
    page.insert_text((_MARGE_G, y), f"{label} : ", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))
    # Calculer la position apres le label
    label_width = fitz.get_text_length(f"{label} : ", fontsize=10, fontname="helv")
    page.insert_text((_MARGE_G + label_width, y), valeur, fontsize=10, fontname="helv")
    y += _INTERLIGNE
    return y


def _generer_pdf_terrain_pymupdf(bdc: BonDeCommande) -> bytes:
    """
    Genere un PDF terrain (sans prix) depuis les donnees en base.

    Contenu :
    - En-tete : nom bailleur + numero BDC
    - Localisation : adresse, residence, logement, occupation, acces
    - Travaux : objet, delai
    - Contact occupant : nom, telephone
    - Prestations : designation, quantite, unite (SANS PRIX)
    - Mention DOCUMENT TERRAIN — SANS PRIX
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    width = page.rect.width
    y = _Y_START

    # ── En-tete ──────────────────────────────────────────────────────────
    bailleur_nom = bdc.bailleur.nom.upper() if bdc.bailleur else "BAILLEUR"
    page.insert_text((_MARGE_G, y), bailleur_nom, fontsize=14, fontname="helv", color=(0.1, 0.1, 0.1))
    y += 22
    page.insert_text((_MARGE_G, y), f"BDC Terrain N\u00b0 {bdc.numero_bdc}", fontsize=12, fontname="helv")
    y += 8
    if bdc.numero_marche:
        page.insert_text((_MARGE_G, y + _INTERLIGNE), f"March\u00e9 {bdc.numero_marche}", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))
        y += _INTERLIGNE
    # Ligne de separation en-tete
    y += 8
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=1)
    y += _INTERLIGNE

    # ── Localisation ─────────────────────────────────────────────────────
    y = _draw_section_title(page, y, "Localisation", width)
    y = _draw_field(page, y, "Adresse", bdc.adresse_complete)
    y = _draw_field(page, y, "R\u00e9sidence", bdc.programme_residence)
    if bdc.logement_numero:
        logement = bdc.logement_type or ""
        if bdc.logement_numero:
            logement += f" n\u00b0{bdc.logement_numero}"
        if bdc.logement_etage:
            logement += f" \u2014 \u00c9tage {bdc.logement_etage}"
        if bdc.logement_porte:
            logement += f" / Porte {bdc.logement_porte}"
        y = _draw_field(page, y, "Logement", logement.strip())
    if bdc.occupation:
        y = _draw_field(page, y, "Occupation", bdc.get_occupation_display())
    y = _draw_field(page, y, "Acc\u00e8s", bdc.modalite_acces)

    # ── Travaux ──────────────────────────────────────────────────────────
    y = _draw_section_title(page, y, "Travaux", width)
    y = _draw_field(page, y, "Objet", bdc.objet_travaux)
    if bdc.delai_execution:
        y = _draw_field(page, y, "D\u00e9lai", bdc.delai_execution.strftime("%d/%m/%Y"))

    # ── Contact occupant ─────────────────────────────────────────────────
    if bdc.occupant_nom or bdc.occupant_telephone:
        y = _draw_section_title(page, y, "Contact occupant", width)
        y = _draw_field(page, y, "Nom", bdc.occupant_nom)
        y = _draw_field(page, y, "T\u00e9l\u00e9phone", bdc.occupant_telephone)

    # ── Prestations (SANS PRIX) ──────────────────────────────────────────
    lignes = list(bdc.lignes_prestation.all().order_by("ordre"))
    if lignes:
        y = _draw_section_title(page, y, "Prestations", width)
        # En-tete tableau
        col_x = [_MARGE_G, width - _MARGE_D - 100, width - _MARGE_D - 40]
        page.insert_text((col_x[0], y), "D\u00e9signation", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        page.insert_text((col_x[1], y), "Qt\u00e9", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        page.insert_text((col_x[2], y), "Unit\u00e9", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 4
        page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.85, 0.85, 0.85), width=0.5)
        y += _INTERLIGNE - 2

        for ligne in lignes:
            designation = str(ligne.designation)
            # Tronquer si trop long pour une ligne
            max_len = 60
            if len(designation) > max_len:
                designation = designation[:max_len - 3] + "..."
            page.insert_text((col_x[0], y), designation, fontsize=9, fontname="helv")
            page.insert_text((col_x[1], y), str(ligne.quantite.normalize()), fontsize=9, fontname="helv")
            page.insert_text((col_x[2], y), ligne.unite or "", fontsize=9, fontname="helv")
            y += _INTERLIGNE

    # ── Mention SANS PRIX ────────────────────────────────────────────────
    y += _SECTION_GAP * 2
    mention = "DOCUMENT TERRAIN \u2014 SANS PRIX"
    mention_width = fitz.get_text_length(mention, fontsize=9, fontname="helv")
    x_center = (width - mention_width) / 2
    page.insert_text((x_center, y), mention, fontsize=9, fontname="helv", color=(0.8, 0, 0))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generer_pdf_terrain(bdc: BonDeCommande) -> BonDeCommande:
    """
    Genere le PDF terrain (sans prix) et le stocke sur le BDC.

    Processus unique pour tous les bailleurs : generation PyMuPDF
    depuis les donnees en base.

    Returns:
        Le BDC avec le champ pdf_terrain mis a jour.
    """
    pdf_bytes = _generer_pdf_terrain_pymupdf(bdc)
    filename = f"{bdc.numero_bdc}_terrain.pdf"
    bdc.pdf_terrain.save(filename, ContentFile(pdf_bytes), save=True)
    return bdc
```

**Step 4: Lancer les tests**

Run: `uv run pytest tests/test_bdc/test_terrain.py::TestGenererPdfTerrainUnifie -v --tb=short`
Expected: PASS (tous les tests)

**Step 5: Lancer tous les tests terrain**

Run: `uv run pytest tests/test_bdc/test_terrain.py -v --tb=short`
Expected: PASS (y compris integration et vues)

---

### Task 3: Nettoyer les anciens tests et le template

**Files:**
- Modify: `tests/test_bdc/test_terrain.py` — supprimer `TestGenererTerrainGDH`, `TestAnonymisationTerrainGDH`, `TestGenererTerrainERILIA`, les helpers `_creer_pdf_*`, le fixture `_mock_weasyprint`
- Delete: `templates/bdc/terrain_erilia.html`

**Step 6: Nettoyer test_terrain.py**

Supprimer :
- `_creer_pdf_2_pages()`
- `_creer_pdf_2_pages_avec_emetteur()`
- `_creer_pdf_1_page()`
- `_fake_pdf()`
- `_mock_weasyprint` fixture
- `class TestGenererTerrainGDH`
- `class TestAnonymisationTerrainGDH`
- `class TestGenererTerrainERILIA`

Garder :
- `_extraire_texte_terrain()` (nouveau helper)
- `class TestGenererPdfTerrainUnifie` (nouveaux tests)
- `class TestGenererPdfTerrain` — adapter pour ne plus utiliser `_creer_pdf_2_pages` ni `_mock_weasyprint`
- `class TestAttributionGenereTerrainIntegration` — adapter idem
- `class TestTelechargerTerrain` — garder tel quel
- `class TestDetailBoutonTerrain` — garder tel quel

Dans `TestGenererPdfTerrain`, les tests de dispatch n'ont plus besoin de pdf_original ni de mock weasyprint :
```python
class TestGenererPdfTerrain:
    def test_genere_gdh(self, bdc_a_faire):
        assert bdc_a_faire.bailleur.code == "GDH"
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_genere_erilia(self, bdc_a_faire, bailleur_erilia):
        bdc_a_faire.bailleur = bailleur_erilia
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_bailleur_inconnu(self, bdc_a_faire):
        from apps.bdc.models import Bailleur
        autre = Bailleur.objects.create(nom="Autre Bailleur", code="AUTRE")
        bdc_a_faire.bailleur = autre
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name
```

Dans `TestAttributionGenereTerrainIntegration`, plus besoin de `pdf_original` ni de `_mock_weasyprint` :
```python
class TestAttributionGenereTerrainIntegration:
    def test_attribution_genere_pdf_terrain(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        bdc.refresh_from_db()
        assert bdc.pdf_terrain

    def test_reattribution_regenere_pdf_terrain(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        autre_st = SousTraitant.objects.create(nom="Martin", telephone="0600000000", actif=True)
        bdc = reattribuer_st(bdc, autre_st, Decimal("70"), utilisateur_cdt)
        bdc.refresh_from_db()
        assert bdc.pdf_terrain

    def test_attribution_reussit_meme_si_terrain_echoue(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS
        assert bdc.sous_traitant == sous_traitant
```

**Step 7: Supprimer terrain_erilia.html**

Delete: `templates/bdc/terrain_erilia.html`

**Step 8: Lancer tous les tests**

Run: `uv run pytest tests/test_bdc/test_terrain.py -v --tb=short`
Expected: PASS (tous les tests)

Run: `uv run pytest -v --tb=short`
Expected: PASS (aucune regression)

**Step 9: Commit**

```bash
git add apps/bdc/terrain.py tests/test_bdc/test_terrain.py
git rm templates/bdc/terrain_erilia.html
git add docs/plans/2026-03-07-terrain-pdf-unifie-design.md docs/plans/2026-03-07-terrain-pdf-unifie.md
git commit -m "feat: processus unifie PDF terrain PyMuPDF (remplace GDH + WeasyPrint)"
```
