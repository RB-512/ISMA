## 1. Configuration SMTP Gmail

- [ ] 1.1 Generer un App Password Gmail pour le compte bybondecommade@gmail.com (activer 2FA si necessaire)
- [ ] 1.2 Configurer EMAIL_HOST_PASSWORD dans .env sur le VPS

## 2. Feedback utilisateur

- [ ] 2.1 Modifier `_notifier_st_si_possible` pour retourner un booleen (email envoye ou non)
- [ ] 2.2 Modifier `attribuer_bdc` view pour afficher messages.warning si email echoue
- [ ] 2.3 Modifier `reattribuer_bdc` view pour afficher messages.warning si email echoue

## 3. Nettoyage

- [ ] 3.1 Supprimer le stub obsolete `apps/bdc/notifications.py` (notifier_st_attribution)
- [ ] 3.2 Supprimer l'import de notifier_st_attribution dans views.py

## 4. Verification

- [ ] 4.1 Deployer sur le VPS et tester l'envoi email via une attribution reelle
- [ ] 4.2 Verifier le message flash warning quand le ST n'a pas d'email
