# Dashboard: Onglets + Sidebar + Colonnes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace dashboard status cards with horizontal tabs, open BDC detail in a right sidebar instead of a new page, add sous-traitant and montant HT columns to the table.

**Architecture:** HTMX-powered tabs and sidebar loaded via server partials. Alpine.js manages sidebar open/close state and transitions. The existing `_liste_partial.html` is refactored to use tabs, and a new `_detail_sidebar.html` partial is created for the sidebar content.

**Tech Stack:** Django, HTMX, Alpine.js, Tailwind CSS (CDN Play)

---

### Task 1: Add sous-traitant select_related and montant annotation to queryset

**Files:**
- Modify: `bdc-peinture/apps/bdc/views.py:43` (liste_bdc queryset)
- Test: `bdc-peinture/apps/bdc/tests/test_views.py`

**Step 1: Write the failing test**

```python
# In the existing test file, add:
def test_liste_bdc_includes_sous_traitant_and_montant(self):
    """Dashboard queryset includes sous_traitant and montant_ht_total annotation."""
    self.client.force_login(self.user_secretaire)
    resp = self.client.get(reverse("bdc:index"))
    bdc = resp.context["page_obj"][0]
    # sous_traitant should be accessible without extra query
    assert hasattr(bdc, "sous_traitant")
    # montant_ht_total annotation should be present
    assert hasattr(bdc, "montant_ht_total")
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && python -m pytest apps/bdc/tests/test_views.py -k "test_liste_bdc_includes_sous_traitant_and_montant" -v`
Expected: FAIL — `montant_ht_total` attribute not found

**Step 3: Write minimal implementation**

In `bdc-peinture/apps/bdc/views.py`, modify line 43:
```python
from django.db.models import Sum

# Replace:
qs = BonDeCommande.objects.select_related("bailleur").all()
# With:
qs = (
    BonDeCommande.objects.select_related("bailleur", "sous_traitant")
    .annotate(montant_ht_total=Sum("lignes_prestation__montant"))
    .all()
)
```

**Step 4: Run test to verify it passes**

Run: `cd bdc-peinture && python -m pytest apps/bdc/tests/test_views.py -k "test_liste_bdc_includes_sous_traitant_and_montant" -v`
Expected: PASS

**Step 5: Run full test suite to check for regressions**

Run: `cd bdc-peinture && python -m pytest apps/bdc/tests/test_views.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add bdc-peinture/apps/bdc/views.py bdc-peinture/apps/bdc/tests/test_views.py
git commit -m "feat: add sous_traitant select_related and montant annotation to dashboard queryset"
```

---

### Task 2: Replace compteurs cards with horizontal tabs in _liste_partial.html

**Files:**
- Modify: `bdc-peinture/templates/bdc/_liste_partial.html:4-29` (replace compteurs grid)

**Step 1: Replace the compteurs section (lines 4-29) with tabs**

Replace the `<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">` block with:

```html
{# ── Onglets par statut ──────────────────────────────────────────── #}
<div class="border-b border-[var(--color-border)]">
    <nav class="flex space-x-1 overflow-x-auto" role="tablist">
        {# Onglet "Tous" #}
        <a href="{% url 'bdc:index' %}{% if recherche %}?q={{ recherche }}{% endif %}"
           hx-get="{% url 'bdc:index' %}{% if recherche %}?q={{ recherche }}{% endif %}"
           hx-target="#isma-dashboard-content"
           hx-push-url="true"
           role="tab"
           class="px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors
                  {% if not filtre.form.statut.value %}
                  text-accent border-b-2 border-accent
                  {% else %}
                  text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-b-2 hover:border-[var(--color-border)]
                  {% endif %}">
            Tous <span class="ml-1 font-mono text-xs">({{ total }})</span>
        </a>
        {% for choix in statut_choices.choices %}
        <a href="{% url 'bdc:index' %}?statut={{ choix.0 }}"
           hx-get="{% url 'bdc:index' %}?statut={{ choix.0 }}"
           hx-target="#isma-dashboard-content"
           hx-push-url="true"
           role="tab"
           class="px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors
                  {% if filtre.form.statut.value == choix.0 %}
                  text-accent border-b-2 border-accent
                  {% else %}
                  text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-b-2 hover:border-[var(--color-border)]
                  {% endif %}">
            {{ choix.1 }}
            <span class="ml-1 font-mono text-xs">({% for k, v in compteurs.items %}{% if k == choix.0 %}{{ v }}{% endif %}{% endfor %})</span>
        </a>
        {% endfor %}
    </nav>
</div>
```

**Step 2: Verify visually**

Run dev server, navigate to dashboard, confirm tabs appear and clicking switches the active tab via HTMX.

