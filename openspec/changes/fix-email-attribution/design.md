## Context

Le code d'envoi d'email est complet et fonctionnel :
- `apps/notifications/email.py` : `envoyer_email_attribution()` construit et envoie l'email avec PDF masqué en PJ
- `apps/bdc/services.py` : `_notifier_st_si_possible()` appelle l'envoi, erreurs non-bloquantes (try/except)
- `config/settings/prod.py` : backend SMTP Gmail configuré

Le problème : `EMAIL_HOST_PASSWORD` est vide dans `.env` sur le VPS. Gmail rejette la connexion SMTP. L'erreur est avalée silencieusement par le try/except, donc l'utilisateur ne voit rien.

## Goals / Non-Goals

**Goals:**
- Rendre l'envoi d'email fonctionnel en prod (configurer le mot de passe SMTP)
- Informer l'utilisateur si l'email échoue (message flash warning)
- Vérifier que le flux complet fonctionne (attribution → email reçu par le ST)

**Non-Goals:**
- Changer de provider email (rester sur Gmail SMTP)
- Implémenter une file d'attente d'emails (Celery, etc.)
- Modifier le contenu des emails

## Decisions

### 1. App Password Gmail

Gmail n'accepte plus les mots de passe classiques en SMTP. Il faut un "mot de passe d'application" généré depuis les paramètres de sécurité du compte Google (`bybondecommade@gmail.com`). La vérification en 2 étapes doit être activée au préalable.

### 2. Feedback utilisateur sur échec email

Actuellement `_notifier_st_si_possible` avale l'exception silencieusement. On modifie pour retourner un booléen et la vue `attribuer_bdc` affiche un `messages.warning` si l'email n'a pas pu être envoyé — sans bloquer l'attribution.

Alternative rejetée : lever une exception → bloquerait l'attribution pour un problème secondaire.

### 3. Nettoyage du stub `notifications.py`

`apps/bdc/notifications.py` contient un stub SMS obsolète (`notifier_st_attribution`) qui n'est plus utilisé par la vue. La vue appelle directement `services._notifier_st_si_possible`. Le stub peut être supprimé pour éviter la confusion.

## Risks / Trade-offs

- [Gmail rate limit 500 emails/jour] → Largement suffisant pour le volume actuel. À surveiller si le volume augmente.
- [App Password en clair dans .env] → Acceptable pour un VPS dédié. Le `.env` n'est pas versionné.
- [Email échoue silencieusement si logs pas consultés] → Mitigé par le message flash warning visible à l'utilisateur.
