## ADDED Requirements

### Requirement: Publication d'une version
Le système SHALL permettre de créer un enregistrement `Version` avec un numéro unique, une date de mise en ligne, un résumé et une liste de changements, via l'interface d'administration Django. Le numéro SHALL suivre le format CalVer `AAAA.MM.JJ`, avec un suffixe `-N` en cas de plusieurs versions publiées le même jour.

#### Scenario: Création d'une version depuis l'admin
- **WHEN** un administrateur crée un enregistrement `Version` avec le numéro `2026.08.15`
- **THEN** la version est enregistrée avec ce numéro, la date de mise en ligne, le résumé, et la liste de changements fournis

#### Scenario: Deux versions le même jour
- **WHEN** une deuxième version est publiée le même jour qu'une version existante
- **THEN** le numéro de la nouvelle version SHALL être distinct (ex. `2026.08.15-2`) pour respecter l'unicité

### Requirement: Consultation de l'historique des versions
Le système SHALL fournir une page listant toutes les versions publiées, triées par date de mise en ligne décroissante, accessible à tout utilisateur authentifié (Secrétaire ou CDT), affichant pour chaque version son numéro, sa date, et son résumé.

#### Scenario: Un utilisateur consulte l'historique
- **WHEN** un utilisateur authentifié accède à `/nouveautes/`
- **THEN** la liste des versions publiées est affichée, la plus récente en premier, avec numéro, date et résumé pour chacune

#### Scenario: Accès sans authentification refusé
- **WHEN** un utilisateur non authentifié accède à `/nouveautes/`
- **THEN** il est redirigé vers la page de connexion

### Requirement: Badge de version courante visible dans l'interface
Le système SHALL afficher, dans la sidebar de l'application, le numéro de la dernière version publiée, sous forme de lien vers la page `/nouveautes/`.

#### Scenario: Badge affiché quand une version existe
- **WHEN** au moins une `Version` a été publiée
- **THEN** la sidebar affiche le numéro de la version la plus récente, cliquable vers `/nouveautes/`

#### Scenario: Aucun badge si aucune version publiée
- **WHEN** aucune `Version` n'existe encore en base
- **THEN** la sidebar n'affiche aucun badge de version (pas d'erreur, zone simplement absente)
