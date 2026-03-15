## Context

L'email d'attribution utilise un objet par defaut `BDC {numero_bdc} — Attribution` et un systeme de template personnalisable via ConfigEmail avec des variables de substitution (`{numero_bdc}`, `{adresse}`, `{ville}`, `{travaux}`, `{delai}`, `{commentaire}`).

## Goals / Non-Goals

**Goals:**
- Ajouter `{nom_st}` dans les variables disponibles
- L'inclure dans l'objet par defaut

**Non-Goals:**
- Modifier le corps du mail par defaut
- Changer le template de reattribution

## Decisions

Ajouter `nom_st` dans le dict `variables` existant dans `envoyer_email_attribution()`. Changer l'objet par defaut de `BDC {numero_bdc} — Attribution` a `BDC {numero_bdc} — Attribution — {nom_st}`. Modification minimale (2 lignes de code + 1 ligne de template).
