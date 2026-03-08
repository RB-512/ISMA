# Checklists de transition configurables — Plan d'implementation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Etendre le mecanisme de checklist existant (A_TRAITER → A_FAIRE) a toutes les transitions du workflow BDC, avec UX inline dans la sidebar.

**Architecture:** Ajout d'un champ `transition` sur le modele `ChecklistItem` existant + garde generique dans `services.py`. Les items existants recoivent `transition="A_TRAITER__A_FAIRE"` via le default de migration. La sidebar detecte si des items existent pour une transition et affiche une checklist inline avant de permettre la validation.

**Tech Stack:** Django 5.1, HTMX 2.x, Alpine.js 3.x, Tailwind CSS, pytest + factory-boy

---

## Task 1 : Ajouter TransitionChoices et le champ `transition` au modele

**Files:**
- Modify: `apps/bdc/models.py:276-292`
- Create: `apps/bdc/migrations/0010_checklistitem_transition.py` (auto-generated)

**Step 1: Ajouter TransitionChoices et le champ transition**

Dans `apps/bdc/models.py`, avant la classe `ChecklistItem` (ligne 276), ajouter l'enum `TransitionChoices`. Puis ajouter le champ `transition` au modele `ChecklistItem` :

```python
class TransitionChoices(models.TextChoices):
    CONTROLE = "A_TRAITER__A_FAIRE", "Controle → A attribuer"
    ATTRIBUTION = "A_FAIRE__EN_COURS", "Attribution → En cours"
    REALISATION = "EN_COURS__A_FACTURER", "Realisation → A facturer"
    FACTURATION = "A_FACTURER__FACTURE", "Facturation → Facture"


class ChecklistItem(models.Model):
    """
    Item de checklist de controle configurable.
    Associe a une transition specifique du workflow.
    """

    libelle = models.CharField(max_length=200)
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)
    transition = models.CharField(
        max_length=30,
        choices=TransitionChoices.choices,
        default=TransitionChoices.CONTROLE,
    )

    class Meta:
        ordering = ["transition", "ordre"]
        verbose_name = "Item de checklist"
        verbose_name_plural = "Items de checklist"

    def __str__(self):
        return self.libelle
```

**Step 2: Generer la migration**

Run: `uv run manage.py makemigrations bdc -n checklistitem_transition`
Expected: migration creee dans `apps/bdc/migrations/`

**Step 3: Appliquer la migration**

Run: `uv run manage.py migrate`
Expected: migration appliquee, les items existants recoivent `A_TRAITER__A_FAIRE` par defaut

**Step 4: Verifier les tests existants**

Run: `uv run pytest tests/test_bdc/test_controle.py -v --tb=short`
Expected: PASS — les items existants ont le default `A_TRAITER__A_FAIRE`

**Step 5: Commit**

```bash
git add apps/bdc/models.py apps/bdc/migrations/0010_checklistitem_transition.py
git commit -m "feat: add transition field to ChecklistItem model"
```

---

## Task 2 : Garde de transition generique dans services.py

**Files:**
- Modify: `apps/bdc/services.py:15,80-87,140-161,164-183,217-260`
- Test: `tests/test_bdc/test_controle.py`

**Step 1: Ecrire les tests pour la garde generique**

Ajouter dans `tests/test_bdc/test_controle.py` :

