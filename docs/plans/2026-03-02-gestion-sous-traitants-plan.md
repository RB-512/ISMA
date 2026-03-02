# Gestion des sous-traitants (CRUD) — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ajouter le CRUD complet des sous-traitants dans l'interface utilisateur (création, modification, désactivation) avec les champs SIRET et adresse.

**Architecture:** Ajout de 2 champs au modèle existant + migration. Un ModelForm unique pour création/modification. 3 vues function-based avec `@group_required("CDT", "Secretaire")`. Templates Tailwind cohérents avec l'existant.

**Tech Stack:** Django 5.1, pytest, Tailwind CSS, HTMX (toggle inactifs)

---

### Task 1: Migration — Ajouter champs siret et adresse

**Files:**
- Modify: `bdc-peinture/apps/sous_traitants/models.py`
- Create: `bdc-peinture/apps/sous_traitants/migrations/0002_add_siret_adresse.py` (auto-generated)

**Step 1: Ajouter les champs au modèle**

Dans `apps/sous_traitants/models.py`, ajouter après le champ `email` :

```python
siret = models.CharField(max_length=14, blank=True, verbose_name="SIRET")
adresse = models.TextField(blank=True, verbose_name="Adresse")
```

**Step 2: Générer la migration**

Run: `cd bdc-peinture && uv run manage.py makemigrations sous_traitants`
Expected: `Migrations for 'sous_traitants': ... - Add field siret ... - Add field adresse ...`

**Step 3: Appliquer la migration**

Run: `cd bdc-peinture && uv run manage.py migrate sous_traitants`
Expected: `Applying sous_traitants.0002_... OK`

**Step 4: Mettre à jour l'admin**

Dans `apps/sous_traitants/admin.py`, ajouter `siret` et `adresse` :

```python
@admin.register(SousTraitant)
class SousTraitantAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email", "siret", "actif")
    list_filter = ("actif",)
    search_fields = ("nom", "telephone", "email", "siret")
```

**Step 5: Commit**

```bash
git add apps/sous_traitants/models.py apps/sous_traitants/migrations/ apps/sous_traitants/admin.py
git commit -m "feat(sous_traitants): ajouter champs siret et adresse au modèle"
```

---

### Task 2: Formulaire SousTraitantForm

**Files:**
- Create: `bdc-peinture/apps/sous_traitants/forms.py`
- Create: `bdc-peinture/tests/test_sous_traitants/__init__.py`
- Create: `bdc-peinture/tests/test_sous_traitants/test_forms.py`

**Step 1: Write the failing tests**

Créer `tests/test_sous_traitants/__init__.py` (vide).

Créer `tests/test_sous_traitants/test_forms.py` :

```python
import pytest

from apps.sous_traitants.forms import SousTraitantForm


@pytest.mark.django_db
class TestSousTraitantForm:
    def test_form_valide_champs_minimaux(self):
        form = SousTraitantForm(data={"nom": "Dupont Peinture", "telephone": "0612345678"})
        assert form.is_valid()

    def test_form_valide_tous_champs(self):
        form = SousTraitantForm(
            data={
                "nom": "Dupont Peinture",
                "telephone": "0612345678",
                "email": "contact@dupont.fr",
                "siret": "12345678901234",
                "adresse": "10 Rue de la Paix, 84000 Avignon",
                "actif": True,
            }
        )
        assert form.is_valid()

    def test_nom_obligatoire(self):
        form = SousTraitantForm(data={"telephone": "0612345678"})
        assert not form.is_valid()
        assert "nom" in form.errors

    def test_telephone_obligatoire(self):
        form = SousTraitantForm(data={"nom": "Dupont Peinture"})
        assert not form.is_valid()
        assert "telephone" in form.errors

    def test_siret_14_chiffres_valide(self):
        form = SousTraitantForm(data={"nom": "Test", "telephone": "0600000000", "siret": "12345678901234"})
        assert form.is_valid()

    def test_siret_trop_court_invalide(self):
        form = SousTraitantForm(data={"nom": "Test", "telephone": "0600000000", "siret": "1234"})
        assert not form.is_valid()
        assert "siret" in form.errors

    def test_siret_avec_lettres_invalide(self):
        form = SousTraitantForm(data={"nom": "Test", "telephone": "0600000000", "siret": "1234567890ABCD"})
        assert not form.is_valid()
        assert "siret" in form.errors

    def test_siret_vide_accepte(self):
        form = SousTraitantForm(data={"nom": "Test", "telephone": "0600000000", "siret": ""})
        assert form.is_valid()
```

