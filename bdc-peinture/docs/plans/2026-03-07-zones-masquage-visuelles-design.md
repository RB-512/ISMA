# Zones de masquage visuelles PDF

**Date** : 2026-03-07
**Statut** : Valide

## Probleme

Le systeme de masquage actuel (checkboxes `champs_masques`) est fragile :
- Il cherche des valeurs textuelles exactes dans le PDF (ex: "11,19")
- Il depend des donnees extraites en base pour trouver quoi masquer
- Il ne sait pas distinguer un prix d'une quantite identique
- L'utilisateur ne comprend pas quels champs correspondent a quoi sur le PDF

## Solution

Remplacer le masquage par recherche textuelle par un systeme de **zones visuelles** :
l'admin dessine des rectangles sur le PDF modele du bailleur, et ces zones sont
masquees (remplies en blanc) sur tous les BDC de ce bailleur.

## Donnees

Nouveau champ `Bailleur.zones_masquage` (JSONField) remplacant `champs_masques` :

```python
zones_masquage = models.JSONField(default=list, blank=True)
# Format : [{"x": 350, "y": 100, "w": 200, "h": 400, "page": 1, "label": "Colonne prix"}]
```

Chaque zone :
- `x`, `y` : coin superieur gauche en points PDF (72 pts = 1 pouce)
- `w`, `h` : largeur et hauteur en points PDF
- `page` : numero de page (1-indexe)
- `label` : description optionnelle

Migration : supprimer `champs_masques`, ajouter `zones_masquage`.

## Interface de configuration

Page dediee par bailleur avec editeur visuel :

1. Le PDF modele est rendu dans un canvas via PDF.js (CDN)
2. L'utilisateur dessine des rectangles (drag souris) sur les zones a masquer
3. Chaque rectangle peut etre nomme et supprime
4. Bouton Enregistrer sauvegarde les zones en JSON
5. Bouton Previsualiser montre le resultat sur un vrai BDC

Stack frontend : PDF.js (CDN) + Alpine.js (deja present) + canvas overlay.

## Backend masquage

`generer_pdf_masque()` simplifie :

```python
for zone in bailleur.zones_masquage:
    page = doc[zone["page"] - 1]
    rect = fitz.Rect(zone["x"], zone["y"], zone["x"] + zone["w"], zone["y"] + zone["h"])
    page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions()
```

Plus de recherche textuelle, plus de variantes de formatage.
Le filtrage de pages (`pages_a_envoyer`) reste en complement.

## Fichiers impactes

- `apps/bdc/models.py` : remplacer `champs_masques` par `zones_masquage`
- `apps/bdc/masquage_pdf.py` : refaire `generer_pdf_masque()` avec logique zones
- `apps/accounts/views.py` : refaire `config_bailleurs` et `config_bailleur_form`
- `templates/accounts/config_bailleur.html` : editeur visuel PDF.js
- `templates/accounts/partials/_config_bailleur_form.html` : supprimer checkboxes
- `apps/bdc/migrations/` : migration champs_masques -> zones_masquage
- Tests : adapter les tests existants

## Ce qui ne change pas

- `pages_a_envoyer` (filtrage de pages)
- Toggle "Vue sous-traitant" dans l'attribution
- `generer_pdf_masque()` API (meme signature, meme resultat)
- Envoi email avec PDF masque
