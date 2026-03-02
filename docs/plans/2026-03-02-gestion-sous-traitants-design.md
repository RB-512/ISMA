# Design — Gestion des sous-traitants (CRUD)

**Date :** 2026-03-02
**Statut :** Validé

## Contexte

Le modèle `SousTraitant` existe mais l'interface ne propose qu'une liste en lecture seule. Les ST ne peuvent être créés/modifiés que via l'admin Django. Cette feature ajoute un CRUD complet dans l'interface utilisateur.

## Modèle

Ajout de 2 champs au modèle `SousTraitant` existant :

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `siret` | CharField(14) | Non | Numéro SIRET (14 chiffres) |
| `adresse` | TextField | Non | Adresse postale du ST |

Les 4 champs existants (nom, telephone, email, actif) ne changent pas.

## Permissions

- CDT et Secrétaire peuvent créer, modifier et désactiver un ST
- La vue liste reste accessible aux deux rôles (`@login_required`)
- Pas de suppression physique : on désactive (`actif=False`)

## Pages

### 1. Liste enrichie (`sous-traitants/`)

- Bouton "Nouveau sous-traitant" en haut
- Colonne "Actions" avec un lien "Modifier" par ligne
- Toggle "Afficher les inactifs" (par défaut : masqués)
- Les ST inactifs apparaissent grisés quand le toggle est activé

### 2. Création (`sous-traitants/nouveau/`)

- Formulaire : nom*, téléphone*, email, siret, adresse, actif (coché par défaut)
- Validation : SIRET = 14 chiffres si renseigné
- Redirect vers la liste après création avec message de succès

### 3. Modification (`sous-traitants/<pk>/modifier/`)

- Même formulaire pré-rempli
- Le toggle actif/inactif sert de "désactivation"
- Redirect vers la liste après modification

## Formulaire

Un seul `ModelForm` pour création et modification :
- Champs : nom, telephone, email, siret, adresse, actif
- Validation custom : SIRET = exactement 14 chiffres (si renseigné)
- Widget Tailwind cohérent avec les formulaires BDC existants

## URLs

```
sous-traitants/                → liste (existante, enrichie)
sous-traitants/nouveau/        → création
sous-traitants/<pk>/modifier/  → modification
```

## Tests

- Test création ST (champs valides)
- Test validation SIRET (14 chiffres, rejet si invalide)
- Test modification ST
- Test désactivation (actif=False)
- Test permissions (login requis)
- Test toggle inactifs sur la liste
