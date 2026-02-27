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

*À spécifier. Écran principal de l'application : liste de tous les BDC, filtrable par statut (équivalent numérique des pochettes), par bailleur, par sous-traitant. Vue temps réel de l'avancement.*

### 5.3 SPEC-003 — Attribution d'un BDC à un sous-traitant

*À spécifier. Le CDT sélectionne un BDC « À faire », choisit un ST, fixe le montant ST, envoie la notification SMS. Inclut la réattribution.*

### 5.4 SPEC-004 — Génération du BDC terrain (sans prix)

*À spécifier. Version imprimable du BDC sans les prix, destinée au sous-traitant. Pour GDH : utiliser la page 2 du PDF original. Pour ERILIA : générer automatiquement une version sans prix.*

### 5.5 SPEC-005 — Suivi de réalisation et validation

*À spécifier. Le CDT marque un BDC comme « réalisé », fait le rapprochement avec les déclarations du ST, valide le passage en facturation.*

### 5.6 SPEC-006 — Export facturation

*À spécifier. Export des BDC validés pour faciliter le rapprochement BDC/factures.*

### 5.7 SPEC-007 — Alertes et rappels (délais)

*À spécifier. Notifications sur les BDC dont le délai d'exécution est dépassé ou proche.*

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
