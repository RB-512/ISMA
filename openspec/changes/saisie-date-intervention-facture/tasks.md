## 1. Modèle

- [x] 1.1 Ajouter `numero_facture`, `date_facturation`, la contrainte d'unicité conditionnelle et le libellé « Date d'intervention » sur `BonDeCommande`
- [x] 1.2 Générer et appliquer la migration

## 2. Services

- [x] 2.1 `valider_realisation(bdc, utilisateur, date_intervention)` : date obligatoire, pas future
- [x] 2.2 `valider_facturation(bdc, utilisateur, numero_facture, date_facturation)` : champs obligatoires, unicité, date ni future ni antérieure à l'intervention, IntegrityError convertie
- [x] 2.3 `changer_statut` refuse EN_COURS → A_FACTURER et A_FACTURER → FACTURE

## 3. Vues

- [x] 3.1 Lire les champs du POST dans `valider_realisation_bdc` et `valider_facturation_bdc`, avec gestion des erreurs `BDCIncomplet`
- [x] 3.2 `sidebar_checklist` : afficher les champs de saisie, les transmettre au service, réafficher avec les valeurs en cas d'erreur

## 4. Templates

- [x] 4.1 Sidebar : les boutons « Valider » et « Passer en facturation » ouvrent toujours le panneau de saisie
- [x] 4.2 Panneau `_checklist_transition.html` : champs date d'intervention / n° + date de facture, puis la checklist éventuelle
- [x] 4.3 Fiche détail : champs inline dans les formulaires de validation et de facturation
- [x] 4.4 Tableau de bord : colonnes « Intervention » et « Facture »

## 5. Tests

- [x] 5.1 Adapter les tests existants aux nouvelles signatures et au refus de la voie générique
- [x] 5.2 Tests des règles : champs manquants, date future, date de facture avant intervention, n° en doublon
- [x] 5.3 Tests des vues (sidebar et fiche détail) et de l'affichage des colonnes du tableau de bord
- [x] 5.4 Suite complète verte, ruff propre, vérification dans le navigateur
