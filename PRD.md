# PRD — BDC Peinture — MVP 1.0

**Version :** MVP 1.0
**Date :** 27 février 2026
**Statut :** En cours de rédaction
**Destinataire :** Claude Code (développement)

---

## 1. Vision du produit

### 1.1 Résumé exécutif

BDC Peinture est une application web de gestion des bons de commande destinée à une entreprise de peinture (~30 employés) travaillant avec des bailleurs sociaux (GDH et ERILIA). Elle remplace le système actuel basé sur des pochettes papier, des feuilles manuscrites et des SMS par un workflow numérique complet, de la réception du BDC jusqu'à la facturation.

### 1.2 Problèmes à résoudre

- Doubles saisies et risques d'erreur sur le suivi papier (pochettes, feuilles du CDT)
- Pas de vision en temps réel sur l'état des BDC (qui fait quoi, où en est-on)
- Difficulté à recouper les BDC attribués vs réalisés en fin de semaine (risque d'erreur sur la facturation)
- Informations dispersées entre IKOS, emails, feuilles papier et SMS
- Pas de traçabilité : impossible de savoir qui a fait quoi et quand

### 1.3 Objectifs MVP

1. Dématérialiser le workflow complet des 7 étapes du BDC (réception à facturation)
2. Offrir une vision en temps réel de tous les BDC (tableau de bord par statut, par ST, par bailleur)
3. Supprimer les doubles saisies grâce à l'extraction automatique des PDF
4. Sécuriser la facturation en traçant chaque attribution et réalisation
5. Garantir la confidentialité des prix (jamais visibles sur le BDC terrain envoyé au ST)

---

## 2. Contexte métier

### 2.1 Les bailleurs

| Bailleur | Canal de réception | Format BDC | Spécificité |
|----------|-------------------|------------|-------------|
| **GDH** (Grand Delta Habitat) | Plateforme IKOS | PDF numérique (2 pages : bon de commande + bon d'intervention) | Le bon d'intervention (page 2) est déjà une version sans prix |
| **ERILIA** | Email | PDF numérique (bon de travaux, prix sur toutes les pages) | Nécessite la génération d'un BDC terrain sans prix |

### 2.2 Les utilisateurs

| Rôle | Responsabilités | Accès V1 |
|------|----------------|----------|
| **Secrétaire** | Créer les BDC (upload PDF + vérification), compléter les infos (vacant/occupé, clés, RDV), préparer les BDC pour le CDT | Création, préparation, modification des BDC. Pas d'attribution ni facturation. |
| **Conducteur de travaux (CDT)** | Re-contrôler les BDC, attribuer aux ST, suivre la réalisation, valider et préparer la facturation | Accès complet : attribution, réattribution, validation, facturation |
| **Sous-traitants (ST)** | Reçoivent les BDC par SMS/email, réalisent les travaux, retournent la liste des logements faits | Pas d'accès à l'application en V1. Notification externe uniquement. |

### 2.3 Volume

- 50 à 150 bons de commande par mois
- 1 BDC = 1 logement
- Sources : IKOS (GDH) + emails (ERILIA) + autres canaux ponctuels

---

## 3. Workflow du BDC

### 3.1 Les 7 étapes

Le cycle de vie d'un BDC suit 7 étapes séquentielles. Chaque étape correspond à un statut dans l'application.

| # | Étape | Responsable | Description |
|---|-------|-------------|-------------|
| 1 | **Réception** | Secrétaire | Le BDC arrive (téléchargé depuis IKOS pour GDH, reçu par email pour ERILIA). La secrétaire uploade le PDF dans l'application. |
| 2 | **Préparation** | Secrétaire | L'application extrait les données du PDF. La secrétaire vérifie, complète les informations manquantes (vacant/occupé, clés/passes, RDV si logement occupé). Objectif : que le CDT n'ait plus qu'à attribuer. |
| 3 | **Attribution** | CDT | Le CDT re-contrôle le BDC, choisit un sous-traitant et lui attribue. Il fixe le montant ST (pourcentage du BDC). Le ST est notifié par SMS avec les infos nécessaires (adresse, vacant/occupé, clés, RDV, contenu des travaux). |
| 4 | **Envoi au ST** | CDT | Le BDC est envoyé au ST dans une version terrain SANS LES PRIX. Pour GDH, c'est la page 2 du PDF original (bon d'intervention). Pour ERILIA, l'application génère une version sans prix. |
| 5 | **Réalisation** | ST (externe) | Le sous-traitant effectue les travaux. Il informe le CDT une fois terminé. |
| 6 | **Signature bailleur** | ST / Bailleur | Le bailleur (ou le locataire) signe le BDC terrain sur place pour attester de la réalisation des travaux. |
| 7 | **Facturation** | CDT | Le CDT fait le rapprochement entre les BDC attribués et les réalisations déclarées par le ST. Les BDC validés passent en facturation. |

### 3.2 Correspondance avec le système actuel (pochettes)

| Pochette papier | Statut application | Étapes correspondantes |
|----------------|-------------------|----------------------|
| **À traiter** | À traiter | Entre étape 1 et 2 (infos manquantes) |
| **À faire** | À faire | Étape 2 terminée, prêt pour attribution |
| **En cours** | En cours | Étapes 3 à 6 (attribué, en réalisation) |
| **À facturer** | À facturer | Étape 7 (travaux validés) |

### 3.3 Règles métier critiques

> **⚠️ Règle de réattribution**
> Un BDC peut être réattribué à un autre sous-traitant UNIQUEMENT avant que le ST se soit rendu sur place (entre les étapes 3 et 5). Lors d'une réattribution : le CDT corrige l'attribution, un nouveau SMS est envoyé au nouveau ST, l'historique conserve la trace de l'ancienne et de la nouvelle attribution.

> **🔒 Règle de confidentialité des prix**
> Les prix ne doivent JAMAIS apparaître sur le BDC terrain envoyé au sous-traitant. Ils sont visibles uniquement dans l'application, pour la secrétaire et le CDT.

> **📋 Règle de recoupement facturation**
> En fin de semaine, le CDT compare les BDC attribués avec les réalisations déclarées par le ST. Les ST se basent parfois sur leur liste de SMS (qui inclut aussi les BDC non réalisés). Le CDT doit donc recouper avec ses propres données. L'application doit faciliter ce recoupement.

---

## 4. Modèle de données d'un BDC

Chaque bon de commande contient les informations suivantes, extraites automatiquement du PDF puis complétées manuellement par la secrétaire.

### 4.1 Données extraites du PDF

| Champ | Description | Exemple (GDH) |
|-------|-------------|----------------|
| **Bailleur** | Origine du BDC | Grand Delta Habitat |
| **Numéro de BDC** | Identifiant unique du bon | 450056 |
| **Numéro de marché** | Référence du marché-cadre | 026322-CPP-003 |
| **Date d'émission** | Date de création du BDC par le bailleur | 09/02/2026 |
| **Objet / Nature des travaux** | Description libre des travaux | Reprise peinture SDB suite trx faience |
| **Délai d'exécution** | Date limite de réalisation | 20/02/2026 |
| **Programme / Résidence** | Nom de la résidence ou du programme | VERONESE BAT 1 ENT 1 |
| **Adresse complète** | Adresse du logement | 3 Rue François 1er, 84000 Avignon |
| **Logement** | Numéro, type, étage, porte | N° 000756, T3, étage 1, porte 107 |
| **Occupant** | Nom, téléphone, email (si renseigné) | MUSELLA Christiane, 0658714328 |
| **Émetteur bailleur** | Contact côté bailleur | Joseph LONEGRO, 0637577004 |
| **Lignes de prestation** | Détail : désignation, quantité, prix unitaire, montant | M-P préparation et mise en peinture, 15m², 11,19€/m² |
| **Totaux** | HT, TVA, TTC | 167,85€ HT / 184,64€ TTC |

### 4.2 Données ajoutées manuellement

| Champ | Description | Obligatoire ? |
|-------|-------------|---------------|
| **Vacant / Occupé** | Le logement est-il vide ou habité | Oui (obligatoire avant enregistrement en « À faire ») |
| **Modalité d'accès** | Clés, passes, gardien, agence... (texte libre) | Non (mais recommandé) |
| **RDV pris** | Oui/Non. Si oui : date et heure | Non (avertissement si occupé et pas de RDV) |
| **Notes** | Commentaires libres | Non |

### 4.3 Données gérées par l'application

| Champ | Description |
|-------|-------------|
| **Statut** | Position dans le workflow (À traiter, À faire, En cours, À facturer, Facturé) |
| **Sous-traitant attribué** | ST désigné par le CDT pour réaliser les travaux |
| **Montant ST** | Montant attribué au ST (pourcentage du BDC, fixé par le CDT) |
| **PDF original** | Le fichier PDF uploadé, toujours consultable |
| **Historique des actions** | Log de toutes les actions : qui a fait quoi, quand (création, modification, attribution, réattribution, validation...) |

---

## 5. Spécifications fonctionnelles MVP

### 5.1 SPEC-001 — Création d'un BDC par upload PDF (GDH)

#### Parcours utilisateur

**Étape 1 — Upload du PDF.** La secrétaire clique sur « Nouveau BDC », sélectionne le fichier PDF depuis son ordinateur (ou le glisse-dépose). L'application accepte uniquement les fichiers PDF.

**Étape 2 — Extraction automatique.** L'application lit le PDF numérique et extrait automatiquement toutes les données structurées : bailleur, numéro, adresse, prestations, montants, délais, occupant, émetteur. Le PDF étant toujours un fichier numérique propre (jamais un scan), l'extraction est fiable.

**Étape 3 — Vérification et complétion.** L'application affiche un formulaire pré-rempli. La secrétaire vérifie les données extraites (elle peut tout modifier si une info est incomplète). Elle complète les champs manuels : vacant/occupé (obligatoire), modalité d'accès, RDV, notes.

**Étape 4 — Validation.** La secrétaire clique sur « Enregistrer ». Le BDC est créé avec le statut « À faire » (prêt pour le CDT). Si des informations manquent et que le BDC n'est pas encore prêt, elle peut l'enregistrer en statut « À traiter ».

#### Règles métier

- Le PDF original est conservé et rattaché au BDC (toujours consultable)
- Tous les champs extraits sont modifiables (pour corriger les infos incomplètes)
- Le champ « Vacant / Occupé » est obligatoire avant enregistrement en « À faire »
- Si logement occupé et pas de RDV renseigné : avertissement (pas de blocage)
- Les prix sont enregistrés mais ne seront jamais visibles sur le BDC terrain
- Un BDC avec un numéro déjà existant est détecté et bloqué (doublon)

#### Critères de validation

1. La secrétaire peut uploader un PDF GDH et voir le formulaire pré-rempli
2. Elle peut modifier n'importe quel champ pré-rempli
3. Elle peut compléter les champs manuels (vacant/occupé, accès, RDV, notes)
4. Elle ne peut pas valider en « À faire » sans avoir renseigné vacant/occupé
5. Le BDC enregistré apparaît avec le bon statut (« À faire » ou « À traiter »)
6. Le PDF original reste consultable depuis la fiche du BDC
7. Un doublon (même numéro) est détecté et bloqué

### 5.2 SPEC-002 — Tableau de bord / Liste des BDC

#### Parcours utilisateur

**Étape 1 — Accès au tableau de bord.** L'utilisateur authentifié (Secrétaire ou CDT) arrive sur l'écran principal de l'application. Il voit la liste de tous les BDC, triée par date de création décroissante, paginée par 25.

**Étape 2 — Compteurs par statut.** En haut de page, des compteurs affichent le nombre de BDC dans chaque statut (À traiter, À faire, En cours, À facturer, Facturé) ainsi que le total. Ces compteurs portent sur l'ensemble des BDC, indépendamment des filtres appliqués.

**Étape 3 — Recherche textuelle.** Un champ de recherche permet de filtrer par numéro de BDC, adresse ou nom d'occupant (recherche partielle, insensible à la casse).

**Étape 4 — Filtres avancés.** L'utilisateur peut combiner les filtres : statut (liste déroulante), bailleur (liste déroulante), ville (texte libre), période de création (date du / date au). Les filtres se cumulent. Un indicateur affiche le nombre de filtres actifs.

**Étape 5 — Alertes délais (CDT uniquement).** Le CDT voit en haut du tableau de bord deux sections d'alerte : les BDC en retard (délai d'exécution dépassé) et les BDC dont le délai est proche (dans les 2 prochains jours). Ces alertes portent uniquement sur les BDC en statut À faire ou En cours.

