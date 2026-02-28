## ADDED Requirements

### Requirement: Le dashboard affiche la liste paginée des BDC
Le système SHALL afficher tous les `BonDeCommande` dans un tableau paginé (25 par page) trié par date de création décroissante. Chaque ligne SHALL afficher : numéro BDC, bailleur, adresse, ville, statut (badge coloré), date de création. La ligne SHALL être cliquable vers la fiche détail.

#### Scenario: Affichage de la liste avec BDC existants
- **WHEN** un utilisateur authentifié accède à `/bdc/`
- **THEN** le système affiche un tableau avec les BDC existants, paginés par 25, triés du plus récent au plus ancien

#### Scenario: Aucun BDC en base
- **WHEN** un utilisateur authentifié accède à `/bdc/` et il n'y a aucun BDC
- **THEN** le système affiche un message "Aucun bon de commande trouvé" avec un lien vers la page d'upload

#### Scenario: Navigation entre pages
- **WHEN** il y a plus de 25 BDC et l'utilisateur clique sur la page 2
- **THEN** le système affiche les BDC 26 à 50 avec les contrôles de pagination (précédent/suivant/numéros de page)

### Requirement: Le dashboard affiche des compteurs par statut
Le système SHALL afficher en haut du dashboard des cards avec le nombre de BDC pour chaque statut (A_TRAITER, A_FAIRE, EN_COURS, A_FACTURER, FACTURE) et le total.

#### Scenario: Compteurs affichés avec les bons totaux
- **WHEN** la base contient 3 BDC A_TRAITER, 5 A_FAIRE, 2 EN_COURS
- **THEN** le dashboard affiche les compteurs correspondants et un total de 10

#### Scenario: Compteurs à zéro
- **WHEN** aucun BDC n'existe pour un statut donné
- **THEN** le compteur de ce statut affiche 0

### Requirement: Les BDC sont filtrables par statut
Le système SHALL permettre de filtrer la liste par statut via un champ select.

#### Scenario: Filtre par statut unique
- **WHEN** l'utilisateur sélectionne le filtre statut = "A_FAIRE"
- **THEN** seuls les BDC en statut A_FAIRE sont affichés et la pagination est recalculée

#### Scenario: Aucun filtre sélectionné
- **WHEN** aucun filtre statut n'est sélectionné
- **THEN** tous les BDC sont affichés quel que soit leur statut

### Requirement: Les BDC sont filtrables par bailleur
Le système SHALL permettre de filtrer la liste par bailleur via un champ select.

#### Scenario: Filtre par bailleur
- **WHEN** l'utilisateur sélectionne le filtre bailleur = "GDH"
- **THEN** seuls les BDC du bailleur GDH sont affichés

### Requirement: Les BDC sont filtrables par ville
Le système SHALL permettre de filtrer par ville via un champ texte (correspondance partielle insensible à la casse).

#### Scenario: Filtre par ville partielle
- **WHEN** l'utilisateur saisit "Marseille" dans le filtre ville
- **THEN** les BDC dont la ville contient "Marseille" (insensible à la casse) sont affichés

### Requirement: Les BDC sont filtrables par plage de dates
Le système SHALL permettre de filtrer par date de création avec un champ "du" et un champ "au".

#### Scenario: Filtre par plage de dates
- **WHEN** l'utilisateur saisit du = "2026-01-01" et au = "2026-01-31"
- **THEN** seuls les BDC créés entre le 1er et le 31 janvier 2026 sont affichés

#### Scenario: Filtre avec uniquement une date de début
- **WHEN** l'utilisateur saisit du = "2026-02-01" sans date de fin
- **THEN** les BDC créés à partir du 1er février 2026 sont affichés

### Requirement: Les BDC sont recherchables par texte libre
Le système SHALL fournir un champ de recherche textuelle qui filtre sur le numéro BDC, l'adresse et le nom de l'occupant (correspondance partielle insensible à la casse).

#### Scenario: Recherche par numéro BDC
- **WHEN** l'utilisateur saisit "2026-001" dans le champ recherche
- **THEN** les BDC dont le numéro contient "2026-001" sont affichés

#### Scenario: Recherche par adresse
- **WHEN** l'utilisateur saisit "Rue de la Paix" dans le champ recherche
- **THEN** les BDC dont l'adresse contient "Rue de la Paix" sont affichés

#### Scenario: Recherche sans résultat
- **WHEN** l'utilisateur saisit une valeur qui ne correspond à aucun BDC
- **THEN** le message "Aucun bon de commande trouvé" est affiché

### Requirement: Les filtres et la recherche sont combinables
Le système SHALL appliquer tous les filtres et la recherche simultanément (intersection / AND).

#### Scenario: Combinaison filtre statut + recherche
- **WHEN** l'utilisateur filtre par statut = "A_FAIRE" et saisit "Marseille" en recherche
- **THEN** seuls les BDC en statut A_FAIRE dont le numéro, l'adresse ou l'occupant contient "Marseille" sont affichés

### Requirement: L'accès au dashboard nécessite une authentification
Le système SHALL restreindre l'accès au dashboard aux utilisateurs authentifiés (Secrétaire et CDT). Un lien "Export facturation" SHALL être affiché pour les utilisateurs CDT, pointant vers `/bdc/export/`.

#### Scenario: Utilisateur non authentifié
- **WHEN** un utilisateur non authentifié accède à `/bdc/`
- **THEN** il est redirigé vers la page de login

#### Scenario: Utilisateur authentifié (Secrétaire ou CDT)
- **WHEN** un utilisateur authentifié accède à `/bdc/`
- **THEN** le dashboard est affiché normalement

#### Scenario: Lien Export facturation pour CDT
- **WHEN** un utilisateur CDT accède à `/bdc/`
- **THEN** un lien "Export facturation" est affiché dans la barre d'actions

#### Scenario: Lien Export facturation masqué pour secrétaire
- **WHEN** une secrétaire accède à `/bdc/`
- **THEN** le lien "Export facturation" n'est pas affiché
