## MODIFIED Requirements

### Requirement: Le dashboard affiche la liste paginée des BDC
Le système SHALL afficher tous les `BonDeCommande` dans un tableau paginé (25 par page) trié par date de création décroissante. Chaque ligne SHALL afficher : numéro BDC (font mono), bailleur, adresse, ville, statut (badge coloré design system), date de création. La ligne SHALL être cliquable vers la fiche détail avec un effet hover. Le tableau SHALL utiliser le style du design system Isma (fond surface-card, bordures subtiles, alternance de lignes en dark mode).

#### Scenario: Affichage de la liste avec BDC existants
- **WHEN** un utilisateur authentifié accède à `/bdc/`
- **THEN** le système affiche un tableau stylisé avec les BDC existants, paginés par 25, triés du plus récent au plus ancien

#### Scenario: Aucun BDC en base
- **WHEN** un utilisateur authentifié accède à `/bdc/` et il n'y a aucun BDC
- **THEN** le système affiche un état vide stylisé avec une illustration et un lien vers la page d'upload

#### Scenario: Navigation entre pages
- **WHEN** il y a plus de 25 BDC et l'utilisateur clique sur la page 2
- **THEN** le système affiche les BDC 26 à 50 avec les contrôles de pagination stylisés

### Requirement: Le dashboard affiche des compteurs par statut
Le système SHALL afficher en haut du dashboard des cards avec le nombre de BDC pour chaque statut (A_TRAITER, A_FAIRE, EN_COURS, A_FACTURER, FACTURE) et le total. Chaque card SHALL utiliser la couleur du statut correspondant et une icône. Les compteurs SHALL être inclus dans la zone HTMX-swappable.

#### Scenario: Compteurs affichés avec les bons totaux
- **WHEN** la base contient 3 BDC A_TRAITER, 5 A_FAIRE, 2 EN_COURS
- **THEN** le dashboard affiche les compteurs correspondants avec les couleurs du design system et un total de 10

#### Scenario: Compteurs à zéro
- **WHEN** aucun BDC n'existe pour un statut donné
- **THEN** le compteur de ce statut affiche 0 avec une opacité réduite

### Requirement: L'accès au dashboard nécessite une authentification
Le système SHALL restreindre l'accès au dashboard aux utilisateurs authentifiés (Secrétaire et CDT). Les liens CDT-only (Export facturation, Recoupement) SHALL être affichés dans la sidebar, pas dans le dashboard.

#### Scenario: Utilisateur non authentifié
- **WHEN** un utilisateur non authentifié accède à `/bdc/`
- **THEN** il est redirigé vers la page de login

#### Scenario: Utilisateur authentifié (Secrétaire ou CDT)
- **WHEN** un utilisateur authentifié accède à `/bdc/`
- **THEN** le dashboard est affiché normalement
