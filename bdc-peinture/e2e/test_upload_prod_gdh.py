"""
Test E2E : Upload de PDFs GDH depuis le partage reseau vers la prod.

Workflow par PDF :
  1. Upload PDF -> extraction automatique
  2. Controle COMPLET de tous les champs extraits sur /nouveau/
  3. Enregistrement du BDC
  4. Verification des champs sur la page de detail /bdc/<pk>/
  5. Controle du BDC (page split-screen) -> passage en "A attribuer"
  6. Verification du statut final

Usage :
  cd bdc-peinture && python e2e/test_upload_prod_gdh.py
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

# Partage reseau des PDFs GDH
PDF_DIR = Path(r"\\SRVBYPEINTURE\secretariat\BON DE CDE GDH\BONS CDE -  GDH")

# Nombre max de PDFs a tester (0 = tous)
MAX_PDFS = 0

# Repertoire pour screenshots et rapport
REPORT_DIR = Path(__file__).resolve().parent / "rapports"
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"

DEFAULT_TIMEOUT = 15_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_pdf_list():
    """Liste les PDFs du partage reseau."""
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if MAX_PDFS > 0:
        pdfs = pdfs[:MAX_PDFS]
    return pdfs


def take_screenshot(page, name):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    path = SCREENSHOT_DIR / f"{ts}_{name}.png"
    try:
        page.screenshot(path=str(path))
    except Exception:
        pass


def extract_text_after_label(page, label_text):
    """Extrait le texte du <dd> qui suit un <dt> contenant label_text."""
    dt = page.locator(f"dt:has-text('{label_text}')").first
    if dt.count():
        parent = dt.locator("..")
        dd = parent.locator("dd").first
        if dd.count():
            txt = dd.inner_text().strip()
            if txt and txt != "\u2014":
                return txt
    return ""


def extract_section_text(page, section_title):
    """Extrait tout le texte d'une <section> dont le <h2> contient section_title."""
    section = page.locator(f"section:has(h2:has-text('{section_title}'))").first
    if section.count():
        return section.inner_text().strip()
    return ""


class FieldCheck:
    """Resultat du controle d'un champ."""
    def __init__(self, nom, valeur, present):
        self.nom = nom
        self.valeur = valeur[:80] if valeur else ""
        self.present = present


class PDFResult:
    def __init__(self, pdf_name):
        self.pdf_name = pdf_name
        self.numero_bdc = ""
        self.bailleur = ""
        self.marche = ""
        self.date_emission = ""
        self.residence = ""
        self.adresse = ""
        self.logement = ""
        self.objet_travaux = ""
        self.delai = ""
        self.occupant_nom = ""
        self.occupant_tel = ""
        self.emetteur_nom = ""
        self.emetteur_tel = ""
        self.montant_ht = ""
        self.nb_lignes = 0
        self.lignes_detail = []  # liste de dicts {designation, qte, unite, pu, montant}
        self.pk = None
        self.upload_ok = False
        self.extraction_ok = False
        self.save_ok = False
        self.detail_ok = False
        self.controle_ok = False
        self.statut_final = ""
        self.champs_nouveau = []  # FieldCheck list (page /nouveau/)
        self.champs_detail = []   # FieldCheck list (page /detail/)
        self.champs_controle = []  # FieldCheck list (page /controle/)
        self.champs_manquants = []
        self.error = ""
        self.duration_s = 0.0

    @property
    def all_ok(self):
        return self.upload_ok and self.extraction_ok and self.save_ok and self.detail_ok and self.controle_ok

    @property
    def nb_champs_ok(self):
        return sum(1 for c in self.champs_nouveau if c.present)

    @property
    def nb_champs_total(self):
        return len(self.champs_nouveau)

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
        elif not self.detail_ok:
            steps.append("detail")
        elif not self.controle_ok:
            steps.append("controle")
        return f"FAIL({','.join(steps)})"


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
    print("[LOGIN] Connecte.")