**Step 2: Run tests to verify they fail**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/test_forms.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.sous_traitants.forms'`

**Step 3: Write the form**

Créer `apps/sous_traitants/forms.py` :

```python
import re

from django import forms

from .models import SousTraitant


class SousTraitantForm(forms.ModelForm):
    class Meta:
        model = SousTraitant
        fields = ["nom", "telephone", "email", "siret", "adresse", "actif"]
        widgets = {
            "adresse": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_siret(self):
        siret = self.cleaned_data.get("siret", "").strip()
        if siret and not re.fullmatch(r"\d{14}", siret):
            raise forms.ValidationError("Le SIRET doit contenir exactement 14 chiffres.")
        return siret
```

**Step 4: Run tests to verify they pass**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/test_forms.py -v`
Expected: 8 passed

**Step 5: Commit**

```bash
git add apps/sous_traitants/forms.py tests/test_sous_traitants/
git commit -m "feat(sous_traitants): formulaire SousTraitantForm avec validation SIRET"
```

---

### Task 3: Vues création et modification

**Files:**
- Modify: `bdc-peinture/apps/sous_traitants/views.py`
- Modify: `bdc-peinture/apps/sous_traitants/urls.py`
- Create: `bdc-peinture/tests/test_sous_traitants/test_views.py`

**Step 1: Write the failing tests**

Créer `tests/test_sous_traitants/test_views.py` :

```python
import pytest
from django.urls import reverse

from apps.sous_traitants.models import SousTraitant


@pytest.mark.django_db
class TestCreerSousTraitant:
    def test_get_formulaire(self, client_secretaire):
        resp = client_secretaire.get(reverse("sous_traitants:create"))
        assert resp.status_code == 200

    def test_creation_valide(self, client_secretaire):
        resp = client_secretaire.post(
            reverse("sous_traitants:create"),
            data={"nom": "Martin Peinture", "telephone": "0699887766", "actif": True},
        )
        assert resp.status_code == 302
        assert SousTraitant.objects.filter(nom="Martin Peinture").exists()

    def test_creation_avec_siret(self, client_cdt):
        resp = client_cdt.post(
            reverse("sous_traitants:create"),
            data={
                "nom": "Artisan Pro",
                "telephone": "0611223344",
                "siret": "12345678901234",
                "actif": True,
            },
        )
        assert resp.status_code == 302
        st = SousTraitant.objects.get(nom="Artisan Pro")
        assert st.siret == "12345678901234"

    def test_creation_siret_invalide(self, client_secretaire):
        resp = client_secretaire.post(
            reverse("sous_traitants:create"),
            data={"nom": "Test", "telephone": "0600000000", "siret": "123", "actif": True},
        )
        assert resp.status_code == 200  # formulaire avec erreurs, pas de redirect

    def test_non_authentifie_redirige(self, client):
        resp = client.get(reverse("sous_traitants:create"))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url


