## MODIFIED Requirements

### Requirement: Template base.html avec layout principal

Le systeme SHALL fournir un template `templates/base.html` avec : bloc `{% block title %}`, bloc `{% block content %}`, chargement de Tailwind CSS, HTMX 2.x et Alpine.js 3.x, barre de navigation avec le nom de l'utilisateur connecte et un bouton de deconnexion. La navigation SHALL inclure des liens vers le tableau de bord (`/bdc/`) et l'upload PDF (`/bdc/upload/`) pour les utilisateurs du groupe Secrétaire.

#### Scenario: Le template de base charge les dependances frontend
- **WHEN** une page utilisant base.html est rendue
- **THEN** le HTML contient les balises script pour HTMX et Alpine.js, et le lien vers le CSS Tailwind

#### Scenario: La navigation affiche le nom de l'utilisateur
- **WHEN** un utilisateur authentifie consulte une page
- **THEN** la barre de navigation affiche son nom et un lien de deconnexion

#### Scenario: Les blocs sont extensibles
- **WHEN** un template enfant definit `{% block content %}Mon contenu{% endblock %}`
- **THEN** "Mon contenu" apparait dans la zone de contenu principal

#### Scenario: La navigation affiche les liens principaux
- **WHEN** un utilisateur authentifié consulte une page
- **THEN** la barre de navigation contient un lien "Tableau de bord" pointant vers `/bdc/` et un lien "Upload PDF" pointant vers `/bdc/upload/`
