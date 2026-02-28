## Context

La fiche détail BDC (`detail.html`) affiche actuellement les informations extraites du PDF en lecture seule : en-tête (numéro, bailleur, statut), localisation, travaux, prestations (sans prix), et historique. Le modèle `BonDeCommande` contient des champs manuels (`occupation`, `modalite_acces`, `rdv_pris`, `rdv_date`, `notes`) et des contacts (`occupant_*`, `emetteur_*`) qui ne sont pas affichés. Les transitions de statut ne sont possibles que via l'admin Django. Le service `changer_statut()` existe déjà dans `services.py` avec toute la logique métier (transitions autorisées, validation occupation).

## Goals / Non-Goals

**Goals:**
- Afficher toutes les informations utiles du BDC sur la fiche détail (contacts, sous-traitant)
- Permettre l'édition des champs manuels directement sur la fiche (sans passer par l'admin)
- Permettre les transitions de statut via boutons sur la fiche
- Garder la cohérence avec la logique métier existante (`changer_statut`, `enregistrer_action`)

**Non-Goals:**
- Pas de modification des champs extraits du PDF (numéro BDC, adresse, montants, etc.)
- Pas d'affichage des montants financiers (confidentiels — jamais sur le BDC terrain)
- Pas de gestion de l'attribution sous-traitant depuis cette page (c'est un autre workflow)
- Pas de notification SMS depuis la fiche détail

## Decisions

### D1 : Formulaire d'édition inline sur la même page (pas de page séparée)
Les champs manuels (occupation, modalité d'accès, RDV, notes) sont édités directement sur la fiche détail via un formulaire HTML classique POST. Pas de page `/edit/` séparée.
**Raison** : Moins de navigation, UX plus fluide pour la secrétaire qui traite les BDC en série.
**Alternative rejetée** : Page d'édition séparée — ajouterait un aller-retour inutile.

### D2 : `BDCEditionForm` — sous-ensemble du ModelForm existant
Nouveau formulaire `BDCEditionForm(ModelForm)` avec seulement les champs manuels : `occupation`, `modalite_acces`, `rdv_pris`, `rdv_date`, `notes`. Le `BonDeCommandeForm` existant reste inchangé pour la création.
**Raison** : Séparation claire entre champs éditables et champs extraits du PDF.

### D3 : Transitions de statut via POST avec boutons individuels
Chaque transition autorisée depuis le statut courant génère un bouton `<form method="POST">` avec le statut cible en champ hidden. La vue appelle `changer_statut()` du service existant.
**Raison** : Réutilise la logique métier existante (validation, traçabilité). Pas de JS nécessaire.
**Alternative rejetée** : API REST + fetch — over-engineering pour une app CRUD.

### D4 : Restriction d'accès — Secrétaire pour l'édition, tous pour la lecture
La vue `detail_bdc` reste `@login_required` (lecture pour tous). Les vues POST `modifier_bdc` et `changer_statut_bdc` sont `@group_required("Secretaire")`.
**Raison** : Cohérent avec le reste de l'application (upload et création réservés aux secrétaires).

### D5 : Affichage conditionnel du formulaire selon le rôle
Le template affiche le formulaire d'édition et les boutons de statut uniquement si l'utilisateur appartient au groupe "Secretaire". Les autres utilisateurs voient la page en lecture seule.
**Raison** : Un seul template, pas de duplication.

## Risks / Trade-offs

- [Concurrence] Si deux secrétaires éditent le même BDC simultanément, le dernier POST gagne → Acceptable à cette échelle (< 10 utilisateurs). Pas de locking.
- [Validation occupation] Le bouton "À faire" sera désactivé si occupation non renseignée → Le formulaire d'édition doit être soumis avant, messages d'erreur clairs.
- [Performance] `historique.all()[:10]` déjà en place → pas de changement.
