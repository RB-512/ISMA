## Why

L'application Isma dispose de 12 templates Django fonctionnels mais le CSS Tailwind n'est pas compilé — l'interface est visuellement non stylée. Les templates utilisent des classes Tailwind utilitaires empilées sans direction de design cohérente, sans identité visuelle, et sans les interactions modernes attendues (dark mode, filtres instantanés, animations). Avant de mettre l'application en test utilisateur, il faut un frontend production-grade avec une identité "Clean Industrial" propre au contexte BTP.

## What Changes

- Remplacement du `base.html` : passage d'une top nav à une sidebar collapsible, intégration du toggle dark/light, recherche globale
- Compilation Tailwind CSS avec config custom (palette Isma, typo Plus Jakarta Sans + JetBrains Mono)
- Refonte visuelle de tous les templates existants (12 fichiers) avec la nouvelle identité
- Ajout du dark mode (CSS variables + toggle persisté en localStorage)
- Stylisation des widgets Django (select, input, textarea) via classes Tailwind cohérentes
- Ajout de micro-animations CSS (transitions hover, badges statut animés, slide-in)
- Intégration HTMX pour les filtres instantanés sur le dashboard (déjà chargé, jamais utilisé)
- Zone drag-and-drop sur la page upload PDF
- Pages d'erreur 404/500 stylisées

## Capabilities

### New Capabilities
- `design-system-isma`: Système de design (palette, typo, composants de base, dark mode, CSS variables) et layout sidebar
- `upload-drag-drop`: Zone de drag-and-drop pour l'upload PDF avec preview et progression
- `filtres-htmx`: Filtrage instantané HTMX sans rechargement de page sur le dashboard

### Modified Capabilities
- `base-template-ui`: Refonte complète du layout (sidebar), intégration dark mode, nouveau système typographique
- `dashboard-liste-bdc`: Refonte visuelle des compteurs, alertes, tableau — filtres HTMX instantanés
- `formulaire-creation-bdc`: Restyling complet des widgets de formulaire avec la nouvelle identité
- `fiche-detail-bdc`: Refonte visuelle des cards, actions, historique avec micro-animations

## Impact

- **Templates** : 12 fichiers HTML modifiés + 2 nouveaux (404.html, 500.html)
- **CSS** : Nouveau `tailwind.config.js`, `input.css` revu avec CSS variables, `output.css` compilé
- **JS** : Pas de nouveau framework — Alpine.js (existant) + HTMX (existant) suffisent
- **Vues Django** : Modification mineure de `liste_bdc` pour supporter les requêtes HTMX (partial rendering)
- **Dépendances** : Aucune nouvelle dépendance Python. Tailwind CLI standalone pour le build CSS.
- **Static** : Ajout des fonts (Google Fonts CDN) et éventuellement un favicon/logo SVG