def step_upload(page, pdf_path, result):
    page.goto(f"{BASE_URL}/upload/", wait_until="domcontentloaded")
    page.set_input_files("#id_pdf_file", str(pdf_path))
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")
    if "/nouveau/" not in page.url:
        err = page.locator(".text-danger, .bg-danger, .text-red-600, .bg-red-100").first
        if err.count():
            raise RuntimeError(f"Upload refuse: {err.inner_text()[:150]}")
        raise RuntimeError(f"URL inattendue apres upload: {page.url}")
    result.upload_ok = True


def step_verify_extraction(page, result):
    """Controle complet de tous les champs affiches sur /nouveau/."""
    checks = []

    # --- En-tete ---
    h1 = page.locator("h1").first
    h1_text = h1.inner_text() if h1.count() else ""

    # Numero BDC
    m = re.search(r"(\d{4,})", h1_text)
    result.numero_bdc = m.group(1) if m else ""
    checks.append(FieldCheck("Numero BDC", result.numero_bdc, bool(result.numero_bdc)))

    # Bailleur + Marche + Date (dans le <p> sous h1)
    p_sub = page.locator("h1 + p").first
    sub_text = p_sub.inner_text().strip() if p_sub.count() else ""

    # Bailleur
    parts = sub_text.split("\u2014")
    result.bailleur = parts[0].strip() if parts else ""
    checks.append(FieldCheck("Bailleur", result.bailleur, bool(result.bailleur) and result.bailleur != "\u2014"))

    # Marche
    m_marche = re.search(r"March[eé]\s+(.+?)(?:\s*\u2014|$)", sub_text)
    result.marche = m_marche.group(1).strip() if m_marche else ""
    checks.append(FieldCheck("Marche", result.marche, bool(result.marche)))

    # Date emission
    m_date = re.search(r"(\d{1,2}\s+\w+\s+\d{4}|\d{2}/\d{2}/\d{4})", sub_text)
    result.date_emission = m_date.group(1) if m_date else ""
    checks.append(FieldCheck("Date emission", result.date_emission, bool(result.date_emission)))

    # --- Localisation ---
    loc_text = extract_section_text(page, "Localisation")

    # Residence
    result.residence = extract_text_after_label(page, "sidence")
    checks.append(FieldCheck("Residence", result.residence, bool(result.residence)))

    # Adresse
    result.adresse = extract_text_after_label(page, "Adresse")
    checks.append(FieldCheck("Adresse", result.adresse, bool(result.adresse)))

    # Logement
    result.logement = extract_text_after_label(page, "Logement")
    checks.append(FieldCheck("Logement", result.logement, bool(result.logement)))

    # --- Travaux ---
    result.objet_travaux = extract_text_after_label(page, "Objet")
    checks.append(FieldCheck("Objet travaux", result.objet_travaux, bool(result.objet_travaux)))

    result.delai = extract_text_after_label(page, "lai")
    checks.append(FieldCheck("Delai", result.delai, bool(result.delai)))

    # --- Contacts ---
    contacts_text = extract_section_text(page, "Contacts")

    # Occupant
    occ_section = page.locator("h3:has-text('Occupant')").first
    if occ_section.count():
        occ_parent = occ_section.locator("..")
        occ_text = occ_parent.inner_text()
        m_nom = re.search(r"Nom\s*:\s*(.+)", occ_text)
        result.occupant_nom = m_nom.group(1).strip() if m_nom else ""
        m_tel = re.search(r"T[eé]l\s*:\s*(\S+)", occ_text)
        result.occupant_tel = m_tel.group(1).strip() if m_tel else ""

    checks.append(FieldCheck("Occupant nom", result.occupant_nom, bool(result.occupant_nom)))
    checks.append(FieldCheck("Occupant tel", result.occupant_tel, bool(result.occupant_tel)))

    # Emetteur
    em_section = page.locator("h3:has-text('metteur')").first
    if em_section.count():
        em_parent = em_section.locator("..")
        em_text = em_parent.inner_text()
        m_nom = re.search(r"Nom\s*:\s*(.+)", em_text)
        result.emetteur_nom = m_nom.group(1).strip() if m_nom else ""
        m_tel = re.search(r"T[eé]l\s*:\s*(\S+)", em_text)
        result.emetteur_tel = m_tel.group(1).strip() if m_tel else ""

    checks.append(FieldCheck("Emetteur nom", result.emetteur_nom, bool(result.emetteur_nom)))
    checks.append(FieldCheck("Emetteur tel", result.emetteur_tel, bool(result.emetteur_tel)))

    # --- Prestations ---
    tbody_rows = page.locator("table tbody tr").all()
    result.nb_lignes = len(tbody_rows)
    checks.append(FieldCheck("Lignes prestation", str(result.nb_lignes), result.nb_lignes > 0))

    # Detail de chaque ligne
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
            result.lignes_detail.append(ligne)

    # Montant HT total
    total_section = page.locator("text=Total HT").first
    if total_section.count():
        parent = total_section.locator("..")
        total_text = parent.inner_text()
        m_total = re.search(r"([\d\s,.]+)\s*\u20ac", total_text)
        result.montant_ht = m_total.group(1).strip() if m_total else ""
    checks.append(FieldCheck("Montant HT", result.montant_ht, bool(result.montant_ht)))

    # --- Bilan ---
    result.champs_nouveau = checks
    result.champs_manquants = [c.nom for c in checks if not c.present]

    if not result.numero_bdc:
        raise RuntimeError(f"Numero BDC non extrait (h1: {h1_text})")

    result.extraction_ok = True  # On continue meme si des champs manquent


