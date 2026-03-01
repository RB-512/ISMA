# Analyse par periode de la charge ST — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ajouter un selecteur de periode sur la page recoupement et le tableau inline d'attribution, avec comparaison automatique N-1, pour permettre au CDT de piloter l'activite dans le temps.

**Architecture:** Enrichir les vues existantes (`recoupement_st_liste`, `attribution_partial`) avec un filtre par periode transmis en query params. Un helper commun `_get_repartition_st()` accepte des bornes de dates et calcule la periode + N-1. Un partial HTMX reutilisable pour le selecteur de periode. Date de reference = `Coalesce(date_emission, created_at)`.

**Tech Stack:** Django 5.1, HTMX 2.x, Tailwind CSS, `django.db.models.functions.Coalesce`

**Test command:** `.venv/Scripts/python.exe -m pytest` (pas `uv run` — uv non disponible dans le shell bash)

---

### Task 1: Helper `_calculer_bornes_periode`

**Files:**
- Create: `apps/bdc/periode.py`
- Create: `tests/test_bdc/test_periode.py`

**Step 1: Write the failing tests**

Create `tests/test_bdc/test_periode.py`:

```python
"""Tests unitaires du calcul de bornes de periode."""
from datetime import date

import pytest

from apps.bdc.periode import calculer_bornes_periode


class TestCalculerBornesPeriode:
    """Tests de calculer_bornes_periode()."""

    def test_mois_courant(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("mois", date(2026, 3, 15))
        assert du == date(2026, 3, 1)
        assert au == date(2026, 3, 31)
        assert du_n1 == date(2026, 2, 1)
        assert au_n1 == date(2026, 2, 28)

    def test_semaine(self):
        # 2026-03-04 est un mercredi → semaine lundi 2 → dimanche 8
        du, au, du_n1, au_n1 = calculer_bornes_periode("semaine", date(2026, 3, 4))
        assert du == date(2026, 3, 2)  # lundi
        assert au == date(2026, 3, 8)  # dimanche
        assert du_n1 == date(2026, 2, 23)
        assert au_n1 == date(2026, 3, 1)

    def test_trimestre(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("trimestre", date(2026, 5, 10))
        assert du == date(2026, 4, 1)  # T2
        assert au == date(2026, 6, 30)
        assert du_n1 == date(2026, 1, 1)  # T1
        assert au_n1 == date(2026, 3, 31)

    def test_annee(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("annee", date(2026, 7, 1))
        assert du == date(2026, 1, 1)
        assert au == date(2026, 12, 31)
        assert du_n1 == date(2025, 1, 1)
        assert au_n1 == date(2025, 12, 31)

    def test_custom_retourne_none(self):
        result = calculer_bornes_periode("custom", date(2026, 3, 1))
        assert result is None

    def test_sans_date_ref_utilise_aujourdhui(self):
        du, au, _, _ = calculer_bornes_periode("mois")
        assert du.day == 1
        assert du.month == date.today().month

    def test_periode_inconnue_retourne_none(self):
        result = calculer_bornes_periode("biannuel", date(2026, 1, 1))
        assert result is None

    def test_mois_janvier_n1_decembre(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("mois", date(2026, 1, 15))
        assert du == date(2026, 1, 1)
        assert au == date(2026, 1, 31)
        assert du_n1 == date(2025, 12, 1)
        assert au_n1 == date(2025, 12, 31)

    def test_trimestre_t1_n1_est_t4_annee_prec(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("trimestre", date(2026, 2, 1))
        assert du == date(2026, 1, 1)
        assert au == date(2026, 3, 31)
        assert du_n1 == date(2025, 10, 1)
        assert au_n1 == date(2025, 12, 31)
```

**Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_periode.py -v --tb=short`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.bdc.periode'`

**Step 3: Write minimal implementation**

Create `apps/bdc/periode.py`:

