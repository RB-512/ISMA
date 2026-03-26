## Context

Le mail d'attribution est envoye via une chaine :
`attribution_split (view)` → `attribuer_st()` → `_notifier_st_si_possible()` → `envoyer_email_attribution()`

Aujourd'hui `commentaire` traverse toute cette chaine. `joindre_bdc` suivra le meme chemin.

## Goals / Non-Goals

**Goals:**
- Ajouter `{etage}` et `{porte}` dans le corps du mail (template par defaut + variables ConfigEmail)
- Ajouter un toggle "Joindre le BDC" dans la barre d'onglets du viewer PDF
- Le toggle controle la visibilite du bouton "Vue sous-traitant" et la piece jointe
- La decision `joindre_bdc` traverse toute la chaine jusqu'a `envoyer_email_attribution()`

**Non-Goals:**
- Modifier la fiche chantier PDF elle-meme
- Changer le comportement du SMS

## Decisions

### Toggle UI (Alpine.js)
Le toggle partage le meme `x-data` que les onglets PDF. Quand `joindre=false` :
- `vueST` est force a `false` (retour sur PDF original)
- Le bouton "Vue sous-traitant" est masque (`x-show="joindre"`)
- Un `<input type="hidden" name="joindre_bdc" :value="joindre ? 'on' : ''">` transmet la valeur

### Chaine de propagation
```
View attribution_split
  └─ joindre_bdc = request.POST.get("joindre_bdc") == "on"
       ↓
attribuer_st(..., joindre_bdc=True/False)
  └─ _notifier_st_si_possible(..., joindre_bdc=True/False)
       ↓
envoyer_email_attribution(bdc, commentaire=..., joindre_bdc=True/False)
  └─ if joindre_bdc: attacher le PDF
     else: pas de PDF, pas de message "non disponible"
```

### Variables email etage/porte
Ajout dans le dict `variables` de `envoyer_email_attribution()` :
- `"etage"` : `bdc.logement_etage or ""`
- `"porte"` : `bdc.logement_porte or ""`

Ajout dans le corps par defaut uniquement si les valeurs existent (evite les lignes vides).

### Reattribution
`envoyer_email_reattribution()` appelle `envoyer_email_attribution()` — passer `joindre_bdc` en cascade.
`reattribuer_st()` et `_notifier_reattribution_si_possible()` suivent le meme pattern.

## Risks / Trade-offs

- **Defaut : joindre=True** — comportement actuel preserve si le champ est absent du POST
- Quand `joindre_bdc=False`, supprimer le message fallback "document non disponible" (il est intentionnel de ne pas joindre)