@pytest.mark.django_db
class TestModifierSousTraitant:
    def test_get_formulaire(self, client_cdt, sous_traitant):
        resp = client_cdt.get(reverse("sous_traitants:update", kwargs={"pk": sous_traitant.pk}))
        assert resp.status_code == 200

    def test_modification_valide(self, client_cdt, sous_traitant):
        resp = client_cdt.post(
            reverse("sous_traitants:update", kwargs={"pk": sous_traitant.pk}),
            data={"nom": "Dupont Rénové", "telephone": "0612345678", "actif": True},
        )
        assert resp.status_code == 302
        sous_traitant.refresh_from_db()
        assert sous_traitant.nom == "Dupont Rénové"

    def test_desactiver_sous_traitant(self, client_secretaire, sous_traitant):
        resp = client_secretaire.post(
            reverse("sous_traitants:update", kwargs={"pk": sous_traitant.pk}),
            data={"nom": sous_traitant.nom, "telephone": sous_traitant.telephone},
            # actif non coché → False
        )
        assert resp.status_code == 302
        sous_traitant.refresh_from_db()
        assert sous_traitant.actif is False
```

**Step 2: Run tests to verify they fail**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/test_views.py -v`
Expected: FAIL with `NoReverseMatch: 'create' is not a valid view function`

**Step 3: Write the views and URLs**

Modifier `apps/sous_traitants/views.py` :

```python
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from apps.accounts.decorators import group_required

from .forms import SousTraitantForm
from .models import SousTraitant


class SousTraitantListView(ListView):
    model = SousTraitant
    template_name = "sous_traitants/list.html"
    context_object_name = "sous_traitants"

    def get_queryset(self):
        qs = SousTraitant.objects.all()
        if not self.request.GET.get("inactifs"):
            qs = qs.filter(actif=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["afficher_inactifs"] = bool(self.request.GET.get("inactifs"))
        return ctx


@group_required("CDT", "Secretaire")
def creer_sous_traitant(request):
    if request.method == "GET":
        form = SousTraitantForm()
        return render(request, "sous_traitants/form.html", {"form": form, "titre": "Nouveau sous-traitant"})

    form = SousTraitantForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f"Sous-traitant « {form.instance.nom} » créé.")
        return redirect("sous_traitants:list")

    return render(request, "sous_traitants/form.html", {"form": form, "titre": "Nouveau sous-traitant"})


@group_required("CDT", "Secretaire")
def modifier_sous_traitant(request, pk):
    st = get_object_or_404(SousTraitant, pk=pk)

    if request.method == "GET":
        form = SousTraitantForm(instance=st)
        return render(request, "sous_traitants/form.html", {"form": form, "titre": f"Modifier {st.nom}", "st": st})

    form = SousTraitantForm(request.POST, instance=st)
    if form.is_valid():
        form.save()
        messages.success(request, f"Sous-traitant « {st.nom} » mis à jour.")
        return redirect("sous_traitants:list")

    return render(request, "sous_traitants/form.html", {"form": form, "titre": f"Modifier {st.nom}", "st": st})
```

Modifier `apps/sous_traitants/urls.py` :

```python
from django.urls import path

from . import views

app_name = "sous_traitants"

urlpatterns = [
    path("", views.SousTraitantListView.as_view(), name="list"),
    path("nouveau/", views.creer_sous_traitant, name="create"),
    path("<int:pk>/modifier/", views.modifier_sous_traitant, name="update"),
]
```

**Step 4: Run tests to verify they pass**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/test_views.py -v`
Expected: 8 passed

**Step 5: Commit**

```bash
git add apps/sous_traitants/views.py apps/sous_traitants/urls.py tests/test_sous_traitants/test_views.py
git commit -m "feat(sous_traitants): vues création et modification avec permissions CDT+Secrétaire"
```

---

### Task 4: Template formulaire (création/modification)

**Files:**
- Create: `bdc-peinture/templates/sous_traitants/form.html`

**Step 1: Créer le template**

Créer `templates/sous_traitants/form.html` — reprendre le style de `bdc/attribuer.html` :

```html
{% extends "base.html" %}

