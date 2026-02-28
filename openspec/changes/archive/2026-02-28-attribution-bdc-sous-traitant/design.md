## Context

Le workflow BDC a 7 étapes (PRD §3.1). Les étapes 1-2 (réception, préparation) sont implémentées. L'étape 3 (attribution) est le pivot : le CDT choisit un ST, fixe le montant, et le BDC passe en "En cours". Le modèle `BonDeCommande` a déjà les champs `sous_traitant` (FK), `montant_st`, `pourcentage_st`. Le modèle `SousTraitant` existe (nom, telephone, email, actif). Les `ActionChoices` ont déjà `ATTRIBUTION` et `REATTRIBUTION`. Le service `changer_statut()` gère la transition `A_FAIRE → EN_COURS`.

## Goals / Non-Goals

**Goals:**
- Permettre au CDT d'attribuer un BDC "À faire" à un ST actif
- Calculer le montant ST depuis le pourcentage et le montant HT du BDC
- Tracer l'attribution dans l'historique (qui, quand, quel ST, quel montant)
- Permettre la réattribution tant que le statut est En cours
- Préparer l'interface de notification SMS (stub — pas d'envoi réel en V1)
- Créer le template de la liste ST

**Non-Goals:**
- Pas d'envoi SMS réel (on logge le message, on prépare l'interface)
- Pas d'espace ST dans l'application (V2)
- Pas de gestion des étapes 4-7 (envoi BDC terrain, réalisation, signature, facturation)
- Pas de génération du BDC terrain sans prix (SPEC-004 PRD, changement séparé)

## Decisions

### D1 : Page d'attribution séparée (pas inline sur la fiche détail)
L'attribution a son propre formulaire sur une page dédiée (`/<pk>/attribuer/`). Le CDT y accède depuis un bouton "Attribuer" sur la fiche détail.
**Raison** : L'attribution implique un choix de ST + montant + confirmation. Trop complexe pour un inline. Page dédiée = plus clair.
**Alternative rejetée** : Modal JS — over-engineering, dépendance JS, plus difficile à tester.

### D2 : Fonction de service `attribuer_st()` dans services.py
Toute la logique métier (validation statut, assignation ST, calcul montant, changement statut, traçabilité) est dans une fonction `attribuer_st(bdc, sous_traitant, pourcentage, utilisateur)`. La vue appelle cette fonction.
**Raison** : Cohérent avec `changer_statut()` existant. Testable unitairement.

### D3 : Réattribution = même formulaire, logique séparée
La réattribution utilise le même `AttributionForm` mais appelle `reattribuer_st()` qui trace l'ancien ST dans l'historique. Accessible uniquement si statut = En cours.
**Raison** : PRD règle de réattribution — possible uniquement avant que le ST se soit rendu sur place. On simplifie : tant que le statut est En cours, la réattribution est possible.

### D4 : Notification SMS = stub avec logging
On crée un module `notifications.py` avec une fonction `notifier_st_attribution(bdc)` qui construit le message SMS (adresse, occupation, accès, travaux — SANS prix) et le logge. Pas d'intégration SMS réelle en V1.
**Raison** : Prépare l'interface sans dépendance externe. Facilite le branchement futur (Twilio, OVH SMS, etc.).

### D5 : Montant ST = pourcentage × montant_ht
Le CDT saisit un pourcentage. Le montant ST est calculé automatiquement : `montant_st = pourcentage_st × montant_ht / 100`. Les deux sont stockés.
**Raison** : Le CDT raisonne en pourcentage (mentionné dans le PRD). Le montant est calculé pour la facturation.

### D6 : Accès CDT uniquement via `@group_required("CDT")`
L'attribution et la réattribution sont réservées au groupe CDT. La secrétaire ne peut pas attribuer.
**Raison** : PRD §6 — attribution réservée au CDT.

## Risks / Trade-offs

- [Montant HT manquant] Si `montant_ht` est None, le calcul du montant ST échoue → On affiche un warning et on permet l'attribution sans montant calculé.
- [SMS en V1] Le stub SMS ne notifie pas réellement → Acceptable, le CDT continue de notifier manuellement en V1. Le log trace ce qui serait envoyé.
- [Réattribution après intervention] Aucun garde-fou technique pour empêcher la réattribution si le ST est déjà sur place → En V1 c'est la responsabilité du CDT. V2 pourra ajouter une confirmation du ST.