**Step 3: Commit**

```bash
git add bdc-peinture/templates/bdc/_liste_partial.html
git commit -m "feat: replace status counter cards with horizontal tabs"
```

---

### Task 3: Add sous-traitant and montant HT columns to the table

**Files:**
- Modify: `bdc-peinture/templates/bdc/_liste_partial.html:138-169` (table section)

**Step 1: Add column headers**

After the `<th>Ville</th>` column header, add:
```html
<th class="px-4 py-3 text-left text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Sous-traitant</th>
<th class="px-4 py-3 text-right text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Montant HT</th>
```

**Step 2: Add column cells in the row loop**

After the `<td>{{ bdc.ville }}</td>` cell, add:
```html
<td class="px-4 py-3 text-sm text-[var(--color-text)]">{{ bdc.sous_traitant.nom|default:"—" }}</td>
<td class="px-4 py-3 text-sm font-mono text-right text-[var(--color-text)]">
    {% if bdc.montant_ht_total %}{{ bdc.montant_ht_total|floatformat:2 }} €{% else %}—{% endif %}
</td>
```

**Step 3: Verify visually**

Check that the two new columns appear in the table with correct data.

**Step 4: Commit**

```bash
git add bdc-peinture/templates/bdc/_liste_partial.html
git commit -m "feat: add sous-traitant and montant HT columns to dashboard table"
```

---

### Task 4: Create the sidebar detail view and URL

**Files:**
- Modify: `bdc-peinture/apps/bdc/views.py` (add new view)
- Modify: `bdc-peinture/apps/bdc/urls.py` (add URL pattern)
- Test: `bdc-peinture/apps/bdc/tests/test_views.py`

**Step 1: Write the failing test**

```python
def test_detail_sidebar_returns_partial(self):
    """Sidebar endpoint returns partial HTML without base layout."""
    self.client.force_login(self.user_secretaire)
    resp = self.client.get(reverse("bdc:detail_sidebar", args=[self.bdc.pk]))
    assert resp.status_code == 200
    assert "ISMA" not in resp.content.decode()  # No base template
    assert self.bdc.numero_bdc in resp.content.decode()

def test_detail_sidebar_requires_login(self):
    resp = self.client.get(reverse("bdc:detail_sidebar", args=[self.bdc.pk]))
    assert resp.status_code == 302
```

**Step 2: Run test to verify it fails**

Run: `cd bdc-peinture && python -m pytest apps/bdc/tests/test_views.py -k "test_detail_sidebar" -v`
Expected: FAIL — NoReverseMatch

**Step 3: Add URL pattern**

In `bdc-peinture/apps/bdc/urls.py`, add before the `<int:pk>/` pattern:
```python
path("<int:pk>/sidebar/", views.detail_sidebar, name="detail_sidebar"),
```

**Step 4: Write the view**

In `bdc-peinture/apps/bdc/views.py`, add:
```python
@login_required
def detail_sidebar(request, pk: int):
    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk
    )
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    is_secretaire = request.user.groups.filter(name="Secretaire").exists()
    is_cdt = request.user.groups.filter(name="CDT").exists()

    transitions = []
    if is_secretaire:
        from .services import TRANSITIONS
        transitions = [
            (s, StatutChoices(s).label)
            for s in TRANSITIONS.get(bdc.statut, [])
            if not (bdc.statut == "A_FAIRE" and s == "EN_COURS")
        ]

    form_edition = None
    if is_secretaire:
        from .forms import BDCEditionForm
        form_edition = BDCEditionForm(instance=bdc)

    return render(request, "bdc/_detail_sidebar.html", {
        "bdc": bdc,
        "lignes": lignes,
        "historique": historique,
        "transitions": transitions,
        "form_edition": form_edition,
        "is_secretaire": is_secretaire,
        "is_cdt": is_cdt,
    })
```

**Step 5: Run test to verify it passes**

Run: `cd bdc-peinture && python -m pytest apps/bdc/tests/test_views.py -k "test_detail_sidebar" -v`
Expected: PASS (after creating the template in next task)

**Step 6: Commit**

```bash
git add bdc-peinture/apps/bdc/views.py bdc-peinture/apps/bdc/urls.py bdc-peinture/apps/bdc/tests/test_views.py
git commit -m "feat: add detail_sidebar view and URL for HTMX sidebar"
```

---

### Task 5: Create _detail_sidebar.html partial template

**Files:**
- Create: `bdc-peinture/templates/bdc/_detail_sidebar.html`

**Step 1: Create the sidebar partial template**

