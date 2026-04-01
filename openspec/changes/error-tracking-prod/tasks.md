## 1. Configuration Django (prod.py)

- [x] 1.1 Ajouter `ADMINS = [("Admin ISMA", "bybondecommande@gmail.com")]` dans `prod.py`
- [x] 1.2 Ajouter le bloc `LOGGING` dans `prod.py` avec `RotatingFileHandler` sur `/data/logs/django.log` (10 Mo, 5 backups) et `AdminEmailHandler` sur le logger `django`

## 2. Infrastructure Docker

- [x] 2.1 Ajouter le volume `log_data` dans la section `volumes:` de `docker-compose.prod.yml`
- [x] 2.2 Monter le volume `log_data:/data/logs` dans le service `web` de `docker-compose.prod.yml`

## 3. Vérification

- [x] 3.1 Lancer les tests : `uv run pytest` (aucun test ne doit échouer)
- [ ] 3.2 Déployer sur le VPS : `bash bdc-peinture/scripts/deploy.sh`
- [ ] 3.3 Vérifier que `/data/logs/django.log` est créé dans le conteneur : `docker exec bdc-peinture-web-1 ls -la /data/logs/`
- [ ] 3.4 Vérifier la réception d'un email de test (provoquer une erreur 500 temporaire ou utiliser `manage.py shell` pour déclencher un log ERROR)
