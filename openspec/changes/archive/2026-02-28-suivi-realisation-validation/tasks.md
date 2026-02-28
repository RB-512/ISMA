## 1. Modèle et migration

- [x] 1.1 Ajouter `date_realisation` (DateField, nullable, blank) sur `BonDeCommande` + créer la migration

## 2. Services — validation et facturation

- [x] 2.1 Implémenter `valider_realisation(bdc, utilisateur)` : vérifie EN_COURS, passe à A_FACTURER, remplit `date_realisation`, trace VALIDATION
- [x] 2.2 Implémenter `valider_facturation(bdc, utilisateur)` : vérifie A_FACTURER, passe à FACTURE, trace FACTURATION
- [x] 2.3 Modifier `changer_statut()` : si transition A_FACTURER → EN_COURS, remettre `date_realisation` à null

## 3. Vues CDT — validation et facturation

- [x] 3.1 Créer la vue `valider_realisation_bdc(pk)` : POST-only, CDT, appelle `valider_realisation()`, redirige vers détail
- [x] 3.2 Créer la vue `valider_facturation_bdc(pk)` : POST-only, CDT, appelle `valider_facturation()`, redirige vers détail
- [x] 3.3 Ajouter les routes `<int:pk>/valider/` et `<int:pk>/facturer/` dans `urls.py`

## 4. Template detail — boutons CDT

- [x] 4.1 Ajouter bouton "Valider réalisation" (vert) pour CDT quand statut = EN_COURS
- [x] 4.2 Ajouter bouton "Passer en facturation" (bleu) pour CDT quand statut = A_FACTURER
- [x] 4.3 Ajouter bouton "Annuler validation" (gris) pour CDT quand statut = A_FACTURER, POST vers `changer_statut` avec `nouveau_statut=EN_COURS`

## 5. Vue recoupement par ST

- [x] 5.1 Créer la vue `recoupement_st_liste` : liste des ST avec compteurs BDC par statut (en cours, à facturer, facturé)
- [x] 5.2 Créer la vue `recoupement_st_detail(st_pk)` : BDC d'un ST donné avec filtre par statut
- [x] 5.3 Ajouter les routes `recoupement/` et `recoupement/<int:st_pk>/` dans `urls.py`
- [x] 5.4 Créer `templates/bdc/recoupement_liste.html` : tableau des ST avec compteurs et liens
- [x] 5.5 Créer `templates/bdc/recoupement_detail.html` : liste des BDC du ST avec filtre statut

## 6. Tests

- [x] 6.1 Tests unitaires `valider_realisation()` : transition OK, refus si pas EN_COURS, date_realisation remplie, historique VALIDATION
- [x] 6.2 Tests unitaires `valider_facturation()` : transition OK, refus si pas A_FACTURER, historique FACTURATION
- [x] 6.3 Tests unitaires retour A_FACTURER → EN_COURS : date_realisation remise à null
- [x] 6.4 Tests vues `valider_realisation_bdc` et `valider_facturation_bdc` : accès CDT, refus secrétaire, GET redirige
- [x] 6.5 Tests template detail : boutons "Valider réalisation", "Passer en facturation", "Annuler validation" conditionnels
- [x] 6.6 Tests vue recoupement : liste ST avec compteurs, détail BDC par ST, filtre statut, accès CDT only

## 7. Validation

- [x] 7.1 Lancer `pytest` et `ruff check` — tous les tests passent, pas de lint