```html
{# Sidebar detail partial — loaded via HTMX into the sidebar panel #}
<div class="h-full flex flex-col">
    {# Header #}
    <div class="p-5 border-b border-[var(--color-border)]">
        <div class="flex items-center justify-between mb-2">
            <h2 class="text-lg font-bold font-mono text-[var(--color-text)]">{{ bdc.numero_bdc }}</h2>
            <button @click="sidebarOpen = false; selectedBdc = null"
                    class="p-1 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-border)]/50 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
            {{ bdc.bailleur.nom }}
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold
                {% if bdc.statut == 'A_TRAITER' %}bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300
                {% elif bdc.statut == 'A_FAIRE' %}bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300
                {% elif bdc.statut == 'EN_COURS' %}bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300
                {% elif bdc.statut == 'A_FACTURER' %}bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300
                {% elif bdc.statut == 'FACTURE' %}bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300
                {% endif %}">
                {{ bdc.get_statut_display }}
            </span>
        </div>

        {# Action buttons #}
        {% if transitions %}
        <div class="flex gap-2 mt-3">
            {% for val, label in transitions %}
            <form method="post" action="{% url 'bdc:changer_statut' pk=bdc.pk %}">
                {% csrf_token %}
                <input type="hidden" name="nouveau_statut" value="{{ val }}">
                <button type="submit" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-accent hover:bg-accent-dark text-white transition-colors">{{ label }}</button>
            </form>
            {% endfor %}
            {% if is_cdt and bdc.statut == 'A_FAIRE' and not bdc.sous_traitant %}
            <a href="{% url 'bdc:attribuer' pk=bdc.pk %}" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors">Attribuer</a>
            {% endif %}
        </div>
        {% endif %}
    </div>

    {# Scrollable content #}
    <div class="flex-1 overflow-y-auto p-5 space-y-5">
        {# Localisation #}
        <div>
            <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Localisation</h3>
            <p class="text-sm text-[var(--color-text)]">{{ bdc.adresse }}, {{ bdc.code_postal }} {{ bdc.ville }}</p>
            {% if bdc.occupation %}<p class="text-sm text-[var(--color-text-muted)]">{{ bdc.get_occupation_display }}</p>{% endif %}
        </div>

        {# Sous-traitant #}
        {% if bdc.sous_traitant %}
        <div>
            <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Sous-traitant</h3>
            <p class="text-sm text-[var(--color-text)]">{{ bdc.sous_traitant.nom }}</p>
            {% if bdc.sous_traitant.telephone %}<p class="text-sm font-mono text-[var(--color-text-muted)]">{{ bdc.sous_traitant.telephone }}</p>{% endif %}
        </div>
        {% endif %}

        {# Travaux #}
        {% if bdc.objet_travaux %}
        <div>
            <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Travaux</h3>
            <p class="text-sm text-[var(--color-text)]">{{ bdc.objet_travaux }}</p>
        </div>
        {% endif %}

        {# Prestations #}
        {% if lignes %}
        <div>
            <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Prestations</h3>
            <div class="space-y-1">
                {% for ligne in lignes %}
                <div class="flex justify-between text-sm">
                    <span class="text-[var(--color-text)] truncate mr-2">{{ ligne.designation|truncatechars:35 }}</span>
                    <span class="font-mono text-[var(--color-text-muted)] flex-shrink-0">{{ ligne.montant|floatformat:2 }} €</span>
                </div>
                {% endfor %}
            </div>
            {% if bdc.montant_ht %}
            <div class="flex justify-between text-sm font-semibold mt-2 pt-2 border-t border-[var(--color-border)]">
                <span class="text-[var(--color-text)]">Total HT</span>
                <span class="font-mono text-[var(--color-text)]">{{ bdc.montant_ht|floatformat:2 }} €</span>
            </div>
            {% endif %}
        </div>
        {% endif %}

        {# Edition form (secretaire only) #}
        {% if form_edition %}
        <div>
            <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Compléter</h3>
            <form method="post" action="{% url 'bdc:modifier' pk=bdc.pk %}" class="space-y-3">
                {% csrf_token %}
                {% for field in form_edition %}
                <div>
                    <label class="text-xs text-[var(--color-text-muted)]">{{ field.label }}</label>
                    {{ field }}
                </div>
                {% endfor %}
                <button type="submit" class="w-full px-3 py-1.5 text-xs font-medium rounded-lg bg-accent hover:bg-accent-dark text-white transition-colors">Enregistrer</button>
            </form>
        </div>
        {% endif %}

        {# Historique #}
        {% if historique %}
        <div>
            <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Historique</h3>
            <div class="space-y-2">
                {% for h in historique %}
                <div class="text-xs">
                    <span class="font-mono text-accent">{{ h.date|date:"d/m H:i" }}</span>
                    <span class="text-[var(--color-text-muted)]">{{ h.description }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {# Link to full page #}
        <div class="pt-2">
            <a href="{% url 'bdc:detail' pk=bdc.pk %}" class="text-sm text-accent hover:underline">Voir la fiche complète →</a>
        </div>
    </div>
</div>
```

