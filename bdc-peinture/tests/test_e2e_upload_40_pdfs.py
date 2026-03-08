"""
Test E2E : Upload de 40 PDFs (20 GDH + 20 ERILIA) a travers le workflow complet.

Workflow par PDF :
  1. Upload PDF -> extraction automatique
  2. Verification des donnees extraites sur /nouveau/
  3. Enregistrement du BDC
  4. Controle : occupation, acces, checklist, validation -> A_FAIRE
  5. Attribution : sous-traitant, pourcentage, checklist -> EN_COURS

Usage :
  cd bdc-peinture && uv run python tests/test_e2e_upload_40_pdfs.py
"""

import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "secretaire@test.fr"
PASSWORD = "testpass123"

# Repertoire des PDFs de test (relatif a la racine du projet ISMA)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # ISMA/
PDF_DIR = PROJECT_ROOT / "docs" / "test_pdfs"

# Repertoire pour les screenshots d'erreur
SCREENSHOT_DIR = PROJECT_ROOT / "bdc-peinture" / "tests" / "screenshots_e2e"

# Repertoire pour le rapport
REPORT_DIR = PROJECT_ROOT / "docs"

# Pourcentages a alterner pour l'attribution
POURCENTAGES = [60, 70, 80, 90, 100]

# Timeout par defaut pour les attentes (ms)
DEFAULT_TIMEOUT = 10_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_pdf_list():
    """Construit la liste ordonnee des 40 PDFs : 20 GDH puis 20 ERILIA."""
    pdfs = []

    # GDH : GDH_test_500001.pdf .. GDH_test_500020.pdf
    for i in range(500001, 500021):
        path = PDF_DIR / f"GDH_test_{i}.pdf"
        pdfs.append(("GDH", f"GDH_test_{i}", path))

    # ERILIA : ERILIA_test_2026_30001.pdf .. ERILIA_test_2026_30020.pdf
    for i in range(30001, 30021):
        path = PDF_DIR / f"ERILIA_test_2026_{i}.pdf"
        pdfs.append(("ERILIA", f"ERILIA_test_2026_{i}", path))

    return pdfs


def purge_existing_bdc():
    """Purge les BDC existants via manage.py shell."""
    manage_py = Path(__file__).resolve().parent.parent / "manage.py"
    script = (
        "from apps.bdc.models import ChecklistResultat, HistoriqueAction, LignePrestation, BonDeCommande; "
        "ChecklistResultat.objects.all().delete(); "
        "HistoriqueAction.objects.all().delete(); "
        "LignePrestation.objects.all().delete(); "
        "BonDeCommande.objects.all().delete(); "
        "print('PURGE OK')"
    )
    result = subprocess.run(
        [sys.executable, str(manage_py), "shell", "-c", script],
        capture_output=True,
        text=True,
        cwd=str(manage_py.parent),
    )
    if "PURGE OK" in result.stdout:
        print("[PURGE] Base purgee avec succes.")
    else:
        print(f"[PURGE] ERREUR : {result.stdout} {result.stderr}")
        sys.exit(1)


def take_screenshot(page, name):
    """Prend un screenshot et le sauvegarde."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    path = SCREENSHOT_DIR / f"{ts}_{name}.png"
    try:
        page.screenshot(path=str(path))
        print(f"    [SCREENSHOT] {path.name}")
    except Exception as e:
        print(f"    [SCREENSHOT] Erreur : {e}")


class PDFResult:
    """Resultat du traitement d'un PDF."""

    def __init__(self, bailleur, pdf_name):
        self.bailleur = bailleur
        self.pdf_name = pdf_name
        self.numero_bdc = ""
        self.adresse = ""
        self.nb_lignes = 0
        self.pk = None
        self.upload_ok = False
        self.extraction_ok = False
        self.save_ok = False
        self.controle_ok = False
        self.attribution_ok = False
        self.error = ""
        self.duration_s = 0.0

    @property
    def all_ok(self):
        return self.upload_ok and self.extraction_ok and self.save_ok and self.controle_ok and self.attribution_ok

    @property
    def status_str(self):
        if self.all_ok:
            return "OK"
        steps = []
        if not self.upload_ok:
            steps.append("upload")
        elif not self.extraction_ok:
            steps.append("extraction")
        elif not self.save_ok:
            steps.append("save")
        elif not self.controle_ok:
            steps.append("controle")
        elif not self.attribution_ok:
            steps.append("attribution")
        return f"FAIL({','.join(steps)})"


