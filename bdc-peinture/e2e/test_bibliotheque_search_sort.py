"""
Tests E2E Playwright - Bibliotheque de prix : recherche et tri par reference.
"""

import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.makedirs("e2e/screenshots", exist_ok=True)

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "testcdt@test.com"
PASSWORD = "testpass123"


def login(page):
    page.goto(BASE_URL + "/accounts/login/")
    page.fill('input[name="login"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_timeout(1500)


def goto_bibliotheque(page):
    page.goto(BASE_URL + "/bibliotheque/")
    page.wait_for_selector("#bibliotheque-table", timeout=8000)
    page.wait_for_timeout(500)


def get_refs(page):
    cells = page.locator("#bibliotheque-table tbody tr td:first-child").all()
    return [c.inner_text().strip() for c in cells if c.inner_text().strip()]


results = []


def run_test(name, fn, page):
    try:
        fn(page)
        results.append((name, "PASS", ""))
        print(f"  PASS")
    except Exception as e:
        results.append((name, "FAIL", str(e)[:120]))
        print(f"  FAIL: {str(e)[:120]}")
        try:
            page.screenshot(path=f"e2e/screenshots/FAIL_{name}.png")
        except Exception:
            pass


# ─── Tests ────────────────────────────────────────────────────────────────────


def t1_no_overlap(page):
    goto_bibliotheque(page)
    pl = page.evaluate(
        "parseFloat(window.getComputedStyle(document.getElementById('q-input')).paddingLeft)"
    )
    icon_right = page.evaluate(
        """() => {
            const svg = document.querySelector('.relative svg');
            const inp = document.getElementById('q-input');
            if (!svg || !inp) return 0;
            return svg.getBoundingClientRect().right - inp.getBoundingClientRect().left;
        }"""
    )
    print(f"    padding-left={pl}px, fin icone={icon_right:.1f}px", end=" ")
    assert pl >= icon_right, f"Superposition! padding={pl}px < icon_right={icon_right}px"
    page.screenshot(path="e2e/screenshots/01_initial.png")


def t2_search_by_ref(page):
    goto_bibliotheque(page)
    before = page.locator("#bibliotheque-table tbody tr").count()
    page.fill("#q-input", "AAA")
    page.wait_for_timeout(600)
    after = page.locator("#bibliotheque-table tbody tr").count()
    print(f"    {before} -> {after} lignes", end=" ")
    assert after < before, f"Pas filtre: avant={before}, apres={after}"
    content = page.locator("#bibliotheque-table").inner_text()
    assert "AAA-001" in content
    assert "REF-001" not in content
    page.screenshot(path="e2e/screenshots/02_search_aaa.png")


def t3_search_by_designation(page):
    goto_bibliotheque(page)
    page.fill("#q-input", "Plafond")
    page.wait_for_timeout(600)
    content = page.locator("#bibliotheque-table").inner_text()
    assert "Plafond blanc" in content
    assert "REF-001" not in content


def t4_clear_search(page):
    goto_bibliotheque(page)
    total = page.locator("#bibliotheque-table tbody tr").count()
    page.fill("#q-input", "ZZZ")
    page.wait_for_timeout(600)
    page.fill("#q-input", "")
    # Déclencher le trigger "search" en appuyant Entrée ou en effacant avec la croix
    page.press("#q-input", "Enter")
    page.wait_for_timeout(600)
    restored = page.locator("#bibliotheque-table tbody tr").count()
    print(f"    {total} -> filtre -> {restored}", end=" ")
    assert restored == total, f"Non restaure: {restored} vs {total}"


def t5_sort_asc_to_desc(page):
    goto_bibliotheque(page)
    refs_before = get_refs(page)
    assert refs_before == sorted(refs_before), f"Pas ASC initialement: {refs_before}"
    page.click("#bibliotheque-table thead button")
    page.wait_for_timeout(600)
    refs_after = get_refs(page)
    print(f"    {refs_before} -> {refs_after}", end=" ")
    assert refs_after == sorted(refs_after, reverse=True), f"Pas DESC: {refs_after}"
    page.screenshot(path="e2e/screenshots/05_sort_desc.png")


def t6_sort_desc_to_asc(page):
    goto_bibliotheque(page)
    # 1er clic -> DESC
    page.click("#bibliotheque-table thead button")
    page.wait_for_timeout(600)
    # 2e clic -> ASC
    page.click("#bibliotheque-table thead button")
    page.wait_for_timeout(600)
    refs = get_refs(page)
    print(f"    {refs}", end=" ")
    assert refs == sorted(refs), f"Pas ASC apres 2 clics: {refs}"


def t7_search_and_sort_combined(page):
    goto_bibliotheque(page)
    page.fill("#q-input", "peinture")
    page.wait_for_timeout(600)
    n_filtered = page.locator("#bibliotheque-table tbody tr").count()
    page.click("#bibliotheque-table thead button")
    page.wait_for_timeout(600)
    n_after = page.locator("#bibliotheque-table tbody tr").count()
    assert n_after == n_filtered, f"Filtre perdu apres tri: {n_after} vs {n_filtered}"
    refs = get_refs(page)
    assert refs == sorted(refs, reverse=True), f"Pas DESC: {refs}"
    print(f"    {n_filtered} lignes triees DESC: {refs}", end=" ")
    page.screenshot(path="e2e/screenshots/07_combined.png")


# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("01_no_overlap",            t1_no_overlap),
        ("02_search_by_ref",         t2_search_by_ref),
        ("03_search_by_designation", t3_search_by_designation),
        ("04_clear_search",          t4_clear_search),
        ("05_sort_asc_to_desc",      t5_sort_asc_to_desc),
        ("06_sort_desc_to_asc",      t6_sort_desc_to_asc),
        ("07_search_sort_combined",  t7_search_and_sort_combined),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        login(page)

        for name, fn in tests:
            print(f"\n[{name}]")
            run_test(name, fn, page)

        browser.close()

    print("\n" + "=" * 50)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    for name, status, detail in results:
        suffix = f" ({detail})" if detail else ""
        print(f"  [{status}] {name}{suffix}")
    print(f"\nResultats: {passed}/{len(results)} PASS")
