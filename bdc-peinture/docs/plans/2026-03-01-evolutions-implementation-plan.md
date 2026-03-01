# Évolutions Contrôle, Attribution & Dashboard — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Three improvements: (1) contrôle form with required fields + rename + remove modalite_acces + CDT renvoi, (2) sidebar read-only after contrôle + toast, (3) collapsible dashboard search.

**Architecture:** Modify existing Django forms (BDCEditionForm), views, services (new transition A_FAIRE→A_TRAITER), templates (controle.html, _detail_sidebar.html, _liste_partial.html, detail.html). Add new model choice RENVOI, new URL + view for renvoi. No new models or migrations beyond adding RENVOI to ActionChoices.

**Tech Stack:** Django 5.1, HTMX 2.x, Alpine.js 3.x, Tailwind CSS, pytest + pytest-django

**Test runner:** `.venv/Scripts/python.exe -m pytest` (uv not available in shell)

**Linter:** `.venv/Scripts/python.exe -m ruff check`

---

## Task 1: Form — Remove modalite_acces, rename notes, add required + clean()

**Files:**
- Modify: `apps/bdc/forms.py:110-129`
- Test: `tests/test_bdc/test_controle.py` (new file)

**Step 1: Write tests for the form changes**

Create `tests/test_bdc/test_controle.py`:

```python
import pytest
from apps.bdc.forms import BDCEditionForm
from apps.bdc.models import BonDeCommande


class TestBDCEditionForm:
    """Tests for BDCEditionForm field changes."""

    def test_modalite_acces_not_in_fields(self):
        """modalite_acces field was removed from form."""
        assert "modalite_acces" not in BDCEditionForm.Meta.fields

    def test_notes_label_is_commentaires(self, bdc_a_traiter):
        form = BDCEditionForm(instance=bdc_a_traiter)
        assert form.fields["notes"].label == "Commentaires"

    def test_occupation_required(self, bdc_a_traiter):
        form = BDCEditionForm(data={"occupation": ""}, instance=bdc_a_traiter)
        assert not form.is_valid()
        assert "occupation" in form.errors

    def test_notes_not_required(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "VACANT", "type_acces": "BADGE_CODE",
                  "acces_complement": "Code 1234"},
            instance=bdc_a_traiter,
        )
        assert form.is_valid()

    def test_vacant_requires_type_acces(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "VACANT", "type_acces": "", "acces_complement": ""},
            instance=bdc_a_traiter,
        )
        assert not form.is_valid()
        assert "type_acces" in form.errors

    def test_vacant_requires_acces_complement(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "VACANT", "type_acces": "BADGE_CODE",
                  "acces_complement": ""},
            instance=bdc_a_traiter,
        )
        assert not form.is_valid()
        assert "acces_complement" in form.errors

    def test_occupe_requires_rdv_date(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "OCCUPE", "rdv_date": ""},
            instance=bdc_a_traiter,
        )
        assert not form.is_valid()
        assert "rdv_date" in form.errors

    def test_occupe_valid_with_rdv(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "OCCUPE", "rdv_date": "2026-03-15T10:00"},
            instance=bdc_a_traiter,
        )
        assert form.is_valid()
```

**Step 2: Run tests — expect failures**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_controle.py -v --tb=short`
Expected: Most tests FAIL (form still has old behavior)

**Step 3: Implement form changes**

Modify `apps/bdc/forms.py` — replace the `BDCEditionForm` class (lines 110-129):

```python
class BDCEditionForm(forms.ModelForm):
    """
    Formulaire d'édition des champs manuels depuis la fiche détail / sidebar.
    Seuls les champs saisissables par la secrétaire sont inclus.
    Inclut un champ hidden pour déclencher une transition de statut en même temps.
    """

    nouveau_statut = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = BonDeCommande
        fields = [
            "occupation", "type_acces", "acces_complement",
            "rdv_date", "notes",
        ]
        widgets = {
            "rdv_date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "notes": "Commentaires",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occupation"].required = True
        # type_acces, acces_complement, rdv_date: conditionally required in clean()
        self.fields["notes"].required = False

    def clean(self):
        cleaned = super().clean()
        occupation = cleaned.get("occupation")

        if occupation == "VACANT":
            if not cleaned.get("type_acces"):
                self.add_error("type_acces", "Ce champ est obligatoire pour un logement vacant.")
            if not cleaned.get("acces_complement"):
                self.add_error("acces_complement", "Ce champ est obligatoire pour un logement vacant.")
        elif occupation == "OCCUPE":
            if not cleaned.get("rdv_date"):
                self.add_error("rdv_date", "La date de RDV est obligatoire pour un logement occupé.")

        return cleaned
