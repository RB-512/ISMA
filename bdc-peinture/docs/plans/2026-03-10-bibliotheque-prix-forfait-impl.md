# Bibliothèque de prix & attribution par forfait — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow CDT to attribute BDCs using either a percentage of montant_ht (existing) or a set of priced lines from a managed price library.

**Architecture:** New `PrixForfaitaire` model for the library, new `LigneForfaitAttribution` model for per-BDC lines. `mode_attribution` field on `BonDeCommande` determines which mode was used. Attribution views/forms updated with Alpine.js toggle. New CRUD page "Bibliothèque" in sidebar.

**Tech Stack:** Django 5.1, HTMX, Alpine.js, Tailwind CSS, pytest

---

### Task 1: Model `PrixForfaitaire`

**Files:**
- Modify: `apps/bdc/models.py`
- Create: `apps/bdc/migrations/0014_prixforfaitaire.py` (auto-generated)

**Step 1: Add the model**

In `apps/bdc/models.py`, after the `ConfigEmail` class (line ~106), add:

```python
# ─── PrixForfaitaire (bibliothèque de prix) ────────────────────────────────


class PrixForfaitaire(models.Model):
    """Ligne de la bibliothèque de prix forfaitaires du CDT."""

    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    unite = models.CharField(max_length=20, verbose_name="Unité", help_text="u, m², ml, forfait…")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (€)")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Prix forfaitaire"
        verbose_name_plural = "Prix forfaitaires"
        ordering = ["reference"]

    def __str__(self):
        return f"{self.reference} — {self.designation} ({self.prix_unitaire} €/{self.unite})"
```

**Step 2: Generate migration**

Run: `cd bdc-peinture && uv run manage.py makemigrations bdc -n prixforfaitaire`

**Step 3: Apply migration**

Run: `cd bdc-peinture && uv run manage.py migrate`

**Step 4: Commit**

```bash
git add apps/bdc/models.py apps/bdc/migrations/0014_prixforfaitaire.py
git commit -m "feat: add PrixForfaitaire model (bibliothèque de prix)"
```

---

### Task 2: Model `LigneForfaitAttribution` + `mode_attribution` on BDC

**Files:**
- Modify: `apps/bdc/models.py`
- Create: `apps/bdc/migrations/0015_ligneforfaitattribution.py` (auto-generated)

**Step 1: Add mode_attribution field to BonDeCommande**

In `apps/bdc/models.py`, in the `BonDeCommande` class, after `pourcentage_st` (line ~234), add:

```python
    mode_attribution = models.CharField(
        max_length=15,
        choices=[("pourcentage", "Pourcentage"), ("forfait", "Forfait")],
        blank=True,
        verbose_name="Mode d'attribution",
    )
```

**Step 2: Add LigneForfaitAttribution model**

After the `LignePrestation` class (line ~311), add:

```python
# ─── LigneForfaitAttribution ────────────────────────────────────────────────


class LigneForfaitAttribution(models.Model):
    """Ligne de devis forfaitaire attribuée à un BDC (mode forfait)."""

    bdc = models.ForeignKey(
        BonDeCommande,
        on_delete=models.CASCADE,
        related_name="lignes_forfait",
        verbose_name="BDC",
    )
    prix_forfaitaire = models.ForeignKey(
        PrixForfaitaire,
        on_delete=models.PROTECT,
        verbose_name="Prix forfaitaire",
    )
    quantite = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix unitaire (€)",
        help_text="Pré-rempli depuis la bibliothèque, modifiable",
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")

    class Meta:
        verbose_name = "Ligne forfait attribution"
        verbose_name_plural = "Lignes forfait attribution"

    def __str__(self):
        return f"{self.prix_forfaitaire.reference} × {self.quantite} = {self.montant} €"
```

**Step 3: Generate and apply migration**

Run: `cd bdc-peinture && uv run manage.py makemigrations bdc -n ligneforfaitattribution && uv run manage.py migrate`

**Step 4: Commit**

```bash
git add apps/bdc/models.py apps/bdc/migrations/0015_ligneforfaitattribution.py
git commit -m "feat: add LigneForfaitAttribution model and mode_attribution field"
```

---

