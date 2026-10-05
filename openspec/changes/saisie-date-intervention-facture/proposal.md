## Why

Les utilisateurs veulent retrouver dans le tableau de bord la date réelle d'intervention et les références de facturation (n° + date) de chaque BDC. Aujourd'hui la date de réalisation est posée automatiquement à la date du clic (et non à la date réelle des travaux), et rien ne trace la facture émise au bailleur.

## What Changes

- Passage EN_COURS → À facturer : la **date d'intervention** devient une saisie obligatoire (pré-remplie à aujourd'hui, pas de date future). Sans elle, le statut ne change pas. Elle est stockée dans le champ existant `date_realisation`, affiché désormais « Date d'intervention ».
- Passage À facturer → Facturé : le **n° de facture** et la **date de facturation** deviennent obligatoires. Le n° est unique (un n° par BDC) ; la date ne peut être ni future ni antérieure à la date d'intervention.
- Nouveaux champs `numero_facture` et `date_facturation` sur `BonDeCommande` (migration).
- Toutes les voies de transition (sidebar du tableau de bord, checklist de transition, fiche détail, `changer_statut` générique) appliquent la règle dans la couche service.
- Le tableau de bord affiche deux colonnes : « Intervention » (date) et « Facture » (n° + date).
- Le retour À facturer → En cours continue d'effacer la date d'intervention.
- **BREAKING** (API interne) : `valider_realisation()` et `valider_facturation()` exigent de nouveaux arguments.

## Capabilities

### New Capabilities
<!-- aucune -->

### Modified Capabilities
- `suivi-realisation` : la date de réalisation n'est plus automatique mais saisie (date d'intervention) ; la facturation exige n° + date de facture.
- `dashboard-liste-bdc` : la liste affiche la date d'intervention et le n° + date de facture.

## Impact

- `apps/bdc/models.py` (+ migration), `apps/bdc/services.py`, `apps/bdc/views.py`
- Templates : `_detail_sidebar.html`, `partials/_checklist_transition.html`, `detail.html`, `_table_body.html`
- Relevés et exports ST : ils filtrent par `date_realisation`, donc ils utiliseront la date d'intervention réelle au lieu de la date du clic (effet voulu).
- Tests : `test_validation.py`, `test_workflow.py` et les fixtures qui font passer des BDC en À facturer / Facturé.