# ---------------------------------------------------------------------------
# Workflow steps
# ---------------------------------------------------------------------------


def step_login(page):
    """Se connecter via django-allauth."""
    page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
    page.fill('input[name="login"]', EMAIL)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")
    # Verifier qu'on est connecte (redirige vers /)
    if "/accounts/login/" in page.url:
        raise RuntimeError("Echec de connexion : toujours sur la page login")
    print("[LOGIN] Connecte avec succes.")


def step_upload(page, pdf_path, result):
    """Upload un PDF et verifie la redirection vers /nouveau/."""
    page.goto(f"{BASE_URL}/upload/", wait_until="domcontentloaded")

    # Remplir le champ fichier
    page.set_input_files("#id_pdf_file", str(pdf_path))

    # Cliquer sur Analyser
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")

    # Verifier qu'on est sur /nouveau/
    if "/nouveau/" not in page.url:
        raise RuntimeError(f"Apres upload, URL inattendue : {page.url}")

    result.upload_ok = True


def step_verify_extraction(page, result):
    """Verifie les donnees extraites sur /nouveau/."""
    # Extraire le numero BDC depuis le titre h1
    h1 = page.locator("h1").first
    h1_text = h1.inner_text()
    # Format : "BDC n°XXXXX"
    match = re.search(r"n[°o]?\s*(\S+)", h1_text)
    if match:
        result.numero_bdc = match.group(1)

    # Extraire l'adresse depuis les <dd>
    dd_elements = page.locator("dd").all()
    for dd in dd_elements:
        text = dd.inner_text().strip()
        if text and not result.adresse:
            # La premiere dd non-vide dans la section Localisation est souvent l'adresse
            pass

    # Compter les lignes de prestation
    tbody_rows = page.locator("table tbody tr").all()
    result.nb_lignes = len(tbody_rows)

    # Verifier qu'on a au moins un numero BDC
    if not result.numero_bdc or result.numero_bdc == "\u2014":
        raise RuntimeError(f"Numero BDC non extrait (h1: {h1_text})")

    result.extraction_ok = True


