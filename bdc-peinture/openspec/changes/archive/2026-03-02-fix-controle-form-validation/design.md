## Context

La vue `controle_bdc` gère le POST en deux blocs distincts : (1) sauvegarde du formulaire et de la checklist, (2) changement de statut optionnel. Deux bugs structurels coexistent :

1. **Transition non gatée** : `changer_statut()` est appelé même si `form.is_valid()` retourne `False`. Les erreurs de `clean()` (ex. rdv_date manquante pour OCCUPE) sont donc silencieusement ignorées et la transition se produit quand même — ou échoue à la couche service avec un message d'erreur générique.

2. **Formulaire lié écrasé** : à la fin du bloc POST, le formulaire lié (qui porte les erreurs de validation) est remplacé par `BDCEditionForm(instance=bdc)` (formulaire vierge). Les erreurs de champ ne sont donc jamais rendues dans le template.

La couche service (`changer_statut`) dispose de sa propre validation (`BDCIncomplet`) qui produit un toast visible — ce qui a masqué le bug jusqu'ici. Mais la validation de formulaire (`clean()`) et les erreurs de champs doivent aussi remonter à l'utilisateur.

## Goals / Non-Goals

**Goals:**
- Bloquer la transition si le formulaire est invalide
- Conserver le formulaire lié avec ses erreurs pour le re-rendu
- Afficher les erreurs de champ dans le template `controle.html`

**Non-Goals:**
- Modifier la couche service (`services.py`) ou les modèles
- Refactorer la logique de checklist
- Changer la structure générale de la vue

## Decisions

### Décision 1 : Gater la transition sur `form.is_valid()`

**Choix** : N'appeler `changer_statut()` que si `form.is_valid()` est True ET que `nouveau_statut` est non-vide.

**Rationale** : La validation form-level (`clean()`) doit être un prérequis à la transition service-level. Sans ce gate, un utilisateur peut bypasser la validation des champs obligatoires (rdv_date, type_acces) grâce aux messages d'erreur de la couche service qui ne couvrent pas tous les cas.

**Alternative rejetée** : Supprimer `clean()` et déléguer entièrement à la couche service. Rejetée car la couche service n't pas accès au contexte HTTP et ne peut pas produire d'erreurs de champ (field errors) affichables dans le template.

### Décision 2 : Préserver le formulaire lié après échec de validation

**Choix** : Initialiser `form_edition` une seule fois (formulaire lié au POST, ou formulaire vierge sur GET), sans écraser par un formulaire vierge en fin de bloc POST.

**Rationale** : Un formulaire lié (`BDCEditionForm(request.POST, instance=bdc)`) conserve les données saisies et les erreurs de validation. Le remplacer par un formulaire vierge (`BDCEditionForm(instance=bdc)`) efface ces erreurs avant qu'elles soient rendues dans le template.

### Décision 3 : Afficher les erreurs dans le template

**Choix** : Ajouter `{{ form_edition.field.errors }}` à côté de chaque champ dans `controle.html`.

**Rationale** : Les erreurs de champ sont stockées dans `form.errors` mais ne s'affichent que si le template les rend explicitement. Le template actuel ne les rend pas du tout.

## Risks / Trade-offs

- **Checklist sauvée même si formulaire invalide** → acceptable, la checklist est indépendante du formulaire de saisie et peut être sauvée partiellement.
- **Erreurs de formulaire + erreurs service simultanées** → si `form.is_valid()` passe mais que la couche service lève `BDCIncomplet`, le comportement actuel (toast d'erreur + refresh depuis DB) est conservé.