### Task 3: Bibliothèque CRUD — URLs, views, forms

**Files:**
- Create: `apps/bdc/views_bibliotheque.py`
- Modify: `apps/bdc/urls.py`

**Step 1: Create views_bibliotheque.py**

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import group_required

from .models import PrixForfaitaire


@login_required
@group_required("CDT")
def bibliotheque_liste(request):
    """Liste des prix forfaitaires avec ajout inline."""
    prix = PrixForfaitaire.objects.all()
    return render(request, "bdc/bibliotheque.html", {"prix_list": prix})


@login_required
@group_required("CDT")
def bibliotheque_ajouter(request):
    """Ajout d'un prix forfaitaire (HTMX)."""
    if request.method != "POST":
        return HttpResponse(status=405)

    reference = request.POST.get("reference", "").strip()
    designation = request.POST.get("designation", "").strip()
    unite = request.POST.get("unite", "").strip()
    prix_unitaire = request.POST.get("prix_unitaire", "").strip()

    errors = []
    if not reference:
        errors.append("La référence est obligatoire.")
    if not designation:
        errors.append("La désignation est obligatoire.")
    if not unite:
        errors.append("L'unité est obligatoire.")
    if not prix_unitaire:
        errors.append("Le prix unitaire est obligatoire.")
    if PrixForfaitaire.objects.filter(reference=reference).exists():
        errors.append(f"La référence « {reference} » existe déjà.")

    if errors:
        for e in errors:
            messages.error(request, e)
        prix = PrixForfaitaire.objects.all()
        return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix})

    PrixForfaitaire.objects.create(
        reference=reference,
        designation=designation,
        unite=unite,
        prix_unitaire=prix_unitaire,
    )
    prix = PrixForfaitaire.objects.all()
    return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix})


@login_required
@group_required("CDT")
def bibliotheque_modifier(request, pk):
    """Modification d'un prix forfaitaire (HTMX)."""
    prix = get_object_or_404(PrixForfaitaire, pk=pk)

    if request.method == "GET":
        return render(request, "bdc/partials/_bibliotheque_row_edit.html", {"prix": prix})

    prix.reference = request.POST.get("reference", prix.reference).strip()
    prix.designation = request.POST.get("designation", prix.designation).strip()
    prix.unite = request.POST.get("unite", prix.unite).strip()
    prix.prix_unitaire = request.POST.get("prix_unitaire", prix.prix_unitaire)
    prix.save()

    prix_list = PrixForfaitaire.objects.all()
    return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix_list})


@login_required
@group_required("CDT")
def bibliotheque_supprimer(request, pk):
    """Suppression d'un prix forfaitaire (HTMX)."""
    prix = get_object_or_404(PrixForfaitaire, pk=pk)

    if prix.ligneforfaitattribution_set.exists():
        messages.error(request, "Ce prix est utilisé dans des attributions et ne peut pas être supprimé.")
    else:
        prix.delete()

    prix_list = PrixForfaitaire.objects.all()
    return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix_list})
```

**Step 2: Add URLs**

In `apps/bdc/urls.py`, add these imports and paths:

```python
from . import views_bibliotheque
```

Add to urlpatterns:
```python
    # ─── Bibliothèque de prix ──────────────────────────────────────────────
    path("bibliotheque/", views_bibliotheque.bibliotheque_liste, name="bibliotheque"),
    path("bibliotheque/ajouter/", views_bibliotheque.bibliotheque_ajouter, name="bibliotheque_ajouter"),
    path("bibliotheque/<int:pk>/modifier/", views_bibliotheque.bibliotheque_modifier, name="bibliotheque_modifier"),
    path("bibliotheque/<int:pk>/supprimer/", views_bibliotheque.bibliotheque_supprimer, name="bibliotheque_supprimer"),
