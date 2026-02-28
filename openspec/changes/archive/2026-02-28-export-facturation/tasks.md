## 1. Dépendance

- [x] 1.1 Ajouter `openpyxl` aux dépendances du projet

## 2. Service d'export Excel

- [x] 2.1 Créer `apps/bdc/exports.py` avec la fonction `generer_export_excel(queryset) -> HttpResponse` qui produit un fichier .xlsx avec les colonnes : N° BDC, Bailleur, Adresse, Ville, Sous-traitant, % ST, Montant HT, Montant ST, Date réalisation, Statut
- [x] 2.2 Le nom du fichier doit suivre le format `export_facturation_YYYY-MM-DD.xlsx`

## 3. Formulaire de filtres

- [x] 3.1 Créer `ExportFacturationForm` dans `forms.py` : champs `statut` (select : A_FACTURER / FACTURE / tous), `sous_traitant` (select), `date_du` (DateField), `date_au` (DateField)

## 4. Vue d'export

- [x] 4.1 Créer la vue `export_facturation` : GET affiche le formulaire avec aperçu du nombre de BDC, POST déclenche le téléchargement Excel
- [x] 4.2 Ajouter la route `export/` dans `urls.py`

## 5. Template

- [x] 5.1 Créer `templates/bdc/export_facturation.html` : formulaire de filtres, aperçu du compte, bouton télécharger (désactivé si 0 résultats)

## 6. Intégration dans les écrans existants

- [x] 6.1 Ajouter un bouton "Exporter" dans `recoupement_liste.html` pointant vers `/bdc/export/`
- [x] 6.2 Ajouter un lien "Export facturation" dans `liste.html` visible uniquement pour les CDT

## 7. Tests

- [x] 7.1 Tests service `generer_export_excel()` : colonnes correctes, données, fichier valide
- [x] 7.2 Tests vue `export_facturation` : accès CDT, refus secrétaire, filtres période/ST/statut, téléchargement
- [x] 7.3 Tests template : aperçu du compte, bouton désactivé si 0, liens dans recoupement et dashboard

## 8. Validation

- [x] 8.1 Lancer `pytest` et `ruff check` — tous les tests passent, pas de lint
