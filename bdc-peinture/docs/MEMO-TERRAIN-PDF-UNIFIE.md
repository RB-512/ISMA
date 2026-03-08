# Memo : PDF Terrain Unifie

## Contexte

Le 07/03/2026, le generateur de PDF terrain a ete reecrit pour unifier le process
GDH et ERILIA en un seul generateur PyMuPDF (plus de WeasyPrint, plus de dispatch par bailleur).

**Probleme initial** : les BDC ERILIA n'avaient jamais de PDF terrain joint aux emails
car WeasyPrint echouait silencieusement (dependances C manquantes GTK/Pango).

## Branches

| Branche | Contenu |
|---------|---------|
| `dev` | Ancienne version (dispatch GDH/ERILIA, WeasyPrint) |
| `feat/terrain-pdf-unifie` | Nouvelle version (generateur unique PyMuPDF) |

## Changer de version

```bash
# Revenir a l'ancienne version
git checkout dev

# Utiliser la nouvelle version
git checkout feat/terrain-pdf-unifie

# Merger definitivement dans dev (quand pret)
git checkout dev
git merge feat/terrain-pdf-unifie
```

## Fichiers modifies

- `apps/bdc/terrain.py` — reecrit : un seul generateur PyMuPDF pour tous bailleurs
- `tests/test_bdc/test_terrain.py` — tests adaptes (24 tests)
- `templates/bdc/terrain_erilia.html` — supprime (plus necessaire)

## Layout du nouveau PDF terrain

```
+-------------------------------------------+
| BAILLEUR (gros)          [LOGO]           |
| BON DE COMMANDE TERRAIN   ISMA Peinture   |
| N° XXXX                   04 90 XX XX XX  |
| Marche XXXX               contact@...     |
|-------------------------------------------|
| LOCALISATION                              |
| Adresse / Residence / Logement            |
|-------------------------------------------|
| TRAVAUX                                   |
| Objet / Delai                             |
|-------------------------------------------|
| PRESTATIONS                               |
| Designation (texte complet)  | Qte | Unite|
|-------------------------------------------|
| COMMENTAIRE                               |
| [zone vide encadree]                      |
|-------------------------------------------|
| SIGNATURE                                 |
| +---------------------------------------+ |
| | Date : ________   Signature :         | |
| | Nom  : ________                       | |
| +---------------------------------------+ |
+-------------------------------------------+
```

## Points cles

- **Sans prix** : les prix unitaires et montants ne figurent jamais sur le terrain
- **Universel** : fonctionne pour GDH, ERILIA, et tout futur bailleur
- **Infos ISMA** : en dur pour l'instant (constantes dans terrain.py)
- **Logo** : emplacement reserve (rectangle pointille), pas d'image encore
- **Commentaire** : zone vide, pas de champ en base (a ajouter plus tard si besoin)
