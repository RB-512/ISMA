### Requirement: Le système identifie les BDC dont le délai d'exécution est dépassé ou proche
Le système SHALL fournir une management command `check_delais` qui identifie les BDC en statut EN_COURS ou A_FAIRE dont le `delai_execution` est dépassé ou dans les 2 jours à venir.

#### Scenario: BDC en retard identifié
- **WHEN** un BDC en statut EN_COURS a un `delai_execution` antérieur à aujourd'hui
- **THEN** il est identifié comme "en retard"

#### Scenario: BDC proche du délai identifié
- **WHEN** un BDC en statut EN_COURS a un `delai_execution` dans les 2 jours à venir
- **THEN** il est identifié comme "délai proche"

#### Scenario: BDC facturés exclus
- **WHEN** un BDC est en statut A_FACTURER ou FACTURE avec un délai dépassé
- **THEN** il n'apparaît pas dans les alertes

### Requirement: Le dashboard affiche les alertes de délai pour le CDT
Le système SHALL afficher un encart d'alertes en haut du dashboard montrant les BDC en retard et ceux proches du délai, visible uniquement pour les utilisateurs CDT.

#### Scenario: Encart alertes visible pour CDT
- **WHEN** un CDT accède au dashboard et des BDC sont en retard
- **THEN** un encart rouge/orange affiche le nombre de BDC en retard et proches du délai avec des liens vers les fiches

#### Scenario: Encart alertes masqué pour secrétaire
- **WHEN** une secrétaire accède au dashboard
- **THEN** l'encart d'alertes n'est pas affiché

#### Scenario: Pas d'encart si aucune alerte
- **WHEN** aucun BDC n'est en retard ni proche du délai
- **THEN** l'encart d'alertes n'est pas affiché

### Requirement: La management command affiche un résumé des alertes
La command `check_delais` SHALL afficher un résumé des BDC en retard et proches du délai dans la console.

#### Scenario: Résumé console
- **WHEN** la commande `python manage.py check_delais` est exécutée
- **THEN** elle affiche le nombre de BDC en retard, le nombre proches du délai, et la liste des numéros BDC concernés