```python
"""Utilitaires de calcul de bornes de periode pour l'analyse de charge ST."""
import calendar
from datetime import date, timedelta


def calculer_bornes_periode(periode: str, date_ref: date | None = None):
    """
    Calcule les bornes d'une periode et de la periode precedente (N-1).

    Args:
        periode: "semaine", "mois", "trimestre", "annee", "custom"
        date_ref: date de reference (defaut: aujourd'hui)

    Returns:
        Tuple (date_du, date_au, date_du_n1, date_au_n1) ou None si custom/inconnu.
    """
    if date_ref is None:
        date_ref = date.today()

    if periode == "semaine":
        lundi = date_ref - timedelta(days=date_ref.weekday())
        dimanche = lundi + timedelta(days=6)
        lundi_n1 = lundi - timedelta(weeks=1)
        dimanche_n1 = lundi - timedelta(days=1)
        return lundi, dimanche, lundi_n1, dimanche_n1

    if periode == "mois":
        du = date_ref.replace(day=1)
        dernier_jour = calendar.monthrange(date_ref.year, date_ref.month)[1]
        au = date_ref.replace(day=dernier_jour)
        # N-1
        if date_ref.month == 1:
            du_n1 = date(date_ref.year - 1, 12, 1)
            au_n1 = date(date_ref.year - 1, 12, 31)
        else:
            du_n1 = date(date_ref.year, date_ref.month - 1, 1)
            dernier_n1 = calendar.monthrange(date_ref.year, date_ref.month - 1)[1]
            au_n1 = date(date_ref.year, date_ref.month - 1, dernier_n1)
        return du, au, du_n1, au_n1

    if periode == "trimestre":
        trimestre = (date_ref.month - 1) // 3
        mois_debut = trimestre * 3 + 1
        du = date(date_ref.year, mois_debut, 1)
        mois_fin = mois_debut + 2
        au = date(date_ref.year, mois_fin, calendar.monthrange(date_ref.year, mois_fin)[1])
        # N-1
        if trimestre == 0:
            du_n1 = date(date_ref.year - 1, 10, 1)
            au_n1 = date(date_ref.year - 1, 12, 31)
        else:
            mois_debut_n1 = (trimestre - 1) * 3 + 1
            mois_fin_n1 = mois_debut_n1 + 2
            du_n1 = date(date_ref.year, mois_debut_n1, 1)
            au_n1 = date(date_ref.year, mois_fin_n1, calendar.monthrange(date_ref.year, mois_fin_n1)[1])
        return du, au, du_n1, au_n1

    if periode == "annee":
        du = date(date_ref.year, 1, 1)
        au = date(date_ref.year, 12, 31)
        du_n1 = date(date_ref.year - 1, 1, 1)
        au_n1 = date(date_ref.year - 1, 12, 31)
        return du, au, du_n1, au_n1

    return None
```

**Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_periode.py -v --tb=short`
Expected: 9 passed

**Step 5: Commit**

```bash
git add apps/bdc/periode.py tests/test_bdc/test_periode.py
git commit -m "feat: add calculer_bornes_periode helper for period-based ST analysis"
```

---

### Task 2: Refactor `_get_repartition_st` to accept date filters

**Files:**
- Modify: `apps/bdc/views.py:565-582` (helper `_get_repartition_st`)
- Create: `tests/test_bdc/test_repartition_periode.py`

**Step 1: Write the failing tests**

Create `tests/test_bdc/test_repartition_periode.py`:

```python
"""Tests de _get_repartition_st avec filtres de periode."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.bdc.models import BonDeCommande, StatutChoices
from apps.bdc.services import attribuer_st
from apps.bdc.views import _get_repartition_st
from apps.sous_traitants.models import SousTraitant


@pytest.fixture
def client_cdt(utilisateur_cdt) -> Client:
    client = Client()
    client.login(username="cdt_test", password="testpass123")
    return client


@pytest.fixture
def st_alpha(db):
    return SousTraitant.objects.create(nom="Alpha Peinture", telephone="0600000001", actif=True)


@pytest.fixture
def st_beta(db):
    return SousTraitant.objects.create(nom="Beta Deco", telephone="0600000002", actif=True)


@pytest.fixture
def bdcs_multi_dates(db, bailleur_gdh, utilisateur_secretaire, st_alpha, st_beta, utilisateur_cdt):
    """Cree des BDC EN_COURS avec des date_emission differentes."""
    bdcs = []
    for num, st, emission, montant_ht in [
        ("P-JAN", st_alpha, date(2026, 1, 15), Decimal("1000")),
        ("P-FEV1", st_alpha, date(2026, 2, 10), Decimal("2000")),
        ("P-FEV2", st_beta, date(2026, 2, 20), Decimal("3000")),
        ("P-MAR", st_beta, date(2026, 3, 5), Decimal("4000")),
    ]:
        bdc = BonDeCommande.objects.create(
            numero_bdc=num, bailleur=bailleur_gdh,
            adresse="Test", code_postal="84000", ville="Avignon",
            objet_travaux="Test", occupation="OCCUPE",
            type_acces="BADGE_CODE", modalite_acces="Badge",
            cree_par=utilisateur_secretaire, statut=StatutChoices.A_FAIRE,
            date_emission=emission, montant_ht=montant_ht,
        )
        attribuer_st(bdc, st, Decimal("65"), utilisateur_cdt)
        bdcs.append(bdc)
    return bdcs


class TestGetRepartitionSTAvecPeriode:
    """Tests du helper _get_repartition_st avec filtres de dates."""

    def test_sans_filtre_retourne_tout(self, bdcs_multi_dates, st_alpha, st_beta):
        qs = _get_repartition_st()
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 2
        assert data["Beta Deco"].nb_bdc == 2

    def test_filtre_fevrier(self, bdcs_multi_dates, st_alpha, st_beta):
        qs = _get_repartition_st(date_du=date(2026, 2, 1), date_au=date(2026, 2, 28))
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 1
        assert data["Beta Deco"].nb_bdc == 1

    def test_filtre_montant_st(self, bdcs_multi_dates):
        qs = _get_repartition_st(date_du=date(2026, 2, 1), date_au=date(2026, 2, 28))
        data = {st.nom: st for st in qs}
        # Alpha: 2000 * 65% = 1300, Beta: 3000 * 65% = 1950
        assert data["Alpha Peinture"].total_montant_st == Decimal("1300.00")
        assert data["Beta Deco"].total_montant_st == Decimal("1950.00")

    def test_fallback_created_at_si_pas_date_emission(self, db, bailleur_gdh, utilisateur_secretaire,
                                                       st_alpha, utilisateur_cdt):
        bdc = BonDeCommande.objects.create(
            numero_bdc="NO-DATE", bailleur=bailleur_gdh,
            adresse="Test", code_postal="84000", ville="Avignon",
            objet_travaux="Test", occupation="OCCUPE",
            type_acces="BADGE_CODE", modalite_acces="Badge",
            cree_par=utilisateur_secretaire, statut=StatutChoices.A_FAIRE,
            date_emission=None,  # pas de date_emission
        )
        attribuer_st(bdc, st_alpha, Decimal("65"), utilisateur_cdt)
        # created_at est aujourd'hui → filtre sur le mois courant doit l'inclure
        today = date.today()
        import calendar
        dernier = calendar.monthrange(today.year, today.month)[1]
        qs = _get_repartition_st(date_du=today.replace(day=1), date_au=today.replace(day=dernier))
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 1

    def test_statuts_filtre(self, bdcs_multi_dates, st_alpha):
        # Par defaut EN_COURS seulement
        qs = _get_repartition_st(statuts=[StatutChoices.EN_COURS])
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 2

    def test_st_sans_bdc_affiche_zero(self, bdcs_multi_dates, db):
        SousTraitant.objects.create(nom="Zeta Vide", telephone="0600000099", actif=True)
        qs = _get_repartition_st(date_du=date(2026, 2, 1), date_au=date(2026, 2, 28))
        data = {st.nom: st for st in qs}
        assert data["Zeta Vide"].nb_bdc == 0
```

**Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_repartition_periode.py -v --tb=short`
Expected: FAIL (signature mismatch — `_get_repartition_st()` doesn't accept args, and no `nb_bdc` annotation)

**Step 3: Refactor `_get_repartition_st` in `apps/bdc/views.py`**

Replace lines 565-582 with:

```python
def _get_repartition_st(date_du=None, date_au=None, statuts=None):
    """
    Retourne tous les ST actifs avec leur charge (nb BDC + montant_st total).

    Args:
        date_du/date_au: bornes de periode (filtre sur Coalesce(date_emission, created_at)).
        statuts: liste de StatutChoices a filtrer (defaut: [EN_COURS]).
    """
    from django.db.models.functions import Coalesce

    from apps.sous_traitants.models import SousTraitant

    if statuts is None:
        statuts = [StatutChoices.EN_COURS]

    filtre = Q(bons_de_commande__statut__in=statuts)

    if date_du and date_au:
        date_ref = Coalesce("bons_de_commande__date_emission", "bons_de_commande__created_at__date")
        filtre &= Q(
            **{
                "bons_de_commande__in": BonDeCommande.objects.annotate(
                    _date_ref=Coalesce("date_emission", "created_at__date")
                ).filter(_date_ref__gte=date_du, _date_ref__lte=date_au)
            }
        )

    return (
        SousTraitant.objects.filter(actif=True)
        .annotate(
            nb_bdc=Count("bons_de_commande", filter=filtre),
            total_montant_st=Sum("bons_de_commande__montant_st", filter=filtre),
        )
        .order_by("nom")
    )
```

Also update all existing callers:
- `attribution_partial` (lines 611, 622): `_get_repartition_st()` calls remain unchanged (no args = default EN_COURS, no date filter)
- Update the `attribution_form.html` template: rename `nb_en_cours` to `nb_bdc` (line 21)

**Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_repartition_periode.py tests/test_bdc/test_attribution.py -v --tb=short`
Expected: All pass (new tests + existing attribution tests still work)

**Step 5: Commit**

```bash
git add apps/bdc/views.py templates/bdc/partials/attribution_form.html tests/test_bdc/test_repartition_periode.py
git commit -m "refactor: _get_repartition_st accepts date and statut filters with Coalesce fallback"
```

---

### Task 3: Period selector partial template

**Files:**
- Create: `templates/bdc/partials/period_selector.html`

**Step 1: Create the partial template**

```html
{# Selecteur de periode reutilisable.
   Context requis :
   - hx_target: id du target HTMX (ex: "#recoupement-table")
   - hx_url: URL a appeler avec les params de periode
   - periode_active: periode selectionnee ("semaine", "mois", "trimestre", "annee", "custom", ou "")
   - date_du / date_au: bornes actuelles (format YYYY-MM-DD)
#}
<div class="flex flex-wrap items-end gap-3">
    <div class="flex gap-1">
        {% for val, label in periodes %}
        <button hx-get="{{ hx_url }}?periode={{ val }}"
                hx-target="{{ hx_target }}" hx-swap="innerHTML"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors
                    {% if periode_active == val %}bg-primary text-white dark:bg-white dark:text-primary
                    {% else %}bg-[var(--color-surface-card)] border border-[var(--color-border)] text-[var(--color-text)] hover:bg-accent/10{% endif %}">
            {{ label }}
        </button>
        {% endfor %}
    </div>

    <div class="flex items-end gap-2">
        <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-0.5">Du</label>
            <input type="date" name="date_du" value="{{ date_du|default:'' }}"
                   class="px-2 py-1.5 text-xs border border-[var(--color-border)] rounded-lg bg-[var(--color-surface-card)] text-[var(--color-text)]"
                   id="period-du">
        </div>
        <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-0.5">Au</label>
            <input type="date" name="date_au" value="{{ date_au|default:'' }}"
                   class="px-2 py-1.5 text-xs border border-[var(--color-border)] rounded-lg bg-[var(--color-surface-card)] text-[var(--color-text)]"
                   id="period-au">
        </div>
        <button hx-get="{{ hx_url }}"
                hx-target="{{ hx_target }}" hx-swap="innerHTML"
                hx-include="#period-du, #period-au"
                class="px-3 py-1.5 text-xs font-medium rounded-lg bg-accent hover:bg-accent-dark text-white transition-colors">
            Appliquer
        </button>
        {% if periode_active or date_du %}
        <a href="{{ hx_url }}"
           hx-get="{{ hx_url }}"
           hx-target="{{ hx_target }}" hx-swap="innerHTML"
           class="px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            Reinitialiser
        </a>
        {% endif %}
    </div>
</div>
```

**Step 2: No test needed** (pure template, tested via integration in Tasks 4 and 5)

**Step 3: Commit**

```bash
git add templates/bdc/partials/period_selector.html
git commit -m "feat: add reusable period selector partial template"
```

---

### Task 4: Integrate period filter into recoupement page

**Files:**
- Modify: `apps/bdc/views.py:667-685` (view `recoupement_st_liste`)
- Modify: `templates/bdc/recoupement_liste.html`
- Create: `tests/test_bdc/test_recoupement_periode.py`

**Step 1: Write the failing tests**

Create `tests/test_bdc/test_recoupement_periode.py`:

```python
"""Tests de la page recoupement avec filtre de periode."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.bdc.models import BonDeCommande, StatutChoices
from apps.bdc.services import attribuer_st
from apps.sous_traitants.models import SousTraitant


