## 1. Dépendance

- [x] 1.1 Ajouter `requests` aux dépendances du projet dans `pyproject.toml`

## 2. Backend SMS abstrait

- [x] 2.1 Créer `apps/notifications/backends.py` avec la classe de base `BaseSmsBackend` et les implémentations `LogSmsBackend` (logging) et `OvhSmsBackend` (API REST OVH)
- [x] 2.2 Ajouter `SMS_BACKEND` dans les settings (log par défaut en base, log en dev, log en test)
- [x] 2.3 Ajouter les settings OVH SMS (`OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`, `OVH_SMS_SERVICE_NAME`, `OVH_SMS_SENDER`) dans `base.py` avec `python-decouple`

## 3. Service SMS

- [x] 3.1 Réécrire `apps/notifications/sms.py` : fonctions `envoyer_sms_attribution(bdc)` et `envoyer_sms_reattribution(bdc, ancien_st_telephone)` qui composent le message (sans prix) et l'envoient via le backend configuré
- [x] 3.2 Ajouter une fonction helper `get_sms_backend()` qui charge dynamiquement le backend depuis `settings.SMS_BACKEND`

## 4. Service Email

- [x] 4.1 Réécrire `apps/notifications/email.py` : fonctions `envoyer_email_attribution(bdc)` et `envoyer_email_reattribution(bdc, ancien_st_email)` qui envoient un email avec le PDF terrain en pièce jointe via `EmailMessage`
- [x] 4.2 La fonction `envoyer_email_attribution` SHALL appeler `generer_bdc_terrain_pdf()` pour obtenir le PDF et l'attacher à l'email

## 5. Branchement dans le workflow

- [x] 5.1 Modifier `attribuer_st()` dans `services.py` pour appeler les notifications SMS et email après attribution (dans un try/except qui logge les erreurs)
- [x] 5.2 Modifier `reattribuer_st()` dans `services.py` pour appeler les notifications d'annulation (ancien ST) et d'attribution (nouveau ST)

## 6. Alertes délais

- [x] 6.1 Créer le service `apps/notifications/alertes.py` avec `get_bdc_en_retard()` et `get_bdc_delai_proche(jours=2)` retournant des querysets
- [x] 6.2 Créer la management command `apps/bdc/management/commands/check_delais.py` qui affiche un résumé des BDC en retard et proches du délai
- [x] 6.3 Modifier la vue `liste_bdc` pour passer les alertes au contexte template (CDT uniquement)
- [x] 6.4 Ajouter un encart d'alertes dans `liste.html` visible uniquement pour le CDT, affichant les BDC en retard (rouge) et proches du délai (orange)

## 7. Tests

- [x] 7.1 Tests backend SMS : `LogSmsBackend` logge correctement, `OvhSmsBackend` appelle l'API (mock requests)
- [x] 7.2 Tests service SMS : message sans prix, gestion ST sans téléphone, échec silencieux
- [x] 7.3 Tests service email : pièce jointe PDF, email sans PDF si erreur, gestion ST sans email
- [x] 7.4 Tests branchement : `attribuer_st` et `reattribuer_st` appellent les notifications, attribution OK même si notification échoue
- [x] 7.5 Tests alertes : BDC en retard identifiés, proches du délai identifiés, facturés exclus, management command, encart dashboard CDT

## 8. Validation

- [x] 8.1 Lancer `pytest` et `ruff check` — tous les tests passent, pas de lint
