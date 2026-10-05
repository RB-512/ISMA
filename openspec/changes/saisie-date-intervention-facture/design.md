## Context

Les transitions EN_COURS → A_FACTURER et A_FACTURER → FACTURE sont déclenchées depuis plusieurs endroits :
- la sidebar du tableau de bord (`_detail_sidebar.html`) : POST direct vers `valider_realisation_bdc` / `valider_facturation_bdc`, ou passage par `sidebar_checklist` quand des points de contrôle existent pour la transition ;
- la fiche détail (`detail.html`) : POST classique vers les mêmes vues ;
- `changer_statut()` générique, qui autorise aussi ces deux transitions (table `TRANSITIONS`).

`date_realisation` existe déjà : elle vaut `date.today()` à la validation, est remise à null au retour en EN_COURS et sert de critère de période aux relevés/exports ST.

## Goals / Non-Goals

**Goals:**
- Aucune voie ne permet de franchir ces deux transitions sans les données requises (garde dans le service).
- Une seule UI de saisie dans la sidebar, qui inclut la checklist quand il y en a une.
- Affichage des trois informations dans la liste du tableau de bord.

**Non-Goals:**
- Renommer le champ en base ou les en-têtes des exports Excel ST (« Date réalisation »).
- Modifier les données d'une facture après passage en FACTURE (état terminal).
- Remplir rétroactivement le n° de facture des BDC déjà facturés.

## Decisions

1. **Réutiliser `date_realisation`** comme date d'intervention (choix validé avec l'utilisateur). Seul le `verbose_name` change. Alternative écartée : un champ séparé, qui aurait doublé une information quasi identique et laissé les relevés sur une date fictive.
2. **Signatures des services** : `valider_realisation(bdc, utilisateur, date_intervention)` et `valider_facturation(bdc, utilisateur, numero_facture, date_facturation)`. Les validations (présence, pas de date future, ordre des dates, unicité) lèvent `BDCIncomplet` avant toute écriture.
3. **`changer_statut` refuse** ces deux transitions avec `BDCIncomplet` en renvoyant vers l'action dédiée, ce qui ferme la voie générique. Le retour A_FACTURER → EN_COURS reste géré par `changer_statut`.
4. **Unicité du n° de facture** : `UniqueConstraint(fields=["numero_facture"], condition=~Q(numero_facture=""))`, compatible avec PostgreSQL et SQLite, plus un contrôle préalable dans le service pour un message lisible (avec le n° du BDC qui l'utilise déjà). `numero_facture` est un `CharField(blank=True, default="")`, normalisé par `strip()`.
5. **UI** : dans la sidebar, les boutons « Valider » / « Passer en facturation » ouvrent toujours le panneau `sidebar_checklist` (renommé fonctionnellement « confirmation de transition »), qui affiche les champs de saisie puis la checklist éventuelle. La fiche détail reçoit des champs inline dans ses formulaires POST. Les vues lisent les champs du POST et en cas d'erreur réaffichent le panneau avec le message et les valeurs saisies.

## Risks / Trade-offs

- [Les BDC déjà FACTURE n'ont pas de n° de facture] → la liste affiche « — » ; pas de reprise de données.
- [Les BDC déjà À facturer ont une date posée au jour du clic] → valeur conservée, l'imprécision historique est acceptée.
- [Colonnes supplémentaires dans un tableau déjà large] → dates en format court, n° et date de facture empilés dans une même cellule.
- [Course sur l'unicité entre deux saisies simultanées] → la contrainte en base tranche ; l'`IntegrityError` est convertie en `BDCIncomplet`.

## Migration Plan

Une migration ajoute `numero_facture` (default "") et `date_facturation` (null), la contrainte d'unicité conditionnelle et le nouveau `verbose_name`. Elle est sûre sur les données existantes et se défait par un retour arrière classique de la migration.