```python
from apps.bdc.models import TransitionChoices
from apps.bdc.services import attribuer_st, valider_realisation, valider_facturation


@pytest.fixture
def checklist_items_attribution(db):
    """Items de checklist pour la transition A_FAIRE → EN_COURS."""
    return [
        ChecklistItem.objects.create(
            libelle="Sous-traitant contacte", ordre=1,
            transition=TransitionChoices.ATTRIBUTION,
        ),
    ]


@pytest.fixture
def checklist_items_realisation(db):
    """Items de checklist pour la transition EN_COURS → A_FACTURER."""
    return [
        ChecklistItem.objects.create(
            libelle="Photos avant/apres prises", ordre=1,
            transition=TransitionChoices.REALISATION,
        ),
    ]


@pytest.fixture
def checklist_items_facturation(db):
    """Items de checklist pour la transition A_FACTURER → FACTURE."""
    return [
        ChecklistItem.objects.create(
            libelle="Facture recue", ordre=1,
            transition=TransitionChoices.FACTURATION,
        ),
    ]


class TestChecklistTransitionGenerique:
    """Tests de la garde checklist generique sur toutes les transitions."""

    def test_attribution_bloquee_si_checklist_incomplete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_attribution
    ):
        with pytest.raises(BDCIncomplet, match="points de controle"):
            attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    def test_attribution_ok_si_checklist_complete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_attribution
    ):
        for item in checklist_items_attribution:
            ChecklistResultat.objects.create(bdc=bdc_a_faire, item=item, coche=True)
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS

    def test_attribution_ok_sans_checklist(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS

    def test_realisation_bloquee_si_checklist_incomplete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_realisation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        with pytest.raises(BDCIncomplet, match="points de controle"):
            valider_realisation(bdc, utilisateur_cdt)

    def test_realisation_ok_si_checklist_complete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_realisation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        for item in checklist_items_realisation:
            ChecklistResultat.objects.create(bdc=bdc, item=item, coche=True)
        bdc = valider_realisation(bdc, utilisateur_cdt)
        assert bdc.statut == StatutChoices.A_FACTURER

    def test_facturation_bloquee_si_checklist_incomplete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_facturation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        bdc = valider_realisation(bdc, utilisateur_cdt)
        with pytest.raises(BDCIncomplet, match="points de controle"):
            valider_facturation(bdc, utilisateur_cdt)

    def test_facturation_ok_si_checklist_complete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_facturation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        bdc = valider_realisation(bdc, utilisateur_cdt)
        for item in checklist_items_facturation:
            ChecklistResultat.objects.create(bdc=bdc, item=item, coche=True)
        bdc = valider_facturation(bdc, utilisateur_cdt)
        assert bdc.statut == StatutChoices.FACTURE

    def test_checklist_controle_filtre_par_transition(
        self, bdc_a_traiter, utilisateur_secretaire, checklist_items, checklist_items_attribution
    ):
        """Les items d'attribution ne bloquent pas la transition A_TRAITER → A_FAIRE."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()
        # Cocher uniquement les items de controle, pas ceux d'attribution
        for item in checklist_items:
            ChecklistResultat.objects.create(bdc=bdc_a_traiter, item=item, coche=True)
        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE
```

**Step 2: Verifier que les tests echouent**

Run: `uv run pytest tests/test_bdc/test_controle.py::TestChecklistTransitionGenerique -v --tb=short`
Expected: FAIL — `_verifier_checklist_transition` n'existe pas encore

**Step 3: Implementer la garde generique**

Dans `apps/bdc/services.py` :

1. Ajouter `TransitionChoices` a l'import (ligne 15) :
```python
from .models import ActionChoices, BonDeCommande, ChecklistItem, HistoriqueAction, StatutChoices, TransitionChoices
```

2. Ajouter la fonction helper apres les exceptions (apres ligne 38) :
```python
def _verifier_checklist_transition(bdc, ancien_statut, nouveau_statut):
    """Verifie que tous les items de checklist sont coches pour une transition donnee."""
    transition_key = f"{ancien_statut}__{nouveau_statut}"
    # Ne verifier que si la transition est dans TransitionChoices
    if transition_key not in TransitionChoices.values:
        return
    items_actifs = ChecklistItem.objects.filter(actif=True, transition=transition_key).count()
    if items_actifs > 0:
        items_coches = bdc.checklist_resultats.filter(
            item__actif=True, item__transition=transition_key, coche=True
        ).count()
        if items_coches < items_actifs:
            raise BDCIncomplet("Tous les points de controle doivent etre coches.")
```

3. Remplacer la checklist inline dans `changer_statut` (lignes 80-87) :
```python
        # Checklist de controle : tous les items actifs doivent etre coches
        _verifier_checklist_transition(bdc, ancien_statut, nouveau_statut)
```

4. Ajouter l'appel dans `valider_realisation` (apres le check de statut, ligne 149) :
```python
    _verifier_checklist_transition(bdc, StatutChoices.EN_COURS, StatutChoices.A_FACTURER)
```

5. Ajouter l'appel dans `valider_facturation` (apres le check de statut, ligne 172) :
```python
    _verifier_checklist_transition(bdc, StatutChoices.A_FACTURER, StatutChoices.FACTURE)
```

6. Ajouter l'appel dans `attribuer_st` (apres le check de statut, ligne 231) :
```python
    _verifier_checklist_transition(bdc, StatutChoices.A_FAIRE, StatutChoices.EN_COURS)
```

**Step 4: Verifier que les tests passent**