```

**Step 3: Commit**

```bash
git add apps/bdc/views_bibliotheque.py apps/bdc/urls.py
git commit -m "feat: add Bibliothèque CRUD views and URLs"
```

---

### Task 4: Bibliothèque templates

**Files:**
- Create: `templates/bdc/bibliotheque.html`
- Create: `templates/bdc/partials/_bibliotheque_table.html`
- Create: `templates/bdc/partials/_bibliotheque_row_edit.html`

**Step 1: Create bibliotheque.html**

Main page extending base.html with:
- Title "Bibliothèque de prix"
- Add form row at top (reference, designation, unite, prix_unitaire, bouton Ajouter)
- `<div id="bibliotheque-table">` containing the table partial
- HTMX: add form posts to `bibliotheque_ajouter`, targets `#bibliotheque-table`

**Step 2: Create _bibliotheque_table.html**

Table partial with columns: Référence, Désignation, Unité, PU, Actions (Modifier, Supprimer).
- Modifier: `hx-get` to `bibliotheque_modifier` → swaps row to edit mode
- Supprimer: `hx-post` to `bibliotheque_supprimer` → reloads table

**Step 3: Create _bibliotheque_row_edit.html**

Single `<tr>` with input fields for reference, designation, unite, prix_unitaire.
- Save button: `hx-post` to `bibliotheque_modifier` → targets `#bibliotheque-table`
- Cancel button: `hx-get` reloads table

**Step 4: Add sidebar link**

In `templates/base.html`, after the "Sous-traitants" link (~line 166), add:

```html
<a href="{% url 'bdc:bibliotheque' %}" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
   {% if '/bibliotheque/' in request.path %}bg-white/15 text-white{% else %}text-white/70 hover:bg-white/10 hover:text-white{% endif %}">
    <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
    <span x-show="!$store.sidebar.collapsed" x-transition class="whitespace-nowrap">Bibliothèque</span>
</a>
```

**Step 5: Commit**

```bash
git add templates/bdc/bibliotheque.html templates/bdc/partials/_bibliotheque_table.html templates/bdc/partials/_bibliotheque_row_edit.html templates/base.html
git commit -m "feat: add Bibliothèque templates and sidebar link"
```

---

### Task 5: Tests Bibliothèque

**Files:**
- Create: `tests/test_bdc/test_bibliotheque.py`

**Step 1: Write tests**

```python
"""Tests CRUD Bibliothèque de prix forfaitaires."""

import pytest
from django.urls import reverse

from apps.bdc.models import PrixForfaitaire


@pytest.fixture
def prix_peinture_t2(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T2",
        designation="Peinture logement T2",
        unite="u",
        prix_unitaire="800.00",
    )


class TestBibliothequeAcces:
    def test_cdt_peut_acceder(self, client_cdt):
        resp = client_cdt.get(reverse("bdc:bibliotheque"))
        assert resp.status_code == 200

    def test_secretaire_refuse(self, client_secretaire):
        resp = client_secretaire.get(reverse("bdc:bibliotheque"))
        assert resp.status_code == 403


class TestBibliothequeAjouter:
    def test_ajout_ok(self, client_cdt):
        resp = client_cdt.post(reverse("bdc:bibliotheque_ajouter"), {
            "reference": "PEINT-T3",
            "designation": "Peinture logement T3",
            "unite": "u",
            "prix_unitaire": "1200.00",
        })
        assert resp.status_code == 200
        assert PrixForfaitaire.objects.filter(reference="PEINT-T3").exists()

    def test_ajout_doublon_refuse(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.post(reverse("bdc:bibliotheque_ajouter"), {
            "reference": "PEINT-T2",
            "designation": "Autre",
            "unite": "u",
            "prix_unitaire": "500.00",
        })
        assert resp.status_code == 200
        assert PrixForfaitaire.objects.filter(reference="PEINT-T2").count() == 1


class TestBibliothequeModifier:
    def test_modification_ok(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.post(
            reverse("bdc:bibliotheque_modifier", args=[prix_peinture_t2.pk]),
            {"reference": "PEINT-T2", "designation": "Peinture T2 modifié", "unite": "u", "prix_unitaire": "850.00"},
        )
        assert resp.status_code == 200
        prix_peinture_t2.refresh_from_db()
        assert prix_peinture_t2.designation == "Peinture T2 modifié"

    def test_get_retourne_formulaire_edition(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.get(reverse("bdc:bibliotheque_modifier", args=[prix_peinture_t2.pk]))
        assert resp.status_code == 200
        assert "PEINT-T2" in resp.content.decode()


class TestBibliothequeSupprimer:
    def test_suppression_ok(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.post(reverse("bdc:bibliotheque_supprimer", args=[prix_peinture_t2.pk]))
        assert resp.status_code == 200
        assert not PrixForfaitaire.objects.filter(pk=prix_peinture_t2.pk).exists()
```

