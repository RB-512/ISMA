# Analyse par periode de la charge sous-traitants

## Resume

Ajouter un selecteur de periode (semaine, mois, trimestre, annee, plage personnalisee) sur la page recoupement et dans le tableau de repartition inline d'attribution. Afficher la comparaison automatique avec la periode precedente (N-1) avec indicateurs delta.

## Decisions

- **Date de reference** : `Coalesce(date_emission, created_at)` -- fallback sur created_at si date_emission est null
- **Emplacement** : page recoupement ET tableau inline d'attribution
- **Comparaison** : periode precedente calculee automatiquement (meme duree, decalee)
- **Metriques** : nb BDC + montant_st (comme actuellement)
- **Selecteur** : boutons raccourcis + plage personnalisee, pas de navigation fleches
- **Approche** : enrichir l'existant (query params + HTMX), pas de nouvelle page

## Design UI

### Selecteur de periode (partial reutilisable)

```
Periode : [Semaine] [Mois] [Trimestre] [Annee] [Personnalise]
           Du [____] Au [____]
```

- Boutons raccourcis : calcul des bornes cote serveur
- Mode personnalise : 2 champs date input
- Transmis en query params : `?periode=mois&date=2026-02` ou `?date_du=...&date_au=...`
- HTMX : `hx-get` avec target adapte au contexte

### Page recoupement enrichie

```
Sous-traitant       | Periode      | Periode N-1  | Delta
                    | BDC  Montant | BDC  Montant |
--------------------|--------------|--------------|------
Dupont Peinture     |  3   12 400  |  2    8 100  | +1
Martin & Fils       |  1    4 200  |  3   11 500  | -2
Leroy Deco          |  5   18 900  |  4   15 200  | +1
```

- Sans filtre periode : comportement actuel (cumul global)
- Filtres statut existants conserves et combines avec le filtre periode

### Tableau inline d'attribution enrichi

Meme structure avec selecteur de periode au-dessus du tableau de repartition.
Filtre par defaut : statut EN_COURS (comme actuellement).
Le selecteur de periode se recharge via HTMX dans `#attribution-zone`.

## Backend

### Helper commun `_get_repartition_st(date_du, date_au, statuts)`

- Filtre BDC dont `Coalesce(date_emission, created_at)` est dans [date_du, date_au]
- Si statuts fourni : filtre sur ces statuts
- Retourne queryset annote avec nb_bdc + total_montant_st

### Helper `_calculer_bornes_periode(periode, date_ref)`

- Input : type de periode + date de reference optionnelle (defaut: aujourd'hui)
- Output : `(date_du, date_au, date_du_n1, date_au_n1)`
- Periodes : semaine (lundi-dimanche), mois, trimestre, annee, custom

## Fichiers a modifier

| Fichier | Action |
|---|---|
| `apps/bdc/views.py` | Modifier `_get_repartition_st()`, ajouter `_calculer_bornes_periode()`, modifier `recoupement_st_liste()`, modifier `attribution_partial()` |
| `templates/bdc/partials/period_selector.html` | Nouveau partial selecteur de periode |
| `templates/bdc/partials/attribution_form.html` | Integrer selecteur de periode |
| `templates/bdc/recoupement_liste.html` | Integrer selecteur + colonnes N-1 + delta |
| `tests/test_bdc/test_analyse_periode.py` | Nouveaux tests |

## Tests

- `test_repartition_filtre_par_periode` : BDC avec dates variees, seuls ceux de la periode apparaissent
- `test_repartition_periode_n1` : periode N-1 correctement calculee
- `test_fallback_created_at` : BDC sans date_emission utilise created_at
- `test_recoupement_avec_periode` : page recoupement avec query params de periode
- `test_attribution_partial_avec_periode` : tableau inline avec filtre periode
- `test_sans_periode_comportement_par_defaut` : sans query params, cumul global (retrocompatibilite)
- `test_calculer_bornes_semaine/mois/trimestre/annee` : calcul correct des bornes
