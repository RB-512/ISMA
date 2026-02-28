## 1. Design System — Fondations

- [x] 1.1 Remplacer le `<head>` de `base.html` : CDN Tailwind Play avec config inline (palette Isma, fonts, darkMode: 'class'), Google Fonts (Plus Jakarta Sans + JetBrains Mono), script inline de détection dark mode depuis localStorage
- [x] 1.2 Ajouter les CSS custom properties (variables) dans `input.css` ou en `<style>` inline : palette light sur `:root`, palette dark sur `.dark`
- [x] 1.3 Styliser globalement les widgets Django (input, select, textarea, checkbox) via la config Tailwind ou un `<style>` global avec les classes du design system

## 2. Layout — Sidebar + Base

- [x] 2.1 Réécrire `base.html` : remplacer la top nav par une sidebar collapsible (Alpine.js, état persisté localStorage), zone contenu principale avec barre supérieure (recherche globale + user info)
- [x] 2.2 Ajouter le toggle dark/light dans la sidebar avec icône soleil/lune et transition
- [x] 2.3 Ajouter les liens de navigation sidebar : Tableau de bord, Upload PDF, Sous-traitants (tous), Recoupement et Export facturation (CDT only)
- [x] 2.4 Réécrire `accounts/login.html` : formulaire centré avec logo "ISMA", champs stylisés, bouton accent, fond design system

## 3. Dashboard — Liste BDC

- [x] 3.1 Réécrire `liste.html` : compteurs par statut avec cards colorées et icônes, alertes CDT (rouge/orange), tableau BDC avec font mono pour les numéros, pagination stylisée
- [x] 3.2 Extraire le fragment HTMX-swappable (compteurs + alertes + tableau + pagination) dans un partial `_liste_partial.html` ou via `{% if request.htmx %}`
- [x] 3.3 Ajouter les attributs HTMX sur le formulaire de filtres (`hx-get`, `hx-target`, `hx-push-url`, `hx-indicator`)
- [x] 3.4 Modifier la vue `liste_bdc` pour détecter `HX-Request` et renvoyer le partial sans le layout base.html

## 4. Upload PDF — Drag-and-drop

- [x] 4.1 Réécrire `upload.html` : zone de drag-and-drop Alpine.js (dragover/drop/dragleave), affichage du nom de fichier sélectionné, bouton de soumission, fallback input file standard

## 5. Formulaire création BDC

- [x] 5.1 Réécrire `creer_bdc.html` : sections avec cards design system, widgets stylisés (bordures arrondies, focus ring accent, labels clairs), tableau des lignes de prestation avec font mono, support dark mode

## 6. Fiche détail BDC

- [x] 6.1 Réécrire `detail.html` : cards design system pour chaque section (Localisation, Travaux, Contacts, Prestations, Historique), boutons d'action colorés, numéros en font mono, support dark mode
- [x] 6.2 Réécrire `attribuer.html` : formulaire attribution/réattribution avec cards et widgets design system

## 7. Pages secondaires

- [x] 7.1 Réécrire `recoupement_liste.html` et `recoupement_detail.html` : tableaux avec design system, badges statut, font mono pour les compteurs
- [x] 7.2 Réécrire `export_facturation.html` : formulaire filtres et bouton export avec design system
- [x] 7.3 Réécrire `sous_traitants/list.html` : tableau avec design system
- [x] 7.4 Créer `templates/404.html` et `templates/500.html` : pages d'erreur stylisées avec logo Isma et lien retour dashboard

## 8. Validation

- [x] 8.1 Lancer `pytest` — tous les tests existants passent (286 tests, pas de régression UI)
- [x] 8.2 Lancer `ruff check` — pas de lint
- [x] 8.3 Vérifier visuellement le rendu light + dark sur les pages principales (dashboard, détail, login)