Run: `uv run pytest tests/test_bdc/test_controle.py -v --tb=short`
Expected: PASS

**Step 5: Lancer la suite complete**

Run: `uv run pytest --tb=short`
Expected: PASS

**Step 6: Commit**

```bash
git add apps/bdc/services.py tests/test_bdc/test_controle.py
git commit -m "feat: generic checklist guard for all transitions"
```

---

## Task 3 : Filtrer la page controle existante par transition

**Files:**
- Modify: `apps/bdc/views.py` (vue `controle_bdc`)
- Test: `tests/test_bdc/test_controle.py`

**Step 1: Ecrire le test**

Ajouter dans `tests/test_bdc/test_controle.py` :

```python
class TestControleFiltrageTransition:
    """La page controle ne montre que les items A_TRAITER__A_FAIRE."""

    def test_controle_ne_montre_pas_items_autres_transitions(
        self, client_secretaire, bdc_a_traiter, checklist_items, checklist_items_attribution
    ):
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        response = client_secretaire.get(url)
        # Seuls les 3 items de controle, pas l'item d'attribution
        assert len(response.context["checklist_items"]) == 3
```

**Step 2: Verifier que le test echoue**

Run: `uv run pytest tests/test_bdc/test_controle.py::TestControleFiltrageTransition -v --tb=short`
Expected: FAIL — 4 items au lieu de 3

**Step 3: Modifier la vue controle_bdc**

Dans `apps/bdc/views.py`, dans la vue `controle_bdc`, remplacer le filtre `ChecklistItem.objects.filter(actif=True)` par :

```python
ChecklistItem.objects.filter(actif=True, transition=TransitionChoices.CONTROLE)
```

Ajouter `TransitionChoices` a l'import en haut du fichier :
```python
from .models import ..., TransitionChoices
```

**Step 4: Verifier que le test passe**

Run: `uv run pytest tests/test_bdc/test_controle.py -v --tb=short`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/bdc/views.py
git commit -m "fix: filter controle page checklist by transition"
```

---

## Task 4 : Ajouter les vues sidebar checklist (GET + POST)

**Files:**
- Modify: `apps/bdc/views.py`
- Modify: `apps/bdc/urls.py`
- Create: `templates/bdc/partials/_checklist_transition.html`
- Test: `tests/test_bdc/test_controle.py`

**Step 1: Ecrire les tests**

Ajouter dans `tests/test_bdc/test_controle.py` :

```python
from decimal import Decimal


