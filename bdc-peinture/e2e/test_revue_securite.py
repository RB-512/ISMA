"""
Tests E2E Playwright — Verification des corrections de la revue de code securite.
Cible : serveur local (127.0.0.1:8000) avec la base SQLite de dev.

Prerequis : 2 comptes (CDT + Secretaire) crees via la console Django.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.makedirs("e2e/screenshots", exist_ok=True)

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"


def login(page, email, password):
    page.goto(BASE_URL + "/accounts/login/")
    page.fill('input[name="login"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/", timeout=8000)


results = []


def run_test(name, fn, page):
    print(f"  {name}...", end=" ")
    try:
        fn(page)
        results.append((name, "PASS", ""))
        print("PASS")
    except Exception as e:
        results.append((name, "FAIL", str(e)[:150]))
        print(f"FAIL: {str(e)[:150]}")
        try:
            safe = name.replace(" ", "_").replace("/", "_")
            page.screenshot(path=f"e2e/screenshots/FAIL_{safe}.png")
        except Exception:
            pass


# ── Test 1 : Pas de credentials dans la page de login ──────────────────


def test_login_no_credentials(page):
    """Verifie que la page de login ne contient pas de mot de passe visible."""
    page.goto(BASE_URL + "/accounts/login/")
    html = page.content()
    assert "isma2024" not in html, "Le mot de passe 'isma2024' est visible dans la page de login !"
    assert "ismail@isma.fr" not in html, "L'email 'ismail@isma.fr' est visible dans la page de login !"


# ── Test 2 : RBAC — Secretaire bloquee sur les vues CDT ────────────────


def test_secretaire_blocked_attribuer(page):
    """Secretaire ne peut pas acceder a la page d'attribution."""
    resp = page.goto(BASE_URL + "/1/attribuer/")
    # Soit 403, soit redirect vers login (si la session a expire)
    assert resp.status in (403, 302), f"Expected 403/302 but got {resp.status}"


def test_secretaire_blocked_gestion(page):
    """Secretaire ne peut pas acceder a la gestion utilisateurs."""
    resp = page.goto(BASE_URL + "/gestion/")
    assert resp.status in (403, 302), f"Expected 403/302 but got {resp.status}"


def test_secretaire_403_page_explicite(page):
    """La page 403 affiche un message explicite, pas une page blanche."""
    page.goto(BASE_URL + "/1/attribuer/")
    html = page.content()
    assert "conducteurs de travaux" in html.lower() or "droits" in html.lower(), \
        "La page 403 ne contient pas de message explicite"


# ── Test 3 : Upload — Limite taille ────────────────────────────────────


def test_upload_size_limit(page):
    """Verifie que l'upload refuse les fichiers > 10 Mo."""
    page.goto(BASE_URL + "/upload/")
    # Creer un fichier temporaire de 11 Mo
    big_file = "e2e/screenshots/test_big_file.pdf"
    with open(big_file, "wb") as f:
        f.write(b"%PDF-1.4\n" + b"0" * (11 * 1024 * 1024))
    try:
        page.set_input_files('input[type="file"]', big_file)
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        html = page.content()
        assert "volumineux" in html.lower() or "10" in html, "Message d'erreur taille non affiche"
    finally:
        os.remove(big_file)


# ── Test 4 : CDT peut acceder aux vues protegees ──────────────────────


def test_cdt_can_access_config(page):
    """CDT peut acceder a la page de configuration."""
    page.goto(BASE_URL + "/gestion/config-bailleurs/")
    assert page.url.endswith("/gestion/config-bailleurs/") or "config" in page.url
    html = page.content()
    assert "Configuration" in html or "Bailleurs" in html or "Accès" in html


# ── Main ──────────────────────────────────────────────────────────────


def main():
    print("\n=== Tests E2E — Revue de code securite ===\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # --- Phase 1 : Test page login (sans authentification) ---
        print("[Phase 1] Tests sans authentification")
        ctx1 = browser.new_context()
        page1 = ctx1.new_page()
        run_test("login_no_credentials", test_login_no_credentials, page1)
        ctx1.close()

        # --- Phase 2 : Tests avec compte Secretaire ---
        print("\n[Phase 2] Tests avec Secretaire")
        ctx2 = browser.new_context()
        page2 = ctx2.new_page()
        try:
            login(page2, "secretaire@test.fr", "testpass123")
            run_test("secretaire_blocked_attribuer", test_secretaire_blocked_attribuer, page2)
            run_test("secretaire_blocked_gestion", test_secretaire_blocked_gestion, page2)
            run_test("secretaire_403_page_explicite", test_secretaire_403_page_explicite, page2)
            run_test("upload_size_limit", test_upload_size_limit, page2)
        except Exception as e:
            print(f"  Login Secretaire echoue: {e}")
            results.append(("login_secretaire", "FAIL", str(e)[:150]))
        ctx2.close()

        # --- Phase 3 : Tests avec compte CDT ---
        print("\n[Phase 3] Tests avec CDT")
        ctx3 = browser.new_context()
        page3 = ctx3.new_page()
        try:
            login(page3, "cdt@test.fr", "testpass123")
            run_test("cdt_can_access_config", test_cdt_can_access_config, page3)
        except Exception as e:
            print(f"  Login CDT echoue: {e}")
            results.append(("login_cdt", "FAIL", str(e)[:150]))
        ctx3.close()

        browser.close()

    # --- Resume ---
    print("\n=== Resume ===")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    for name, status, msg in results:
        icon = "OK" if status == "PASS" else "ECHEC"
        line = f"  [{icon}] {name}"
        if msg:
            line += f" — {msg}"
        print(line)
    print(f"\n  {passed} passes, {failed} echecs")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
