# Checklists de transition configurables

**Date** : 2026-03-07
**Statut** : Approuve

## Contexte

Le systeme actuel a une checklist uniquement pour la transition A_TRAITER -> A_FAIRE (controle secretaire). L'objectif est d'etendre ce mecanisme a toutes les transitions du workflow : A_FAIRE -> EN_COURS, EN_COURS -> A_FACTURER, A_FACTURER -> FACTURE.

Les checklists sont optionnelles (une transition sans items de checklist passe directement) et bloquantes (tous les items doivent etre coches pour autoriser la transition).

## Decisions

- **Approche A** : ajout d'un champ `transition` sur le modele `ChecklistItem` existant (pas de nouveau modele)
- **UX** : checklist inline dans la sidebar du dashboard (pas de modale)
- **Blocage** : toujours bloquant — tous les items actifs doivent etre coches
- **Notes** : supprimees — juste une case a cocher par item
- **Migration** : les items existants recoivent `transition="A_TRAITER__A_FAIRE"` via le default
- **Scope** : une seule checklist par transition, partagee par tous les utilisateurs

## Modele de donnees

### ChecklistItem (modifie)

Ajout du champ `transition` :

```python
class TransitionChoices(models.TextChoices):
    CONTROLE = "A_TRAITER__A_FAIRE", "Controle -> A attribuer"
    ATTRIBUTION = "A_FAIRE__EN_COURS", "Attribution -> En cours"
    REALISATION = "EN_COURS__A_FACTURER", "Realisation -> A facturer"
    FACTURATION = "A_FACTURER__FACTURE", "Facturation -> Facture"

class ChecklistItem(models.Model):
    libelle = models.CharField(max_length=200)
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)
    transition = models.CharField(
        max_length=30,
        choices=TransitionChoices.choices,
        default=TransitionChoices.CONTROLE,
    )
```

### ChecklistResultat (inchange)

Le FK vers ChecklistItem suffit — on connait la transition via `item.transition`.

## Services

### Garde de transition generique

```python
def _verifier_checklist_transition(bdc, ancien_statut, nouveau_statut):
    transition_key = f"{ancien_statut}__{nouveau_statut}"
    items_actifs = ChecklistItem.objects.filter(actif=True, transition=transition_key).count()
    if items_actifs > 0:
        items_coches = bdc.checklist_resultats.filter(
            item__actif=True, item__transition=transition_key, coche=True
        ).count()
        if items_coches < items_actifs:
            raise BDCIncomplet("Tous les points de controle doivent etre coches.")
```

Appelee dans :
- `changer_statut()` — toutes transitions
- `attribuer_st()` — A_FAIRE -> EN_COURS
- `valider_realisation()` — EN_COURS -> A_FACTURER
- `valider_facturation()` — A_FACTURER -> FACTURE

### Comportement quand pas de checklist

Si aucun item actif n'existe pour une transition, la validation passe directement (0 items = 0 a cocher = OK).

## UX — Sidebar du dashboard

### Flux avec checklist

1. CDT clique "Valider realisation" dans la sidebar
2. hx-get charge un partial checklist dans la sidebar
3. Le partial affiche les items a cocher + boutons "Confirmer" / "Annuler"
4. Au clic "Confirmer" : hx-post sauvegarde les resultats + tente la transition
5. Succes : sidebar se met a jour (nouveau statut), dashboard se rafraichit (HX-Trigger: bdc-updated)
6. Echec : erreur affichee dans la sidebar

### Flux sans checklist

Le bouton fait directement le POST de validation (comportement actuel, 1 clic).

### Detection automatique

La vue verifie s'il existe des items actifs pour la transition. Si oui, elle affiche la checklist. Si non, elle fait la transition directement.

## Page de gestion

La page `/gestion/checklist/` s'enrichit avec des onglets par transition :

```
[Controle] [Attribution] [Realisation] [Facturation]
```

Chaque onglet filtre les items par `transition`. Le formulaire d'ajout inclut la transition en hidden field (deduit de l'onglet actif).

## Page de controle existante

La page controle (split-screen PDF + checklist pour A_TRAITER -> A_FAIRE) filtre desormais les items par `transition="A_TRAITER__A_FAIRE"` au lieu de prendre tous les items actifs.

## Impact sur les tests

- Tests existants sur la checklist : adapter les filtres (ajouter `transition=`)
- Nouveaux tests : verification checklist pour chaque transition
- Tests sidebar : flux HTMX checklist inline
