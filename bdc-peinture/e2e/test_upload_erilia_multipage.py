"""
Test E2E : Upload d'un PDF ERILIA multi-pages (prestations sur 2+ pages).

Verifie que le parser ERILIA extrait correctement toutes les prestations
meme quand elles s'etalent sur plusieurs pages du PDF.

Workflow :
  1. Upload PDF -> extraction automatique
  2. Controle des champs extraits sur /nouveau/
  3. Verification du nombre de lignes de prestation (doit etre > 4, preuve du multi-pages)
  4. Enregistrement du BDC
  5. Verification sur la page de detail

Usage :
  cd bdc-peinture && python e2e/test_upload_erilia_multipage.py
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://51.83.197.18"
EMAIL = "admin@isma.fr"
PASSWORD = "isma2024"

# PDF ERILIA multi-pages (3 pages, 11 prestations)
PDF_PATH = Path(r"\\SRVBYPEINTURE\secretariat\BON DE CDE ERILIA\Bon ERILIA\BT 2026 30624.pdf")

SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"
DEFAULT_TIMEOUT = 15_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def take_screenshot(page, name):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    path = SCREENSHOT_DIR / f"{ts}_{name}.png"
    try:
        page.screenshot(path=str(path))
        print(f"  Screenshot: {path}")
    except Exception:
        pass


def extract_text_after_label(page, label_text):
    dt = page.locator(f"dt:has-text('{label_text}')").first
    if dt.count():
        parent = dt.locator("..")
        dd = parent.locator("dd").first
        if dd.count():
            txt = dd.inner_text().strip()
            if txt and txt != "\u2014":
                return txt
    return ""


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def step_login(page):
    page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
    page.fill('input[name="login"]', EMAIL)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")
    if "/accounts/login/" in page.url:
        raise RuntimeError("Echec de connexion")
    print("[OK] Connecte")


def step_upload(page, pdf_path):
    page.goto(f"{BASE_URL}/upload/", wait_until="domcontentloaded")
    page.set_input_files("#id_pdf_file", str(pdf_path))
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")
    if "/nouveau/" not in page.url:
        err = page.locator(".text-danger, .bg-danger, .text-red-600, .bg-red-100").first
        if err.count():
            raise RuntimeError(f"Upload refuse: {err.inner_text()[:150]}")
        raise RuntimeError(f"URL inattendue apres upload: {page.url}")
    print("[OK] Upload reussi -> /nouveau/")


def step_verify_extraction(page):
    """Controle les champs extraits sur la page /nouveau/."""
    results = {}
    errors = []

    # Numero BDC
    h1 = page.locator("h1").first
    h1_text = h1.inner_text() if h1.count() else ""
    m = re.search(r"(\d{4,})", h1_text)
    results["numero_bdc"] = m.group(1) if m else ""
    print(f"  Numero BDC: {results['numero_bdc']}")
    if not results["numero_bdc"]:
        errors.append("Numero BDC manquant")

    # Bailleur
    p_sub = page.locator("h1 + p").first
    sub_text = p_sub.inner_text().strip() if p_sub.count() else ""
    results["bailleur"] = sub_text.split("\u2014")[0].strip() if sub_text else ""
    print(f"  Bailleur: {results['bailleur']}")
    if "ERILIA" not in results["bailleur"].upper():
        errors.append(f"Bailleur inattendu: {results['bailleur']}")

    # Marche
    m_marche = re.search(r"March[eé]\s+(.+?)(?:\s*\u2014|$)", sub_text)
    results["marche"] = m_marche.group(1).strip() if m_marche else ""
    print(f"  Marche: {results['marche']}")

    # Date emission
    m_date = re.search(r"(\d{1,2}\s+\w+\s+\d{4}|\d{2}/\d{2}/\d{4})", sub_text)
    results["date_emission"] = m_date.group(1) if m_date else ""
    print(f"  Date emission: {results['date_emission']}")

    # Adresse
    results["adresse"] = extract_text_after_label(page, "Adresse")
    print(f"  Adresse: {results['adresse']}")

    # Residence
    results["residence"] = extract_text_after_label(page, "sidence")
    print(f"  Residence: {results['residence']}")

    # Objet travaux
    results["objet"] = extract_text_after_label(page, "Objet")
    print(f"  Objet: {results['objet']}")

    # Delai
    results["delai"] = extract_text_after_label(page, "lai")
    print(f"  Delai: {results['delai']}")

    # Emetteur
    em_section = page.locator("h3:has-text('metteur')").first
    if em_section.count():
        em_text = em_section.locator("..").inner_text()
        m_nom = re.search(r"Nom\s*:\s*(.+)", em_text)
        results["emetteur_nom"] = m_nom.group(1).strip() if m_nom else ""
        m_tel = re.search(r"T[eé]l\s*:\s*(\S+)", em_text)
        results["emetteur_tel"] = m_tel.group(1).strip() if m_tel else ""
        print(f"  Emetteur: {results.get('emetteur_nom', '')} | Tel: {results.get('emetteur_tel', '')}")

    # === PRESTATIONS (le coeur du test multi-pages) ===
    tbody_rows = page.locator("table tbody tr").all()
    nb_lignes = len(tbody_rows)
    results["nb_lignes"] = nb_lignes
    print(f"\n  === PRESTATIONS: {nb_lignes} lignes ===")

    lignes = []
    for i, row in enumerate(tbody_rows):
        cells = row.locator("td").all()
        if len(cells) >= 5:
            ligne = {
                "designation": cells[0].inner_text().strip(),
                "qte": cells[1].inner_text().strip(),
                "unite": cells[2].inner_text().strip(),
                "pu_ht": cells[3].inner_text().strip(),
                "montant_ht": cells[4].inner_text().strip(),
            }
            lignes.append(ligne)
            desig = ligne["designation"][:55]
            print(f"    {i + 1:>2}. {desig:<55}  Qte={ligne['qte']}  {ligne['unite']}  PU={ligne['pu_ht']}  MT={ligne['montant_ht']}")

    results["lignes"] = lignes

    # Montant HT total
    total_section = page.locator("text=Total HT").first
    if total_section.count():
        parent = total_section.locator("..")
        total_text = parent.inner_text()
        m_total = re.search(r"([\d\s,.]+)\s*\u20ac", total_text)
        results["montant_ht"] = m_total.group(1).strip() if m_total else ""
    else:
        results["montant_ht"] = ""
    print(f"\n  Montant HT total: {results['montant_ht']}")

    # === VERIFICATION CLE : multi-pages ===
    # Le BDC BT 2026 30624 a 11 prestations sur 2 pages.
    # Si on n'extrait que la page 1, on aura ~4 lignes.
    # Si le fix multi-pages fonctionne, on doit avoir 11 lignes.
    MIN_EXPECTED_LINES = 7  # au moins 7 pour prouver le multi-pages
    if nb_lignes < MIN_EXPECTED_LINES:
        errors.append(
            f"MULTI-PAGES ECHOUE: seulement {nb_lignes} lignes extraites "
            f"(attendu >= {MIN_EXPECTED_LINES}). "
            f"Le parser n'extrait probablement que la page 1."
        )
        print(f"\n  [FAIL] MULTI-PAGES: {nb_lignes} lignes < {MIN_EXPECTED_LINES} attendues")
    else:
        print(f"\n  [OK] MULTI-PAGES: {nb_lignes} lignes extraites (>= {MIN_EXPECTED_LINES})")

    return results, errors


def step_save(page):
    page.click('button[type="submit"]:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")
    match = re.search(r"/(\d+)/", page.url)
    if match:
        pk = int(match.group(1))
        print(f"[OK] Enregistre: pk={pk}")
        return pk
    raise RuntimeError(f"pk non trouve dans {page.url}")


def step_verify_detail(page, pk, expected_lignes):
    """Verifie les champs sur la page de detail."""
    page.goto(f"{BASE_URL}/{pk}/", wait_until="domcontentloaded")
    errors = []

    # Statut
    p_sub = page.locator("h1 + p").first
    sub_text = p_sub.inner_text() if p_sub.count() else ""
    if "traiter" in sub_text.lower():
        print(f"  Statut: A traiter [OK]")
    else:
        errors.append(f"Statut inattendu: {sub_text[:40]}")

    # Lignes de prestation sur detail
    detail_rows = page.locator("table tbody tr").all()
    nb_detail = len(detail_rows)
    if nb_detail == expected_lignes:
        print(f"  Lignes detail: {nb_detail} [OK]")
    else:
        errors.append(f"Lignes detail: {nb_detail} (attendu {expected_lignes})")
        print(f"  Lignes detail: {nb_detail} (attendu {expected_lignes}) [FAIL]")

    # PDF original
    pdf_link = page.locator("a:has-text('Voir le PDF')").first
    if pdf_link.count():
        print(f"  PDF original: present [OK]")
    else:
        errors.append("Lien PDF original absent")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    from playwright.sync_api import sync_playwright

    if not PDF_PATH.exists():
        print(f"[ERREUR] PDF introuvable: {PDF_PATH}")
        sys.exit(1)

    print(f"[INFO] Test upload ERILIA multi-pages")
    print(f"[INFO] PDF: {PDF_PATH.name}")
    print()

    start = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        all_errors = []

        try:
            step_login(page)
            print()

            step_upload(page, PDF_PATH)
            print()

            print("--- Verification extraction ---")
            results, extraction_errors = step_verify_extraction(page)
            all_errors.extend(extraction_errors)
            take_screenshot(page, "erilia_extraction")
            print()

            pk = step_save(page)
            print()

            print("--- Verification detail ---")
            detail_errors = step_verify_detail(page, pk, results["nb_lignes"])
            all_errors.extend(detail_errors)
            take_screenshot(page, "erilia_detail")
            print()

        except Exception as e:
            all_errors.append(f"Exception: {e}")
            print(f"\n[ERREUR] {e}")
            take_screenshot(page, "erilia_error")

        browser.close()

    duration = time.time() - start

    # === BILAN ===
    print("=" * 80)
    print(f"  BILAN - Test ERILIA multi-pages - {duration:.1f}s")
    print("=" * 80)

    if all_errors:
        print(f"\n  {len(all_errors)} erreur(s):")
        for err in all_errors:
            print(f"    - {err}")
        print()
        sys.exit(1)
    else:
        print(f"\n  SUCCES: Toutes les verifications passent.")
        print(f"  - {results['nb_lignes']} lignes de prestation extraites (multi-pages OK)")
        print(f"  - Montant HT: {results.get('montant_ht', 'N/A')}")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
