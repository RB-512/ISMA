## Context

Le CDT rencontre des erreurs 500 lors de l'attribution d'un BDC. L'analyse de `services.py` révèle que `_calculer_montant_st(bdc, pourcentage)` ne gère pas le cas `pourcentage=None` quand `bdc.montant_ht` est renseigné.

Scénario reproductible :
1. Mode `forfait` sélectionné dans le formulaire
2. Aucune ligne forfait soumise dans le POST (ex : l'utilisateur n'a pas rempli les lignes)
3. `_parse_lignes_forfait` retourne `[]` (liste vide = falsy)
4. Dans `attribuer_st` : `if mode == "forfait" and lignes_forfait:` → False → on entre dans `else`
5. `_calculer_montant_st(bdc, None)` → `bdc.montant_ht * None` → `TypeError` → 500

Par ailleurs, `attribution_partial` (vue HTMX inline) n'envoie pas `joindre_bdc` à `attribuer_st`/`reattribuer_st`, contrairement à `attribution_split`. Comportement incohérent.

## Goals / Non-Goals

**Goals:**
- Corriger le `TypeError` dans `_calculer_montant_st` quand `pourcentage=None`
- Aligner `attribution_partial` sur `attribution_split` pour le paramètre `joindre_bdc`

**Non-Goals:**
- Pas de refactoring du formulaire d'attribution
- Pas de validation côté serveur sur les lignes forfait (déjà partiellement géré)

## Decisions

**Guard minimal dans `_calculer_montant_st`**
→ Ajouter `if pourcentage is None: return None` en tête de fonction. Cohérent avec le guard existant sur `montant_ht`. Simple, ciblé, sans effet de bord.

**Lire `joindre_bdc` dans `attribution_partial`**
→ Même logique que dans `attribution_split` : `joindre_bdc = request.POST.get("joindre_bdc") == "on"`. Aligne les deux vues.

## Risks / Trade-offs

- [Bug non encore confirmé par les logs] → Le fix est défensif et sans effet de bord : si `pourcentage` est None, `montant_st` reste None (comportement cohérent avec les BDC sans montant HT). Risque de fix nul.
- [Autres causes de 500 possibles] → Ce fix couvre le cas identifié. Une fois le tracking d'erreurs en place (change `error-tracking-prod`), d'autres causes potentielles seront visibles.

## Migration Plan

1. Modifier `services.py` : ajouter guard dans `_calculer_montant_st`
2. Modifier `views.py` : ajouter `joindre_bdc` dans `attribution_partial`
3. Lancer les tests : `uv run pytest apps/bdc/`
4. Déployer
