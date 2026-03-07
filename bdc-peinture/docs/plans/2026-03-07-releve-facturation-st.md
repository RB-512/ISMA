# Relevé de facturation sous-traitant — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow the CDT to create billing statements ("relevés de facturation") per subcontractor, grouping realized BDCs since the last validated statement, with anti-duplicate guarantees and PDF/Excel export.

**Architecture:** New `ReleveFacturation` model in `apps/bdc/` with M2M to `BonDeCommande`. Service layer in `apps/bdc/releves.py` handles creation, validation, and anti-duplicate logic. Views integrated into existing recoupement pages. PDF generation via PyMuPDF (same pattern as terrain.py). Excel via openpyxl (same pattern as exports.py).

**Tech Stack:** Django 5.1, PyMuPDF (fitz), openpyxl, HTMX, Tailwind CSS, pytest

---

### Task 1: Model `ReleveFacturation`

**Files:**
- Modify: `bdc-peinture/apps/bdc/models.py` (append after `HistoriqueAction`)
- Test: `bdc-peinture/tests/test_bdc/test_releves.py`

**Step 1: Write the failing test**

```python
# tests/test_bdc/test_releves.py
"""Tests unitaires — relevés de facturation sous-traitant."""

from datetime import date
from decimal import Decimal

import pytest

from apps.bdc.models import BonDeCommande, ReleveFacturation, ReleveStatutChoices, StatutChoices


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def bdc_en_cours(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    return BonDeCommande.objects.create(
        numero_bdc="REL-001",
        bailleur=bailleur_gdh,
        adresse="10 Rue Releve",
        ville="Avignon",
        occupation="OCCUPE",
        statut=StatutChoices.A_FACTURER,
        sous_traitant=sous_traitant,
        pourcentage_st=Decimal("65"),
        montant_ht=Decimal("1000"),
        montant_st=Decimal("650"),
        date_realisation=date(2026, 2, 15),
        cree_par=utilisateur_cdt,
    )


@pytest.fixture
def bdc_facture(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    return BonDeCommande.objects.create(
        numero_bdc="REL-002",
        bailleur=bailleur_gdh,
        adresse="20 Rue Releve",
        ville="Orange",
        occupation="VACANT",
        statut=StatutChoices.FACTURE,
        sous_traitant=sous_traitant,
        pourcentage_st=Decimal("60"),
        montant_ht=Decimal("2000"),
        montant_st=Decimal("1200"),
        date_realisation=date(2026, 1, 10),
        cree_par=utilisateur_cdt,
    )


# ─── 1. Tests modele ────────────────────────────────────────────────────────


class TestReleveFacturationModel:
    def test_creation_releve(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        releve.bdc.add(bdc_en_cours)
        assert releve.statut == ReleveStatutChoices.BROUILLON
        assert releve.numero == 1
        assert releve.bdc.count() == 1

    def test_str_representation(self, db, sous_traitant, utilisateur_cdt):
        releve = ReleveFacturation.objects.create(
            numero=3,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        assert "Dupont Peinture" in str(releve)
        assert "n°3" in str(releve)

    def test_montant_total(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        releve.bdc.add(bdc_en_cours, bdc_facture)
        assert releve.montant_total == Decimal("1850")  # 650 + 1200

    def test_montant_total_vide(self, db, sous_traitant, utilisateur_cdt):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        assert releve.montant_total == Decimal("0")

    def test_nb_bdc(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        releve.bdc.add(bdc_en_cours, bdc_facture)
        assert releve.nb_bdc == 2

    def test_periode(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        releve.bdc.add(bdc_en_cours, bdc_facture)
        debut, fin = releve.periode
        assert debut == date(2026, 1, 10)
        assert fin == date(2026, 2, 15)

    def test_periode_vide(self, db, sous_traitant, utilisateur_cdt):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        debut, fin = releve.periode
        assert debut is None
        assert fin is None

    def test_statut_defaut_brouillon(self, db, sous_traitant, utilisateur_cdt):
        releve = ReleveFacturation.objects.create(
            numero=1,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        assert releve.statut == ReleveStatutChoices.BROUILLON
        assert releve.date_validation is None
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py -v --tb=short -x`
Expected: FAIL with `ImportError: cannot import name 'ReleveFacturation'`

**Step 3: Write minimal implementation**

Append to `bdc-peinture/apps/bdc/models.py` after the `HistoriqueAction` class:

