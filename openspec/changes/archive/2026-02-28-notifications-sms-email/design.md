## Context

L'app `notifications` existe déjà avec des stubs (`sms.py`, `email.py`) qui lèvent `NotImplementedError`. Le modèle `SousTraitant` a les champs `telephone` et `email`. Les settings Django sont déjà configurés : `EMAIL_BACKEND` console en dev, SMTP en prod, `locmem` en test. Les fonctions `attribuer_st` et `reattribuer_st` dans `services.py` ne font actuellement aucun appel de notification.

## Goals / Non-Goals

**Goals:**
- Envoyer un SMS au ST lors d'attribution/réattribution (adresse, travaux, accès — jamais de prix)
- Envoyer un email avec le BDC terrain PDF en pièce jointe au ST
- Alerter le CDT sur les BDC dont le délai d'exécution est dépassé ou proche (J-2)
- Architecture de backend SMS/Email interchangeable (logging en dev, envoi réel en prod)

**Non-Goals:**
- Espace sous-traitant (V2)
- Notification push / temps réel
- Envoi SMS via Twilio (on utilise OVH SMS, plus simple et sans dépendance lourde)

## Decisions

### D1 — Backend SMS abstrait via settings

Plutôt que d'appeler directement l'API OVH, on crée un système de backends SMS similaire au `EMAIL_BACKEND` de Django.

- `SMS_BACKEND = "apps.notifications.backends.LogSmsBackend"` (dev/test) — log le SMS
- `SMS_BACKEND = "apps.notifications.backends.OvhSmsBackend"` (prod) — appel API REST OVH

**Pourquoi** : permet de tester sans credentials, de basculer facilement, et de rajouter d'autres providers (Twilio) sans toucher au code métier.

### D2 — OVH SMS via API REST (requests)

OVH expose une API REST simple (`POST /sms/{serviceName}/jobs`). On utilise `requests` (déjà couramment disponible) plutôt qu'un SDK OVH dédié.

**Pourquoi** : un seul endpoint à appeler, pas besoin d'un SDK complet. `requests` est léger et standard.

### D3 — Email via Django send_mail avec pièce jointe

On utilise `django.core.mail.EmailMessage` pour envoyer l'email avec le PDF terrain en pièce jointe. Le PDF est généré à la volée via `generer_bdc_terrain_pdf()` existant.

**Pourquoi** : Django gère déjà les backends email (console/SMTP/locmem). Pas besoin de dépendance externe.

### D4 — Notifications appelées dans services.py (pas dans les vues)

Les appels SMS/email sont faits dans `attribuer_st()` et `reattribuer_st()` après la logique métier. Les erreurs de notification sont loggées mais ne bloquent pas l'attribution.

**Pourquoi** : cohérent avec le pattern service layer du projet. L'attribution ne doit pas échouer à cause d'un SMS raté.

### D5 — Alertes délais via management command

Une management command `check_delais` identifie les BDC dont le `delai_execution` est dépassé ou à J-2. Elle peut être lancée manuellement ou via cron.

**Pourquoi** : plus simple qu'un système de tâches asynchrones (Celery) pour le MVP. Le CDT peut lancer la commande ou la voir dans le dashboard.

### D6 — Widget alertes dans le dashboard

Un encart "Alertes" en haut du dashboard affiche les BDC en retard ou proches du délai, visible uniquement pour le CDT.

**Pourquoi** : le CDT voit immédiatement les urgences sans action supplémentaire.

## Risks / Trade-offs

- **[SMS échoue silencieusement]** → Les erreurs sont loggées avec `logger.warning`. Le BDC reste attribué. On pourra ajouter un champ `notification_envoyee` plus tard si besoin de retry.
- **[Credentials OVH absents en dev]** → Le `LogSmsBackend` par défaut évite toute erreur. Aucun appel réseau en dev/test.
- **[PDF terrain non généré]** → Si la génération PDF échoue, l'email est envoyé sans pièce jointe avec un message indiquant de récupérer le PDF dans l'application.
- **[Alertes délais non temps réel]** → Acceptable pour le MVP. Le dashboard affiche l'état au moment du chargement de la page.