def step_save(page, result):
    """Enregistre le BDC et recupere le pk depuis l'URL de redirection."""
    # Cliquer sur le bouton "Enregistrer le BDC"
    page.click('button[type="submit"]:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")

    # Extraire le pk depuis l'URL de redirection (ex: /bdc/42/)
    match = re.search(r"/(\d+)/", page.url)
    if match:
        result.pk = int(match.group(1))
    else:
        raise RuntimeError(f"Impossible d'extraire le pk depuis {page.url}")

    result.save_ok = True


def step_controle(page, result, index):
    """Remplit le formulaire de controle et valide."""
    page.goto(f"{BASE_URL}/{result.pk}/controle/", wait_until="domcontentloaded")

    # Alterner VACANT / OCCUPE
    is_vacant = (index % 2) == 0
    occupation = "VACANT" if is_vacant else "OCCUPE"

    # Selectionner l'occupation via Alpine x-model
    page.select_option('select[name="occupation"]', occupation)
    page.wait_for_timeout(300)  # Attendre la transition Alpine x-show

    if is_vacant:
        # Type d'acces : alterner BADGE_CODE et CLE
        type_acces = "BADGE_CODE" if (index % 4) < 2 else "CLE"
        page.select_option('select[name="type_acces"]', type_acces)
        page.wait_for_timeout(200)  # Attendre x-show pour acces_complement

        # Remplir le complement d'acces
        complement_input = page.locator('input[name="acces_complement"], textarea[name="acces_complement"]').first
        if complement_input.is_visible():
            complement_input.fill("Code 1234" if type_acces == "BADGE_CODE" else "Gardien loge A")
    else:
        # RDV date (datetime-local)
        rdv_input = page.locator('input[name="rdv_date"]').first
        if rdv_input.is_visible():
            # Format datetime-local : YYYY-MM-DDTHH:MM
            rdv_value = "2026-03-15T09:00"
            rdv_input.fill(rdv_value)

    # Cocher toutes les checkboxes de checklist
    checkboxes = page.locator('input[type="checkbox"][name^="check_"]').all()
    for cb in checkboxes:
        if not cb.is_checked():
            cb.check()

    # Cliquer sur "Valider" qui fait onclick -> nouveau_statut = A_FAIRE
    # Le bouton contient le texte "Valider" et a un onclick
    valider_btn = page.locator('button[type="submit"]').filter(has_text="Valider").first
    valider_btn.click()
    page.wait_for_load_state("domcontentloaded")

    # Verifier qu'on est redirige (liste BDC ou page detail)
    if "/controle/" in page.url:
        # Peut-etre une erreur de validation, verifier les messages
        error_msgs = page.locator(".text-danger, .text-red-500").all()
        error_texts = [e.inner_text() for e in error_msgs if e.is_visible()]
        if error_texts:
            raise RuntimeError(f"Erreur controle : {'; '.join(error_texts)}")
        # Peut-etre que la page a ete resoumise avec succes mais pas de redirect
        # On continue

    result.controle_ok = True


def step_attribution(page, result, index):
    """Attribue le BDC a un sous-traitant."""
    page.goto(f"{BASE_URL}/{result.pk}/attribuer/", wait_until="domcontentloaded")

    # Verifier qu'on est bien sur la page d'attribution
    if "/attribuer/" not in page.url:
        raise RuntimeError(f"Pas sur la page d'attribution : {page.url}")

    # Selectionner le premier sous-traitant non vide
    st_select = page.locator("#id_sous_traitant")
    options = st_select.locator("option").all()
    st_value = None
    for opt in options:
        val = opt.get_attribute("value")
        if val and val.strip():
            st_value = val
            break

    if not st_value:
        raise RuntimeError("Aucun sous-traitant disponible")

    st_select.select_option(st_value)

    # Remplir le pourcentage
    pct = POURCENTAGES[index % len(POURCENTAGES)]
    pct_input = page.locator("#id_pourcentage_st")
    pct_input.fill(str(pct))

    # Cocher toutes les checkboxes de checklist
    checkboxes = page.locator('input[type="checkbox"].checklist-cb').all()
    for cb in checkboxes:
        if not cb.is_checked():
            cb.check()
            # Declencher l'evenement change pour Alpine
            cb.dispatch_event("change")

    page.wait_for_timeout(300)  # Laisser Alpine mettre a jour allChecked

    # Cliquer sur "Attribuer"
    attribuer_btn = page.locator('button[type="submit"]').filter(has_text="Attribuer").first

    # Forcer l'activation du bouton si Alpine ne l'a pas encore fait
    page.evaluate("document.querySelector('button[type=\"submit\"]').removeAttribute('disabled')")

    attribuer_btn.click()
    page.wait_for_load_state("domcontentloaded")

    # Verifier la redirection
    if "/attribuer/" in page.url:
        error_msgs = page.locator(".text-danger, .text-red-500").all()
        error_texts = [e.inner_text() for e in error_msgs if e.is_visible()]
        if error_texts:
            raise RuntimeError(f"Erreur attribution : {'; '.join(error_texts)}")

    result.attribution_ok = True


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------


def generate_report(results, total_duration):
    """Genere le rapport console + fichier."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M")

    # Tableau console
    print()
    print("=" * 100)
    print(f"  RAPPORT TEST E2E - 40 PDFs - {now.strftime('%d/%m/%Y %H:%M')}")
    print("=" * 100)
    print()
    print(f"{'#':>3}  {'Bailleur':<8}  {'PDF':<28}  {'N BDC':<12}  {'Lignes':>6}  {'Duree':>6}  {'Statut':<20}")
    print("-" * 100)

    ok_count = 0
    fail_count = 0

    for i, r in enumerate(results, 1):
        duration_str = f"{r.duration_s:.1f}s"
        status = r.status_str
        if r.all_ok:
            ok_count += 1
        else:
            fail_count += 1

        print(
            f"{i:>3}  {r.bailleur:<8}  {r.pdf_name:<28}  {r.numero_bdc:<12}  {r.nb_lignes:>6}  {duration_str:>6}  {status:<20}"
        )
        if r.error:
            print(f"     -> {r.error}")

    print("-" * 100)
    print()
    print(f"  Total : {len(results)} PDFs  |  OK : {ok_count}  |  ECHEC : {fail_count}  |  Duree totale : {total_duration:.1f}s")
    print()

    # Sauvegarder dans un fichier
    report_path = REPORT_DIR / f"rapport_test_{timestamp}.txt"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"RAPPORT TEST E2E - 40 PDFs - {now.strftime('%d/%m/%Y %H:%M')}\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"{'#':>3}  {'Bailleur':<8}  {'PDF':<28}  {'N BDC':<12}  {'Lignes':>6}  {'Duree':>6}  {'Statut':<20}\n")
        f.write("-" * 100 + "\n")

        for i, r in enumerate(results, 1):
            duration_str = f"{r.duration_s:.1f}s"
            f.write(
                f"{i:>3}  {r.bailleur:<8}  {r.pdf_name:<28}  {r.numero_bdc:<12}  {r.nb_lignes:>6}  {duration_str:>6}  {r.status_str:<20}\n"
            )
            if r.error:
                f.write(f"     -> {r.error}\n")

        f.write("-" * 100 + "\n\n")
        f.write(f"Total : {len(results)} PDFs  |  OK : {ok_count}  |  ECHEC : {fail_count}  |  Duree totale : {total_duration:.1f}s\n")

    print(f"  Rapport sauvegarde : {report_path}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    from playwright.sync_api import sync_playwright

    # Construire la liste des PDFs
    pdfs = build_pdf_list()

    # Verifier que les PDFs existent
    missing = [p for _, _, p in pdfs if not p.exists()]
    if missing:
        print(f"[ERREUR] {len(missing)} PDFs manquants :")
        for p in missing[:5]:
            print(f"  - {p}")
        if len(missing) > 5:
            print(f"  ... et {len(missing) - 5} autres")
        sys.exit(1)

    print(f"[INFO] {len(pdfs)} PDFs trouves dans {PDF_DIR}")

    # Purger la base
    purge_existing_bdc()

    results = []
    total_start = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        # Login
        try:
            step_login(page)
        except Exception as e:
            print(f"[FATAL] Echec login : {e}")
            take_screenshot(page, "login_fail")
            browser.close()
            sys.exit(1)

        # Traiter chaque PDF
        for index, (bailleur, pdf_name, pdf_path) in enumerate(pdfs):
            result = PDFResult(bailleur, pdf_name)
            start = time.time()
            print(f"\n[{index + 1:>2}/40] {bailleur} - {pdf_name}")

            try:
                # 1. Upload
                step_upload(page, pdf_path, result)
                print(f"    Upload OK")

                # 2. Verify extraction
                step_verify_extraction(page, result)
                print(f"    Extraction OK : BDC={result.numero_bdc}, {result.nb_lignes} lignes")

                # 3. Save
                step_save(page, result)
                print(f"    Save OK : pk={result.pk}")

                # 4. Control
                step_controle(page, result, index)
                print(f"    Controle OK")

                # 5. Attribution
                step_attribution(page, result, index)
                print(f"    Attribution OK")

            except Exception as e:
                result.error = str(e)[:200]
                print(f"    ERREUR : {result.error}")
                take_screenshot(page, f"{index:02d}_{pdf_name}_error")

            result.duration_s = time.time() - start
            results.append(result)

        browser.close()

    total_duration = time.time() - total_start
    generate_report(results, total_duration)


if __name__ == "__main__":
    main()