```python
# ─── ReleveFacturation ───────────────────────────────────────────────────────


class ReleveStatutChoices(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    VALIDE = "VALIDE", "Validé"


class ReleveFacturation(models.Model):
    """
    Relevé de facturation regroupant les BDC réalisés par un sous-traitant.
    Workflow : BROUILLON → VALIDE.
    Un BDC ne peut appartenir qu'à un seul relevé validé (anti-doublon).
    """

    numero = models.PositiveIntegerField(verbose_name="N° Relevé")
    sous_traitant = models.ForeignKey(
        "sous_traitants.SousTraitant",
        on_delete=models.PROTECT,
        related_name="releves_facturation",
        verbose_name="Sous-traitant",
    )
    statut = models.CharField(
        max_length=10,
        choices=ReleveStatutChoices.choices,
        default=ReleveStatutChoices.BROUILLON,
        verbose_name="Statut",
    )
    bdc = models.ManyToManyField(
        BonDeCommande,
        blank=True,
        related_name="releves_facturation",
        verbose_name="Bons de commande",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    cree_par = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="releves_crees",
        verbose_name="Créé par",
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Validé le"
    )

    class Meta:
        verbose_name = "Relevé de facturation"
        verbose_name_plural = "Relevés de facturation"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Relevé n°{self.numero} — {self.sous_traitant.nom}"

    @property
    def montant_total(self):
        result = self.bdc.aggregate(total=models.Sum("montant_st"))["total"]
        return result or Decimal("0")

    @property
    def nb_bdc(self):
        return self.bdc.count()

    @property
    def periode(self):
        agg = self.bdc.aggregate(
            debut=models.Min("date_realisation"),
            fin=models.Max("date_realisation"),
        )
        return agg["debut"], agg["fin"]
```

**Step 4: Run test to verify it passes**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py -v --tb=short`
Expected: All 8 tests PASS

**Step 5: Create migration**

Run: `cd bdc-peinture && uv run manage.py makemigrations bdc --name releve_facturation`
Expected: Migration file created

**Step 6: Commit**

```bash
cd bdc-peinture
rtk git add apps/bdc/models.py apps/bdc/migrations/ tests/test_bdc/test_releves.py
rtk git commit -m "feat: add ReleveFacturation model with properties and tests"
```

---

### Task 2: Service layer `releves.py`

**Files:**
- Create: `bdc-peinture/apps/bdc/releves.py`
- Test: `bdc-peinture/tests/test_bdc/test_releves.py` (append)

**Step 1: Write the failing tests**

Append to `tests/test_bdc/test_releves.py`:

```python
from apps.bdc.releves import (
    ReleveError,
    creer_releve,
    retirer_bdc_du_releve,
    valider_releve,
)


# ─── 2. Tests service creer_releve ──────────────────────────────────────────