@pytest.fixture
def client_cdt(utilisateur_cdt) -> Client:
    client = Client()
    client.login(username="cdt_test", password="testpass123")
    return client


@pytest.fixture
def setup_recoupement(db, bailleur_gdh, utilisateur_secretaire, utilisateur_cdt):
    """2 ST avec BDC sur des mois differents."""
    st1 = SousTraitant.objects.create(nom="Recoup Alpha", telephone="0600000001", actif=True)
    st2 = SousTraitant.objects.create(nom="Recoup Beta", telephone="0600000002", actif=True)

    for num, st, emission in [
        ("R-JAN", st1, date(2026, 1, 10)),
        ("R-FEV", st1, date(2026, 2, 15)),
        ("R-FEV2", st2, date(2026, 2, 20)),
    ]:
        bdc = BonDeCommande.objects.create(
            numero_bdc=num, bailleur=bailleur_gdh,
            adresse="Test", code_postal="84000", ville="Avignon",
            objet_travaux="Test", occupation="OCCUPE",
            type_acces="BADGE_CODE", modalite_acces="Badge",
            cree_par=utilisateur_secretaire, statut=StatutChoices.A_FAIRE,
            date_emission=emission, montant_ht=Decimal("1000"),
        )
        attribuer_st(bdc, st, Decimal("65"), utilisateur_cdt)
    return st1, st2