**Step 2: Run tests**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_bibliotheque.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_bdc/test_bibliotheque.py
git commit -m "test: add tests for Bibliothèque CRUD"
```

---

### Task 6: Update attribution form — mode toggle

**Files:**
- Modify: `apps/bdc/forms.py`

**Step 1: Update AttributionForm**

Replace the existing `AttributionForm` with:

```python
class AttributionForm(forms.Form):
    """Formulaire d'attribution d'un BDC à un sous-traitant."""

    sous_traitant = forms.ModelChoiceField(
        queryset=SousTraitant.objects.filter(actif=True),
        label="Sous-traitant",
        empty_label="— Choisir un sous-traitant —",
    )
    mode_attribution = forms.ChoiceField(
        choices=[("pourcentage", "Pourcentage"), ("forfait", "Forfait")],
        initial="pourcentage",
        widget=forms.HiddenInput(),
    )
    pourcentage_st = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Pourcentage ST (%)",
        min_value=0,
        max_value=100,
        required=False,
    )
    commentaire = forms.CharField(
        required=False,
        label="Commentaire pour le sous-traitant",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Commentaire ajouté dans l'email au ST…"}),
    )

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode_attribution")
        if mode == "pourcentage" and not cleaned.get("pourcentage_st"):
            self.add_error("pourcentage_st", "Le pourcentage est obligatoire en mode pourcentage.")
        return cleaned
```

**Step 2: Commit**

```bash
git add apps/bdc/forms.py
git commit -m "feat: update AttributionForm with mode_attribution toggle"
```

---

### Task 7: Update services — forfait attribution logic

**Files:**
- Modify: `apps/bdc/services.py`

**Step 1: Update attribuer_st signature and logic**

Update `attribuer_st()` to accept optional `mode` and `lignes_forfait` params:

```python
def attribuer_st(
    bdc: BonDeCommande,
    sous_traitant: SousTraitant,
    pourcentage: Decimal | None,
    utilisateur: User,
    commentaire: str = "",
    mode: str = "pourcentage",
    lignes_forfait: list[dict] | None = None,
) -> BonDeCommande:
```

Inside the function, after setting sous_traitant:
- If `mode == "pourcentage"`: existing logic (calculate montant_st from pourcentage)
- If `mode == "forfait"`:
  - Import `LigneForfaitAttribution`
  - Delete existing `bdc.lignes_forfait.all()`
  - Create `LigneForfaitAttribution` for each line in `lignes_forfait`
  - `montant_st = sum of all line montants`
  - `pourcentage_st = (montant_st / montant_ht * 100)` if montant_ht else None
- Set `bdc.mode_attribution = mode`
- Add `mode_attribution` to `update_fields`

Do the same update for `reattribuer_st()`.

**Step 2: Commit**

```bash
git add apps/bdc/services.py
git commit -m "feat: support forfait mode in attribuer_st/reattribuer_st"
```

---

### Task 8: Update views — handle forfait POST data

**Files:**
- Modify: `apps/bdc/views.py`

**Step 1: Update attribuer_bdc, reattribuer_bdc, attribution_split, attribution_partial**

In all 4 views, after form validation, detect the mode:

```python
mode = form.cleaned_data.get("mode_attribution", "pourcentage")
lignes_forfait = None

if mode == "forfait":
    # Parse lignes from POST data (formset-like: ligne_0_prix, ligne_0_qty, ligne_0_pu)
    lignes_forfait = _parse_lignes_forfait(request.POST)

if reattribution:
    reattribuer_st(bdc, st, pct, request.user, commentaire=commentaire, mode=mode, lignes_forfait=lignes_forfait)
else:
    attribuer_st(bdc, st, pct, request.user, commentaire=commentaire, mode=mode, lignes_forfait=lignes_forfait)