```

Also remove `modalite_acces` from `BonDeCommandeForm.Meta.fields` (line 30) and its widget (line 38).

**Step 4: Run tests — expect all pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_controle.py -v --tb=short`
Expected: All 8 tests PASS

**Step 5: Remove modalite_acces validation from services.py**

In `apps/bdc/services.py`, lines 77-80 — remove the `modalite_acces` check:

```python
# DELETE these lines:
        if not bdc.modalite_acces:
            raise BDCIncomplet(
                "La modalité d'accès est obligatoire avant passage en 'À attribuer'."
            )
```

**Step 6: Run full test suite**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`
Expected: All tests pass (some existing tests may need adjustment if they relied on modalite_acces)

**Step 7: Commit**

```bash
git add apps/bdc/forms.py apps/bdc/services.py tests/test_bdc/test_controle.py
git commit -m "refactor: BDCEditionForm — remove modalite_acces, rename notes, add conditional required fields"
```

---

## Task 2: Templates — required field markers + remove modalite_acces

**Files:**
- Modify: `templates/bdc/controle.html:84-134`
- Modify: `templates/bdc/_detail_sidebar.html:112-156`
- Modify: `templates/bdc/detail.html:140-148`
- Modify: `templates/bdc/controle.html:176-197` (read-only section)

**Step 1: Update controle.html editable section**

In `controle.html`, update the "Informations complémentaires" section (lines 84-134):

- Add red `*` after each required field label: `<span class="text-red-500">*</span>`
- Remove the "Modalité d'accès" block (lines 116-120)
- The `notes` field label updates automatically from form (now "Commentaires"), no `*` needed

For each label line, change pattern from:
```html
<label class="text-xs text-[var(--color-text-muted)]">{{ form_edition.occupation.label }}</label>
```
to:
```html
<label class="text-xs text-[var(--color-text-muted)]">{{ form_edition.occupation.label }} <span class="text-red-500">*</span></label>
```

Apply `*` to: `occupation`, `type_acces`, `acces_complement`, `rdv_date`. NOT to `notes`.

Delete the modalite_acces div (lines 116-120):
```html
{# Modalité d'accès #}
<div>
    <label ...>{{ form_edition.modalite_acces.label }}</label>
    {{ form_edition.modalite_acces }}
</div>
```

**Step 2: Update controle.html read-only section**

Remove the `modalite_acces` display block (lines 192-197):
```html
{% if bdc.modalite_acces %}
<div class="flex justify-between">
    <span ...>Modalité d'accès</span>
    <span ...>{{ bdc.modalite_acces }}</span>
</div>
{% endif %}
```

Change the "Notes" label to "Commentaires" (line 200):
```html
<span class="text-[var(--color-text-muted)]">Commentaires</span>
```

**Step 3: Update _detail_sidebar.html**

Remove the modalite_acces block (lines 140-144):
```html
{# Modalité d'accès (toujours visible) #}
<div>
    <label ...>{{ form_edition.modalite_acces.label }}</label>
    {{ form_edition.modalite_acces }}
</div>
```

Add `*` markers to required field labels (same pattern as controle.html).

**Step 4: Update detail.html**

Remove the modalite_acces display (lines 146-148):
```html
{% if bdc.modalite_acces %}
<div><dt ...>Modalité d'accès :</dt> <dd ...>{{ bdc.modalite_acces }}</dd></div>
{% endif %}
```

**Step 5: Run full tests**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`
Expected: All pass

**Step 6: Commit**

```bash
git add templates/bdc/controle.html templates/bdc/_detail_sidebar.html templates/bdc/detail.html
git commit -m "feat: required field markers, remove modalite_acces from templates"
```

---

## Task 3: Renvoi CDT → Secrétaire (model + service + view + URL)

**Files:**
- Modify: `apps/bdc/models.py:301-309` (add RENVOI to ActionChoices)
- Modify: `apps/bdc/services.py` (add renvoyer_controle function)
- Modify: `apps/bdc/urls.py` (add renvoi URL)
- Modify: `apps/bdc/views.py` (add renvoyer_controle view)
- Test: `tests/test_bdc/test_controle.py` (append tests)

**Step 1: Write tests**

Append to `tests/test_bdc/test_controle.py`:

```python
from django.urls import reverse
from apps.bdc.models import ActionChoices, HistoriqueAction, StatutChoices
from apps.bdc.services import TransitionInvalide


class TestRenvoiControle:
    """Tests for CDT renvoi BDC to secrétaire."""

    def test_renvoi_changes_statut_to_a_traiter(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"commentaire": "Occupation manquante"})
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.A_TRAITER
        assert resp.status_code == 302

    def test_renvoi_creates_historique_with_comment(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        client_cdt.post(url, {"commentaire": "RDV non renseigné"})
        hist = HistoriqueAction.objects.filter(
            bdc=bdc_a_faire, action=ActionChoices.RENVOI
        ).first()
        assert hist is not None
        assert hist.details["commentaire"] == "RDV non renseigné"

    def test_renvoi_requires_commentaire(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"commentaire": ""})
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.A_FAIRE  # unchanged

    def test_renvoi_only_from_a_faire(self, client_cdt, bdc_a_traiter):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_traiter.pk})
        resp = client_cdt.post(url, {"commentaire": "Test"})
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER  # unchanged (was already A_TRAITER)

    def test_renvoi_forbidden_for_secretaire(self, client_secretaire, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_secretaire.post(url, {"commentaire": "Test"})
        assert resp.status_code == 403

    def test_renvoi_get_not_allowed(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url)
        assert resp.status_code == 302  # redirects to detail
```

**Step 2: Run tests — expect failures**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_controle.py::TestRenvoiControle -v --tb=short`
Expected: FAIL (URL not found, action RENVOI doesn't exist)

**Step 3: Add RENVOI to ActionChoices**

In `apps/bdc/models.py`, add after line 309 (FACTURATION):

```python
    RENVOI = "RENVOI", "Renvoi au contrôle"
```

**Step 4: Create migration**

Run: `.venv/Scripts/python.exe manage.py makemigrations bdc -n add_renvoi_action`
Then: `.venv/Scripts/python.exe manage.py migrate`

**Step 5: Add renvoyer_controle service function**

In `apps/bdc/services.py`, add after `valider_facturation` (after line 186):

```python
def renvoyer_controle(bdc: BonDeCommande, commentaire: str, utilisateur: User) -> BonDeCommande:
    """
    Renvoie un BDC A_FAIRE au contrôle (A_TRAITER) avec un commentaire du CDT.
    """
    if bdc.statut != StatutChoices.A_FAIRE:
        raise TransitionInvalide(
            f"Renvoi impossible : le BDC est en '{bdc.get_statut_display()}', "
            f"il doit être en 'À attribuer'."
        )

    bdc.statut = StatutChoices.A_TRAITER
    bdc.save(update_fields=["statut", "updated_at"])

    HistoriqueAction.objects.create(
        bdc=bdc,
        utilisateur=utilisateur,
        action=ActionChoices.RENVOI,
        details={"commentaire": commentaire},
    )

    return bdc
```

**Step 6: Add URL**

In `apps/bdc/urls.py`, add after the `controle` path (after line 15):

```python
    path("<int:pk>/renvoyer/", views.renvoyer_controle_bdc, name="renvoyer_controle"),
```

**Step 7: Add view**

In `apps/bdc/views.py`, add the view:

```python
@group_required("CDT")
def renvoyer_controle_bdc(request, pk: int):
    """POST: CDT renvoie un BDC A_FAIRE au contrôle avec un commentaire."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande, pk=pk)
    commentaire = request.POST.get("commentaire", "").strip()

    if not commentaire:
        messages.error(request, "Le commentaire est obligatoire pour renvoyer un BDC.")
        return redirect("bdc:detail", pk=pk)

    try:
        renvoyer_controle(bdc, commentaire, request.user)
        messages.success(request, f"BDC n°{bdc.numero_bdc} renvoyé au contrôle.")
    except TransitionInvalide as e:
        messages.error(request, str(e))

    return redirect("bdc:detail", pk=pk)
```

Add import of `renvoyer_controle` from services at the top of views.py.

**Step 8: Run tests — expect pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_controle.py -v --tb=short`
Expected: All pass

**Step 9: Run full suite**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`

**Step 10: Commit**

```bash
git add apps/bdc/models.py apps/bdc/services.py apps/bdc/views.py apps/bdc/urls.py apps/bdc/migrations/ tests/test_bdc/test_controle.py
git commit -m "feat: CDT can send BDC back to contrôle with a comment (renvoi)"
```

---

## Task 4: Renvoi UI — sidebar button + alert on contrôle page

**Files:**
- Modify: `templates/bdc/_detail_sidebar.html` (add renvoi button for CDT)
- Modify: `templates/bdc/detail.html` (add renvoi button)
- Modify: `templates/bdc/controle.html` (show renvoi alert)
- Modify: `apps/bdc/views.py` (pass renvoi info to controle context)

**Step 1: Add renvoi button to sidebar**

In `_detail_sidebar.html`, after the existing CDT "Attribuer" link (lines 26-32), add a "Renvoyer" section:

```html
{% if is_cdt and bdc.statut == 'A_FAIRE' and not bdc.sous_traitant %}
<div class="mt-3" x-data="{ showRenvoi: false }">
    <a href="{% url 'bdc:attribution_split' pk=bdc.pk %}"
       class="inline-block px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors">
        Attribuer
    </a>
    <button @click="showRenvoi = !showRenvoi"
            class="inline-block px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-colors">
        Renvoyer au contr&ocirc;le
    </button>
    <form x-show="showRenvoi" x-transition
          method="POST" action="{% url 'bdc:renvoyer_controle' pk=bdc.pk %}"
          class="mt-2 space-y-2">
        {% csrf_token %}
        <textarea name="commentaire" rows="2" required
                  placeholder="Motif du renvoi..."
                  class="w-full rounded-lg border px-3 py-2 text-xs border-[var(--color-border)] bg-[var(--color-surface-card)] text-[var(--color-text)]"></textarea>
        <button type="submit"
                class="w-full px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-colors">
            Confirmer le renvoi
        </button>
    </form>
</div>
{% endif %}
```

**Step 2: Add renvoi button to detail.html**

In `detail.html`, inside the CDT `A_FAIRE` section (line 42-47), add a similar renvoi button/form.

**Step 3: Show renvoi alert on contrôle page**

In `apps/bdc/views.py`, in `controle_bdc()`, add before `return render(...)`:

```python
# Check for recent renvoi (CDT comment)
dernier_renvoi = bdc.historique.filter(action=ActionChoices.RENVOI).first()
```

Pass `dernier_renvoi` to template context.

In `controle.html`, add after the header (before the split-screen div):

```html
{% if dernier_renvoi %}
<div class="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
    <div class="flex items-start gap-3">
        <svg class="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
        <div>
            <h3 class="text-sm font-semibold text-amber-800 dark:text-amber-300">Renvoy&eacute; par {{ dernier_renvoi.utilisateur.get_full_name }}</h3>
            <p class="text-sm text-amber-700 dark:text-amber-400 mt-1">{{ dernier_renvoi.details.commentaire }}</p>
            <p class="text-xs text-amber-600/70 dark:text-amber-500 mt-1">{{ dernier_renvoi.created_at|date:"d/m/Y H:i" }}</p>
        </div>
    </div>
</div>
{% endif %}
```

**Step 4: Run full tests**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`

**Step 5: Commit**

```bash
git add templates/bdc/_detail_sidebar.html templates/bdc/detail.html templates/bdc/controle.html apps/bdc/views.py
git commit -m "feat: renvoi UI — sidebar button, detail button, alert on contrôle page"
```

---

## Task 5: Sidebar read-only after contrôle

**Files:**
- Modify: `apps/bdc/views.py:384-414` (detail_sidebar)
- Modify: `apps/bdc/views.py:467-518` (sidebar_save_and_transition)
- Modify: `templates/bdc/_detail_sidebar.html:99-179` (replace form with read-only)
- Test: `tests/test_bdc/test_controle.py` (append)

**Step 1: Write tests**

Append to `tests/test_bdc/test_controle.py`:

```python
class TestSidebarReadOnly:
    """After contrôle (A_TRAITER), sidebar shows read-only fields."""

    def test_sidebar_a_faire_no_form(self, client_secretaire, bdc_a_faire):
        """Secretaire sees no edit form for A_FAIRE BDC."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_faire.pk})
        resp = client_secretaire.get(url)
        content = resp.content.decode()
        assert "id_occupation" not in content  # no dropdown
        assert "Occupé" in content  # read-only display

    def test_sidebar_a_traiter_has_controle_button(self, client_secretaire, bdc_a_traiter):
        """A_TRAITER shows 'Contrôler' button, not form."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_traiter.pk})
        resp = client_secretaire.get(url)
        content = resp.content.decode()
        assert "Contr" in content  # "Contrôler ce BDC"
```

**Step 2: Modify view — stop sending form_edition for non-A_TRAITER**

In `apps/bdc/views.py`, `detail_sidebar()` (line 404):

Change:
```python
form_edition = BDCEditionForm(instance=bdc) if is_secretaire else None
```
To:
```python
form_edition = BDCEditionForm(instance=bdc) if (is_secretaire and bdc.statut == StatutChoices.A_TRAITER) else None
```

Same change in `sidebar_save_and_transition()` (line 505) and `detail_bdc()` (line 429).

**Step 3: Add read-only info section to sidebar template**

In `_detail_sidebar.html`, after the contrôle button block and after the `{% elif form_edition %}` block, add a new `{% else %}` block (or modify existing) to display read-only info when no form is present and statut is not A_TRAITER:

```html
{% elif bdc.statut != 'A_TRAITER' %}
{# Read-only info for completed contrôle #}
<div>
    <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Informations</h3>
    <dl class="space-y-2 text-sm">
        {% if bdc.occupation %}
        <div><dt class="inline text-[var(--color-text-muted)]">Occupation :</dt> <dd class="inline text-[var(--color-text)]">{{ bdc.get_occupation_display }}</dd></div>
        {% endif %}
        {% if bdc.type_acces %}
        <div><dt class="inline text-[var(--color-text-muted)]">Type d'acc&egrave;s :</dt> <dd class="inline text-[var(--color-text)]">{{ bdc.get_type_acces_display }}</dd></div>
        {% endif %}
        {% if bdc.acces_complement %}
        <div><dt class="inline text-[var(--color-text-muted)]">D&eacute;tail acc&egrave;s :</dt> <dd class="inline text-[var(--color-text)]">{{ bdc.acces_complement }}</dd></div>
        {% endif %}
        {% if bdc.rdv_date %}
        <div><dt class="inline text-[var(--color-text-muted)]">RDV :</dt> <dd class="inline text-[var(--color-text)]">{{ bdc.rdv_date|date:"d/m/Y H:i" }}</dd></div>
        {% endif %}
        {% if bdc.notes %}
        <div><dt class="inline text-[var(--color-text-muted)]">Commentaires :</dt> <dd class="inline text-[var(--color-text)]">{{ bdc.notes }}</dd></div>
        {% endif %}
    </dl>
</div>
{% endif %}
```

**Step 4: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_controle.py -v --tb=short`
Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`

**Step 5: Commit**

```bash
git add apps/bdc/views.py templates/bdc/_detail_sidebar.html
git commit -m "feat: sidebar read-only after contrôle — no more edit form for non-A_TRAITER"
```

---

## Task 6: Toast confirmation after contrôle validation

**Files:**
- Modify: `apps/bdc/views.py:930-937` (controle_bdc POST handler)
- Test: `tests/test_bdc/test_controle.py` (append)

**Step 1: Write test**

Append to `tests/test_bdc/test_controle.py`:

```python
from apps.bdc.models import ChecklistItem


class TestControleToast:
    """Toast message after contrôle validation."""

    def test_validation_shows_success_toast(self, client_secretaire, bdc_a_traiter):
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        # Fill required fields + transition
        bdc_a_traiter.occupation = "OCCUPE"
        bdc_a_traiter.rdv_date = "2026-03-15T10:00"
        bdc_a_traiter.save()
        resp = client_secretaire.post(url, {
            "occupation": "OCCUPE",
            "rdv_date": "2026-03-15T10:00",
            "nouveau_statut": "A_FAIRE",
        }, follow=True)
        messages_list = list(resp.context["messages"])
        assert any("validé" in str(m) and "À attribuer" in str(m) for m in messages_list)
```

**Step 2: Add message in view**

In `apps/bdc/views.py`, `controle_bdc()`, after `changer_statut(bdc, nouveau_statut, request.user)` (line 934), before `return redirect("bdc:index")`:

```python
                changer_statut(bdc, nouveau_statut, request.user)
                messages.success(
                    request,
                    f"BDC n°{bdc.numero_bdc} validé — statut : À attribuer.",
                )
                return redirect("bdc:index")
```

**Step 3: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_bdc/test_controle.py::TestControleToast -v --tb=short`
Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`

**Step 4: Commit**

```bash
git add apps/bdc/views.py tests/test_bdc/test_controle.py
git commit -m "feat: toast confirmation after contrôle validation"
```

---

## Task 7: Dashboard — collapsible search/filter zone

**Files:**
- Modify: `templates/bdc/_liste_partial.html:82-135`
- Test: Manual testing (Alpine.js behavior)

**Step 1: Rewrite the filter section**

Replace the filter block (lines 82-135) in `_liste_partial.html` with a collapsible version:

```html
{# ── Filtres + Recherche (collapsible) ──────────────────────────────────── #}
{% with active_filters=filtre.form.bailleur.value|default:""|add:filtre.form.ville.value|default:""|add:filtre.form.date_du.value|default:""|add:filtre.form.date_au.value|default:"" %}
<div class="bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-4"
     x-data="{ filtersOpen: {{ active_filters|yesno:'true,false' }} }">
    <form method="get" action="{% url 'bdc:index' %}"
          hx-get="{% url 'bdc:index' %}"
          hx-target="#isma-dashboard-content"
          hx-push-url="true"
          hx-indicator="#loading-indicator">

        {# Always visible: search + filters toggle #}
        <div class="flex items-end gap-3">
            <div class="flex-1">
                <input type="text" name="q" value="{{ recherche }}"
                       placeholder="N° BDC, adresse, occupant..."
                       class="w-full">
            </div>
            <button type="button" @click="filtersOpen = !filtersOpen"
                    class="px-4 py-2 rounded-lg border border-[var(--color-border)] text-sm font-medium text-[var(--color-text)] hover:bg-accent/10 transition-colors flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg>
                Filtres
                {% if active_filters %}
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-accent text-white text-xs font-bold">
                    {% widthratio 1 1 0 as count %}
                    {% if filtre.form.bailleur.value %}{% widthratio count 1 1 as count %}{% endif %}
                    {% if filtre.form.ville.value %}{% widthratio count 1 1 as count %}{% endif %}
                    {% if filtre.form.date_du.value %}{% widthratio count 1 1 as count %}{% endif %}
                    {% if filtre.form.date_au.value %}{% widthratio count 1 1 as count %}{% endif %}
                </span>
                {% endif %}
            </button>
            <button type="submit"
                    class="bg-accent hover:bg-accent-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 shadow-sm hover:shadow-md">
                Rechercher
            </button>
            <div id="loading-indicator" class="htmx-indicator">
                <svg class="w-4 h-4 animate-spin text-accent" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            </div>
        </div>

        {# Collapsible filter fields #}
        <div x-show="filtersOpen" x-transition class="mt-3 space-y-3">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                    <label for="id_bailleur" class="text-xs text-[var(--color-text-muted)]">Bailleur</label>
                    {{ filtre.form.bailleur }}
                </div>
                <div>
                    <label for="id_ville" class="text-xs text-[var(--color-text-muted)]">Ville</label>
                    <input type="text" name="ville" id="id_ville" value="{{ filtre.form.ville.value|default:'' }}"
                           placeholder="Ville...">
                </div>
            </div>
            <div class="flex items-end gap-3">
                <div>
                    <label for="id_date_du" class="text-xs text-[var(--color-text-muted)]">Du</label>
                    <input type="date" name="date_du" id="id_date_du" value="{{ filtre.form.date_du.value|default:'' }}">
                </div>
                <div>
                    <label for="id_date_au" class="text-xs text-[var(--color-text-muted)]">Au</label>
                    <input type="date" name="date_au" id="id_date_au" value="{{ filtre.form.date_au.value|default:'' }}">
                </div>
                <a href="{% url 'bdc:index' %}" class="text-sm text-[var(--color-text-muted)] hover:text-accent transition-colors whitespace-nowrap">R&eacute;initialiser</a>
            </div>
        </div>
    </form>
</div>
{% endwith %}
```

Note: The badge count implementation using Django template tags is tricky. A simpler approach is to compute `nb_filtres_actifs` in the view and pass it to the context. Do this in the `liste_bdc` view.

**Step 2: Add filter count to view**

In the `liste_bdc` view, compute the active filter count and pass it to context:

```python
nb_filtres = sum([
    bool(request.GET.get("bailleur")),
    bool(request.GET.get("ville")),
    bool(request.GET.get("date_du")),
    bool(request.GET.get("date_au")),
])
```

Pass `"nb_filtres": nb_filtres` to the template context.

Then in the template, replace the complex widthratio with:

```html
{% if nb_filtres %}
<span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-accent text-white text-xs font-bold">{{ nb_filtres }}</span>
{% endif %}
```

And for `filtersOpen` default:

```html
x-data="{ filtersOpen: {% if nb_filtres %}true{% else %}false{% endif %} }"
```

**Step 3: Run full test suite**

Run: `.venv/Scripts/python.exe -m pytest --tb=short -q`
Expected: All pass (template changes don't break logic)

**Step 4: Lint check**

Run: `.venv/Scripts/python.exe -m ruff check apps/bdc/views.py`

**Step 5: Commit**

```bash
git add templates/bdc/_liste_partial.html apps/bdc/views.py
git commit -m "feat: collapsible dashboard search — filters hidden by default, badge count"
```

---

## Task 8: Final verification

**Step 1: Run full test suite**

Run: `.venv/Scripts/python.exe -m pytest -v --tb=short`
Expected: All tests pass

**Step 2: Lint**

Run: `.venv/Scripts/python.exe -m ruff check .`
Expected: Clean

**Step 3: Manual verification checklist**

1. **Contrôle page** : required `*` markers visible, no "Modalité d'accès", Notes → Commentaires
2. **Contrôle validation** : toast "BDC n°XXX validé — statut : À attribuer." appears
3. **Sidebar A_FAIRE (CDT)** : "Attribuer" + "Renvoyer au contrôle" buttons
4. **Renvoi** : click renvoi → comment field → confirm → BDC returns to A_TRAITER
5. **Contrôle page after renvoi** : alert banner shows CDT's comment
6. **Sidebar A_FAIRE (Secrétaire)** : read-only display, no dropdowns
7. **Dashboard** : search bar + "Filtres" button replié by default, click opens filters, badge shows count