**Étape 6 — Navigation vers le détail.** L'utilisateur clique sur un BDC pour ouvrir sa fiche détaillée (sidebar HTMX ou page complète).

#### Règles métier

- Le tableau de bord est accessible à tous les utilisateurs authentifiés (Secrétaire et CDT)
- Les compteurs par statut ne sont pas affectés par les filtres actifs (vision globale permanente)
- Les alertes délais ne sont visibles que par le CDT
- Le seuil d'alerte « délai proche » est de 2 jours
- La recherche porte sur : numéro de BDC, adresse, nom d'occupant
- La pagination est de 25 BDC par page
- Les requêtes HTMX ne rechargent que le fragment de liste, pas la page entière

#### Critères de validation

1. Un utilisateur authentifié voit la liste paginée des BDC
2. Les compteurs par statut sont affichés et corrects
3. La recherche filtre par numéro, adresse ou occupant
4. Les filtres (statut, bailleur, ville, dates) se cumulent correctement
5. Le CDT voit les alertes de délai (retard + proche)
6. La Secrétaire ne voit pas les alertes de délai
7. Le clic sur un BDC ouvre sa fiche détaillée
8. La pagination fonctionne correctement (25 par page)

### 5.3 SPEC-003 — Attribution d'un BDC à un sous-traitant

