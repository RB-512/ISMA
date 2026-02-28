## ADDED Requirements

### Requirement: Le design system Isma définit la palette de couleurs via CSS variables
Le système SHALL définir un jeu de CSS custom properties sur `:root` pour le thème light et sur `.dark` pour le thème dark. Les couleurs principales SHALL être : primary (#1B2B3A bleu pétrole), accent (#E8853D ambre), success (#2D9F6F), warning (#D4842A), danger (#C4423C), surface (#F7F5F2 beige chaud en light, #131A22 bleu nuit en dark).

#### Scenario: Variables CSS disponibles en light mode
- **WHEN** la page est rendue sans la classe `dark` sur `<html>`
- **THEN** les CSS variables `--color-primary`, `--color-accent`, `--color-surface`, `--color-surface-card` sont définies avec les valeurs light

#### Scenario: Variables CSS disponibles en dark mode
- **WHEN** la classe `dark` est présente sur `<html>`
- **THEN** les CSS variables sont redéfinies avec les valeurs dark (surface: #131A22, surface-card: #1B2B3A, text: #E8E4DF)

### Requirement: La typographie utilise Plus Jakarta Sans et JetBrains Mono
Le système SHALL charger Plus Jakarta Sans (400, 500, 600, 700) et JetBrains Mono (400, 500) via Google Fonts CDN. Plus Jakarta Sans SHALL être la font par défaut pour tout le texte. JetBrains Mono SHALL être utilisée pour les données chiffrées (numéros BDC, montants, pourcentages) via une classe utilitaire `font-mono`.

#### Scenario: Les fonts sont chargées
- **WHEN** une page est rendue
- **THEN** le HTML contient les balises `<link>` Google Fonts pour Plus Jakarta Sans et JetBrains Mono

#### Scenario: Les numéros BDC utilisent la font mono
- **WHEN** un numéro de BDC est affiché dans un tableau ou une fiche
- **THEN** le texte utilise la police JetBrains Mono

### Requirement: Le dark mode est toggleable et persisté
Le système SHALL fournir un bouton toggle dark/light dans la sidebar. L'état SHALL être persisté en localStorage sous la clé `isma-theme`. Au chargement, un script inline dans `<head>` SHALL appliquer la classe `dark` sur `<html>` AVANT le premier rendu pour éviter le flash.

#### Scenario: Toggle vers dark mode
- **WHEN** l'utilisateur clique sur le toggle thème en mode light
- **THEN** la classe `dark` est ajoutée à `<html>`, le localStorage est mis à jour, et toutes les couleurs changent

#### Scenario: Persistance du thème
- **WHEN** l'utilisateur a choisi le dark mode et recharge la page
- **THEN** la page s'affiche directement en dark sans flash de thème light

#### Scenario: Thème par défaut
- **WHEN** aucune préférence n'est stockée en localStorage
- **THEN** le thème light est appliqué par défaut

### Requirement: Les badges de statut utilisent des couleurs distinctes et cohérentes
Le système SHALL afficher les statuts BDC avec des badges colorés : A_TRAITER (jaune/amber), A_FAIRE (bleu), EN_COURS (indigo), A_FACTURER (orange), FACTURE (vert). Chaque badge SHALL avoir un fond léger et un texte foncé de la même teinte.

#### Scenario: Badge statut EN_COURS
- **WHEN** un BDC en statut EN_COURS est affiché
- **THEN** le badge affiche "En cours" avec fond indigo clair et texte indigo foncé

#### Scenario: Cohérence light/dark
- **WHEN** un badge statut est affiché en dark mode
- **THEN** les couleurs du badge restent lisibles avec un contraste suffisant

### Requirement: Les widgets de formulaire Django sont stylisés uniformément
Le système SHALL appliquer des classes Tailwind cohérentes à tous les widgets Django (input, select, textarea, checkbox) via les attributs `attrs` dans les formulaires ou via CSS global. Les champs SHALL avoir des bordures arrondies, un focus ring accent, et un style cohérent light/dark.

#### Scenario: Champ input text stylisé
- **WHEN** un formulaire Django est rendu avec un champ TextInput
- **THEN** le champ a des bordures arrondies, un padding cohérent, et un ring de focus coloré

#### Scenario: Champ select stylisé
- **WHEN** un formulaire Django est rendu avec un champ Select
- **THEN** le select a le même style que les inputs (bordures, padding, focus ring)
