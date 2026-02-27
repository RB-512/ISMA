## ADDED Requirements

### Requirement: Template base.html avec layout principal

Le systeme SHALL fournir un template `templates/base.html` avec : bloc `{% block title %}`, bloc `{% block content %}`, chargement de Tailwind CSS, HTMX 2.x et Alpine.js 3.x, barre de navigation avec le nom de l'utilisateur connecte et un bouton de deconnexion.

#### Scenario: Le template de base charge les dependances frontend
- **WHEN** une page utilisant base.html est rendue
- **THEN** le HTML contient les balises script pour HTMX et Alpine.js, et le lien vers le CSS Tailwind

#### Scenario: La navigation affiche le nom de l'utilisateur
- **WHEN** un utilisateur authentifie consulte une page
- **THEN** la barre de navigation affiche son nom et un lien de deconnexion

#### Scenario: Les blocs sont extensibles
- **WHEN** un template enfant definit `{% block content %}Mon contenu{% endblock %}`
- **THEN** "Mon contenu" apparait dans la zone de contenu principal

### Requirement: Page de login stylisee

Le systeme SHALL fournir un template `templates/accounts/login.html` avec un formulaire de connexion (email, mot de passe, bouton) style avec Tailwind CSS.

#### Scenario: Le formulaire de login est affiche
- **WHEN** un utilisateur accede a /accounts/login/
- **THEN** un formulaire avec champs email et mot de passe est affiche, style avec Tailwind CSS

### Requirement: Tailwind CSS genere via CLI standalone

Le systeme SHALL utiliser le binaire Tailwind CSS standalone pour generer `static/css/output.css` a partir des classes utilisees dans les templates. Un fichier `tailwind.config.js` SHALL configurer le scan des templates Django.

#### Scenario: Le CSS est genere sans Node.js
- **WHEN** le developpeur execute la commande Tailwind CLI en mode watch
- **THEN** le fichier `static/css/output.css` est genere et mis a jour a chaque modification de template

### Requirement: HTMX disponible dans tous les templates

Le systeme SHALL charger HTMX 2.x dans base.html de sorte que tout template enfant puisse utiliser les attributs `hx-get`, `hx-post`, `hx-target`, `hx-swap` sans configuration supplementaire.

#### Scenario: Un attribut HTMX fonctionne dans un template enfant
- **WHEN** un template enfant utilise `hx-get="/test/"` sur un bouton
- **THEN** HTMX intercepte le clic et effectue une requete GET vers /test/

### Requirement: Alpine.js disponible dans tous les templates

Le systeme SHALL charger Alpine.js 3.x dans base.html de sorte que tout template enfant puisse utiliser les directives `x-data`, `x-show`, `x-on` sans configuration supplementaire.

#### Scenario: Une directive Alpine.js fonctionne
- **WHEN** un template enfant utilise `x-data="{ open: false }"` et `x-show="open"`
- **THEN** l'element est masque par defaut et visible quand `open` passe a `true`
