## Context

Actuellement, la "Vue sous-traitant" et la piece jointe email utilisent le PDF original du bailleur avec un systeme de masquage (zones blanches sur les prix) et filtrage de pages. Ce systeme est fragile : erreurs 500 frequentes, config specifique par bailleur, et certains PDFs n'ont pas de page terrain exploitable.

Les donnees necessaires (adresse, occupant, prestations, commentaire CDT) sont deja extraites et stockees en base.

## Goals / Non-Goals

**Goals:**
- Generer une fiche chantier PDF propre a partir des donnees en base
- Utiliser cette fiche comme preview "Vue ST" et comme piece jointe email
- Supprimer le systeme de masquage PDF (masquage_pdf.py)
- Fonctionner de facon identique pour tous les bailleurs

**Non-Goals:**
- Supprimer les champs `zones_masquage` et `pages_a_envoyer` du modele Bailleur (cleanup ulterieur)
- Personnaliser le template de fiche par bailleur
- Generer des fiches pour les BDC non attribues

## Decisions

### 1. Generation PDF : template Django HTML + WeasyPrint

**Choix** : Template HTML Django rendu en PDF via WeasyPrint.

**Alternatives considerees** :
- ReportLab : verbose, bas niveau, difficile a maintenir
- PyMuPDF (fitz) : deja utilise mais pour la manipulation, pas la generation
- xhtml2pdf : moins fiable que WeasyPrint, rendu CSS limite

**Rationale** : WeasyPrint utilise le meme systeme de templates Django que le reste de l'app. Le CDT peut voir un apercu HTML avant conversion PDF. Facile a modifier le layout.

### 2. Emplacement du template

`templates/bdc/fiche_chantier_st.html` — un seul template pour tous les bailleurs.

### 3. Service de generation

`apps/bdc/fiche_chantier.py` avec une fonction `generer_fiche_chantier(bdc) -> bytes` qui :
1. Rend le template HTML avec le contexte du BDC
2. Convertit en PDF via WeasyPrint
3. Retourne les bytes du PDF

### 4. Integration dans le workflow

- **Vue ST** : la vue `pdf_masque_preview` est remplacee. Meme URL (`/<pk>/pdf-st/`), mais sert la fiche generee.
- **Email** : `_obtenir_pdf_masque()` dans `apps/notifications/email.py` est remplacee par un appel a `generer_fiche_chantier()`.

## Risks / Trade-offs

- [WeasyPrint est lourd] → Deja des deps lourdes (PyMuPDF, pdfplumber). WeasyPrint ajoute ~30MB mais c'est acceptable en Docker.
- [Premiere generation lente] → WeasyPrint a un cold start. Acceptable pour une operation ponctuelle (attribution).
- [Perte du PDF bailleur original en piece jointe] → Le ST recoit une fiche plus claire et complete. Le PDF original reste accessible dans l'app.
