# Évolutions Contrôle, Attribution & Dashboard — Design

**Date** : 2026-03-01
**Statut** : Approuvé

---

## Contexte

Trois évolutions demandées pour améliorer l'ergonomie du workflow BDC :
1. Phase Contrôle — champs obligatoires, nettoyage, renvoi CDT
2. Sidebar read-only après contrôle + message de confirmation
3. Dashboard — zone de recherche réductible

---

## Évolution 1 : Phase Contrôle

### 1a. Champs obligatoires marqués `*`

Tous les champs du formulaire de contrôle (`BDCEditionForm`) deviennent obligatoires **sauf** "Commentaires" (ex "Notes libres").

- Backend : `required=True` sur `occupation`, `type_acces` (si VACANT), `acces_complement` (si VACANT), `rdv_date` (si OCCUPE). `notes` reste `required=False`.
- Frontend : astérisque rouge `*` à côté du label de chaque champ obligatoire.
- La validation conditionnelle (type_acces obligatoire seulement si VACANT, rdv_date seulement si OCCUPE) est gérée dans la méthode `clean()` du formulaire.

### 1b. Renommer "Notes libres" → "Commentaires"

- Changer le `label` du champ `notes` dans `BDCEditionForm` : `"Commentaires"`.
- Templates `controle.html` et `_detail_sidebar.html` utilisent `{{ form.notes.label }}` donc se mettent à jour automatiquement.

### 1c. Supprimer "Modalité d'accès"

- Retirer `modalite_acces` de la liste `fields` de `BDCEditionForm`.
- Retirer les sections `modalite_acces` des templates `controle.html` et `_detail_sidebar.html`.
- Le champ reste dans le modèle `BonDeCommande` (pas de migration destructive).
- Retirer l'affichage dans `detail.html` également.

### 1d. Renvoi CDT → Secrétaire

Nouveau workflow : le CDT peut renvoyer un BDC "À attribuer" (`A_FAIRE`) vers "À contrôler" (`A_TRAITER`).

- **Sidebar** : pour les BDC `A_FAIRE`, ajouter un bouton "Renvoyer au contrôle" sous le bouton "Attribuer".
- **Clic** : ouvre un champ texte (commentaire obligatoire) + bouton "Confirmer le renvoi".
- **Backend** : nouvelle vue `renvoyer_controle(request, pk)` :
  - Vérifie `statut == A_FAIRE`, utilisateur est CDT.
  - Passe le statut à `A_TRAITER`.
  - Enregistre le commentaire dans l'historique (`HistoriqueAction` avec action `RENVOI` et details contenant le commentaire).
  - Ajouter `RENVOI` aux choix d'action de `HistoriqueAction`.
  - Ajouter la transition `A_FAIRE → A_TRAITER` dans `TRANSITIONS_VALIDES`.
- **Historique** : le commentaire du CDT est visible dans l'historique du BDC.
- **Alerte secrétaire** : quand la secrétaire ouvre un BDC renvoyé (statut A_TRAITER avec un historique RENVOI récent), afficher un bandeau d'alerte avec le commentaire du CDT.

---

## Évolution 2 : Sidebar read-only + toast confirmation

### 2a. Sidebar read-only après contrôle

Pour les BDC qui ne sont plus en `A_TRAITER` :
- La sidebar affiche les champs remplis (occupation, type d'accès, complément, RDV) en **texte simple** (pas de dropdown/input).
- Le formulaire d'édition (`form_edition`) n'est plus injecté dans le contexte pour ces statuts.
- Applicable à **tous les utilisateurs** (secrétaire incluse).

Sections affichées en lecture seule :
- Occupation : `{{ bdc.get_occupation_display }}`
- Type d'accès : `{{ bdc.get_type_acces_display }}` (si renseigné)
- Complément accès : `{{ bdc.acces_complement }}` (si renseigné)
- RDV : `{{ bdc.rdv_date|date:"d/m/Y H:i" }}` (si renseigné)
- Commentaires : `{{ bdc.notes }}` (si renseigné)

### 2b. Toast de confirmation après validation contrôle

Quand la secrétaire valide un BDC via "Valider → À attribuer" sur la page contrôle :
- `messages.success(request, "BDC n°XXX validé — statut : À attribuer.")`
- Redirection vers le dashboard (déjà en place).
- Le système de toasts existant affiche le message.

---

## Évolution 3 : Dashboard — zone de recherche réductible

### Layout

- **État replié (défaut)** : champ de recherche texte + bouton "Filtres" avec icône entonnoir.
- **État déplié** : champ recherche + bouton "Filtres" en haut, puis :
  - Ligne 1 : Bailleur (dropdown) + Ville (texte)
  - Ligne 2 : Du (date) + Au (date) + Filtrer (bouton) + Réinitialiser (lien)
- **Animation** : Alpine.js `x-show` + `x-transition` pour l'ouverture/fermeture.
- **Badge filtres actifs** : quand des filtres sont appliqués et la zone est repliée, afficher "Filtres (N)" avec N = nombre de filtres actifs.

### Implémentation

- Variable Alpine `filtersOpen` (défaut `false`).
- Compter les filtres actifs côté template : bailleur sélectionné + ville renseignée + dates renseignées.
- Le comportement HTMX des filtres ne change pas.
- Les onglets par statut restent au-dessus, inchangés.

---

## Fichiers impactés

| Fichier | Évolutions |
|---|---|
| `apps/bdc/forms.py` | 1a, 1b, 1c |
| `apps/bdc/views.py` | 1d, 2a, 2b |
| `apps/bdc/services.py` | 1d (transition A_FAIRE→A_TRAITER) |
| `apps/bdc/models.py` | 1d (action RENVOI dans HistoriqueAction) |
| `apps/bdc/urls.py` | 1d (nouvelle URL renvoi) |
| `templates/bdc/controle.html` | 1a, 1b, 1c |
| `templates/bdc/_detail_sidebar.html` | 1a, 1c, 1d, 2a |
| `templates/bdc/detail.html` | 1c |
| `templates/bdc/_liste_partial.html` | 3 |
| `tests/` | Tous |
