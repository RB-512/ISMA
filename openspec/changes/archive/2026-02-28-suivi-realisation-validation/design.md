## Context

Le workflow BDC couvre actuellement les étapes 1 à 4 (réception → envoi terrain). Les transitions EN_COURS → A_FACTURER et A_FACTURER → FACTURE existent déjà dans le dictionnaire TRANSITIONS de services.py, mais aucune vue CDT ne permet de les déclencher. Les ActionChoices VALIDATION et FACTURATION sont déjà définis dans les modèles.

Le CDT a besoin de :
1. Valider la réalisation d'un BDC (EN_COURS → A_FACTURER) après retour du ST
2. Passer un BDC en facturation (A_FACTURER → FACTURE) après recoupement
3. Un écran de recoupement par ST pour comparer les BDC attribués vs réalisés

## Goals / Non-Goals

**Goals:**
- Permettre au CDT de valider la réalisation et passer en facturation depuis la fiche détail
- Tracer chaque action (VALIDATION, FACTURATION) dans l'historique
- Offrir un écran de recoupement par ST : liste des BDC d'un ST groupés par statut
- Stocker la date de réalisation déclarée

**Non-Goals:**
- Pas de module facturation complet (hors MVP, SPEC-006)
- Pas d'interface ST pour déclarer la réalisation (V2)
- Pas de gestion des signatures numériques (V4)
- Pas d'export PDF/Excel du recoupement (SPEC-006)

## Decisions

### D1 — Fonctions de service dédiées plutôt que `changer_statut` générique

Créer `valider_realisation(bdc, utilisateur)` et `valider_facturation(bdc, utilisateur)` dans services.py plutôt que réutiliser `changer_statut()` directement.

**Pourquoi :** Ces transitions ont une sémantique métier propre (date de réalisation, action historique spécifique). Des fonctions dédiées permettent d'ajouter la logique métier sans surcharger `changer_statut`.

**Alternative rejetée :** Appeler `changer_statut()` depuis les vues — cela ne trace pas VALIDATION/FACTURATION spécifiquement et ne gère pas `date_realisation`.

### D2 — Champ `date_realisation` sur BonDeCommande

Ajouter `date_realisation = DateField(null=True, blank=True)` sur le modèle. Rempli automatiquement à `date.today()` lors de la validation, modifiable par le CDT.

**Pourquoi :** Le PRD indique que le CDT fait le recoupement en fin de semaine. Savoir quand un BDC a été déclaré réalisé est essentiel pour ce rapprochement.

### D3 — Vue recoupement : filtrage par ST via la liste BDC existante

Créer une vue dédiée `recoupement_st` qui prend un ST en paramètre et affiche ses BDC groupés par statut (en cours, à facturer, facturé). Le CDT peut aussi voir un résumé par ST (nombre de BDC par statut).

**Pourquoi :** Le PRD décrit un besoin de recoupement hebdomadaire où le CDT compare ses données par ST. Une vue dédiée est plus claire qu'un filtre supplémentaire dans le dashboard existant.

**Alternative rejetée :** Ajouter un filtre ST dans la liste BDC existante — ne permet pas la vue résumé par ST.

### D4 — Boutons CDT sur la fiche détail

Ajouter les boutons directement sur la fiche détail dans l'en-tête, à côté des boutons existants (Réattribuer, BDC terrain) :
- "Valider réalisation" (vert) : visible pour CDT quand statut = EN_COURS
- "Passer en facturation" (bleu) : visible pour CDT quand statut = A_FACTURER

**Pourquoi :** Cohérent avec le pattern existant (boutons Attribuer/Réattribuer sont déjà dans l'en-tête).

### D5 — Retour en arrière possible : A_FACTURER → EN_COURS

La transition A_FACTURER → EN_COURS existe déjà dans TRANSITIONS. Le bouton sera visible pour le CDT pour corriger une validation prématurée.

## Risks / Trade-offs

- **[Déclaration de réalisation unilatérale]** → Le CDT déclare la réalisation sans confirmation du ST. En V2, l'espace ST permettra une déclaration bilatérale. Pour le MVP, c'est le comportement attendu (le CDT recueille l'info par téléphone/SMS).
- **[Pas de retour depuis FACTURE]** → L'état FACTURE est terminal. Si erreur, pas de rollback possible. Mitigation : le CDT doit valider consciemment. Message de confirmation côté UI avant passage en FACTURE.