class TestRecoupementAvecPeriode:
    """Tests de la vue recoupement avec filtre de periode."""

    def test_sans_filtre_cumul_global(self, client_cdt, setup_recoupement):
        resp = client_cdt.get(reverse("bdc:recoupement_liste"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Recoup Alpha" in content
        assert "Recoup Beta" in content

    def test_filtre_mois_fevrier(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?date_du=2026-02-01&date_au=2026-02-28"
        resp = client_cdt.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Recoup Alpha" in content

    def test_filtre_periode_raccourci(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?periode=mois"
        resp = client_cdt.get(url)
        assert resp.status_code == 200

    def test_comparaison_n1_presente(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?periode=mois&date=2026-02-15"
        resp = client_cdt.get(url)
        content = resp.content.decode()
        # La colonne N-1 doit etre presente
        assert "N-1" in content or "riode pr" in content  # "Période préc."

    def test_htmx_retourne_partial(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?periode=mois"
        resp = client_cdt.get(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        content = resp.content.decode()
        # Pas de balise <html> dans un partial
        assert "<html" not in content.lower()
```

**Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_recoupement_periode.py -v --tb=short`
Expected: FAIL (view doesn't handle period params yet)

**Step 3: Modify `recoupement_st_liste` view**

In `apps/bdc/views.py`, replace lines 667-685:

```python
@group_required("CDT")
def recoupement_st_liste(request):
    """Liste des sous-traitants avec compteurs BDC par statut, filtrable par periode."""
    from apps.bdc.periode import calculer_bornes_periode

    statuts = [StatutChoices.EN_COURS, StatutChoices.A_FACTURER, StatutChoices.FACTURE]

    # Parse period params
    periode = request.GET.get("periode", "")
    date_du_str = request.GET.get("date_du", "")
    date_au_str = request.GET.get("date_au", "")
    date_du = date_au = date_du_n1 = date_au_n1 = None
    periode_active = ""

    if periode and periode != "custom":
        date_ref_str = request.GET.get("date", "")
        date_ref = _parse_date(date_ref_str) if date_ref_str else None
        bornes = calculer_bornes_periode(periode, date_ref)
        if bornes:
            date_du, date_au, date_du_n1, date_au_n1 = bornes
            periode_active = periode
    elif date_du_str and date_au_str:
        date_du = _parse_date(date_du_str)
        date_au = _parse_date(date_au_str)
        if date_du and date_au:
            delta = date_au - date_du
            date_au_n1 = date_du - timedelta(days=1)
            date_du_n1 = date_au_n1 - delta
            periode_active = "custom"

    sous_traitants = _get_repartition_st(date_du=date_du, date_au=date_au, statuts=statuts)

    # Periode N-1
    sous_traitants_n1 = None
    if date_du_n1 and date_au_n1:
        sous_traitants_n1_qs = _get_repartition_st(date_du=date_du_n1, date_au=date_au_n1, statuts=statuts)
        sous_traitants_n1 = {st.pk: st for st in sous_traitants_n1_qs}

    periodes_choices = [
        ("semaine", "Semaine"),
        ("mois", "Mois"),
        ("trimestre", "Trimestre"),
        ("annee", "Année"),
    ]

    context = {
        "sous_traitants": sous_traitants,
        "sous_traitants_n1": sous_traitants_n1,
        "periodes": periodes_choices,
        "periode_active": periode_active,
        "date_du": date_du.isoformat() if date_du else "",
        "date_au": date_au.isoformat() if date_au else "",
        "hx_url": reverse("bdc:recoupement_liste"),
        "hx_target": "#recoupement-content",
    }

    if request.headers.get("HX-Request"):
        return render(request, "bdc/_recoupement_content.html", context)

    return render(request, "bdc/recoupement_liste.html", context)
```

Add `from datetime import timedelta` to the imports at the top (line 7, add to `from datetime import date`):

```python
from datetime import date, timedelta
```

**Step 4: Update templates**

Modify `templates/bdc/recoupement_liste.html` to include the period selector and N-1 columns.

Create `templates/bdc/_recoupement_content.html` as a partial for HTMX responses.

The recoupement_liste.html wraps `_recoupement_content.html` inside the layout.
The `_recoupement_content.html` contains the period selector + table.

**Step 5: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_recoupement_periode.py -v --tb=short`
Expected: All pass

**Step 6: Run full test suite**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`
Expected: All pass

**Step 7: Commit**

```bash
git add apps/bdc/views.py templates/bdc/recoupement_liste.html templates/bdc/_recoupement_content.html tests/test_bdc/test_recoupement_periode.py
git commit -m "feat: add period filter with N-1 comparison to recoupement page"
```

---

### Task 5: Integrate period filter into attribution inline partial

**Files:**
- Modify: `apps/bdc/views.py:585-626` (view `attribution_partial`)
- Modify: `templates/bdc/partials/attribution_form.html`
- Add tests to: `tests/test_bdc/test_attribution.py`

**Step 1: Write the failing test**

Append to the existing `TestAttributionPartial` class in `tests/test_bdc/test_attribution.py`:

```python
    def test_get_avec_periode_filtre_repartition(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url + "?periode=mois")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Semaine" in content  # period selector present
        assert "Mois" in content
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_attribution.py::TestAttributionPartial::test_get_avec_periode_filtre_repartition -v --tb=short`
Expected: FAIL (period selector not in template yet)

**Step 3: Modify `attribution_partial` view**

Update the view to parse period params and pass them to `_get_repartition_st` and to the template context:

```python
@group_required("CDT")
def attribution_partial(request, pk: int):
    """Partial HTMX : tableau repartition ST + formulaire attribution/reattribution."""
    from apps.bdc.periode import calculer_bornes_periode

    bdc = get_object_or_404(BonDeCommande, pk=pk)
    reattribution = bdc.statut == StatutChoices.EN_COURS

    # Parse period params
    periode = request.GET.get("periode", "")
    date_du_str = request.GET.get("date_du", "")
    date_au_str = request.GET.get("date_au", "")
    date_du = date_au = date_du_n1 = date_au_n1 = None
    periode_active = ""

    if periode and periode != "custom":
        bornes = calculer_bornes_periode(periode)
        if bornes:
            date_du, date_au, date_du_n1, date_au_n1 = bornes
            periode_active = periode
    elif date_du_str and date_au_str:
        date_du = _parse_date(date_du_str)
        date_au = _parse_date(date_au_str)
        if date_du and date_au:
            delta = date_au - date_du
            date_au_n1 = date_du - timedelta(days=1)
            date_du_n1 = date_au_n1 - delta
            periode_active = "custom"

    if request.method == "POST":
        form = AttributionForm(request.POST)
        if form.is_valid():
            st = form.cleaned_data["sous_traitant"]
            pct = form.cleaned_data["pourcentage_st"]
            try:
                if reattribution:
                    reattribuer_st(bdc, st, pct, request.user)
                else:
                    attribuer_st(bdc, st, pct, request.user)
            except TransitionInvalide as e:
                messages.error(request, str(e))
                return redirect("bdc:detail", pk=pk)
            notifier_st_attribution(bdc)
            msg = "reattribue" if reattribution else "attribue"
            messages.success(request, f"BDC n\u00b0{bdc.numero_bdc} {msg} a {st}.")
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("bdc:detail", kwargs={"pk": bdc.pk})
            return response
        # Form invalide : re-render
        repartition = _get_repartition_st(date_du=date_du, date_au=date_au)
        repartition_n1 = None
        if date_du_n1 and date_au_n1:
            repartition_n1 = {st.pk: st for st in _get_repartition_st(date_du=date_du_n1, date_au=date_au_n1)}
        return render(request, "bdc/partials/attribution_form.html", {
            "bdc": bdc, "form": form, "reattribution": reattribution,
            "repartition": repartition, "repartition_n1": repartition_n1,
            "periodes": [("semaine", "Semaine"), ("mois", "Mois"), ("trimestre", "Trimestre"), ("annee", "Annee")],
            "periode_active": periode_active,
            "date_du": date_du.isoformat() if date_du else "",
            "date_au": date_au.isoformat() if date_au else "",
            "hx_url": reverse("bdc:attribution_partial", kwargs={"pk": bdc.pk}),
            "hx_target": "#attribution-zone",
        })

    # GET
    initial = {}
    if reattribution and bdc.sous_traitant:
        initial = {"sous_traitant": bdc.sous_traitant, "pourcentage_st": bdc.pourcentage_st}
    form = AttributionForm(initial=initial)
    repartition = _get_repartition_st(date_du=date_du, date_au=date_au)
    repartition_n1 = None
    if date_du_n1 and date_au_n1:
        repartition_n1 = {st.pk: st for st in _get_repartition_st(date_du=date_du_n1, date_au=date_au_n1)}

    return render(request, "bdc/partials/attribution_form.html", {
        "bdc": bdc, "form": form, "reattribution": reattribution,
        "repartition": repartition, "repartition_n1": repartition_n1,
        "periodes": [("semaine", "Semaine"), ("mois", "Mois"), ("trimestre", "Trimestre"), ("annee", "Annee")],
        "periode_active": periode_active,
        "date_du": date_du.isoformat() if date_du else "",
        "date_au": date_au.isoformat() if date_au else "",
        "hx_url": reverse("bdc:attribution_partial", kwargs={"pk": bdc.pk}),
        "hx_target": "#attribution-zone",
    })
```

**Step 4: Update `attribution_form.html`**

Add the period selector and N-1 columns to the template.

**Step 5: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_attribution.py -v --tb=short`
Expected: All pass (existing + new test)

**Step 6: Commit**

```bash
git add apps/bdc/views.py templates/bdc/partials/attribution_form.html tests/test_bdc/test_attribution.py
git commit -m "feat: add period filter to attribution inline partial"
```

---

### Task 6: Linting + full test suite + manual verification

**Step 1: Run ruff**

Run: `.venv/Scripts/python.exe -m ruff check apps/bdc/views.py apps/bdc/periode.py templates/`
Expected: All checks passed

**Step 2: Run full test suite**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`
Expected: All pass (existing + new)

**Step 3: Manual Playwright test**

- Navigate to `/recoupement/` as CDT
- Verify period selector appears
- Click "Mois" → table filters, N-1 columns appear with delta indicators
- Click "Reinitialiser" → back to cumul global
- Enter custom dates → click "Appliquer" → table filters
- Navigate to a BDC A_FAIRE detail → click "Attribuer"
- Verify period selector appears in the inline form
- Click "Mois" → repartition table updates with period filter

**Step 4: Commit (if any fixes needed)**

```bash
git commit -m "fix: linting and adjustments from manual testing"
```
