## Context

L'application Isma a 12 templates Django avec des classes Tailwind utilitaires mais le CSS n'est pas compilé (output.css = 10 lignes de reset). HTMX et Alpine.js sont chargés via CDN dans base.html mais quasi-inutilisés. L'identité visuelle "Clean Industrial" a été définie : bleu pétrole + ambre chantier, Plus Jakarta Sans, sidebar nav, dark/light mode.

## Goals / Non-Goals

**Goals:**
- Interface production-grade avec identité visuelle "Clean Industrial" cohérente
- Dark mode et light mode avec toggle persisté
- Sidebar navigation collapsible remplaçant la top nav
- Tailwind CSS compilé avec config custom
- Widgets Django stylisés uniformément
- Filtres HTMX instantanés sur le dashboard
- Upload PDF en drag-and-drop
- Micro-animations CSS pour les transitions et hover states

**Non-Goals:**
- Migration vers React/Vue — on reste en Django templates
- Refonte du backend ou des vues (modifications minimales côté Python)
- Responsive mobile complet (desktop-first, responsive basique acceptable)
- Système de composants réutilisables type design system library

## Decisions

### D1 — Tailwind CSS via CDN Play (pas de build pipeline)

**Choix :** Utiliser le CDN Tailwind Play (`<script src="https://cdn.tailwindcss.com">`) avec une config inline plutôt qu'un build pipeline CLI.

**Alternatives considérées :**
- Tailwind CLI standalone : nécessite un process de build, complexité d'install sur Windows
- PostCSS pipeline : encore plus complexe, overkill pour du Django templates

**Raison :** Le CDN Play supporte la config custom (couleurs, fonts), le dark mode, et les classes arbitraires. Zéro setup, fonctionne immédiatement. En production on pourra migrer vers le CLI pour optimiser la taille du CSS.

### D2 — Layout sidebar avec Alpine.js

**Choix :** Sidebar gérée par Alpine.js (état collapsed/expanded stocké en localStorage). La sidebar se réduit en icônes seulement sur clic, pas sur breakpoint.

**Alternatives considérées :**
- CSS-only sidebar : limité pour la persistance d'état
- HTMX pour la sidebar : overkill, pas de requête serveur nécessaire

**Raison :** Alpine.js est déjà chargé et parfait pour ce type d'interactivité locale.

### D3 — Dark mode via classe CSS + localStorage

**Choix :** Dark mode via la classe `dark` sur `<html>` (Tailwind darkMode: 'class'). Toggle géré par Alpine.js, état persisté en localStorage.

**Raison :** Approche standard Tailwind, pas de flash de thème au chargement (script inline dans `<head>` applique la classe avant le rendu).

### D4 — Filtres HTMX avec partial template

**Choix :** Le formulaire de filtres sur le dashboard envoie des requêtes GET via `hx-get` + `hx-target` pour remplacer uniquement le tableau et les compteurs. La vue Django détecte `request.headers.get("HX-Request")` et renvoie un partial (fragment HTML sans le layout).

**Alternatives considérées :**
- Full page reload (actuel) : fonctionnel mais lent
- JavaScript fetch custom : réinvente la roue, HTMX fait ça nativement

**Raison :** HTMX est déjà chargé. Le pattern partial template est standard en Django+HTMX.

### D5 — Fonts via Google Fonts CDN

**Choix :** Plus Jakarta Sans (headings + body) et JetBrains Mono (données chiffrées) chargées via Google Fonts `<link>` dans `<head>`.

**Raison :** Zéro setup, cache CDN performant, fonts gratuites.

### D6 — Upload drag-and-drop via Alpine.js

**Choix :** La zone d'upload utilise Alpine.js pour gérer les événements dragover/drop/dragleave et afficher un état visuel. Le fichier est toujours soumis via le formulaire HTML standard (pas d'upload AJAX).

**Raison :** Simple, progressif (fonctionne sans JS), pas besoin de feedback de progression côté serveur pour un seul fichier PDF.

## Risks / Trade-offs

- **CDN Tailwind en production** → Le CDN Play n'est pas recommandé en production (poids, parsing runtime). Mitigation : migrer vers Tailwind CLI quand l'app sera déployée. Le CDN est parfait pour la phase de test/dev actuelle.
- **Pas de build pipeline** → On ne peut pas purger les classes inutilisées. Mitigation : acceptable pour le MVP, le CDN charge tout Tailwind (~300KB gzipped).
- **HTMX partial templates** → Nécessite de maintenir un partial en plus du template complet. Mitigation : utiliser un seul template avec `{% if request.htmx %}` pour conditionner le layout.