def step_save(page, result):
    page.click('button[type="submit"]:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")
    match = re.search(r"/(\d+)/", page.url)
    if match:
        result.pk = int(match.group(1))
    else:
        raise RuntimeError(f"pk non trouve dans {page.url}")
    result.save_ok = True


def step_verify_detail(page, result):
    """Verifie les champs sur la page de detail apres enregistrement."""
    checks = []

    # Numero BDC dans h1
    h1 = page.locator("h1").first
    h1_text = h1.inner_text() if h1.count() else ""
    m = re.search(r"(\d{4,})", h1_text)
    num_detail = m.group(1) if m else ""
    match_num = num_detail == result.numero_bdc
    checks.append(FieldCheck("Numero BDC", num_detail, match_num))

    # Statut (doit etre "A traiter")
    p_sub = page.locator("h1 + p").first
    sub_text = p_sub.inner_text() if p_sub.count() else ""
    has_statut = "traiter" in sub_text.lower()
    checks.append(FieldCheck("Statut", "A traiter" if has_statut else sub_text[:40], has_statut))

    # Localisation
    loc = extract_section_text(page, "Localisation")
    checks.append(FieldCheck("Section Localisation", loc[:60], bool(loc)))

    # Adresse sur detail
    addr_detail = extract_text_after_label(page, "Adresse")
    checks.append(FieldCheck("Adresse (detail)", addr_detail, bool(addr_detail)))

    # Travaux
    objet_detail = extract_text_after_label(page, "Objet")
    checks.append(FieldCheck("Objet (detail)", objet_detail, bool(objet_detail)))

    # Contacts
    contacts = extract_section_text(page, "Contacts")
    checks.append(FieldCheck("Section Contacts", contacts[:60], bool(contacts)))

    # Prestations sur page detail
    detail_rows = page.locator("table tbody tr").all()
    nb_detail = len(detail_rows)
    lignes_match = nb_detail == result.nb_lignes
    checks.append(FieldCheck(
        "Lignes prestation (detail)",
        f"{nb_detail} (attendu {result.nb_lignes})",
        lignes_match,
    ))

    # PDF original disponible
    pdf_link = page.locator("a:has-text('Voir le PDF')").first
    has_pdf = pdf_link.count() > 0
    checks.append(FieldCheck("Lien PDF original", "present" if has_pdf else "absent", has_pdf))

    result.champs_detail = checks
    detail_manquants = [c.nom for c in checks if not c.present]
    if detail_manquants:
        result.champs_manquants.extend([f"[detail] {m}" for m in detail_manquants])

    result.detail_ok = len(detail_manquants) == 0


def step_controle(page, result):
    """Ouvre la page de controle, remplit occupation, et valide -> A attribuer."""
    checks = []

    # Aller sur la page de controle
    page.goto(f"{BASE_URL}/bdc/{result.pk}/controle/", wait_until="domcontentloaded")

    # Verifier qu'on est bien sur la page de controle (pas 404)
    if "404" in page.title() or page.locator("text=Page non").count():
        raise RuntimeError(f"Page controle 404 pour pk={result.pk}")

    # Verifier le header
    h1 = page.locator("h1").first
    h1_text = h1.inner_text() if h1.count() else ""
    has_bdc_num = result.numero_bdc in h1_text
    checks.append(FieldCheck("Num BDC dans header", h1_text, has_bdc_num))

    # Verifier le statut badge "A traiter"
    badge = page.locator("span.rounded-full").first
    badge_text = badge.inner_text().strip() if badge.count() else ""
    checks.append(FieldCheck("Statut badge", badge_text, "traiter" in badge_text.lower()))

    # Verifier le PDF viewer (iframe)
    iframe = page.locator("iframe").first
    has_pdf = iframe.count() > 0
    checks.append(FieldCheck("PDF viewer", "present" if has_pdf else "absent", has_pdf))

    # Verifier le formulaire editable
    form = page.locator("form").first
    has_form = form.count() > 0
    checks.append(FieldCheck("Formulaire editable", "present" if has_form else "absent", has_form))

    # Cocher toutes les checkboxes de controle
    checkboxes = page.locator("input[type='checkbox'][name^='check_']").all()
    checks.append(FieldCheck("Checkboxes controle", str(len(checkboxes)), True))
    for cb in checkboxes:
        if not cb.is_checked():
            cb.check()

    # Remplir le champ occupation = OCCUPE (le plus courant)
    select_occupation = page.locator("select[name='occupation']").first
    if select_occupation.count():
        select_occupation.select_option("OCCUPE")
        checks.append(FieldCheck("Occupation", "OCCUPE", True))

        # Remplir RDV (obligatoire quand OCCUPE) - date dans 7 jours
        page.wait_for_timeout(300)  # attendre Alpine.js x-show transition
        rdv_input = page.locator("input[name='rdv_date']").first
        if rdv_input.count() and rdv_input.is_visible():
            from datetime import timedelta
            rdv_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT09:00")
            rdv_input.fill(rdv_date)
            checks.append(FieldCheck("RDV date", rdv_date, True))
        else:
            checks.append(FieldCheck("RDV date", "non visible", False))
    else:
        checks.append(FieldCheck("Occupation", "select absent", False))

    # Cliquer "Valider -> A attribuer"
    btn_valider = page.locator("button:has-text('attribuer')").first
    if btn_valider.count():
        btn_valider.click()
        page.wait_for_load_state("domcontentloaded")
        checks.append(FieldCheck("Bouton Valider", "clique", True))
    else:
        raise RuntimeError("Bouton 'Valider -> A attribuer' introuvable")

    # Verifier la redirection (vers la liste ou detail)
    # Apres validation, on est redirige vers bdc:index avec un message de succes
    current_url = page.url
    is_redirected = "/bdc/" in current_url or current_url.endswith("/")
    checks.append(FieldCheck("Redirection apres validation", current_url[-50:], is_redirected))

    # Verifier le message de succes
    success_msg = page.locator(".bg-green-100, .bg-emerald-100, .text-green-700, [class*='success']").first
    if success_msg.count():
        msg_text = success_msg.inner_text().strip()[:80]
        checks.append(FieldCheck("Message succes", msg_text, True))
    else:
        # Verifier s'il y a une erreur
        err_msg = page.locator(".text-red-500, .bg-red-100, .text-danger").first
        if err_msg.count():
            err_text = err_msg.inner_text().strip()[:80]
            checks.append(FieldCheck("Message erreur", err_text, False))
            result.champs_manquants.append(f"[controle] Erreur: {err_text[:50]}")
        else:
            checks.append(FieldCheck("Message succes", "non trouve", False))

    # Verifier le statut final en allant sur la page detail
    page.goto(f"{BASE_URL}/bdc/{result.pk}/", wait_until="domcontentloaded")
    p_sub = page.locator("h1 + p").first
    sub_text = p_sub.inner_text() if p_sub.count() else ""

    if "attribuer" in sub_text.lower():
        result.statut_final = "A_FAIRE"
        checks.append(FieldCheck("Statut final", "A attribuer", True))
    elif "traiter" in sub_text.lower():
        result.statut_final = "A_TRAITER"
        checks.append(FieldCheck("Statut final", "Toujours A traiter (echec transition)", False))
        result.champs_manquants.append("[controle] Statut non change")
    else:
        result.statut_final = sub_text[:30]
        checks.append(FieldCheck("Statut final", sub_text[:40], False))

    result.champs_controle = checks
    controle_manquants = [c.nom for c in checks if not c.present]
    if controle_manquants:
        result.champs_manquants.extend([f"[controle] {m}" for m in controle_manquants])

    result.controle_ok = result.statut_final == "A_FAIRE"


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------


def generate_report(results, total_duration):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M")

    lines = []

    def out(text=""):
        print(text)
        lines.append(text)

    out()
    out("=" * 130)
    out(f"  RAPPORT COMPLET - TEST UPLOAD GDH PROD - {now.strftime('%d/%m/%Y %H:%M')}")
    out("=" * 130)

    ok_count = sum(1 for r in results if r.all_ok)
    fail_count = len(results) - ok_count
    doublon_count = sum(1 for r in results if "doublon" in r.error.lower() or "Upload refuse" in r.error)

    out()
    out(f"  Total: {len(results)} PDFs  |  OK: {ok_count}  |  ECHEC: {fail_count}  |  Doublons: {doublon_count}  |  Duree: {total_duration:.1f}s")
    out()

    # --- Tableau resume ---
    header = f"{'#':>3}  {'PDF':<38}  {'N BDC':<8}  {'Champs':>7}  {'Lignes':>6}  {'Montant':>10}  {'Final':>12}  {'Duree':>6}  {'Statut':<15}"
    out(header)
    out("-" * 130)

    for i, r in enumerate(results, 1):
        name_short = r.pdf_name[:36] if len(r.pdf_name) > 36 else r.pdf_name
        champs_str = f"{r.nb_champs_ok}/{r.nb_champs_total}" if r.nb_champs_total > 0 else "-"
        montant_str = r.montant_ht if r.montant_ht else "-"
        final_str = r.statut_final if r.statut_final else "-"
        duration_str = f"{r.duration_s:.1f}s"
        out(f"{i:>3}  {name_short:<38}  {r.numero_bdc:<8}  {champs_str:>7}  {r.nb_lignes:>6}  {montant_str:>10}  {final_str:>12}  {duration_str:>6}  {r.status_str:<15}")
        if r.champs_manquants:
            out(f"     -> Manquants: {', '.join(r.champs_manquants)}")
        if r.error:
            out(f"     -> {r.error[:120]}")

    out("-" * 130)

    # --- Detail par BDC ---
    out()
    out("=" * 130)
    out("  DETAIL DES CONTROLES PAR BDC")
    out("=" * 130)

    for i, r in enumerate(results, 1):
        if not r.upload_ok:
            continue  # Pas de detail pour les echecs upload/doublon

        out()
        out(f"--- [{i}] {r.pdf_name} --- BDC {r.numero_bdc} --- {r.status_str} ---")

        # Champs page /nouveau/
        if r.champs_nouveau:
            out("  Page /nouveau/ :")
            for c in r.champs_nouveau:
                status = "[OK]" if c.present else "[--]"
                out(f"    {status} {c.nom:<22} : {c.valeur}")

        # Lignes de prestation
        if r.lignes_detail:
            out(f"  Lignes de prestation ({len(r.lignes_detail)}) :")
            for j, lg in enumerate(r.lignes_detail, 1):
                desig = lg['designation'][:50]
                out(f"    {j}. {desig:<50}  Qte={lg['qte']}  {lg['unite']}  PU={lg['pu_ht']}  MT={lg['montant_ht']}")

        # Champs page detail
        if r.champs_detail:
            out(f"  Page detail /bdc/{r.pk}/ :")
            for c in r.champs_detail:
                status = "[OK]" if c.present else "[--]"
                out(f"    {status} {c.nom:<28} : {c.valeur}")

        # Champs page controle
        if r.champs_controle:
            out(f"  Page controle /bdc/{r.pk}/controle/ :")
            for c in r.champs_controle:
                status = "[OK]" if c.present else "[--]"
                out(f"    {status} {c.nom:<28} : {c.valeur}")

    out()
    out("=" * 130)

    # --- Stats globales ---
    out()
    out("  STATISTIQUES GLOBALES")
    out("-" * 60)

    # Compter les champs manquants les plus frequents
    from collections import Counter
    manquants_counter = Counter()
    for r in results:
        for m in r.champs_manquants:
            manquants_counter[m] += 1

    if manquants_counter:
        out("  Champs les plus souvent manquants :")
        for champ, count in manquants_counter.most_common(10):
            pct = count / len(results) * 100
            out(f"    {champ:<35} : {count:>3} fois ({pct:.0f}%)")
    else:
        out("  Aucun champ manquant !")

    out()

    # Sauvegarder
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"rapport_complet_gdh_{timestamp}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Rapport sauvegarde: {report_path}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    from playwright.sync_api import sync_playwright

    pdfs = build_pdf_list()
    if not pdfs:
        print(f"[ERREUR] Aucun PDF trouve dans {PDF_DIR}")
        sys.exit(1)

    print(f"[INFO] {len(pdfs)} PDFs a tester depuis {PDF_DIR}")

    results = []
    total_start = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        try:
            step_login(page)
        except Exception as e:
            print(f"[FATAL] Login: {e}")
            take_screenshot(page, "login_fail")
            browser.close()
            sys.exit(1)

        for index, pdf_path in enumerate(pdfs):
            pdf_name = pdf_path.stem
            result = PDFResult(pdf_name)
            start = time.time()
            print(f"\n[{index + 1:>2}/{len(pdfs)}] {pdf_path.name}")

            try:
                step_upload(page, pdf_path, result)
                print(f"    Upload OK")

                step_verify_extraction(page, result)
                ok_n = result.nb_champs_ok
                total_n = result.nb_champs_total
                manq = f" (manquants: {', '.join(result.champs_manquants)})" if result.champs_manquants else ""
                print(f"    Extraction: BDC={result.numero_bdc}, {result.nb_lignes} lignes, {ok_n}/{total_n} champs{manq}")

                # Afficher les lignes
                for j, lg in enumerate(result.lignes_detail, 1):
                    print(f"      L{j}: {lg['designation'][:45]}  Qte={lg['qte']}  {lg['unite']}  PU={lg['pu_ht']}  MT={lg['montant_ht']}")
                if result.montant_ht:
                    print(f"      Total HT: {result.montant_ht}")

                step_save(page, result)
                print(f"    Enregistre: pk={result.pk}")

                step_verify_detail(page, result)
                detail_ok = sum(1 for c in result.champs_detail if c.present)
                detail_total = len(result.champs_detail)
                print(f"    Detail: {detail_ok}/{detail_total} controles OK")

                step_controle(page, result)
                ctrl_ok = sum(1 for c in result.champs_controle if c.present)
                ctrl_total = len(result.champs_controle)
                print(f"    Controle: {ctrl_ok}/{ctrl_total} checks OK -> Statut: {result.statut_final}")

            except Exception as e:
                result.error = str(e)[:200]
                print(f"    ERREUR: {result.error}")
                take_screenshot(page, f"{index:02d}_{pdf_name[:20]}_error")

            result.duration_s = time.time() - start
            results.append(result)

        browser.close()

    total_duration = time.time() - total_start
    generate_report(results, total_duration)


if __name__ == "__main__":
    main()