class TestSidebarChecklistTransition:
    """Tests du flux checklist inline dans la sidebar."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    @pytest.fixture
    def bdc_a_facturer(self, bdc_en_cours, utilisateur_cdt):
        return valider_realisation(bdc_en_cours, utilisateur_cdt)

    def test_get_checklist_realisation(
        self, client_cdt, bdc_en_cours, checklist_items_realisation
    ):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        resp = client_cdt.get(url, {"transition": "EN_COURS__A_FACTURER"})
        assert resp.status_code == 200
        assert "Photos avant/apres" in resp.content.decode()

    def test_get_checklist_sans_items_redirige_vers_action(
        self, client_cdt, bdc_en_cours
    ):
        """Si pas d'items pour cette transition, rend un partial vide avec message."""
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        resp = client_cdt.get(url, {"transition": "EN_COURS__A_FACTURER"})
        assert resp.status_code == 200
        # Pas d'items, donc le partial affiche un message "Aucun point de controle"
        # ou realise la transition directement

    def test_post_checklist_complete_valide_transition(
        self, client_cdt, bdc_en_cours, checklist_items_realisation
    ):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        data = {"transition": "EN_COURS__A_FACTURER"}
        for item in checklist_items_realisation:
            data[f"check_{item.pk}"] = "on"
        resp = client_cdt.post(url, data, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER

    def test_post_checklist_incomplete_bloque(
        self, client_cdt, bdc_en_cours, checklist_items_realisation
    ):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        data = {"transition": "EN_COURS__A_FACTURER"}
        # Ne pas cocher → bloque
        resp = client_cdt.post(url, data, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS
        assert "points de controle" in resp.content.decode().lower()

    def test_post_checklist_facturation(
        self, client_cdt, bdc_a_facturer, checklist_items_facturation
    ):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_a_facturer.pk})
        data = {"transition": "A_FACTURER__FACTURE"}
        for item in checklist_items_facturation:
            data[f"check_{item.pk}"] = "on"
        resp = client_cdt.post(url, data, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE
```

**Step 2: Verifier que les tests echouent**

Run: `uv run pytest tests/test_bdc/test_controle.py::TestSidebarChecklistTransition -v --tb=short`
Expected: FAIL — URL et vue n'existent pas

**Step 3: Ajouter l'URL**

Dans `apps/bdc/urls.py`, ajouter :
```python
path("<int:pk>/sidebar-checklist/", views.sidebar_checklist, name="sidebar_checklist"),
```

**Step 4: Creer le partial template**

Creer `templates/bdc/partials/_checklist_transition.html` :

```html
{# Checklist de transition inline dans la sidebar #}
<div class="p-5 space-y-4">
    <h3 class="text-sm font-semibold text-[var(--color-text)]">
        Points de controle
    </h3>

    {% if error_message %}
    <div class="p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger">
        {{ error_message }}
    </div>
    {% endif %}

    <form hx-post="{% url 'bdc:sidebar_checklist' pk=bdc.pk %}"
          hx-target="#sidebar-content" hx-swap="innerHTML">
        {% csrf_token %}
        <input type="hidden" name="transition" value="{{ transition_key }}">

        <div class="space-y-2">
            {% for item in checklist_items %}
            <label class="flex items-start gap-3 p-2 rounded-lg hover:bg-[var(--color-surface)]/50 cursor-pointer">
                <input type="checkbox" name="check_{{ item.pk }}"
                       {% if item.pk in items_deja_coches %}checked{% endif %}
                       class="mt-0.5 rounded border-[var(--color-border)] text-accent focus:ring-accent">
                <span class="text-sm text-[var(--color-text)]">{{ item.libelle }}</span>
            </label>
            {% endfor %}
        </div>

        <div class="flex items-center gap-2 mt-4">
            <button type="submit"
                    class="flex-1 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors">
                Confirmer
            </button>
            <button type="button"
                    hx-get="{% url 'bdc:detail_sidebar' pk=bdc.pk %}"
                    hx-target="#sidebar-content" hx-swap="innerHTML"
                    class="flex-1 px-4 py-2 text-sm font-medium rounded-lg border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface)] transition-colors">
                Annuler
            </button>
        </div>
    </form>
</div>
```

**Step 5: Creer la vue sidebar_checklist**

Dans `apps/bdc/views.py`, ajouter :

```python
# Map transition_key → (service_function, success_message)
TRANSITION_ACTIONS = {
    "EN_COURS__A_FACTURER": (valider_realisation, "realisation validee"),
    "A_FACTURER__FACTURE": (valider_facturation, "passe en facturation"),
    "A_FAIRE__EN_COURS": (None, ""),  # attribution geree separement
}


@login_required
def sidebar_checklist(request, pk: int):
    """GET: affiche la checklist pour une transition. POST: sauvegarde + tente la transition."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    transition_key = request.GET.get("transition") or request.POST.get("transition", "")

    items = ChecklistItem.objects.filter(actif=True, transition=transition_key)

    if request.method == "POST":
        # Sauvegarder les resultats
        for item in items:
            coche = f"check_{item.pk}" in request.POST
            ChecklistResultat.objects.update_or_create(
                bdc=bdc, item=item,
                defaults={"coche": coche},
            )

        # Tenter la transition
        action_info = TRANSITION_ACTIONS.get(transition_key)
        if action_info and action_info[0]:
            try:
                action_info[0](bdc, request.user)
                return _render_sidebar(
                    request, bdc,
                    success_message=f"BDC n°{bdc.numero_bdc} : {action_info[1]}."
                )
            except (TransitionInvalide, BDCIncomplet) as e:
                # Re-afficher la checklist avec l'erreur
                items_deja_coches = set(
                    bdc.checklist_resultats.filter(
                        item__transition=transition_key, coche=True
                    ).values_list("item_id", flat=True)
                )
                return render(request, "bdc/partials/_checklist_transition.html", {
                    "bdc": bdc, "checklist_items": items,
                    "transition_key": transition_key,
                    "items_deja_coches": items_deja_coches,
                    "error_message": str(e),
                })

        return _render_sidebar(request, bdc)

    # GET : afficher la checklist
    if not items.exists():
        # Pas de checklist → faire la transition directement
        action_info = TRANSITION_ACTIONS.get(transition_key)
        if action_info and action_info[0]:
            try:
                action_info[0](bdc, request.user)
                return _render_sidebar(
                    request, bdc,
                    success_message=f"BDC n°{bdc.numero_bdc} : {action_info[1]}."
                )
            except (TransitionInvalide, BDCIncomplet) as e:
                return _render_sidebar(request, bdc, error_message=str(e))

    items_deja_coches = set(
        bdc.checklist_resultats.filter(
            item__transition=transition_key, coche=True
        ).values_list("item_id", flat=True)
    )
    return render(request, "bdc/partials/_checklist_transition.html", {
        "bdc": bdc, "checklist_items": items,
        "transition_key": transition_key,
        "items_deja_coches": items_deja_coches,
    })
```

**Step 6: Verifier que les tests passent**

Run: `uv run pytest tests/test_bdc/test_controle.py::TestSidebarChecklistTransition -v --tb=short`
Expected: PASS

**Step 7: Lancer la suite complete**

Run: `uv run pytest --tb=short`
Expected: PASS

**Step 8: Commit**

```bash
git add apps/bdc/views.py apps/bdc/urls.py templates/bdc/partials/_checklist_transition.html tests/test_bdc/test_controle.py
git commit -m "feat: sidebar checklist views for all transitions"
```

---

## Task 5 : Modifier la sidebar pour utiliser les checklists de transition

**Files:**
- Modify: `templates/bdc/_detail_sidebar.html:51-79`
- Modify: `apps/bdc/views.py` (detail_sidebar, _render_sidebar)

**Step 1: Ajouter le contexte has_checklist dans les vues**

Dans `apps/bdc/views.py`, dans `_render_sidebar` et `detail_sidebar`, ajouter au contexte :

```python
# Determiner si des checklists existent pour les transitions du statut courant
checklist_transitions = {}
if bdc.statut == StatutChoices.EN_COURS:
    checklist_transitions["EN_COURS__A_FACTURER"] = ChecklistItem.objects.filter(
        actif=True, transition=TransitionChoices.REALISATION
    ).exists()
elif bdc.statut == StatutChoices.A_FACTURER:
    checklist_transitions["A_FACTURER__FACTURE"] = ChecklistItem.objects.filter(
        actif=True, transition=TransitionChoices.FACTURATION
    ).exists()
```

Passer `checklist_transitions` dans le contexte du template.

**Step 2: Modifier le template sidebar**

Dans `templates/bdc/_detail_sidebar.html`, remplacer les boutons EN_COURS et A_FACTURER pour utiliser `hx-get` vers la checklist quand des items existent :

Pour EN_COURS (lignes 51-66) :
```html
{% elif bdc.statut == 'EN_COURS' %}
<div class="mt-3 flex items-center gap-2">
    {% if checklist_transitions.EN_COURS__A_FACTURER %}
    <button type="button"
            hx-get="{% url 'bdc:sidebar_checklist' pk=bdc.pk %}?transition=EN_COURS__A_FACTURER"
            hx-target="#sidebar-content" hx-swap="innerHTML"
            class="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-sm">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        Valider r&eacute;alisation
    </button>
    {% else %}
    <form hx-post="{% url 'bdc:valider_realisation' pk=bdc.pk %}"
          hx-target="#sidebar-content" hx-swap="innerHTML">
        {% csrf_token %}
        <button type="submit"
                class="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Valider r&eacute;alisation
        </button>
    </form>
    {% endif %}
    <a href="{% url 'bdc:attribution_split' pk=bdc.pk %}"
       class="inline-block px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-colors">
        R&eacute;attribuer
    </a>
</div>
```

Pour A_FACTURER (lignes 67-79) :
```html
{% elif bdc.statut == 'A_FACTURER' %}
<div class="mt-3">
    {% if checklist_transitions.A_FACTURER__FACTURE %}
    <button type="button"
            hx-get="{% url 'bdc:sidebar_checklist' pk=bdc.pk %}?transition=A_FACTURER__FACTURE"
            hx-target="#sidebar-content" hx-swap="innerHTML"
            class="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-sm">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        Passer en facturation
    </button>
    {% else %}
    <form hx-post="{% url 'bdc:valider_facturation' pk=bdc.pk %}"
          hx-target="#sidebar-content" hx-swap="innerHTML">
        {% csrf_token %}
        <button type="submit"
                class="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Passer en facturation
        </button>
    </form>
    {% endif %}
</div>
```

**Step 3: Verifier les tests existants**

Run: `uv run pytest tests/test_bdc/ -v --tb=short`
Expected: PASS

**Step 4: Commit**

```bash
git add apps/bdc/views.py templates/bdc/_detail_sidebar.html
git commit -m "feat: sidebar buttons show checklist when items exist"
```

---

## Task 6 : Onglets par transition dans la page de gestion checklist

**Files:**
- Modify: `apps/accounts/views.py:166-177`
- Modify: `templates/accounts/checklist.html`

**Step 1: Modifier la vue checklist_liste**

Dans `apps/accounts/views.py`, modifier `checklist_liste` pour gerer les onglets :

```python
@login_required
def checklist_liste(request):
    transition = request.GET.get("transition", TransitionChoices.CONTROLE)
    if transition not in TransitionChoices.values:
        transition = TransitionChoices.CONTROLE

    if request.method == "POST":
        libelle = request.POST.get("libelle", "").strip()
        post_transition = request.POST.get("transition", transition)
        if libelle:
            max_ordre = ChecklistItem.objects.filter(transition=post_transition).aggregate(
                m=models.Max("ordre")
            )["m"] or 0
            ChecklistItem.objects.create(libelle=libelle, ordre=max_ordre + 1, transition=post_transition)
            messages.success(request, f"Point de controle « {libelle} » ajoute.")
        else:
            messages.error(request, "Le libelle ne peut pas etre vide.")
        return redirect(f"{reverse('gestion:checklist_liste')}?transition={post_transition}")

    items = ChecklistItem.objects.filter(transition=transition).order_by("ordre")
    transitions_list = TransitionChoices.choices
    return render(request, "accounts/checklist.html", {
        "items": items,
        "transitions_list": transitions_list,
        "transition_active": transition,
    })
```

Ajouter l'import de `TransitionChoices` en haut de `apps/accounts/views.py` :
```python
from apps.bdc.models import ..., TransitionChoices
```

**Step 2: Modifier le template checklist.html**

Ajouter les onglets en haut de la page, avant la liste :

```html
{# ── Onglets par transition ── #}
<div class="flex items-center gap-1 bg-[var(--color-surface-card)] rounded-xl border border-[var(--color-border)] p-1">
    {% for value, label in transitions_list %}
    <a href="?transition={{ value }}"
       class="px-4 py-2 rounded-lg text-sm font-medium transition-colors
              {% if transition_active == value %}bg-accent text-white{% else %}text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]{% endif %}">
        {{ label }}
    </a>
    {% endfor %}
</div>
```

Ajouter un champ hidden `transition` dans le formulaire de creation :
```html
<input type="hidden" name="transition" value="{{ transition_active }}">
```

**Step 3: Verifier les tests existants**

Run: `uv run pytest --tb=short`
Expected: PASS

**Step 4: Commit**

```bash
git add apps/accounts/views.py templates/accounts/checklist.html
git commit -m "feat: checklist management page with transition tabs"
```

---

## Task 7 : Mettre a jour les fixtures de test existantes

**Files:**
- Modify: `tests/test_bdc/test_controle.py:73-80`

**Step 1: Mettre a jour la fixture checklist_items**

La fixture `checklist_items` doit explicitement specifier `transition=TransitionChoices.CONTROLE` pour etre explicite :

```python
@pytest.fixture
def checklist_items(db):
    """Cree 3 items de checklist actifs pour la transition A_TRAITER → A_FAIRE."""
    return [
        ChecklistItem.objects.create(
            libelle="Nature des prestations verifiee", ordre=1,
            transition=TransitionChoices.CONTROLE,
        ),
        ChecklistItem.objects.create(
            libelle="Coherence surface / type de logement", ordre=2,
            transition=TransitionChoices.CONTROLE,
        ),
        ChecklistItem.objects.create(
            libelle="Montant verifie", ordre=3,
            transition=TransitionChoices.CONTROLE,
        ),
    ]
```

**Step 2: Verifier la suite complete**

Run: `uv run pytest --tb=short`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_bdc/test_controle.py
git commit -m "refactor: explicit transition in checklist test fixtures"
```

---

## Task 8 : Verification finale et nettoyage

**Step 1: Lancer tous les tests**

Run: `uv run pytest -v --tb=short`
Expected: Tous les tests passent

**Step 2: Linting**

Run: `uv run ruff check .`
Expected: Pas d'erreurs

**Step 3: Formattage**

Run: `uv run ruff format .`
Expected: Fichiers formates

**Step 4: Commit final si necessaire**

```bash
git add -A
git commit -m "chore: lint and format"
```
