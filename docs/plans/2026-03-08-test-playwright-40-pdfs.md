# Test Playwright 40 PDFs — Plan d'implémentation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Script Playwright Python autonome qui teste le workflow complet (Upload → Extraction → Enregistrement → Contrôle → Attribution) pour 40 PDFs de test, puis génère un rapport.

**Architecture:** Script standalone utilisant Playwright sync API. Se connecte au serveur Django local (127.0.0.1:8000), purge les BDC existants via manage.py, puis boucle sur chaque PDF. Le rapport est affiché en console et sauvegardé en fichier.

**Tech Stack:** Python 3.12, Playwright (sync API), subprocess (pour manage.py shell)

---

### Task 1 : Installer Playwright

**Step 1 : Ajouter playwright aux dépendances dev**

```bash
cd bdc-peinture && uv add --dev playwright
```

**Step 2 : Installer les navigateurs Chromium**

```bash
cd bdc-peinture && uv run playwright install chromium
```

**Step 3 : Vérifier l'installation**

```bash
cd bdc-peinture && uv run python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

Expected: `OK`

---

### Task 2 : Créer le script — structure et purge

**Files:**
- Create: `bdc-peinture/tests/test_e2e_upload_40_pdfs.py`

**Step 1 : Créer le squelette du script**

```python
"""
Test E2E : Upload et traitement de 40 PDFs via Playwright.

Usage:
    cd bdc-peinture
    uv run python tests/test_e2e_upload_40_pdfs.py

Pré-requis:
    - Serveur Django lancé sur http://127.0.0.1:8000
    - Utilisateur connecté dans le navigateur OU credentials configurés ci-dessous
"""

import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, expect

# ─── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "http://127.0.0.1:8000"
PDF_DIR = Path(__file__).resolve().parent.parent / "docs" / "test_pdfs"
MANAGE_PY = Path(__file__).resolve().parent.parent / "manage.py"

# Credentials (django-allauth login par email)
LOGIN_EMAIL = "secretaire@test.fr"
LOGIN_PASSWORD = "testpass123"

# Données variables pour le contrôle
OCCUPATIONS = ["VACANT", "OCCUPE"]
TYPES_ACCES = ["BADGE_CODE", "CLE"]
POURCENTAGES = [60, 70, 80, 90, 100]

# ─── Rapport ────────────────────────────────────────────────────────────────

class Resultat:
    def __init__(self, fichier: str):
        self.fichier = fichier
        self.bailleur = ""
        self.numero_bdc = ""
        self.extraction_ok = False
        self.champs_manquants: list[str] = []
        self.enregistrement_ok = False
        self.controle_ok = False
        self.attribution_ok = False
        self.erreurs: list[str] = []
        self.screenshot: str = ""

    @property
    def statut_global(self) -> str:
        if all([self.extraction_ok, self.enregistrement_ok,
                self.controle_ok, self.attribution_ok]):
            return "✅"
        if any([self.extraction_ok, self.enregistrement_ok]):
            return "⚠️"
        return "❌"