**Step 2: Run the sidebar tests from Task 4**

Run: `cd bdc-peinture && python -m pytest apps/bdc/tests/test_views.py -k "test_detail_sidebar" -v`
Expected: PASS

**Step 3: Commit**

```bash
git add bdc-peinture/templates/bdc/_detail_sidebar.html
git commit -m "feat: create sidebar detail partial template"
```

---

### Task 6: Add sidebar container and Alpine.js toggle to _liste_partial.html

**Files:**
- Modify: `bdc-peinture/templates/bdc/_liste_partial.html` (wrap in Alpine scope, add sidebar panel, update table rows)

**Step 1: Wrap the dashboard content div with Alpine.js state**

Change the opening `<div id="isma-dashboard-content">` to:
```html
<div id="isma-dashboard-content" x-data="{ sidebarOpen: false, selectedBdc: null }">
```

**Step 2: Update table row onclick to open sidebar via HTMX**

Replace the existing `onclick="window.location='...'"` on `<tr>` with:
```html
<tr class="hover:bg-accent/5 dark:hover:bg-accent/10 cursor-pointer transition-colors duration-100"
    :class="{ 'bg-accent/10 dark:bg-accent/15': selectedBdc == {{ bdc.pk }} }"
    hx-get="{% url 'bdc:detail_sidebar' pk=bdc.pk %}"
    hx-target="#sidebar-content"
    hx-swap="innerHTML"
    @htmx:after-swap.window="sidebarOpen = true; selectedBdc = {{ bdc.pk }}">
```

**Step 3: Add the sidebar panel after the table container div**

Before the closing `</div>{# /isma-dashboard-content #}`, add:

```html
{# ── Sidebar detail panel ────────────────────────────────────────── #}
<div x-show="sidebarOpen" x-transition:enter="transition ease-out duration-200" x-transition:enter-start="translate-x-full" x-transition:enter-end="translate-x-0" x-transition:leave="transition ease-in duration-150" x-transition:leave-start="translate-x-0" x-transition:leave-end="translate-x-full"
     class="fixed top-0 right-0 h-full w-[420px] bg-[var(--color-surface-card)] border-l border-[var(--color-border)] shadow-2xl z-50"
     @click.outside="sidebarOpen = false; selectedBdc = null"
     @keydown.escape.window="sidebarOpen = false; selectedBdc = null">
    <div id="sidebar-content" class="h-full"></div>
</div>

{# Overlay #}
<div x-show="sidebarOpen" x-transition:enter="transition ease-out duration-200" x-transition:enter-start="opacity-0" x-transition:enter-end="opacity-100" x-transition:leave="transition ease-in duration-150" x-transition:leave-start="opacity-100" x-transition:leave-end="opacity-0"
     class="fixed inset-0 bg-black/20 dark:bg-black/40 z-40"
     @click="sidebarOpen = false; selectedBdc = null">
</div>
```

**Step 4: Verify visually**

Start dev server, navigate to dashboard, click a BDC row. Sidebar should slide in from the right with BDC details.

**Step 5: Run full test suite**

Run: `cd bdc-peinture && python -m pytest -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add bdc-peinture/templates/bdc/_liste_partial.html
git commit -m "feat: add sidebar panel with Alpine.js and HTMX integration"
```

---

### Task 7: Final integration test and visual verification

**Files:**
- Test: `bdc-peinture/apps/bdc/tests/test_views.py`

**Step 1: Write integration test for tabs filtering**

```python
def test_tab_filtering_by_statut(self):
    """Filtering by statut via query param returns only matching BDCs."""
    self.client.force_login(self.user_secretaire)
    resp = self.client.get(reverse("bdc:index") + "?statut=A_TRAITER")
    assert resp.status_code == 200
    for bdc in resp.context["page_obj"]:
        assert bdc.statut == "A_TRAITER"
```

**Step 2: Run all tests**

Run: `cd bdc-peinture && python -m pytest -v`
Expected: All tests pass

**Step 3: Run ruff check**

Run: `cd bdc-peinture && ruff check .`
Expected: No errors

**Step 4: Visual verification with Playwright**

Test dashboard tabs (click each tab), sidebar (click a BDC row), both in light and dark mode.

**Step 5: Final commit**

```bash
git add -A
git commit -m "test: add integration tests for dashboard tabs and sidebar"
```
