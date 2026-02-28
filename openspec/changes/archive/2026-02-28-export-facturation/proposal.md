## Why

Le CDT a besoin d'exporter les BDC passés en facturation pour préparer les factures et les transmettre à la comptabilité. Aujourd'hui, le recoupement est fait dans l'application (SPEC-005), mais il n'existe aucun moyen d'extraire ces données sous forme exploitable (Excel/CSV). Le CDT doit pouvoir exporter les BDC facturés par période et par sous-traitant pour alimenter le processus de facturation externe.

## What Changes

- Ajout d'une vue d'export accessible au CDT permettant de télécharger un fichier Excel (.xlsx) des BDC à facturer ou facturés
- Le fichier contient : numéro BDC, bailleur, adresse, sous-traitant, montant HT, montant ST, pourcentage ST, date réalisation, statut
- Filtres disponibles : par période (date de réalisation), par sous-traitant, par statut (à facturer / facturé)
- Ajout d'un lien "Exporter" sur la page de recoupement par ST et sur le tableau de bord

## Capabilities

### New Capabilities
- `export-facturation`: Export Excel/CSV des BDC à facturer et facturés, avec filtres par période, sous-traitant et statut

### Modified Capabilities
- `recoupement-st`: Ajout d'un bouton "Exporter" sur la liste et le détail du recoupement
- `dashboard-liste-bdc`: Ajout d'un lien "Export facturation" dans la barre d'actions du tableau de bord

## Impact

- Nouvelle dépendance : `openpyxl` pour la génération de fichiers Excel
- Nouveaux fichiers : vue d'export, template formulaire de filtres, service de génération Excel
- Modification templates existants : `recoupement_liste.html`, `recoupement_detail.html`, `liste.html` (ajout liens export)
- Routes : ajout de `export/` dans `urls.py`
