## MODIFIED Requirements

### Requirement: Template base.html avec layout principal
Le système SHALL fournir un template `templates/base.html` avec un layout sidebar + contenu principal. La sidebar SHALL contenir : le logo "ISMA" en texte stylisé, les liens de navigation (Tableau de bord, Upload PDF, Sous-traitants, Recoupement, Export facturation — ces deux derniers CDT uniquement), un toggle dark/light mode, le nom de l'utilisateur connecté avec son groupe, et un bouton de déconnexion. La sidebar SHALL être collapsible (icônes seulement) via un bouton, l'état persisté en localStorage. Le contenu principal SHALL inclure une barre supérieure avec un champ de recherche globale. Les blocs `{% block title %}`, `{% block content %}`, `{% block extra_head %}`, `{% block extra_scripts %}` SHALL rester disponibles.

#### Scenario: Le template de base charge les dépendances frontend
- **WHEN** une page utilisant base.html est rendue
- **THEN** le HTML contient le CDN Tailwind avec config custom, les liens Google Fonts, les scripts HTMX et Alpine.js

#### Scenario: La sidebar affiche les liens de navigation
- **WHEN** un utilisateur authentifié consulte une page
- **THEN** la sidebar affiche les liens Tableau de bord et Upload PDF avec des icônes

#### Scenario: La sidebar est collapsible
- **WHEN** l'utilisateur clique sur le bouton de collapse de la sidebar
- **THEN** la sidebar se réduit en mode icônes seulement et l'état est persisté en localStorage

#### Scenario: Les blocs sont extensibles
- **WHEN** un template enfant définit `{% block content %}Mon contenu{% endblock %}`
- **THEN** "Mon contenu" apparaît dans la zone de contenu principal à droite de la sidebar

#### Scenario: La navigation affiche le nom de l'utilisateur
- **WHEN** un utilisateur authentifié consulte une page
- **THEN** la sidebar affiche son nom, son groupe (badge), et un lien de déconnexion

### Requirement: Sidebar sans scrollbar visible
La scrollbar de la sidebar DOIT être masquée visuellement tout en gardant le scroll fonctionnel.

#### Scenario: Écran court
- **WHEN** la hauteur du viewport est insuffisante
- **THEN** le scroll fonctionne mais aucune scrollbar n'est visible

### Requirement: Page de login stylisée
Le système SHALL fournir un template `templates/accounts/login.html` avec un formulaire de connexion centré, le logo "ISMA" en grand, des champs email et mot de passe stylisés avec le design system, et un fond utilisant la palette Isma.

#### Scenario: Le formulaire de login est affiché
- **WHEN** un utilisateur accède à /accounts/login/
- **THEN** un formulaire centré avec le logo ISMA, les champs email et mot de passe stylisés, et un bouton de connexion accent est affiché

### Requirement: Tailwind CSS chargé via CDN Play avec config custom
Le système SHALL utiliser le CDN Tailwind Play (`cdn.tailwindcss.com`) avec une configuration inline définissant : la palette de couleurs Isma, les fonts custom (Plus Jakarta Sans, JetBrains Mono), le darkMode en mode 'class'.

#### Scenario: La config Tailwind custom est active
- **WHEN** une page est rendue
- **THEN** les classes Tailwind custom (bg-primary, text-accent, font-display) fonctionnent correctement

### Requirement: HTMX disponible dans tous les templates
Le système SHALL charger HTMX 2.x dans base.html de sorte que tout template enfant puisse utiliser les attributs `hx-get`, `hx-post`, `hx-target`, `hx-swap` sans configuration supplémentaire.

#### Scenario: Un attribut HTMX fonctionne dans un template enfant
- **WHEN** un template enfant utilise `hx-get="/test/"` sur un bouton
- **THEN** HTMX intercepte le clic et effectue une requête GET vers /test/

### Requirement: Alpine.js disponible dans tous les templates
Le système SHALL charger Alpine.js 3.x dans base.html de sorte que tout template enfant puisse utiliser les directives `x-data`, `x-show`, `x-on` sans configuration supplémentaire.

#### Scenario: Une directive Alpine.js fonctionne
- **WHEN** un template enfant utilise `x-data="{ open: false }"` et `x-show="open"`
- **THEN** l'élément est masqué par défaut et visible quand `open` passe à `true`

### Requirement: Pages d'erreur 404 et 500 stylisées
Le système SHALL fournir des templates `404.html` et `500.html` utilisant le design system Isma avec un message clair et un lien de retour au dashboard.

#### Scenario: Page 404 affichée
- **WHEN** un utilisateur accède à une URL inexistante
- **THEN** une page 404 stylisée avec le branding Isma est affichée avec un lien vers le dashboard

#### Scenario: Page 500 affichée
- **WHEN** une erreur serveur se produit
- **THEN** une page 500 stylisée est affichée avec un message d'erreur générique