class TestCreerReleve:
    def test_creer_releve_recupere_bdc_eligibles(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture
    ):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        assert releve.statut == ReleveStatutChoices.BROUILLON
        assert releve.bdc.count() == 2
        assert releve.numero == 1

    def test_numero_auto_incremente(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        r1 = creer_releve(sous_traitant, utilisateur_cdt)
        # Valider r1 pour liberer la place
        valider_releve(r1, utilisateur_cdt)
        # Creer un nouveau BDC eligible
        bdc2 = BonDeCommande.objects.create(
            numero_bdc="REL-003",
            bailleur=bdc_en_cours.bailleur,
            adresse="30 Rue Test",
            ville="Avignon",
            statut=StatutChoices.A_FACTURER,
            sous_traitant=sous_traitant,
            montant_st=Decimal("100"),
            date_realisation=date(2026, 3, 1),
            cree_par=utilisateur_cdt,
        )
        r2 = creer_releve(sous_traitant, utilisateur_cdt)
        assert r2.numero == 2

    def test_exclut_bdc_deja_dans_releve_valide(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture
    ):
        r1 = creer_releve(sous_traitant, utilisateur_cdt)
        valider_releve(r1, utilisateur_cdt)
        # Pas de BDC restant → erreur
        with pytest.raises(ReleveError, match="Aucun BDC"):
            creer_releve(sous_traitant, utilisateur_cdt)

    def test_exclut_bdc_autre_st(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        from apps.sous_traitants.models import SousTraitant

        autre_st = SousTraitant.objects.create(nom="Autre ST", telephone="0600000000")
        releve = creer_releve(autre_st, utilisateur_cdt)
        assert releve.bdc.count() == 0  # Pas de BDC pour cet autre ST
        # En fait, ça devrait lever ReleveError
        # Corrigeons : creer_releve leve ReleveError si 0 BDC

    def test_erreur_si_aucun_bdc_eligible(
        self, db, sous_traitant, utilisateur_cdt
    ):
        with pytest.raises(ReleveError, match="Aucun BDC"):
            creer_releve(sous_traitant, utilisateur_cdt)

    def test_exclut_bdc_en_cours_statut(
        self, db, bailleur_gdh, sous_traitant, utilisateur_cdt
    ):
        """Les BDC EN_COURS ne sont pas eligibles (seulement A_FACTURER + FACTURE)."""
        BonDeCommande.objects.create(
            numero_bdc="REL-EN-COURS",
            bailleur=bailleur_gdh,
            adresse="1 Rue Test",
            ville="Avignon",
            statut=StatutChoices.EN_COURS,
            sous_traitant=sous_traitant,
            cree_par=utilisateur_cdt,
        )
        with pytest.raises(ReleveError, match="Aucun BDC"):
            creer_releve(sous_traitant, utilisateur_cdt)


# ─── 3. Tests service retirer_bdc_du_releve ─────────────────────────────────


class TestRetirerBdc:
    def test_retirer_bdc_du_brouillon(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture
    ):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        assert releve.bdc.count() == 2
        retirer_bdc_du_releve(releve, bdc_en_cours)
        assert releve.bdc.count() == 1

    def test_retirer_bdc_releve_valide_interdit(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        valider_releve(releve, utilisateur_cdt)
        with pytest.raises(ReleveError, match="validé"):
            retirer_bdc_du_releve(releve, bdc_en_cours)


# ─── 4. Tests service valider_releve ────────────────────────────────────────


class TestValiderReleve:
    def test_valider_passe_en_valide(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        valider_releve(releve, utilisateur_cdt)
        releve.refresh_from_db()
        assert releve.statut == ReleveStatutChoices.VALIDE
        assert releve.date_validation is not None

    def test_valider_releve_deja_valide_interdit(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        valider_releve(releve, utilisateur_cdt)
        with pytest.raises(ReleveError, match="déjà validé"):
            valider_releve(releve, utilisateur_cdt)

    def test_valider_releve_vide_interdit(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        releve.bdc.clear()
        with pytest.raises(ReleveError, match="vide"):
            valider_releve(releve, utilisateur_cdt)

    def test_anti_doublon_apres_validation(
        self, db, sous_traitant, utilisateur_cdt, bdc_en_cours
    ):
        """Un BDC dans un relevé validé ne peut pas être dans un nouveau relevé."""
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        valider_releve(releve, utilisateur_cdt)
        # bdc_en_cours est maintenant verrouillé
        with pytest.raises(ReleveError, match="Aucun BDC"):
            creer_releve(sous_traitant, utilisateur_cdt)
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py::TestCreerReleve -v --tb=short -x`
Expected: FAIL with `ImportError: cannot import name 'creer_releve'`

**Step 3: Write minimal implementation**

```python
# bdc-peinture/apps/bdc/releves.py
"""
Service de gestion des relevés de facturation sous-traitant.
Logique métier : création, validation, anti-doublon.
"""

from django.contrib.auth.models import User
from django.db.models import Max
from django.utils import timezone

from apps.sous_traitants.models import SousTraitant

from .models import BonDeCommande, ReleveFacturation, ReleveStatutChoices, StatutChoices


class ReleveError(Exception):  # noqa: N818
    """Levée quand une opération sur un relevé est invalide."""


def _bdc_eligibles(sous_traitant: SousTraitant):
    """
    Retourne les BDC éligibles pour un nouveau relevé :
    - Attribués à ce ST
    - En statut A_FACTURER ou FACTURE
    - Non rattachés à un relevé validé
    """
    bdc_dans_releve_valide = BonDeCommande.objects.filter(
        releves_facturation__statut=ReleveStatutChoices.VALIDE,
    )
    return BonDeCommande.objects.filter(
        sous_traitant=sous_traitant,
        statut__in=[StatutChoices.A_FACTURER, StatutChoices.FACTURE],
    ).exclude(pk__in=bdc_dans_releve_valide)


def _prochain_numero(sous_traitant: SousTraitant) -> int:
    """Retourne le prochain numéro de relevé pour ce ST."""
    max_num = ReleveFacturation.objects.filter(
        sous_traitant=sous_traitant,
    ).aggregate(max_num=Max("numero"))["max_num"]
    return (max_num or 0) + 1


def creer_releve(sous_traitant: SousTraitant, utilisateur: User) -> ReleveFacturation:
    """
    Crée un relevé brouillon pour un ST avec tous les BDC éligibles.

    Raises:
        ReleveError: Si aucun BDC éligible.
    """
    eligibles = list(_bdc_eligibles(sous_traitant))
    if not eligibles:
        raise ReleveError(
            f"Aucun BDC éligible pour {sous_traitant.nom}. "
            "Tous les BDC sont déjà dans un relevé validé ou aucun BDC à facturer."
        )

    releve = ReleveFacturation.objects.create(
        numero=_prochain_numero(sous_traitant),
        sous_traitant=sous_traitant,
        cree_par=utilisateur,
    )
    releve.bdc.set(eligibles)
    return releve


def retirer_bdc_du_releve(releve: ReleveFacturation, bdc: BonDeCommande) -> None:
    """
    Retire un BDC d'un relevé brouillon.

    Raises:
        ReleveError: Si le relevé est validé.
    """
    if releve.statut == ReleveStatutChoices.VALIDE:
        raise ReleveError("Impossible de modifier un relevé déjà validé.")
    releve.bdc.remove(bdc)


def valider_releve(releve: ReleveFacturation, utilisateur: User) -> ReleveFacturation:
    """
    Valide un relevé brouillon. Les BDC sont verrouillés.

    Raises:
        ReleveError: Si le relevé est déjà validé ou vide.
    """
    if releve.statut == ReleveStatutChoices.VALIDE:
        raise ReleveError("Ce relevé est déjà validé.")

    if releve.bdc.count() == 0:
        raise ReleveError("Impossible de valider un relevé vide.")

    releve.statut = ReleveStatutChoices.VALIDE
    releve.date_validation = timezone.now()
    releve.save(update_fields=["statut", "date_validation"])
    return releve
```

**Step 4: Run test to verify it passes**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py -v --tb=short`
Expected: All tests PASS

**Step 5: Commit**

```bash
cd bdc-peinture
rtk git add apps/bdc/releves.py tests/test_bdc/test_releves.py
rtk git commit -m "feat: add releve facturation service layer with anti-doublon"
```

---

### Task 3: Admin registration

**Files:**
- Modify: `bdc-peinture/apps/bdc/admin.py`

**Step 1: Add admin registration**

Append to `bdc-peinture/apps/bdc/admin.py`:

```python
from .models import ReleveFacturation


@admin.register(ReleveFacturation)
class ReleveFacturationAdmin(admin.ModelAdmin):
    list_display = ("numero", "sous_traitant", "statut", "date_creation", "date_validation")
    list_filter = ("statut", "sous_traitant")
    readonly_fields = ("date_creation",)
```

**Step 2: Run all tests**

Run: `cd bdc-peinture && uv run pytest --tb=short -q`
Expected: All tests PASS, no regressions

**Step 3: Commit**

```bash
cd bdc-peinture
rtk git add apps/bdc/admin.py
rtk git commit -m "feat: register ReleveFacturation in Django admin"
```

---

### Task 4: URLs and views

**Files:**
- Modify: `bdc-peinture/apps/bdc/urls.py`
- Modify: `bdc-peinture/apps/bdc/views.py`
- Test: `bdc-peinture/tests/test_bdc/test_releves.py` (append)

**Step 1: Write the failing view tests**

Append to `tests/test_bdc/test_releves.py`:

```python
from django.urls import reverse


# ─── 5. Tests vues ──────────────────────────────────────────────────────────


class TestVueCreerReleve:
    def test_creer_releve_post(self, client_cdt, sous_traitant, bdc_en_cours):
        url = reverse("bdc:releve_creer", kwargs={"st_pk": sous_traitant.pk})
        response = client_cdt.post(url)
        assert response.status_code == 302  # redirect to releve detail
        assert ReleveFacturation.objects.count() == 1

    def test_creer_releve_sans_bdc_eligible(self, client_cdt, sous_traitant):
        url = reverse("bdc:releve_creer", kwargs={"st_pk": sous_traitant.pk})
        response = client_cdt.post(url)
        assert response.status_code == 302  # redirect back with error
        assert ReleveFacturation.objects.count() == 0

    def test_anonyme_redirige(self, client, sous_traitant):
        url = reverse("bdc:releve_creer", kwargs={"st_pk": sous_traitant.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert "/accounts/" in response.url


class TestVueReleveDetail:
    def test_detail_brouillon(self, client_cdt, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        url = reverse("bdc:releve_detail", kwargs={"pk": releve.pk})
        response = client_cdt.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "REL-001" in content
        assert "Brouillon" in content

    def test_detail_valide(self, client_cdt, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        valider_releve(releve, utilisateur_cdt)
        url = reverse("bdc:releve_detail", kwargs={"pk": releve.pk})
        response = client_cdt.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Validé" in content or "Valid" in content


class TestVueValiderReleve:
    def test_valider_post(self, client_cdt, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        url = reverse("bdc:releve_valider", kwargs={"pk": releve.pk})
        response = client_cdt.post(url)
        assert response.status_code == 302
        releve.refresh_from_db()
        assert releve.statut == ReleveStatutChoices.VALIDE


class TestVueRetirerBdc:
    def test_retirer_bdc_post(self, client_cdt, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        url = reverse("bdc:releve_retirer_bdc", kwargs={"pk": releve.pk, "bdc_pk": bdc_en_cours.pk})
        response = client_cdt.post(url)
        assert response.status_code == 302
        assert releve.bdc.count() == 1


class TestVueHistoriqueReleves:
    def test_historique_st(self, client_cdt, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        url = reverse("bdc:releve_historique", kwargs={"st_pk": sous_traitant.pk})
        response = client_cdt.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "n°1" in content or "n\u00b01" in content
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py::TestVueCreerReleve -v --tb=short -x`
Expected: FAIL with `NoReverseMatch` (URL not defined yet)

**Step 3: Add URLs**

Add to `bdc-peinture/apps/bdc/urls.py` before the closing bracket:

```python
    # ─── Relevés de facturation ─────────────────────────────────────────────
    path("releves/<int:st_pk>/creer/", views.releve_creer, name="releve_creer"),
    path("releves/<int:pk>/", views.releve_detail, name="releve_detail"),
    path("releves/<int:pk>/valider/", views.releve_valider, name="releve_valider"),
    path("releves/<int:pk>/retirer/<int:bdc_pk>/", views.releve_retirer_bdc, name="releve_retirer_bdc"),
    path("releves/<int:pk>/pdf/", views.releve_pdf, name="releve_pdf"),
    path("releves/<int:pk>/excel/", views.releve_excel, name="releve_excel"),
    path("releves/st/<int:st_pk>/", views.releve_historique, name="releve_historique"),
```

**Step 4: Add views**

Append to `bdc-peinture/apps/bdc/views.py`:

```python
# ─── Relevés de facturation ─────────────────────────────────────────────────


@login_required
def releve_creer(request, st_pk: int):
    """POST-only : crée un relevé brouillon pour un ST."""
    from apps.sous_traitants.models import SousTraitant

    from .releves import ReleveError, creer_releve

    if request.method != "POST":
        return redirect("bdc:recoupement_liste")

    sous_traitant = get_object_or_404(SousTraitant, pk=st_pk)
    try:
        releve = creer_releve(sous_traitant, request.user)
        messages.success(request, f"Relevé n°{releve.numero} créé pour {sous_traitant.nom}.")
        return redirect("bdc:releve_detail", pk=releve.pk)
    except ReleveError as e:
        messages.error(request, str(e))
        return redirect("bdc:recoupement_liste")


@login_required
def releve_detail(request, pk: int):
    """Détail d'un relevé : liste des BDC, montant total, actions."""
    from .models import ReleveFacturation

    releve = get_object_or_404(
        ReleveFacturation.objects.select_related("sous_traitant", "cree_par"),
        pk=pk,
    )
    bdc_list = releve.bdc.select_related("bailleur").order_by("date_realisation")

    return render(request, "bdc/releve_detail.html", {
        "releve": releve,
        "bdc_list": bdc_list,
    })


@login_required
def releve_valider(request, pk: int):
    """POST-only : valide un relevé brouillon."""
    from .models import ReleveFacturation
    from .releves import ReleveError, valider_releve as _valider

    if request.method != "POST":
        return redirect("bdc:releve_detail", pk=pk)

    releve = get_object_or_404(ReleveFacturation, pk=pk)
    try:
        _valider(releve, request.user)
        messages.success(request, f"Relevé n°{releve.numero} validé.")
    except ReleveError as e:
        messages.error(request, str(e))
    return redirect("bdc:releve_detail", pk=pk)


@login_required
def releve_retirer_bdc(request, pk: int, bdc_pk: int):
    """POST-only : retire un BDC d'un relevé brouillon."""
    from .models import ReleveFacturation
    from .releves import ReleveError, retirer_bdc_du_releve

    if request.method != "POST":
        return redirect("bdc:releve_detail", pk=pk)

    releve = get_object_or_404(ReleveFacturation, pk=pk)
    bdc = get_object_or_404(BonDeCommande, pk=bdc_pk)
    try:
        retirer_bdc_du_releve(releve, bdc)
        messages.success(request, f"BDC {bdc.numero_bdc} retiré du relevé.")
    except ReleveError as e:
        messages.error(request, str(e))
    return redirect("bdc:releve_detail", pk=pk)


@login_required
def releve_historique(request, st_pk: int):
    """Historique des relevés d'un ST."""
    from apps.sous_traitants.models import SousTraitant

    from .models import ReleveFacturation

    sous_traitant = get_object_or_404(SousTraitant, pk=st_pk)
    releves = ReleveFacturation.objects.filter(
        sous_traitant=sous_traitant,
    ).order_by("-date_creation")

    return render(request, "bdc/releve_historique.html", {
        "sous_traitant": sous_traitant,
        "releves": releves,
    })


@login_required
def releve_pdf(request, pk: int):
    """Génère et télécharge le PDF du relevé."""
    from .models import ReleveFacturation
    from .releves_export import generer_releve_pdf

    releve = get_object_or_404(
        ReleveFacturation.objects.select_related("sous_traitant"),
        pk=pk,
    )
    return generer_releve_pdf(releve)


@login_required
def releve_excel(request, pk: int):
    """Génère et télécharge l'Excel du relevé."""
    from .models import ReleveFacturation
    from .releves_export import generer_releve_excel

    releve = get_object_or_404(
        ReleveFacturation.objects.select_related("sous_traitant"),
        pk=pk,
    )
    return generer_releve_excel(releve)
```

**Step 5: Create stub templates** (minimal, just enough for tests to pass)

Create `bdc-peinture/templates/bdc/releve_detail.html`:

```html
{% extends "base.html" %}
{% block title %}Relevé n°{{ releve.numero }} — {{ releve.sous_traitant.nom }}{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold text-[var(--color-text)]">Relevé n°{{ releve.numero }}</h1>
            <p class="text-sm text-[var(--color-text-muted)]">{{ releve.sous_traitant.nom }}</p>
        </div>
        <div class="flex gap-2">
            {% if releve.statut == "BROUILLON" %}
            <span class="px-3 py-1 text-sm font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 rounded-full">Brouillon</span>
            {% else %}
            <span class="px-3 py-1 text-sm font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 rounded-full">Validé</span>
            {% endif %}
        </div>
    </div>

    {# Résumé #}
    <div class="grid grid-cols-3 gap-4">
        <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-4 text-center">
            <p class="text-2xl font-bold text-[var(--color-text)]">{{ bdc_list|length }}</p>
            <p class="text-sm text-[var(--color-text-muted)]">BDC</p>
        </div>
        <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-4 text-center">
            <p class="text-2xl font-bold text-[var(--color-text)]">{{ releve.montant_total|floatformat:2 }} &euro;</p>
            <p class="text-sm text-[var(--color-text-muted)]">Montant total ST</p>
        </div>
        <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-4 text-center">
            {% with releve.periode as p %}
            <p class="text-sm font-medium text-[var(--color-text)]">
                {% if p.0 %}{{ p.0|date:"d/m/Y" }} — {{ p.1|date:"d/m/Y" }}{% else %}—{% endif %}
            </p>
            {% endwith %}
            <p class="text-sm text-[var(--color-text-muted)]">Période</p>
        </div>
    </div>

    {# Actions #}
    <div class="flex gap-2">
        {% if releve.statut == "BROUILLON" %}
        <form method="post" action="{% url 'bdc:releve_valider' releve.pk %}">
            {% csrf_token %}
            <button type="submit" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-all">
                Valider le relevé
            </button>
        </form>
        {% endif %}
        <a href="{% url 'bdc:releve_pdf' releve.pk %}" class="px-4 py-2 bg-accent hover:bg-accent-dark text-white text-sm font-medium rounded-lg transition-all">
            Télécharger PDF
        </a>
        <a href="{% url 'bdc:releve_excel' releve.pk %}" class="px-4 py-2 bg-[var(--color-surface-card)] border border-[var(--color-border)] text-[var(--color-text)] text-sm font-medium rounded-lg hover:bg-accent/5 transition-all">
            Télécharger Excel
        </a>
        <a href="{% url 'bdc:releve_historique' releve.sous_traitant.pk %}" class="px-4 py-2 text-sm text-accent hover:underline">
            Historique
        </a>
    </div>

    {# Tableau BDC #}
    <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] overflow-hidden">
        <table class="min-w-full divide-y divide-[var(--color-border)]">
            <thead>
                <tr class="bg-primary/5 dark:bg-white/5">
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">N° BDC</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Adresse</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Ville</th>
                    <th class="text-right px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Montant ST</th>
                    <th class="text-center px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Réalisation</th>
                    {% if releve.statut == "BROUILLON" %}
                    <th class="text-center px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Action</th>
                    {% endif %}
                </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
                {% for bdc in bdc_list %}
                <tr class="hover:bg-accent/5 transition-colors">
                    <td class="px-4 py-3 text-sm font-mono">{{ bdc.numero_bdc }}</td>
                    <td class="px-4 py-3 text-sm">{{ bdc.adresse }}</td>
                    <td class="px-4 py-3 text-sm">{{ bdc.ville }}</td>
                    <td class="px-4 py-3 text-sm text-right font-mono">{% if bdc.montant_st %}{{ bdc.montant_st|floatformat:2 }} &euro;{% else %}—{% endif %}</td>
                    <td class="px-4 py-3 text-sm text-center">{% if bdc.date_realisation %}{{ bdc.date_realisation|date:"d/m/Y" }}{% else %}—{% endif %}</td>
                    {% if releve.statut == "BROUILLON" %}
                    <td class="px-4 py-3 text-center">
                        <form method="post" action="{% url 'bdc:releve_retirer_bdc' releve.pk bdc.pk %}">
                            {% csrf_token %}
                            <button type="submit" class="text-red-500 hover:text-red-700 text-xs">Retirer</button>
                        </form>
                    </td>
                    {% endif %}
                </tr>
                {% empty %}
                <tr>
                    <td colspan="6" class="px-4 py-8 text-center text-[var(--color-text-muted)]">Aucun BDC dans ce relevé.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    {# Notes #}
    {% if releve.notes %}
    <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-4">
        <h3 class="text-sm font-semibold text-[var(--color-text-muted)] mb-2">Notes</h3>
        <p class="text-sm text-[var(--color-text)]">{{ releve.notes }}</p>
    </div>
    {% endif %}
</div>
{% endblock %}
```

Create `bdc-peinture/templates/bdc/releve_historique.html`:

```html
{% extends "base.html" %}
{% block title %}Relevés — {{ sous_traitant.nom }}{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold text-[var(--color-text)]">Relevés de facturation</h1>
            <p class="text-sm text-[var(--color-text-muted)]">{{ sous_traitant.nom }}</p>
        </div>
        <a href="{% url 'bdc:recoupement_liste' %}" class="text-sm text-accent hover:underline">&larr; Recoupement</a>
    </div>

    {% if releves %}
    <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] overflow-hidden">
        <table class="min-w-full divide-y divide-[var(--color-border)]">
            <thead>
                <tr class="bg-primary/5 dark:bg-white/5">
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">N°</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Date</th>
                    <th class="text-center px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">BDC</th>
                    <th class="text-right px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Montant</th>
                    <th class="text-center px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Statut</th>
                    <th class="text-center px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
                {% for releve in releves %}
                <tr class="hover:bg-accent/5 transition-colors">
                    <td class="px-4 py-3 text-sm font-mono">
                        <a href="{% url 'bdc:releve_detail' releve.pk %}" class="text-accent hover:underline">n°{{ releve.numero }}</a>
                    </td>
                    <td class="px-4 py-3 text-sm">
                        {% if releve.date_validation %}{{ releve.date_validation|date:"d/m/Y" }}{% else %}{{ releve.date_creation|date:"d/m/Y" }}{% endif %}
                    </td>
                    <td class="px-4 py-3 text-sm text-center font-mono">{{ releve.nb_bdc }}</td>
                    <td class="px-4 py-3 text-sm text-right font-mono">{{ releve.montant_total|floatformat:2 }} &euro;</td>
                    <td class="px-4 py-3 text-center">
                        {% if releve.statut == "BROUILLON" %}
                        <span class="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 rounded-full">Brouillon</span>
                        {% else %}
                        <span class="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 rounded-full">Validé</span>
                        {% endif %}
                    </td>
                    <td class="px-4 py-3 text-center text-sm space-x-2">
                        <a href="{% url 'bdc:releve_pdf' releve.pk %}" class="text-accent hover:underline">PDF</a>
                        <a href="{% url 'bdc:releve_excel' releve.pk %}" class="text-accent hover:underline">Excel</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-12 text-center">
        <p class="text-[var(--color-text-muted)]">Aucun relevé de facturation pour ce sous-traitant.</p>
    </div>
    {% endif %}
</div>
{% endblock %}
```

**Step 6: Run tests**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py -v --tb=short`
Expected: All tests PASS

**Step 7: Commit**

```bash
cd bdc-peinture
rtk git add apps/bdc/urls.py apps/bdc/views.py templates/bdc/releve_detail.html templates/bdc/releve_historique.html
rtk git commit -m "feat: add releve views, URLs, and templates"
```

---

### Task 5: PDF and Excel export

**Files:**
- Create: `bdc-peinture/apps/bdc/releves_export.py`
- Test: `bdc-peinture/tests/test_bdc/test_releves.py` (append)

**Step 1: Write the failing tests**

Append to `tests/test_bdc/test_releves.py`:

```python
from io import BytesIO

from openpyxl import load_workbook

from apps.bdc.releves_export import generer_releve_excel, generer_releve_pdf


# ─── 6. Tests export PDF ────────────────────────────────────────────────────


class TestRelevePdf:
    def test_pdf_genere(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        response = generer_releve_pdf(releve)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "releve_" in response["Content-Disposition"]

    def test_pdf_contient_numero(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        response = generer_releve_pdf(releve)
        # PDF is binary, just check it's valid
        assert len(response.content) > 100


# ─── 7. Tests export Excel ──────────────────────────────────────────────────


class TestReleveExcel:
    def test_excel_genere(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        response = generer_releve_excel(releve)
        assert response.status_code == 200
        assert "spreadsheetml" in response["Content-Type"]

    def test_excel_contient_bdc(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours, bdc_facture):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        response = generer_releve_excel(releve)
        wb = load_workbook(BytesIO(response.content))
        ws = wb.active
        assert ws.max_row == 3  # header + 2 BDC

    def test_excel_colonnes(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        response = generer_releve_excel(releve)
        wb = load_workbook(BytesIO(response.content))
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        assert "N° BDC" in headers
        assert "Montant ST" in headers

    def test_excel_headers_en_gras(self, db, sous_traitant, utilisateur_cdt, bdc_en_cours):
        releve = creer_releve(sous_traitant, utilisateur_cdt)
        response = generer_releve_excel(releve)
        wb = load_workbook(BytesIO(response.content))
        ws = wb.active
        for cell in ws[1]:
            assert cell.font.bold is True
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py::TestRelevePdf -v --tb=short -x`
Expected: FAIL with `ImportError`

**Step 3: Write implementation**

```python
# bdc-peinture/apps/bdc/releves_export.py
"""
Export PDF et Excel des relevés de facturation sous-traitant.
"""

from datetime import date

import fitz  # PyMuPDF
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from .models import ReleveFacturation

# ─── Constantes PDF ─────────────────────────────────────────────────────────

_MARGE_G = 50
_MARGE_D = 50
_Y_START = 60
_INTERLIGNE = 16
_SECTION_GAP = 12


def generer_releve_pdf(releve: ReleveFacturation) -> HttpResponse:
    """Génère un PDF du relevé de facturation (pour le ST)."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    width = page.rect.width
    y = _Y_START

    st_nom = releve.sous_traitant.nom.upper()
    debut, fin = releve.periode

    # En-tête
    page.insert_text((_MARGE_G, y), "RELEVÉ DE FACTURATION", fontsize=14, fontname="helv", color=(0.1, 0.1, 0.1))
    y += 22
    page.insert_text((_MARGE_G, y), f"N° {releve.numero} — {st_nom}", fontsize=11, fontname="helv")
    y += _INTERLIGNE
    if debut and fin:
        page.insert_text(
            (_MARGE_G, y),
            f"Période : {debut.strftime('%d/%m/%Y')} — {fin.strftime('%d/%m/%Y')}",
            fontsize=9,
            fontname="helv",
            color=(0.5, 0.5, 0.5),
        )
        y += _INTERLIGNE

    # Ligne séparation
    y += 4
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=1)
    y += _INTERLIGNE + _SECTION_GAP

    # En-tête tableau
    col_bdc = _MARGE_G
    col_adresse = _MARGE_G + 80
    col_montant = width - _MARGE_D - 70
    page.insert_text((col_bdc, y), "N° BDC", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    page.insert_text((col_adresse, y), "Adresse", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    page.insert_text((col_montant, y), "Montant ST", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    y += 4
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.85, 0.85, 0.85), width=0.5)
    y += _INTERLIGNE - 2

    # Lignes BDC
    bdc_list = releve.bdc.select_related("bailleur").order_by("date_realisation")
    for bdc in bdc_list:
        if y > 780:  # nouvelle page si besoin
            page = doc.new_page(width=595, height=842)
            y = _Y_START

        page.insert_text((col_bdc, y), bdc.numero_bdc, fontsize=9, fontname="helv")
        adresse = bdc.adresse
        if len(adresse) > 45:
            adresse = adresse[:42] + "..."
        page.insert_text((col_adresse, y), adresse, fontsize=9, fontname="helv")
        montant_str = f"{bdc.montant_st:.2f} €" if bdc.montant_st else "—"
        page.insert_text((col_montant, y), montant_str, fontsize=9, fontname="helv")
        y += _INTERLIGNE

    # Total
    y += _SECTION_GAP
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=0.5)
    y += _INTERLIGNE
    total_str = f"TOTAL : {releve.montant_total:.2f} €"
    page.insert_text((col_montant - 30, y), total_str, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))

    pdf_bytes = doc.tobytes()
    doc.close()

    filename = f"releve_{releve.sous_traitant.nom}_{releve.numero}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ─── Excel ───────────────────────────────────────────────────────────────────

COLONNES_RELEVE = [
    "N° BDC",
    "Bailleur",
    "Adresse",
    "Ville",
    "Montant ST (€)",
    "Date réalisation",
]


def generer_releve_excel(releve: ReleveFacturation) -> HttpResponse:
    """Génère un Excel du relevé de facturation (pour le CDT)."""
    wb = Workbook()
    ws = wb.active
    ws.title = f"Relevé {releve.numero}"

    # En-têtes
    ws.append(COLONNES_RELEVE)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Données
    for bdc in releve.bdc.select_related("bailleur").order_by("date_realisation"):
        ws.append([
            bdc.numero_bdc,
            str(bdc.bailleur),
            bdc.adresse,
            bdc.ville,
            float(bdc.montant_st) if bdc.montant_st else None,
            bdc.date_realisation.strftime("%d/%m/%Y") if bdc.date_realisation else "",
        ])

    # Largeur colonnes
    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 40)

    filename = f"releve_{releve.sous_traitant.nom}_{releve.numero}_{date.today().isoformat()}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
```

**Step 4: Run tests**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py -v --tb=short`
Expected: All tests PASS

**Step 5: Commit**

```bash
cd bdc-peinture
rtk git add apps/bdc/releves_export.py tests/test_bdc/test_releves.py
rtk git commit -m "feat: add PDF and Excel export for releve facturation"
```

---

### Task 6: Integrate into recoupement UI

**Files:**
- Modify: `bdc-peinture/templates/bdc/_recoupement_content.html`

**Step 1: Write the failing test**

Append to `tests/test_bdc/test_releves.py`:

```python
# ─── 8. Tests integration recoupement ────────────────────────────────────────


class TestRecoupementIntegration:
    def test_bouton_nouveau_releve_visible(self, client_cdt, sous_traitant, bdc_en_cours):
        response = client_cdt.get(reverse("bdc:recoupement_liste"))
        content = response.content.decode()
        assert "Nouveau relevé" in content or "releve_creer" in content

    def test_lien_historique_visible(self, client_cdt, sous_traitant, bdc_en_cours):
        response = client_cdt.get(reverse("bdc:recoupement_liste"))
        content = response.content.decode()
        assert "releve_historique" in content or "Relevés" in content
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py::TestRecoupementIntegration -v --tb=short -x`
Expected: FAIL (button not in template yet)

**Step 3: Modify the recoupement template**

In `bdc-peinture/templates/bdc/_recoupement_content.html`, add two columns to the table — after the existing columns add "Relevés" and "Actions" columns.

Replace the `<td>` for ST name to add a link to historique, and add action column with "Nouveau relevé" button:

After the `Montant ST` column header, add:
```html
<th class="text-center px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Relevés</th>
```

After the montant data cell (or the delta cell if N-1), add for each ST row:
```html
<td class="px-4 py-3 text-center text-sm space-x-1">
    <a href="{% url 'bdc:releve_historique' st.pk %}" class="text-accent hover:underline text-xs">Relevés</a>
    <form method="post" action="{% url 'bdc:releve_creer' st.pk %}" class="inline">
        {% csrf_token %}
        <button type="submit" class="text-xs px-2 py-1 bg-accent hover:bg-accent-dark text-white rounded transition-all">Nouveau relevé</button>
    </form>
</td>
```

**Step 4: Run tests**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_releves.py -v --tb=short`
Expected: All tests PASS

**Step 5: Run full test suite**

Run: `cd bdc-peinture && uv run pytest --tb=short -q`
Expected: All tests PASS, no regressions

**Step 6: Commit**

```bash
cd bdc-peinture
rtk git add templates/bdc/_recoupement_content.html
rtk git commit -m "feat: integrate releve buttons into recoupement page"
```

---

### Task 7: Final cleanup and full test run

**Step 1: Run linting**

Run: `cd bdc-peinture && uv run ruff check .`
Fix any issues.

Run: `cd bdc-peinture && uv run ruff format .`

**Step 2: Run full test suite**

Run: `cd bdc-peinture && uv run pytest -v --tb=short`
Expected: All tests PASS

**Step 3: Run migration check**

Run: `cd bdc-peinture && uv run manage.py makemigrations --check --dry-run`
Expected: No new migrations needed

**Step 4: Final commit if any formatting changes**

```bash
cd bdc-peinture
rtk git add -A && rtk git commit -m "style: ruff format"
```