{% block title %}{{ titre }} — ISMA{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto space-y-6">

    <div>
        <h1 class="text-2xl font-bold text-[var(--color-text)]">{{ titre }}</h1>
    </div>

    <section class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-5">
        <form method="POST">
            {% csrf_token %}
            <div class="space-y-4 text-sm">
                {% for field in form %}
                {% if field.name != "actif" %}
                <div>
                    <label for="{{ field.id_for_label }}" class="block text-sm font-medium text-[var(--color-text)] mb-1">
                        {{ field.label }}{% if field.field.required %} <span class="text-danger">*</span>{% endif %}
                    </label>
                    {{ field }}
                    {% if field.help_text %}
                    <p class="text-xs text-[var(--color-text-muted)] mt-1">{{ field.help_text }}</p>
                    {% endif %}
                    {% for error in field.errors %}
                    <p class="text-danger text-xs mt-1">{{ error }}</p>
                    {% endfor %}
                </div>
                {% endif %}
                {% endfor %}

                {# Actif — checkbox séparée #}
                <div class="flex items-center gap-2 pt-2">
                    {{ form.actif }}
                    <label for="{{ form.actif.id_for_label }}" class="text-sm text-[var(--color-text)]">
                        {{ form.actif.label }}
                    </label>
                </div>
            </div>

            <div class="mt-6 flex items-center gap-3">
                <button type="submit" class="px-5 py-2.5 bg-accent hover:bg-accent-dark text-white text-sm font-medium rounded-lg transition-all duration-150 shadow-sm hover:shadow-md">
                    {% if st %}Enregistrer{% else %}Créer{% endif %}
                </button>
                <a href="{% url 'sous_traitants:list' %}" class="px-4 py-2 bg-[var(--color-surface-card)] border border-[var(--color-border)] text-[var(--color-text)] text-sm font-medium rounded-lg hover:bg-accent/10 transition-colors">
                    Annuler
                </a>
            </div>
        </form>
    </section>

</div>
{% endblock %}
```

**Step 2: Vérifier que les tests passent toujours**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/ -v`
Expected: All passed

**Step 3: Commit**

```bash
git add templates/sous_traitants/form.html
git commit -m "feat(sous_traitants): template formulaire création/modification"
```

---

### Task 5: Enrichir le template liste

**Files:**
- Modify: `bdc-peinture/templates/sous_traitants/list.html`
- Create: `bdc-peinture/tests/test_sous_traitants/test_liste.py`

**Step 1: Write the failing tests**

Créer `tests/test_sous_traitants/test_liste.py` :

```python
import pytest
from django.urls import reverse

from apps.sous_traitants.models import SousTraitant


@pytest.mark.django_db
class TestListeSousTraitants:
    def test_liste_affiche_actifs(self, client_secretaire, sous_traitant):
        resp = client_secretaire.get(reverse("sous_traitants:list"))
        assert resp.status_code == 200
        assert sous_traitant.nom in resp.content.decode()

    def test_liste_masque_inactifs_par_defaut(self, client_secretaire, sous_traitant):
        sous_traitant.actif = False
        sous_traitant.save()
        resp = client_secretaire.get(reverse("sous_traitants:list"))
        assert sous_traitant.nom not in resp.content.decode()

    def test_liste_affiche_inactifs_avec_toggle(self, client_secretaire, sous_traitant):
        sous_traitant.actif = False
        sous_traitant.save()
        resp = client_secretaire.get(reverse("sous_traitants:list") + "?inactifs=1")
        assert sous_traitant.nom in resp.content.decode()

    def test_bouton_nouveau_present(self, client_secretaire):
        resp = client_secretaire.get(reverse("sous_traitants:list"))
        assert "Nouveau sous-traitant" in resp.content.decode()

    def test_lien_modifier_present(self, client_secretaire, sous_traitant):
        resp = client_secretaire.get(reverse("sous_traitants:list"))
        assert f"/sous-traitants/{sous_traitant.pk}/modifier/" in resp.content.decode()
```

**Step 2: Run tests to verify they fail**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/test_liste.py -v`
Expected: Some fail (bouton nouveau, lien modifier, toggle inactifs)

**Step 3: Mettre à jour le template liste**

Réécrire `templates/sous_traitants/list.html` :

```html
{% extends "base.html" %}

{% block title %}Sous-traitants — ISMA{% endblock %}

{% block content %}
<div class="space-y-6">

    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-[var(--color-text)]">Sous-traitants</h1>
        <a href="{% url 'sous_traitants:create' %}" class="px-4 py-2 bg-accent hover:bg-accent-dark text-white text-sm font-medium rounded-lg transition-all duration-150 shadow-sm hover:shadow-md">
            Nouveau sous-traitant
        </a>
    </div>

    {# Toggle inactifs #}
    <div class="flex items-center gap-2 text-sm">
        {% if afficher_inactifs %}
        <a href="{% url 'sous_traitants:list' %}" class="text-accent hover:underline">Masquer les inactifs</a>
        {% else %}
        <a href="{% url 'sous_traitants:list' %}?inactifs=1" class="text-[var(--color-text-muted)] hover:text-accent hover:underline">Afficher les inactifs</a>
        {% endif %}
    </div>

    {% if sous_traitants %}
    <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] overflow-hidden">
        <table class="min-w-full divide-y divide-[var(--color-border)]">
            <thead>
                <tr class="bg-primary/5 dark:bg-white/5">
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Nom</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Téléphone</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Email</th>
                    <th class="text-left px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">SIRET</th>
                    <th class="text-right px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
                {% for st in sous_traitants %}
                <tr class="hover:bg-accent/5 dark:hover:bg-accent/10 transition-colors duration-100 {% if not st.actif %}opacity-50{% endif %}">
                    <td class="px-4 py-3 text-sm font-medium text-[var(--color-text)]">
                        {{ st.nom }}
                        {% if not st.actif %}
                        <span class="ml-1 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">inactif</span>
                        {% endif %}
                    </td>
                    <td class="px-4 py-3 text-sm font-mono text-[var(--color-text)]">{{ st.telephone }}</td>
                    <td class="px-4 py-3 text-sm text-[var(--color-text)]">{{ st.email|default:"—" }}</td>
                    <td class="px-4 py-3 text-sm font-mono text-[var(--color-text)]">{{ st.siret|default:"—" }}</td>
                    <td class="px-4 py-3 text-sm text-right">
                        <a href="{% url 'sous_traitants:update' st.pk %}" class="text-accent hover:underline">Modifier</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-12 text-center">
        <p class="text-[var(--color-text-muted)]">Aucun sous-traitant{% if not afficher_inactifs %} actif{% endif %}.</p>
    </div>
    {% endif %}

</div>
{% endblock %}
```

**Step 4: Run tests to verify they pass**

Run: `cd bdc-peinture && uv run pytest tests/test_sous_traitants/ -v`
Expected: All passed

**Step 5: Commit**

```bash
git add templates/sous_traitants/list.html tests/test_sous_traitants/test_liste.py
git commit -m "feat(sous_traitants): liste enrichie avec bouton créer, modifier, toggle inactifs"
```

---

### Task 6: Tests de régression et vérification finale

**Files:**
- All test files in `tests/test_sous_traitants/`

**Step 1: Lancer tous les tests du projet**

Run: `cd bdc-peinture && uv run pytest -v --tb=short`
Expected: All passed (y compris les tests existants non impactés)

**Step 2: Lancer le linting**

Run: `cd bdc-peinture && uv run ruff check .`
Expected: No errors

**Step 3: Vérifier le formatage**

Run: `cd bdc-peinture && uv run ruff format --check .`
Expected: All files already formatted (or fix with `uv run ruff format .`)

**Step 4: Commit final si corrections**

Si des corrections de lint/format ont été nécessaires :

```bash
git add -A
git commit -m "style: ruff format sur les fichiers sous_traitants"
```
