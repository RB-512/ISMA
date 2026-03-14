## 1. Filtre template |montant

- [x] 1.1 Creer `apps/bdc/templatetags/__init__.py` et `apps/bdc/templatetags/bdc_filters.py` avec le filtre `|montant`
- [x] 1.2 Le filtre formate : separateur milliers (espace insecable), virgule decimale, espace insecable + €, tiret cadratin si null

## 2. Dashboard — nowrap montants et badges

- [x] 2.1 Ajouter `whitespace-nowrap` sur les cellules montant HT et montant ST dans `_liste_partial.html`
- [x] 2.2 Ajouter `whitespace-nowrap` sur les cellules badge statut dans `_liste_partial.html`
- [x] 2.3 Remplacer `floatformat:2` + ` €` par `|montant` dans `_liste_partial.html`

## 3. Fiche detail — nowrap montants prestations

- [x] 3.1 Ajouter `whitespace-nowrap` sur les cellules P.U. HT et Montant HT dans `detail.html`
- [x] 3.2 Remplacer `floatformat:2` + ` €` par `|montant` dans `detail.html` (prestations + totaux)

## 4. Page controle/attribution — hauteur PDF viewer

- [x] 4.1 Reduire les marges/paddings et maximiser la hauteur de l'iframe PDF dans `controle.html`
- [x] 4.2 Appliquer la meme correction dans `attribution_split.html` si applicable

## 5. Deploiement

- [x] 5.1 Deployer en prod et verifier visuellement
