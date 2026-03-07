# Anonymisation PDF terrain GDH

## Objectif

Masquer le telephone et l'email de l'emetteur dans le PDF terrain GDH avant envoi au sous-traitant. Le texte original est physiquement supprime et remplace par `***`.

## Perimetre

- **Champs masques** : telephone et email de l'emetteur du BDC (pas de l'occupant)
- **Bailleurs concernes** : GDH uniquement (ERILIA genere le PDF depuis un template HTML, deja controle)
- **Style** : redaction PyMuPDF avec texte de remplacement `***`

## Implementation

### Fichier modifie

`apps/bdc/terrain.py`

### Fonction ajoutee

```python
def _anonymiser_page(page: fitz.Page) -> None:
```

- Extrait le texte de la page
- Identifie le telephone emetteur via regex (`Tel : \d+` apres `Emetteur`)
- Identifie l'email emetteur via regex (`Mail : ...@...` apres `Emetteur`)
- Cherche les valeurs dans le PDF avec `page.search_for()`
- Applique la redaction avec `***` comme texte de remplacement

### Integration

Appelee dans `_generer_terrain_gdh()` apres extraction de la page 2, avant `tobytes()`.

## Impact

- Un seul fichier modifie, pas de migration
- Les PDFs terrain existants ne sont pas affectes
- Test unitaire a ajouter
