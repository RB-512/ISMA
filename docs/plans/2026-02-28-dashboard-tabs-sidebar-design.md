# Dashboard: Onglets, Sidebar Detail, Colonnes ST + Montant HT

## Contexte

Le dashboard actuel affiche des cards compteurs par statut, un tableau de BDC, et navigue vers une page detail au clic. On veut :
1. Remplacer les cards par des onglets horizontaux filtrant par statut
2. Ouvrir un panneau lateral droit au clic (au lieu de naviguer)
3. Ajouter les colonnes sous-traitant et montant HT au tableau

## 1. Onglets horizontaux par statut

Les 6 cards compteurs sont remplacees par une barre d'onglets epuree :

```
 Tous (5) | A traiter (1) | A faire (1) | En cours (1) | A facturer (1) | Facture (1)
```

- Onglet actif : `border-b-2 border-accent`, texte accent
- Onglets inactifs : texte muted, hover subtle
- Compteur entre parentheses dans le label
- Clic = requete HTMX `hx-get="/?statut=A_TRAITER"` qui swap le tableau
- Onglet "Tous" n'envoie pas de filtre statut
- Les filtres existants (recherche, bailleur, ville, dates) restent en dessous et se combinent avec l'onglet actif

## 2. Sidebar de detail (HTMX)

Au clic sur une ligne du tableau, une sidebar s'ouvre a droite :

```
+------------------------------------------+---------------------+
|  [Onglets]                               |                     |
|  [Filtres]                               |  BDC-2026-1000      |
|  +--------------------------------------+|  Statut: A traiter  |
|  | BDC-2026-1004  GDH  Marseille        ||  [Bouton: A faire]  |
|  | BDC-2026-1003  GDH  Marseille        ||                     |
|  | BDC-2026-1002  GDH  Marseille        ||  LOCALISATION       |
|  |>BDC-2026-1000  GDH  Marseille<       ||  10 rue de la Paix  |
|  +--------------------------------------+|                     |
|                                          |  SOUS-TRAITANT      |
|                                          |  Peinture Pro SARL  |
|                                          |                     |
|                                          |  PRESTATIONS        |
|                                          |  ...                |
|                                          |                     |
|                                          |  HISTORIQUE         |
|                                          |  ...       [X]      |
+------------------------------------------+---------------------+
```

### Comportement
- Largeur : ~400px fixe, le tableau se comprime
- Transition : slide-in depuis la droite (CSS + Alpine.js toggle)
- Chargement : `hx-get="/<pk>/sidebar/"` retourne un partial `_detail_sidebar.html`
- Fermeture : bouton X + clic en dehors
- Ligne selectionnee surlignee dans le tableau

### Actions disponibles dans la sidebar
- Changer le statut (bouton contextuel selon le statut actuel)
- Attribuer / reattribuer un sous-traitant
- Editer les champs : occupation, modalite d'acces, RDV, notes
- Enregistrer les modifications

### Backend
- Nouvelle vue `detail_sidebar(request, pk)` retournant `_detail_sidebar.html`
- Nouvelle URL `<int:pk>/sidebar/`
- La vue existante `detail` reste pour l'acces direct par URL

## 3. Colonnes tableau

Le tableau passe de 6 a 8 colonnes :

```
N BDC | BAILLEUR | ADRESSE | VILLE | SOUS-TRAITANT | MONTANT HT | STATUT | DATE
```

- **Sous-traitant** : nom du ST attribue ou "—"
- **Montant HT** : somme des lignes de prestation, format `1 234,50 EUR`, font mono. "—" si aucune prestation
- `select_related('sous_traitant')` pour eviter les N+1 queries
- Annotation `Sum('lignes__montant_ht')` sur le queryset

## Decisions techniques

- **HTMX** pour le chargement de la sidebar (coherent avec l'archi existante)
- **Alpine.js** pour le toggle ouvert/ferme de la sidebar et les transitions
- Le partial `_liste_partial.html` est mis a jour pour inclure les onglets
- Le partial `_detail_sidebar.html` est cree pour le contenu de la sidebar
