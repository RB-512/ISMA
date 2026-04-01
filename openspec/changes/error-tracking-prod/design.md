## Context

En production (VPS OVH, Docker Compose), Django tourne avec `DEBUG=False`. Les erreurs 500 génèrent un log dans Docker stderr via le handler par défaut, mais sans configuration LOGGING explicite : pas de fichier persistant, pas de notification. Pour diagnostiquer les erreurs à distance (ex : bug attribution signalé par le CDT), il faut se connecter en SSH et lire `docker logs`, ce qui est réactif et limité.

Le SMTP est déjà configuré dans `prod.py` (EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, etc.). L'adresse `bybondecommande@gmail.com` est utilisée pour l'envoi des emails applicatifs.

## Goals / Non-Goals

**Goals:**
- Recevoir un email à `bybondecommande@gmail.com` à chaque erreur 500 avec stack trace complète
- Persister les logs dans `/data/logs/django.log` (fichier rotatif, accessible par SSH sur le VPS)
- Zéro dépendance externe ajoutée

**Non-Goals:**
- Pas d'intégration Sentry ou autre service tiers
- Pas de log des requêtes HTTP normales (200, 302...)
- Pas d'interface de visualisation des erreurs dans l'app

## Decisions

**Utiliser Django LOGGING natif avec AdminEmailHandler**
→ Intégré dans Django, utilise le SMTP déjà configuré, zéro package à installer.
Alternative écartée : Sentry (externe, dépendance, overkill pour ce volume).

**Fichier rotatif plutôt que stdout seul**
→ `RotatingFileHandler` (10 Mo, 5 backups) dans `/data/logs/django.log`. Permet de chercher dans l'historique par SSH sans dépendre de `docker logs` (qui peut être tronqué).
Nécessite un volume Docker dédié `log_data`.

**ADMINS hardcodé dans prod.py**
→ `ADMINS = [("Admin ISMA", "bybondecommande@gmail.com")]`. Valeur fixe, pas besoin de variable d'env pour ce projet mono-admin.

**Niveau ERROR uniquement pour les emails**
→ `AdminEmailHandler` déclenché sur `ERROR` et au-dessus. Évite le spam sur les warnings.

## Risks / Trade-offs

- [Emails filtrés comme spam par Gmail] → L'expéditeur est le même compte Gmail ; risque faible car envoi depuis le même domaine. À surveiller au premier test.
- [Volume logs non créé au premier déploiement] → Le répertoire `/data/logs/` doit exister avant le démarrage de Django. Géré par le volume Docker qui crée le répertoire automatiquement.
- [Rotation logs] → Si le disque VPS est plein, les anciens logs sont écrasés. Acceptable pour ce volume (application légère).

## Migration Plan

1. Modifier `prod.py` : ajouter `ADMINS` + bloc `LOGGING`
2. Modifier `docker-compose.prod.yml` : ajouter volume `log_data` + mount sur le service `web`
3. Déployer via `bash bdc-peinture/scripts/deploy.sh`
4. Vérifier : provoquer une erreur 500 volontaire en dev et vérifier la réception email + fichier log
