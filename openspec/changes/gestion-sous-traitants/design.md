## Context

Le modèle `SousTraitant` existe avec les champs `nom`, `telephone`, `email`, `actif`. La vue actuelle est un simple `ListView` en lecture seule (actifs uniquement). Le CDT gère les ST via l'admin Django, ce qui n'est pas viable en production. Le modèle est utilisé en FK par `BonDeCommande.sous_traitant` (on_delete=SET_NULL) et dans les forms d'attribution (`AttributionForm`, `ExportFacturationForm`). La sidebar a déjà un lien "Sous-traitants" pointant vers `/sous-traitants/`.

## Goals / Non-Goals

**Goals:**
- Ajouter les champs `siret`, `adresse`, `code_postal`, `ville` au modèle
- CRUD complet dans l'interface web (créer, modifier, désactiver/réactiver)
- Validation SIRET (14 chiffres, format valide)
- Vue liste avec recherche par nom/SIRET/ville
- Accès : CDT peut tout faire, Secrétaire peut voir la liste uniquement

**Non-Goals:**
- Pas de suppression physique (désactivation uniquement, le modèle a déjà `actif`)
- Pas de vérification SIRET via API externe (INSEE) — validation format seulement
- Pas de géolocalisation ou carte
- Pas de portail ST (V2)

## Decisions

### D1 : Vues fonctions avec @group_required (pas CBV)
Les vues CRUD utilisent des fonctions décorées avec `@group_required("CDT")` pour créer/modifier/désactiver. La liste reste accessible aux deux groupes (CDT et Secrétaire) via `@login_required`.
**Raison** : Cohérent avec le pattern des vues `gestion:*` (accounts). Simple, testable, pas de mixin complexe.

### D2 : Formulaire unique pour création et modification
Un seul `SousTraitantForm(ModelForm)` pour créer et modifier. Champs : nom, siret, telephone, email, adresse, code_postal, ville.
**Raison** : Les champs sont identiques. Pas besoin de deux formulaires.

### D3 : Validation SIRET côté form (clean_siret)
Le SIRET est validé dans `clean_siret()` : 14 chiffres exactement, unicité. Pas d'algorithme de Luhn (trop de SIRET invalides en pratique).
**Raison** : Validation pragmatique. L'algorithme de Luhn rejette des SIRET réels (cas connus dans le BTP).

### D4 : Désactivation au lieu de suppression
Le bouton "Désactiver" met `actif=False`. Les ST inactifs restent visibles dans la liste (avec un badge "Inactif") et peuvent être réactivés. Pas de bouton "Supprimer".
**Raison** : Un ST peut être lié à des BDC historiques. La désactivation préserve la traçabilité. Pattern identique à la gestion des utilisateurs.

### D5 : Template inline sur la page liste (pas de page séparée)
La création et la modification se font via un formulaire collapsible en haut de la liste (création) et un modal HTMX (modification), comme pour la gestion des utilisateurs.
**Raison** : UX cohérente avec la page "Gestion des accès". Pas de navigation supplémentaire.

### D6 : Recherche côté serveur avec filtre GET
La recherche filtre par `nom__icontains`, `siret__icontains`, `ville__icontains` via un paramètre GET `?q=`. Pas de JS, juste un formulaire GET.
**Raison** : Simple, rapide pour le volume attendu (< 100 ST).

## Risks / Trade-offs

- [Migration] L'ajout de champs au modèle existant nécessite une migration. Les champs `siret`, `adresse`, `code_postal`, `ville` sont `blank=True` pour ne pas casser les données existantes.
- [SIRET optionnel] Le SIRET est recommandé mais pas obligatoire — certains artisans n'ont pas de SIRET formalisé. Unicité vérifiée seulement si renseigné.
- [Affichage inactifs] Montrer les ST inactifs dans la même liste pourrait être confus → on les affiche en opacité réduite avec badge "Inactif" (même pattern que les utilisateurs).
