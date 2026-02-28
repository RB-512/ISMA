## ADDED Requirements

### Requirement: Les filtres du dashboard appliquent le filtrage sans rechargement de page
Le formulaire de filtres sur le dashboard SHALL utiliser HTMX pour envoyer les requêtes de filtrage en arrière-plan et remplacer uniquement le contenu du tableau et des compteurs sans recharger la page entière.

#### Scenario: Filtrage instantané par statut
- **WHEN** l'utilisateur change le filtre statut sur le dashboard
- **THEN** le tableau des BDC et les compteurs sont mis à jour sans rechargement de page

#### Scenario: Filtrage avec indicateur de chargement
- **WHEN** une requête HTMX de filtrage est en cours
- **THEN** un indicateur visuel (opacity réduite ou spinner) signale le chargement

#### Scenario: URL mise à jour avec les filtres
- **WHEN** un filtre est appliqué via HTMX
- **THEN** l'URL du navigateur est mise à jour avec les paramètres de filtre (via hx-push-url) pour permettre le partage de lien et le retour arrière

### Requirement: La vue dashboard supporte le rendu partiel HTMX
La vue `liste_bdc` SHALL détecter les requêtes HTMX via le header `HX-Request` et renvoyer uniquement le fragment HTML (compteurs + tableau + pagination) sans le layout complet (base.html).

#### Scenario: Requête HTMX reçoit un fragment
- **WHEN** une requête GET avec header `HX-Request: true` est envoyée à `/bdc/`
- **THEN** la réponse contient uniquement le fragment HTML des compteurs, tableau et pagination, sans le `<html>`, `<head>`, nav, etc.

#### Scenario: Requête normale reçoit la page complète
- **WHEN** une requête GET sans header `HX-Request` est envoyée à `/bdc/`
- **THEN** la réponse contient la page complète avec le layout base.html
