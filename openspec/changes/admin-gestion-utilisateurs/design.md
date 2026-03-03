## Context

La page "Gestion des acces" (`/gestion/`) est reservee au CDT. Elle permet aujourd'hui de creer un utilisateur (username, prenom, nom, mot de passe, role), modifier son role et desactiver son compte.

Lacunes identifiees :
- **Pas d'email** a la creation alors que django-allauth utilise l'email pour le login
- **Pas de modification** des informations utilisateur (prenom, nom, email) apres creation
- **Pas de reinitialisation** du mot de passe par l'admin
- **Pas de reactivation** d'un compte desactive

Stack existante : Django 5.1, django-allauth (EmailAddress model), HTMX 2.x, Alpine.js, Tailwind CSS. Namespace URL : `gestion`.

## Goals / Non-Goals

**Goals:**
- Ajouter le champ email obligatoire a la creation, avec creation auto de `EmailAddress` allauth (verified=True, primary=True)
- Permettre la modification du profil (prenom, nom, email, role) par le CDT
- Permettre la reinitialisation du mot de passe par le CDT (generation d'un mot de passe temporaire affiche une seule fois)
- Permettre la reactivation d'un compte desactive
- Utiliser HTMX pour les actions inline (eviter les rechargements complets de page)

**Non-Goals:**
- Envoi d'email de reinitialisation (pas de SMTP garanti en dev) — le CDT communique le mot de passe temporaire a l'oral
- Self-service : l'utilisateur ne modifie pas son propre profil (hors scope)
- Gestion de permissions fines (on reste sur le systeme de groupes Secretaire/CDT)
- Ajout de nouveaux roles au-dela de Secretaire et CDT

## Decisions

### D1 : Formulaire de creation — ajout du champ email

**Choix** : Ajouter un champ `email` (EmailField, obligatoire) a `CreerUtilisateurForm`. Le `save()` cree aussi un `EmailAddress(user=user, email=email, verified=True, primary=True)`.

**Rationale** : allauth exige une EmailAddress verified+primary pour le login par email. La creation simultanee evite les etats inconsistants.

**Alternative rejetee** : Envoyer un email de verification — trop lourd pour un contexte ou le CDT cree les comptes en face-a-face.

### D2 : Formulaire de modification — nouveau form distinct

**Choix** : Creer `ModifierUtilisateurForm(ModelForm)` avec les champs `first_name`, `last_name`, `email`, `role`. Le save() met a jour le User ET synchronise l'EmailAddress allauth.

**Rationale** : Un formulaire separe de la creation (pas de champs mot de passe) simplifie la logique. Le role est un champ non-model gere dans `save()` comme pour la creation.

**Alternative rejetee** : Reutiliser CreerUtilisateurForm avec champs optionnels — complexifie inutilement la validation.

### D3 : Reinitialisation du mot de passe — generation cote serveur

**Choix** : Vue `reset_password_utilisateur(request, pk)` qui genere un mot de passe aleatoire via `User.objects.make_random_password(length=10)`, l'applique avec `user.set_password()`, et retourne le mot de passe temporaire dans la reponse HTMX (affiche une seule fois dans un toast/modal).

**Rationale** : Pas de dependance SMTP. Le CDT communique le mot de passe a l'oral. Simple et fiable.

**Alternative rejetee** : Lien de reinitialisation par email — necessite SMTP fonctionnel, over-engineering pour le contexte.

### D4 : Reactivation — simple bascule is_active

**Choix** : Vue `reactiver_utilisateur(request, pk)` qui met `is_active=True`. Meme pattern que `desactiver_utilisateur` mais inverse.

**Rationale** : Symetrique avec la desactivation existante, pas de complexite supplementaire.

### D5 : Interactions HTMX inline

**Choix** : Les actions (modifier, reset password, reactiver) utilisent des modals Alpine.js ou des panneaux inline charges via `hx-get` / `hx-post` avec `hx-target` sur la ligne utilisateur ou un conteneur modal.

**Rationale** : Coherent avec le reste de l'app (attribution_split utilise HTMX). Evite les rechargements complets.

### D6 : Synchronisation EmailAddress allauth

**Choix** : A la modification de l'email, mettre a jour `User.email` ET `EmailAddress.objects.filter(user=user, primary=True).update(email=new_email)`. Si pas d'EmailAddress existante, en creer une.

**Rationale** : allauth utilise EmailAddress pour le login. Les deux doivent rester synchronises.

## Risks / Trade-offs

- **Mot de passe temporaire affiche en clair** : Le CDT voit le mot de passe genere. Acceptable dans un contexte PME ou le CDT gere physiquement son equipe. Mitigation : affichage unique dans un toast qui disparait.
- **Pas de force-change au prochain login** : Django n'a pas de flag natif "must change password". Mitigation : hors scope MVP, pourra etre ajoute plus tard.
- **Email unique non enforce cote DB** : Le modele User de Django n'a pas `unique=True` sur email par defaut. Mitigation : validation dans le formulaire (clean_email) + contrainte allauth.