def purger_bdc():
    """Supprime tous les BDC existants via manage.py shell."""
    cmd = [
        sys.executable, str(MANAGE_PY), "shell", "-c",
        (
            "from apps.bdc.models import BonDeCommande, HistoriqueAction, "
            "LignePrestation, ChecklistResultat; "
            "ChecklistResultat.objects.all().delete(); "
            "HistoriqueAction.objects.all().delete(); "
            "LignePrestation.objects.all().delete(); "
            "n, _ = BonDeCommande.objects.all().delete(); "
            "print(f'{n} BDC supprimés')"
        ),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(MANAGE_PY.parent))
    print(f"[PURGE] {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"[PURGE ERREUR] {result.stderr.strip()}")
        sys.exit(1)
```

**Step 2 : Vérifier que le script s'importe**

```bash
cd bdc-peinture && uv run python -c "import tests.test_e2e_upload_40_pdfs; print('OK')"
```

---

### Task 3 : Login et fonctions d'upload

**Files:**
- Modify: `bdc-peinture/tests/test_e2e_upload_40_pdfs.py`

**Step 1 : Ajouter la fonction login**

```python
def login(page: Page):
    """Se connecte via django-allauth (login par email)."""
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="login"]', LOGIN_EMAIL)
    page.fill('input[name="password"]', LOGIN_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/**")
    print("[LOGIN] Connecté")
```

**Step 2 : Ajouter la fonction upload_pdf**

```python
def upload_pdf(page: Page, pdf_path: Path, resultat: Resultat) -> bool:
    """Upload un PDF et vérifie l'extraction. Retourne True si succès."""
    try:
        page.goto(f"{BASE_URL}/upload/")
        page.wait_for_selector('#id_pdf_file')

        # Upload du fichier
        page.set_input_files('#id_pdf_file', str(pdf_path))

        # Cliquer "Analyser le PDF"
        page.click('button[type="submit"]')

        # Attendre la page de confirmation ou une erreur
        page.wait_for_load_state("networkidle", timeout=15000)

        # Vérifier si on est sur /nouveau/ (succès) ou toujours sur /upload/ (erreur)
        if "/nouveau/" not in page.url and "/nouveau" not in page.url:
            # Chercher un message d'erreur
            erreur = page.query_selector(".text-red-500, .alert-danger, .errorlist")
            msg = erreur.inner_text() if erreur else "Extraction échouée (pas de redirection)"
            resultat.erreurs.append(f"Upload: {msg}")
            return False

        return True

    except Exception as e:
        resultat.erreurs.append(f"Upload: {e}")
        return False
```

---

### Task 4 : Vérification extraction et enregistrement

**Files:**
- Modify: `bdc-peinture/tests/test_e2e_upload_40_pdfs.py`

**Step 1 : Ajouter la fonction verifier_extraction**

```python
def verifier_extraction(page: Page, resultat: Resultat):
    """Vérifie les champs extraits sur la page /nouveau/."""
    # Les champs sont affichés dans des <dd> à côté de <dt>
    champs_a_verifier = {
        "Numéro BDC": "numero_bdc",
        "Bailleur": "bailleur",
        "Adresse": "adresse",
        "Objet des travaux": "objet_travaux",
    }

    page_text = page.inner_text("body")

    # Extraire le numéro BDC depuis la page
    # Chercher dans les <dd> ou le texte affiché
    for label, attr in champs_a_verifier.items():
        # Chercher un <dt> contenant le label suivi d'un <dd> non vide
        dt = page.query_selector(f"dt:has-text('{label}')")
        if dt:
            dd = dt.evaluate_handle("el => el.nextElementSibling")
            if dd:
                valeur = dd.evaluate("el => el.textContent.trim()")
                if not valeur or valeur == "-" or valeur == "—":
                    resultat.champs_manquants.append(label)
        else:
            # Essayer de trouver le texte directement
            if label.lower() not in page_text.lower():
                resultat.champs_manquants.append(label)

    # Vérifier les lignes de prestation (tableau)
    lignes = page.query_selector_all("table tbody tr")
    if not lignes:
        resultat.champs_manquants.append("Lignes de prestation")

    resultat.extraction_ok = len(resultat.champs_manquants) == 0
```

**Step 2 : Ajouter la fonction enregistrer_bdc**

```python
def enregistrer_bdc(page: Page, resultat: Resultat) -> int | None:
    """Clique 'Enregistrer le BDC'. Retourne le pk du BDC créé."""
    try:
        # Cliquer le bouton d'enregistrement
        page.click('button[type="submit"]:has-text("Enregistrer")')
        page.wait_for_load_state("networkidle", timeout=10000)

        # Vérifier qu'on n'est plus sur /nouveau/
        if "/nouveau" in page.url:
            erreur = page.query_selector(".text-red-500, .alert-danger, .errorlist")
            msg = erreur.inner_text() if erreur else "Enregistrement échoué"
            resultat.erreurs.append(f"Enregistrement: {msg}")
            return None

        # Extraire le pk depuis l'URL (ex: /42/ ou /42/controle/)
        import re
        match = re.search(r"/(\d+)/", page.url)
        if match:
            pk = int(match.group(1))
            resultat.enregistrement_ok = True
            return pk

        resultat.enregistrement_ok = True
        return None

    except Exception as e:
        resultat.erreurs.append(f"Enregistrement: {e}")
        return None
```

---

### Task 5 : Contrôle (occupation, accès, checklist)

**Files:**
- Modify: `bdc-peinture/tests/test_e2e_upload_40_pdfs.py`

**Step 1 : Ajouter la fonction controler_bdc**

```python
def controler_bdc(page: Page, pk: int, index: int, resultat: Resultat) -> bool:
    """Remplit le formulaire de contrôle et passe en 'À attribuer'."""
    try:
        page.goto(f"{BASE_URL}/{pk}/controle/")
        page.wait_for_load_state("networkidle", timeout=10000)

        # Vérifier qu'on est bien sur la page de contrôle
        if "/controle" not in page.url:
            resultat.erreurs.append("Contrôle: page non accessible")
            return False

        # Alterner Vacant / Occupé
        occupation = OCCUPATIONS[index % 2]
        page.select_option('#id_occupation', occupation)

        # Attendre que Alpine.js affiche les champs conditionnels
        time.sleep(0.5)

        if occupation == "VACANT":
            type_acces = TYPES_ACCES[index % 2]
            page.select_option('#id_type_acces', type_acces)
            time.sleep(0.3)
            # Remplir le complément d'accès
            complement = page.query_selector('#id_acces_complement')
            if complement:
                complement.fill("Code 1234" if type_acces == "BADGE_CODE" else "Chez gardien")
        else:
            # Remplir date de RDV (demain 10h)
            demain = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00")
            rdv_input = page.query_selector('#id_rdv_date')
            if rdv_input:
                rdv_input.fill(demain)

        # Cocher toutes les cases de la checklist
        checkboxes = page.query_selector_all('input[type="checkbox"][name^="check_"]')
        for cb in checkboxes:
            if not cb.is_checked():
                cb.check()

        # Cliquer "Valider → À attribuer"
        # Ce bouton met le hidden input nouveau_statut = A_FAIRE
        btn_valider = page.query_selector('button:has-text("Valider")')
        if btn_valider:
            btn_valider.click()
        else:
            resultat.erreurs.append("Contrôle: bouton Valider non trouvé")
            return False

        page.wait_for_load_state("networkidle", timeout=10000)

        # Vérifier que la transition a fonctionné (pas d'erreur)
        if "/controle" in page.url:
            erreur = page.query_selector(".text-red-500, .alert-danger, .errorlist")
            if erreur:
                msg = erreur.inner_text()
                resultat.erreurs.append(f"Contrôle: {msg}")
                return False

        resultat.controle_ok = True
        return True

    except Exception as e:
        resultat.erreurs.append(f"Contrôle: {e}")
        return False
```

---

### Task 6 : Attribution sous-traitant

**Files:**
- Modify: `bdc-peinture/tests/test_e2e_upload_40_pdfs.py`

**Step 1 : Ajouter la fonction attribuer_bdc**

```python
def attribuer_bdc(page: Page, pk: int, index: int, resultat: Resultat) -> bool:
    """Attribue un sous-traitant au BDC."""
    try:
        page.goto(f"{BASE_URL}/{pk}/attribuer/")
        page.wait_for_load_state("networkidle", timeout=10000)

        # Sélectionner le premier sous-traitant disponible
        select_st = page.query_selector('#id_sous_traitant')
        if not select_st:
            resultat.erreurs.append("Attribution: dropdown sous-traitant non trouvé")
            return False

        # Prendre la première option non vide
        options = page.query_selector_all('#id_sous_traitant option')
        first_value = None
        for opt in options:
            val = opt.get_attribute("value")
            if val:
                first_value = val
                break

        if not first_value:
            resultat.erreurs.append("Attribution: aucun sous-traitant disponible")
            return False

        page.select_option('#id_sous_traitant', first_value)

        # Pourcentage variable
        pourcentage = POURCENTAGES[index % len(POURCENTAGES)]
        page.fill('#id_pourcentage_st', str(pourcentage))

        # Cocher toutes les cases de la checklist d'attribution
        checkboxes = page.query_selector_all('input[type="checkbox"].checklist-cb')
        for cb in checkboxes:
            if not cb.is_checked():
                cb.check()

        # Petite pause pour Alpine.js (allChecked)
        time.sleep(0.3)

        # Cliquer "Attribuer"
        btn = page.query_selector('button[type="submit"]:has-text("Attribuer")')
        if btn:
            btn.click()
        else:
            resultat.erreurs.append("Attribution: bouton Attribuer non trouvé")
            return False

        page.wait_for_load_state("networkidle", timeout=10000)

        # Vérifier succès (redirection vers detail)
        if "/attribuer" in page.url:
            erreur = page.query_selector(".text-red-500, .alert-danger, .errorlist")
            if erreur:
                msg = erreur.inner_text()
                resultat.erreurs.append(f"Attribution: {msg}")
                return False

        resultat.attribution_ok = True
        return True

    except Exception as e:
        resultat.erreurs.append(f"Attribution: {e}")
        return False
```

---

### Task 7 : Fonction main et génération du rapport

**Files:**
- Modify: `bdc-peinture/tests/test_e2e_upload_40_pdfs.py`

**Step 1 : Ajouter la génération de rapport**

```python
def generer_rapport(resultats: list[Resultat]):
    """Affiche et sauvegarde le rapport de test."""
    # En-tête
    print("\n" + "=" * 120)
    print("RAPPORT DE TEST — Upload 40 PDFs")
    print("=" * 120)

    # Tableau
    header = f"{'#':>3} | {'Fichier':<35} | {'Bailleur':<8} | {'Extraction':<10} | {'Enregistr.':<10} | {'Contrôle':<10} | {'Attrib.':<10} | {'Erreurs'}"
    print(header)
    print("-" * 120)

    for i, r in enumerate(resultats, 1):
        ext = "✅" if r.extraction_ok else "❌"
        enr = "✅" if r.enregistrement_ok else "❌"
        ctrl = "✅" if r.controle_ok else "❌"
        attr = "✅" if r.attribution_ok else "❌"
        champs = f" (manquants: {', '.join(r.champs_manquants)})" if r.champs_manquants else ""
        erreurs = " | ".join(r.erreurs) if r.erreurs else "-"
        print(f"{i:>3} | {r.fichier:<35} | {r.bailleur:<8} | {ext:<10} | {enr:<10} | {ctrl:<10} | {attr:<10} | {erreurs}{champs}")

    # Synthèse
    total = len(resultats)
    ok = sum(1 for r in resultats if r.statut_global == "✅")
    partiel = sum(1 for r in resultats if r.statut_global == "⚠️")
    ko = sum(1 for r in resultats if r.statut_global == "❌")

    print("\n" + "=" * 120)
    print(f"SYNTHÈSE : {ok}/{total} OK | {partiel} partiels | {ko} en échec")
    print("=" * 120)

    # Problèmes récurrents
    from collections import Counter
    tous_champs_manquants = Counter()
    for r in resultats:
        for c in r.champs_manquants:
            tous_champs_manquants[c] += 1

    if tous_champs_manquants:
        print("\nChamps souvent manquants :")
        for champ, count in tous_champs_manquants.most_common():
            print(f"  - {champ} : {count}/{total}")

    toutes_erreurs = []
    for r in resultats:
        for e in r.erreurs:
            toutes_erreurs.append(f"  [{r.fichier}] {e}")
    if toutes_erreurs:
        print(f"\nErreurs détaillées ({len(toutes_erreurs)}) :")
        for e in toutes_erreurs:
            print(e)

    # Sauvegarde fichier
    rapport_path = Path(__file__).resolve().parent.parent / "docs" / f"rapport_test_{datetime.now():%Y%m%d_%H%M}.txt"
    with open(rapport_path, "w", encoding="utf-8") as f:
        f.write(f"Rapport de test — {datetime.now():%Y-%m-%d %H:%M}\n")
        f.write(f"Résultat : {ok}/{total} OK | {partiel} partiels | {ko} en échec\n\n")
        for i, r in enumerate(resultats, 1):
            f.write(f"{i}. {r.fichier} [{r.statut_global}]\n")
            if r.champs_manquants:
                f.write(f"   Champs manquants: {', '.join(r.champs_manquants)}\n")
            if r.erreurs:
                for e in r.erreurs:
                    f.write(f"   ERREUR: {e}\n")
    print(f"\nRapport sauvegardé : {rapport_path}")
```

**Step 2 : Ajouter la fonction main**

```python
def main():
    # 1. Lister les PDFs
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[ERREUR] Aucun PDF trouvé dans {PDF_DIR}")
        sys.exit(1)
    print(f"[INFO] {len(pdfs)} PDFs trouvés")

    # Trier : GDH d'abord, puis ERILIA
    pdfs_gdh = [p for p in pdfs if p.name.startswith("GDH")]
    pdfs_erilia = [p for p in pdfs if p.name.startswith("ERILIA")]
    pdfs = pdfs_gdh + pdfs_erilia
    print(f"[INFO] {len(pdfs_gdh)} GDH + {len(pdfs_erilia)} ERILIA")

    # 2. Purger les BDC existants
    purger_bdc()

    # 3. Lancer Playwright
    resultats: list[Resultat] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 4. Login
        login(page)

        # 5. Boucle sur chaque PDF
        for i, pdf_path in enumerate(pdfs):
            print(f"\n[{i+1}/{len(pdfs)}] {pdf_path.name}")
            resultat = Resultat(pdf_path.name)
            resultat.bailleur = "GDH" if pdf_path.name.startswith("GDH") else "ERILIA"

            # Upload
            ok = upload_pdf(page, pdf_path, resultat)
            if not ok:
                print(f"  ❌ Upload échoué")
                resultats.append(resultat)
                continue

            # Vérifier extraction
            verifier_extraction(page, resultat)
            if resultat.extraction_ok:
                print(f"  ✅ Extraction OK")
            else:
                print(f"  ⚠️ Extraction partielle: manque {resultat.champs_manquants}")

            # Enregistrer
            pk = enregistrer_bdc(page, resultat)
            if not pk:
                print(f"  ❌ Enregistrement échoué")
                resultats.append(resultat)
                continue
            print(f"  ✅ Enregistré (pk={pk})")

            # Contrôle
            ok = controler_bdc(page, pk, i, resultat)
            if not ok:
                print(f"  ❌ Contrôle échoué")
                resultats.append(resultat)
                continue
            print(f"  ✅ Contrôle OK → À attribuer")

            # Attribution
            ok = attribuer_bdc(page, pk, i, resultat)
            if ok:
                print(f"  ✅ Attribution OK (ST, {POURCENTAGES[i % len(POURCENTAGES)]}%)")
            else:
                print(f"  ❌ Attribution échouée")

            resultats.append(resultat)

        browser.close()

    # 6. Rapport
    generer_rapport(resultats)


if __name__ == "__main__":
    main()
```

---

### Task 8 : Test du script sur 2 PDFs

**Step 1 : S'assurer que le serveur tourne**

```bash
cd bdc-peinture && uv run manage.py runserver
```

(dans un autre terminal)

**Step 2 : Lancer le script sur 2 PDFs pour valider**

Modifier temporairement le `main()` pour ne prendre que les 2 premiers PDFs (ajouter `pdfs = pdfs[:2]` après le tri), puis :

```bash
cd bdc-peinture && uv run python tests/test_e2e_upload_40_pdfs.py
```

Expected: Le navigateur s'ouvre, se connecte, uploade 2 PDFs, et affiche un mini-rapport.

**Step 3 : Retirer la limitation et lancer les 40**

Supprimer `pdfs = pdfs[:2]`, puis relancer.

**Step 4 : Commit**

```bash
git add bdc-peinture/tests/test_e2e_upload_40_pdfs.py
git commit -m "feat: script Playwright E2E pour tester upload de 40 PDFs"
```

---

## Notes importantes

- **Serveur Django** doit tourner sur `127.0.0.1:8000` avant de lancer le script
- **headless=False** pour voir le navigateur en action (changer en `True` pour CI)
- **Screenshots** : en cas d'erreur, le script pourrait être enrichi pour capturer des screenshots (page.screenshot())
- **Login** : utilise django-allauth, login par email. Adapter si les credentials de prod sont différents
- **Sous-traitant** : il faut qu'au moins un sous-traitant actif existe en base. S'il n'y en a pas, l'attribution échouera pour tous les PDFs