```

Add helper `_parse_lignes_forfait(post_data)`:

```python
def _parse_lignes_forfait(post_data):
    """Parse les lignes forfait du POST (format: ligne_N_prix, ligne_N_qty, ligne_N_pu)."""
    lignes = []
    i = 0
    while f"ligne_{i}_prix" in post_data:
        prix_id = post_data.get(f"ligne_{i}_prix")
        qty = post_data.get(f"ligne_{i}_qty")
        pu = post_data.get(f"ligne_{i}_pu")
        if prix_id and qty and pu:
            lignes.append({"prix_id": int(prix_id), "quantite": Decimal(qty), "prix_unitaire": Decimal(pu)})
        i += 1
    return lignes
```

Also pass `prix_forfaitaires` (active list) to template context in all GET handlers:

```python
from .models import PrixForfaitaire
# In context building:
ctx["prix_forfaitaires"] = PrixForfaitaire.objects.filter(actif=True)
```

**Step 2: Commit**

```bash
git add apps/bdc/views.py
git commit -m "feat: handle forfait mode in attribution views"
```

---

### Task 9: Update attribution templates — Alpine.js mode toggle

**Files:**
- Modify: `templates/bdc/attribuer.html`
- Modify: `templates/bdc/partials/attribution_form.html`
- Modify: `templates/bdc/partials/_attribution_panel.html`

**Step 1: Add mode toggle UI**

In all three templates, replace the pourcentage field section with an Alpine.js component:

```html
<div x-data="{ mode: '{{ form.mode_attribution.value|default:'pourcentage' }}', lignes: [], total: 0 }">
    <input type="hidden" name="mode_attribution" :value="mode">

    {# Mode toggle #}
    <div class="flex rounded-lg border border-[var(--color-border)] overflow-hidden mb-4">
        <button type="button" @click="mode = 'pourcentage'"
                :class="mode === 'pourcentage' ? 'bg-accent text-white' : 'bg-[var(--color-surface-card)] text-[var(--color-text)]'"
                class="flex-1 px-4 py-2 text-sm font-medium transition-colors">
            Pourcentage
        </button>
        <button type="button" @click="mode = 'forfait'"
                :class="mode === 'forfait' ? 'bg-accent text-white' : 'bg-[var(--color-surface-card)] text-[var(--color-text)]'"
                class="flex-1 px-4 py-2 text-sm font-medium transition-colors">
            Forfait
        </button>
    </div>

    {# Mode pourcentage #}
    <div x-show="mode === 'pourcentage'">
        <label>Pourcentage ST (%)</label>
        {{ form.pourcentage_st }}
    </div>

    {# Mode forfait #}
    <div x-show="mode === 'forfait'">
        {# Ligne selector: dropdown prix + qty + PU + bouton ajouter #}
        <div class="flex gap-2 mb-3">
            <select x-ref="prixSelect" class="flex-1 ...">
                <option value="">— Choisir —</option>
                {% for p in prix_forfaitaires %}
                <option value="{{ p.pk }}" data-pu="{{ p.prix_unitaire }}" data-ref="{{ p.reference }}" data-des="{{ p.designation }}" data-unite="{{ p.unite }}">
                    {{ p.reference }} — {{ p.designation }} ({{ p.prix_unitaire }} €/{{ p.unite }})
                </option>
                {% endfor %}
            </select>
            <input type="number" x-ref="qtyInput" placeholder="Qté" step="0.01" min="0.01" class="w-20 ...">
            <button type="button" @click="..." class="px-3 py-2 bg-accent text-white rounded-lg text-sm">+</button>
        </div>

        {# Table of added lines #}
        <table x-show="lignes.length > 0">
            <thead><tr><th>Réf</th><th>Désignation</th><th>Qté</th><th>PU</th><th>Montant</th><th></th></tr></thead>
            <tbody>
                <template x-for="(l, idx) in lignes" :key="idx">
                    <tr>
                        <td x-text="l.ref"></td>
                        <td x-text="l.des"></td>
                        <td><input :name="'ligne_'+idx+'_qty'" x-model="l.qty" type="number" step="0.01" @input="l.montant = (l.qty * l.pu).toFixed(2); total = lignes.reduce((s,x) => s + parseFloat(x.montant), 0).toFixed(2)"></td>
                        <td><input :name="'ligne_'+idx+'_pu'" x-model="l.pu" type="number" step="0.01" @input="l.montant = (l.qty * l.pu).toFixed(2); total = lignes.reduce((s,x) => s + parseFloat(x.montant), 0).toFixed(2)"></td>
                        <td x-text="l.montant + ' €'"></td>
                        <td><button type="button" @click="lignes.splice(idx, 1); total = lignes.reduce((s,x) => s + parseFloat(x.montant), 0).toFixed(2)">✕</button></td>
                        <input type="hidden" :name="'ligne_'+idx+'_prix'" :value="l.prix_id">
                    </tr>
                </template>
            </tbody>
            <tfoot>
                <tr><td colspan="4" class="text-right font-semibold">Total :</td><td x-text="total + ' €'" class="font-mono font-semibold"></td><td></td></tr>
            </tfoot>
        </table>
    </div>
</div>
```

**Step 2: Commit**

```bash
git add templates/bdc/attribuer.html templates/bdc/partials/attribution_form.html templates/bdc/partials/_attribution_panel.html
git commit -m "feat: add forfait/pourcentage mode toggle in attribution templates"
```

---

### Task 10: Tests attribution forfait

**Files:**
- Modify: `tests/test_bdc/test_attribution.py`

**Step 1: Add fixture and tests**

```python
from apps.bdc.models import LigneForfaitAttribution, PrixForfaitaire


@pytest.fixture
def prix_t2(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T2", designation="Peinture T2", unite="u", prix_unitaire="800.00"
    )


@pytest.fixture
def prix_t3(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T3", designation="Peinture T3", unite="u", prix_unitaire="1200.00"
    )


class TestAttribuerForfait:
    def test_attribution_forfait_cree_lignes(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_t2, prix_t3):
        lignes = [
            {"prix_id": prix_t2.pk, "quantite": Decimal("2"), "prix_unitaire": Decimal("800.00")},
            {"prix_id": prix_t3.pk, "quantite": Decimal("1"), "prix_unitaire": Decimal("1200.00")},
        ]
        bdc = attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt, mode="forfait", lignes_forfait=lignes)

        assert bdc.mode_attribution == "forfait"
        assert bdc.montant_st == Decimal("2800.00")  # 2*800 + 1*1200
        assert bdc.lignes_forfait.count() == 2

    def test_attribution_forfait_pu_modifiable(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_t2):
        lignes = [{"prix_id": prix_t2.pk, "quantite": Decimal("1"), "prix_unitaire": Decimal("750.00")}]
        bdc = attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt, mode="forfait", lignes_forfait=lignes)

        assert bdc.montant_st == Decimal("750.00")
        assert bdc.lignes_forfait.first().prix_unitaire == Decimal("750.00")

    def test_attribution_pourcentage_inchangee(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc_a_faire.montant_ht = Decimal("1000.00")
        bdc_a_faire.save(update_fields=["montant_ht"])
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.mode_attribution == "pourcentage"
        assert bdc.montant_st == Decimal("650.00")
        assert bdc.lignes_forfait.count() == 0


class TestAttribuerForfaitVue:
    def test_post_forfait_via_vue(self, client_cdt, bdc_a_faire, sous_traitant, prix_t2):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.post(url, {
            "sous_traitant": sous_traitant.pk,
            "mode_attribution": "forfait",
            "ligne_0_prix": prix_t2.pk,
            "ligne_0_qty": "3",
            "ligne_0_pu": "800.00",
        })
        assert resp.status_code == 302
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.mode_attribution == "forfait"
        assert bdc_a_faire.montant_st == Decimal("2400.00")
```

**Step 2: Run tests**

Run: `cd bdc-peinture && uv run pytest tests/test_bdc/test_attribution.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_bdc/test_attribution.py
git commit -m "test: add tests for forfait attribution mode"
```

---

### Task 11: Lint, format, final check

**Step 1: Lint and format**

Run: `cd bdc-peinture && uv run ruff check --fix . && uv run ruff format .`

**Step 2: Run full test suite**

Run: `cd bdc-peinture && uv run pytest -v --tb=short`
Expected: All PASS

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: lint and format"
```
