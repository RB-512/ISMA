## Context

Retours de tests utilisateurs en production (mars 2026). 5 corrections localisées dans des fichiers existants — pas de migration.

## Goals / Non-Goals

**Goals:**
- Éliminer l'erreur 500 sur la facturation
- Corriger les incohérences d'affichage
- Améliorer l'esthétique de la sidebar

**Non-Goals:**
- Refonte du workflow de facturation
- Responsive design complet

## Decisions

- **D1** : Ajout catch `BDCIncomplet` + `Exception` générique avec logging dans la vue facturation
- **D2** : Condition `bdc.occupation and bdc.occupant_nom` pour afficher le bloc occupant
- **D3** : Ajout colonne "Ville" dans l'export PDF du relevé (HTML et Excel l'avaient déjà)
- **D4** : Reproduction du pattern `detail.html` pour étage/porte dans `fiche_chantier_st.html`
- **D5** : CSS `scrollbar-width: none` + `::-webkit-scrollbar { display: none }` sur la nav sidebar

## Risks / Trade-offs

- **D1** : Le `except Exception` générique est large mais logge l'erreur — acceptable pour éviter les 500
- **D5** : Scrollbar masquée réduit la discoverabilité — acceptable car le nombre d'items est limité
