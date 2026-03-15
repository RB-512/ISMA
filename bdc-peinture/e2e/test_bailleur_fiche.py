"""
Test E2E Playwright — Onglet Bailleurs + Preview fiche chantier.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.makedirs("e2e/screenshots", exist_ok=True)

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"


def main():
    print("\n=== Test E2E — Bailleurs + Fiche chantier ===\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()

        # Login CDT
        print("[1] Login CDT...")
        page.goto(BASE_URL + "/accounts/login/")
        page.fill('input[name="login"]', "cdt@test.fr")
        page.fill('input[name="password"]', "testpass123")
        page.click('button[type="submit"]')
        page.wait_for_url("**/", timeout=8000)
        print("    OK")

        # Aller sur Configuration
        print("[2] Navigation vers Configuration...")
        page.goto(BASE_URL + "/gestion/config-bailleurs/")
        page.wait_for_timeout(1000)
        page.screenshot(path="e2e/screenshots/config_page.png")
        print("    OK")

        # Cliquer sur l'onglet Bailleurs
        print("[3] Onglet Bailleurs...")
        page.click("text=Bailleurs")
        page.wait_for_timeout(500)
        page.screenshot(path="e2e/screenshots/onglet_bailleurs.png")

        # Verifier que le bailleur GDH est affiche
        html = page.content()
        if "Grand Delta Habitat" in html:
            print("    GDH trouve dans la liste")
        else:
            print("    ATTENTION: GDH non trouve")

        # Verifier le nombre de BDC
        if "BDC" in html:
            print("    Compteur BDC present")

        # Cliquer sur "Previsualiser la fiche chantier"
        print("[4] Previsualisation fiche chantier...")
        preview_btn = page.locator("text=Previsualiser la fiche chantier").first
        if preview_btn.count():
            preview_btn.click()
            page.wait_for_timeout(500)
            page.screenshot(path="e2e/screenshots/preview_dropdown.png")

            # Choisir un BDC dans le dropdown
            bdc_link = page.locator("a:has-text('E2E-001')").first
            if bdc_link.count():
                print("    BDC E2E-001 trouve dans le dropdown")

                # Ouvrir dans un nouvel onglet (target=_blank)
                with page.expect_popup() as popup_info:
                    bdc_link.click()
                popup = popup_info.value
                popup.wait_for_load_state("networkidle")

                content_type = popup.evaluate("() => document.contentType")
                print(f"    Content-Type: {content_type}")

                if "pdf" in content_type.lower():
                    print("    PASS: Fiche chantier PDF generee")
                else:
                    popup.screenshot(path="e2e/screenshots/fiche_chantier_result.png")
                    body = popup.content()
                    if "erreur" in body.lower() or "error" in body.lower():
                        print(f"    ECHEC: Page d'erreur affichee")
                    else:
                        print(f"    Resultat: page HTML (pas un PDF)")

                popup.close()
            else:
                print("    Aucun BDC dans le dropdown")
                page.screenshot(path="e2e/screenshots/dropdown_vide.png")
        else:
            print("    Bouton preview non trouve (aucun BDC pour ce bailleur?)")

        # Tester aussi en tant que Secretaire
        print("\n[5] Test acces Secretaire sur Configuration...")
        ctx2 = browser.new_context()
        page2 = ctx2.new_page()
        page2.goto(BASE_URL + "/accounts/login/")
        page2.fill('input[name="login"]', "secretaire@test.fr")
        page2.fill('input[name="password"]', "testpass123")
        page2.click('button[type="submit"]')
        page2.wait_for_url("**/", timeout=8000)

        page2.goto(BASE_URL + "/gestion/config-bailleurs/")
        page2.wait_for_timeout(1000)

        # La Secretaire doit pouvoir voir la page (lecture seule)
        if "Configuration" in page2.content():
            print("    Secretaire peut voir la page Configuration")
        else:
            print("    ATTENTION: Secretaire ne peut pas voir Configuration")

        page2.screenshot(path="e2e/screenshots/config_secretaire.png")
        ctx2.close()

        print("\n[6] Screenshots sauvegardes dans e2e/screenshots/")
        print("    - config_page.png")
        print("    - onglet_bailleurs.png")
        print("    - preview_dropdown.png")
        print("    - config_secretaire.png")

        # Garder le navigateur ouvert 5s pour visualiser
        page.wait_for_timeout(3000)
        ctx.close()
        browser.close()

    print("\n=== Termine ===")


if __name__ == "__main__":
    main()
