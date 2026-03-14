## 1. Fix erreur 500 facturation (critique)

- [x] 1.1 Investiguer la cause exacte : `BDCIncomplet` non catchée dans `valider_facturation_bdc`
- [x] 1.2 Ajouter catch `BDCIncomplet` + `Exception` générique avec logging dans views.py
- [x] 1.3 Vérifier : facturation ne crash plus, affiche un message clair

## 2. Fix affichage contact occupant

- [x] 2.1 Ajouter vérification `bdc.occupation` en plus de `bdc.occupant_nom` dans detail.html
- [x] 2.2 Vérifier : BDC avec occupation="" ne montre plus le bloc Occupant

## 3. Ville dans relevé facturation

- [x] 3.1 Identifier champ ville dans modèle BDC (champ `ville` dédié existant)
- [x] 3.2 Template HTML : déjà OK (colonne Ville présente)
- [x] 3.3 Export PDF : ajout colonne Ville dans releves_export.py
- [x] 3.4 Export Excel : déjà OK (colonne Ville présente)

## 4. Étage et porte sur fiche chantier ST

- [x] 4.1 Ajout affichage conditionnel étage/porte dans fiche_chantier_st.html

## 5. Sidebar scrollbar masquée

- [x] 5.1 CSS scrollbar-width: none + ::-webkit-scrollbar dans base.html