#### Parcours utilisateur

**Étape 1 — Accès à l'attribution.** Le CDT ouvre un BDC en statut « À faire » et clique sur « Attribuer ». Il accède à une page split-screen : le PDF original à gauche, le panneau d'attribution à droite.

**Étape 2 — Répartition de la charge.** Le panneau d'attribution affiche la répartition actuelle des BDC par sous-traitant (nombre de BDC en cours, montant total). Un sélecteur de période (semaine, mois, trimestre, année, personnalisé) permet de filtrer cette répartition. Si une période est sélectionnée, les données N-1 (même période l'année précédente) sont affichées pour comparaison.

**Étape 3 — Sélection du sous-traitant.** Le CDT sélectionne un sous-traitant dans la liste déroulante (seuls les ST actifs apparaissent) et saisit le pourcentage du BDC attribué au ST (0-100%).

**Étape 4 — Calcul du montant ST.** Le montant ST est calculé automatiquement : montant HT du BDC × pourcentage / 100, arrondi au centime.

**Étape 5 — Validation.** Le CDT valide l'attribution. Le BDC passe en statut « En cours ». L'historique enregistre l'attribution avec le ST, le pourcentage et le montant.

**Étape 6 — Génération du PDF terrain.** Le PDF terrain (sans prix) est généré automatiquement : pour GDH, extraction de la page 2 du PDF original ; pour ERILIA, génération HTML→PDF. La génération est non-bloquante (un échec ne bloque pas l'attribution).

**Étape 7 — Notification au sous-traitant.** Un SMS et un email sont envoyés au ST. Le SMS contient : numéro de BDC, adresse, occupation, modalité d'accès, objet des travaux, délai. L'email contient les mêmes informations avec le PDF terrain en pièce jointe. Les notifications sont non-bloquantes. Les prix ne sont JAMAIS inclus.

**Étape 8 — Réattribution.** Si le BDC est en statut « En cours » et que le ST ne s'est pas encore rendu sur place, le CDT peut réattribuer le BDC à un autre ST. Le formulaire est pré-rempli avec le ST et le pourcentage actuels. Lors de la réattribution : le statut reste « En cours », l'historique trace l'ancien et le nouveau ST, l'ancien ST est notifié de l'annulation par SMS et email, le nouveau ST reçoit les notifications d'attribution.

#### Règles métier

- Seul le CDT peut attribuer ou réattribuer un BDC
- L'attribution n'est possible que depuis le statut « À faire » (→ « En cours »)
- La réattribution n'est possible que depuis le statut « En cours » (le statut ne change pas)
- Le pourcentage ST est un nombre décimal entre 0 et 100
- Le montant ST est calculé : montant HT × pourcentage / 100
- Les prix ne figurent JAMAIS dans les SMS, emails ou PDF terrain
- Les notifications SMS/email sont non-bloquantes (un échec n'empêche pas l'attribution)
- La génération du PDF terrain est non-bloquante
- L'historique trace toute attribution et réattribution avec les détails complets

#### Critères de validation

1. Le CDT peut attribuer un BDC « À faire » à un ST actif
2. Le BDC passe en statut « En cours » après attribution
3. Le montant ST est calculé correctement
4. Le PDF terrain est généré (GDH : page 2, ERILIA : HTML→PDF)
5. Le SMS et l'email sont envoyés au ST (sans prix)
6. Le CDT peut réattribuer un BDC « En cours »
7. L'ancien ST reçoit une notification d'annulation
8. L'historique enregistre les attributions et réattributions
9. La Secrétaire ne peut pas attribuer un BDC
10. La répartition ST avec comparaison N-1 s'affiche correctement

### 5.4 SPEC-004 — Génération du BDC terrain (sans prix)

#### Parcours utilisateur

**Étape 1 — Déclenchement automatique.** La génération du PDF terrain se déclenche automatiquement lors de l'attribution ou de la réattribution d'un BDC à un sous-traitant. Aucune action manuelle n'est requise.

**Étape 2 — Stratégie GDH.** Pour les BDC du bailleur GDH, le PDF terrain est la page 2 du PDF original (bon d'intervention), qui est nativement sans prix. L'application extrait cette page via PyMuPDF et la stocke comme fichier indépendant.

**Étape 3 — Stratégie ERILIA.** Pour les BDC du bailleur ERILIA (et tout autre bailleur futur), le PDF terrain est généré à partir des données du BDC via un template HTML rendu en PDF par WeasyPrint. Ce template inclut toutes les informations nécessaires au sous-traitant (adresse, logement, travaux, délai) mais exclut systématiquement les prix (prix unitaires, montants, totaux HT/TVA/TTC).

**Étape 4 — Stockage.** Le PDF terrain est enregistré sur le champ `pdf_terrain` du BDC avec le nom `{numero_bdc}_terrain.pdf`.

**Étape 5 — Téléchargement.** Tout utilisateur authentifié peut télécharger le PDF terrain depuis la fiche détaillée du BDC. Le fichier est servi en téléchargement avec le nom `BDC_{numero_bdc}_terrain.pdf`.

**Étape 6 — Envoi par email.** Le PDF terrain est automatiquement joint à l'email d'attribution envoyé au sous-traitant. Si le PDF terrain n'est pas disponible, l'email est quand même envoyé avec une note invitant le ST à récupérer le document auprès du CDT.

#### Règles métier

- Les prix ne doivent JAMAIS apparaître sur le PDF terrain (règle de confidentialité absolue)
- Pour GDH : la page 2 du PDF original est utilisée (nativement sans prix)
- Pour ERILIA et autres : génération HTML→PDF via WeasyPrint, sans aucun champ prix
- Le PDF original doit avoir au moins 2 pages pour la stratégie GDH (sinon erreur)
- La génération est non-bloquante : un échec est logué mais n'empêche pas l'attribution
- Le PDF terrain est régénéré à chaque réattribution
- Le téléchargement retourne une 404 si aucun PDF terrain n'est disponible

#### Critères de validation

1. Le PDF terrain GDH contient uniquement la page 2 du PDF original
2. Le PDF terrain ERILIA est généré sans aucun prix
3. Le PDF terrain est stocké et téléchargeable depuis la fiche BDC
4. Le PDF terrain est joint à l'email d'attribution
5. Un échec de génération ne bloque pas l'attribution
6. Le PDF terrain est régénéré lors d'une réattribution

### 5.5 SPEC-005 — Suivi de réalisation et validation

#### Parcours utilisateur

**Étape 1 — Contrôle par la Secrétaire.** Avant qu'un BDC passe en « À faire », la Secrétaire le contrôle sur une page split-screen : le PDF original à gauche, le formulaire d'édition et la checklist à droite. Elle complète les champs manuels (vacant/occupé, type d'accès, date de RDV, notes) et coche tous les points de contrôle de la checklist. Si un BDC a été renvoyé par le CDT, le commentaire du dernier renvoi est affiché en haut de page.

**Étape 2 — Renvoi au contrôle par le CDT.** Le CDT peut renvoyer un BDC « À faire » vers le statut « À traiter » avec un commentaire obligatoire expliquant ce qui doit être corrigé. L'historique enregistre le renvoi et le commentaire.

**Étape 3 — Validation de la réalisation.** Le CDT valide la réalisation d'un BDC « En cours » (le sous-traitant a effectué les travaux). Le BDC passe en statut « À facturer ». La date de réalisation est automatiquement fixée à la date du jour.

**Étape 4 — Retour en cours.** Si nécessaire, un BDC « À facturer » peut être repassé en « En cours » (par exemple si la réalisation n'est finalement pas conforme). La date de réalisation est alors remise à null.

**Étape 5 — Validation de la facturation.** Le CDT valide la facturation d'un BDC « À facturer ». Le BDC passe en statut « Facturé » (état terminal).

**Étape 6 — Recoupement par sous-traitant.** Le CDT accède à une page de recoupement listant tous les sous-traitants ayant des BDC en cours, à facturer ou facturés. Pour chaque ST : nombre de BDC et montant total. Un sélecteur de période (semaine, mois, trimestre, année, personnalisé) filtre les données. Si une période est sélectionnée, les données N-1 sont affichées avec le delta (écart en nombre de BDC). Le CDT peut cliquer sur un ST pour voir le détail de ses BDC, filtrable par statut.

#### Règles métier

- Seul le CDT peut valider la réalisation, la facturation et renvoyer au contrôle
- La Secrétaire peut éditer les champs manuels et cocher la checklist uniquement sur les BDC « À traiter »
- Tous les points de contrôle actifs doivent être cochés avant passage en « À faire »
- Le champ « Vacant / Occupé » est obligatoire avant passage en « À faire »
- Le type d'accès est obligatoire si le logement est vacant
- La date de RDV est obligatoire si le logement est occupé
- Le renvoi au contrôle exige un commentaire obligatoire
- La date de réalisation est fixée automatiquement au jour de la validation
- Le retour « À facturer » → « En cours » remet la date de réalisation à null
- « Facturé » est un état terminal (aucune transition possible)
- Le recoupement porte sur les statuts : En cours, À facturer, Facturé
- La comparaison N-1 utilise la même durée de période décalée d'un an

#### Critères de validation

1. La Secrétaire peut éditer et cocher la checklist sur un BDC « À traiter »
2. Le passage « À traiter » → « À faire » exige : occupation, type d'accès/RDV, checklist complète
3. Le CDT peut renvoyer un BDC « À faire » → « À traiter » avec commentaire obligatoire
4. Le commentaire de renvoi est visible sur la page de contrôle
5. Le CDT peut valider la réalisation (« En cours » → « À facturer »)
6. La date de réalisation est fixée au jour de la validation
7. Le retour « À facturer » → « En cours » remet la date de réalisation à null
8. Le CDT peut valider la facturation (« À facturer » → « Facturé »)
9. Le recoupement liste les ST avec compteurs et montants
10. La comparaison N-1 affiche les données de la même période l'année précédente

### 5.6 SPEC-006 — Export facturation

#### Parcours utilisateur

**Étape 1 — Accès à l'export.** Le CDT accède à la page d'export facturation depuis le menu. Il voit un formulaire de filtres et un compteur indiquant le nombre de BDC correspondants.

**Étape 2 — Filtrage.** Le CDT peut filtrer par : statut (« À facturer », « Facturé », ou les deux), sous-traitant (liste déroulante), période de réalisation (date du / date au, portant sur la date de réalisation). Les filtres se cumulent. Le compteur se met à jour en temps réel.

**Étape 3 — Aperçu.** Le CDT voit le nombre de BDC qui seront exportés avant de lancer le téléchargement.

**Étape 4 — Téléchargement.** Le CDT clique sur « Exporter ». Un fichier Excel (.xlsx) est téléchargé avec le nom `export_facturation_{date_du_jour}.xlsx`.

**Étape 5 — Contenu du fichier.** Le fichier Excel contient une ligne par BDC avec les colonnes : N° BDC, Bailleur, Adresse, Ville, Sous-traitant, % ST, Montant HT (€), Montant ST (€), Date réalisation, Statut. Les en-têtes sont en gras. Les largeurs de colonnes sont ajustées automatiquement (maximum 40 caractères).

#### Règles métier

- Seul le CDT peut accéder à l'export facturation
- L'export porte uniquement sur les BDC en statut « À facturer » ou « Facturé »
- Le filtre de dates porte sur la date de réalisation (pas la date de création)
- Le format de sortie est Excel (.xlsx) via openpyxl
- Le fichier est nommé avec la date du jour de l'export

#### Critères de validation

1. Le CDT accède au formulaire d'export
2. Les filtres (statut, ST, dates) fonctionnent et se cumulent
3. Le compteur de BDC est correct avant export
4. Le fichier Excel est téléchargé avec le bon nom
5. Le fichier contient les 10 colonnes attendues avec en-têtes en gras
6. La Secrétaire ne peut pas accéder à l'export

### 5.7 SPEC-007 — Alertes et rappels (délais)

#### Parcours utilisateur

**Étape 1 — Affichage automatique.** Les alertes sont affichées automatiquement en haut du tableau de bord (SPEC-002) pour le CDT. Aucune action de configuration n'est nécessaire.

**Étape 2 — Alertes de retard.** Les BDC dont le délai d'exécution est dépassé (date antérieure à aujourd'hui) et qui sont en statut « À faire » ou « En cours » sont listés comme BDC en retard.

**Étape 3 — Alertes de délai proche.** Les BDC dont le délai d'exécution est dans les 2 prochains jours (date comprise entre aujourd'hui et aujourd'hui + 2 jours inclus) et qui sont en statut « À faire » ou « En cours » sont listés comme BDC avec délai proche.

**Étape 4 — Consultation.** Le CDT peut cliquer sur un BDC en alerte pour accéder directement à sa fiche détaillée et prendre les actions nécessaires (attribuer, relancer le ST, etc.).

#### Règles métier

- Les alertes ne sont visibles que par le CDT
- Les alertes portent uniquement sur les BDC en statut « À faire » ou « En cours »
- Les BDC « À traiter », « À facturer » et « Facturé » ne déclenchent pas d'alerte
- Le seuil de « délai proche » est de 2 jours
- Un BDC en retard n'apparaît pas dans les « délais proches » (les deux catégories sont mutuellement exclusives)
- Les alertes sont calculées à chaque chargement du tableau de bord (temps réel)

#### Critères de validation

1. Le CDT voit les BDC en retard sur le tableau de bord
2. Le CDT voit les BDC à délai proche (2 jours) sur le tableau de bord
3. Un BDC en retard n'apparaît pas dans les délais proches
4. Un BDC « À facturer » ou « Facturé » ne déclenche pas d'alerte
5. La Secrétaire ne voit pas les alertes
6. Le clic sur un BDC en alerte mène à sa fiche détaillée

---

## 6. Gestion des accès (rôles)

| Action | Secrétaire | CDT | Direction (V2) |
|--------|-----------|-----|----------------|
| Créer un BDC | ✅ Oui | ✅ Oui | ❌ Non |
| Modifier / compléter un BDC | ✅ Oui | ✅ Oui | ❌ Non |
| Attribuer / réattribuer | ❌ Non | ✅ Oui | ❌ Non |
| Valider la réalisation | ❌ Non | ✅ Oui | ❌ Non |
| Gérer la facturation | ❌ Non | ✅ Oui | ❌ Non |
| Voir le tableau de bord | ✅ Oui | ✅ Oui | ✅ Oui (lecture seule) |
| Voir les prix | ✅ Oui | ✅ Oui | ✅ Oui |

---

## 7. Contraintes et choix techniques

- Application web (navigateur), pas de mobile en V1
- Interface en français uniquement
- Approche MVP progressive : chaque fonctionnalité est développée, testée et validée avant de passer à la suivante
- Les PDF des BDC sont toujours des fichiers numériques propres (pas de scans), ce qui permet une extraction fiable
- Les notifications aux ST se font par SMS/email (hors application, pas d'espace ST en V1)

---

## 8. Hors périmètre MVP (roadmap)

Les fonctionnalités suivantes sont identifiées mais explicitement hors du périmètre MVP. Elles sont listées ici pour référence et ne doivent pas être développées dans cette version.

| Phase | Fonctionnalité |
|-------|---------------|
| **V2** | Espace sous-traitant (accès restreint, confirmation, déclaration) |
| **V2** | Import automatique depuis IKOS (plus besoin de télécharger manuellement) |
| **V2** | Import email ERILIA (parsing automatique des emails) |
| **V3** | Module facturation complet |
| **V3** | Statistiques avancées |
| **V3** | Application mobile / PWA |
| **V4** | Gestion documentaire (photos, PV, signatures numériques) |

---

## 9. Annexes

### 9.1 Exemple de BDC GDH (n° 450056)

Bon de commande Grand Delta Habitat — Reprise peinture SDB suite travaux faïence.

- Page 1 : Bon de commande (version complète avec prix) — usage interne
- Page 2 : Bon d'intervention (version sans prix, avec zone de signature) — BDC terrain

**Données clés :** Marché 026322-CPP-003, adresse 3 Rue François 1er Avignon, logement T3 étage 1 porte 107, occupant MUSELLA Christiane (0658714328), émetteur Joseph LONEGRO (0637577004), prestation M-P préparation et mise en peinture 15m², total 167,85€ HT / 184,64€ TTC, délai 20/02/2026.

### 9.2 Exemple de BDC ERILIA (n° 2026 20205)

Bon de travaux ERILIA Agence Avignon — Peinture finition (WC, cuisine, plafonds T3).

- Format : 2 pages, prix visibles partout (pas de version terrain intégrée)
- Pas d'occupant renseigné → probablement logement vacant

**Données clés :** Marché 2025 356 4 1, adresse 5 Rue de la Petite Vitesse Avignon, résidence LES TERRASSES DE MERCURE BAT D, 3 lignes de prestation (WC 198,30€ TTC + cuisine 344,41€ TTC + plafonds T3 635,83€ TTC), total 1 071,40€ HT / 1 178,54€ TTC, délai 10 jours (06/02 au 15/02/2026).

### 9.3 Glossaire

| Terme | Définition |
|-------|-----------|
| **BDC** | Bon de commande. Document émis par un bailleur pour commander des travaux de peinture. |
| **BDC terrain** | Version du BDC sans les prix, destinée au sous-traitant et signée sur place. |
| **CDT** | Conducteur de travaux. Responsable de l'attribution aux ST et du suivi. |
| **ST** | Sous-traitant. Artisan qui réalise les travaux de peinture. |
| **GDH** | Grand Delta Habitat. Bailleur social, BDC reçus via la plateforme IKOS. |
| **ERILIA** | Bailleur social, BDC reçus par email. |
| **IKOS** | Plateforme web de GDH où sont publiés les bons de commande. |
| **Pochette** | Système physique actuel de classement des BDC par statut (À traiter, À faire, En cours, À facturer). |
