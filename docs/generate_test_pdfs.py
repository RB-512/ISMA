"""
Script pour generer des PDFs de test BDC avec des numeros uniques.
Utilise PyMuPDF (fitz) - remplacement direct dans les content streams du PDF.
"""

import os
import shutil

import fitz  # PyMuPDF

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(DOCS_DIR, "test_pdfs")


def replace_in_content_streams(src_path, dst_path, replacements):
    """Remplace du texte directement dans les content streams PDF (byte-level)."""
    doc = fitz.open(src_path)
    for page in doc:
        xrefs = page.get_contents()
        for xref in xrefs:
            stream = doc.xref_stream(xref)
            for old_text, new_text in replacements:
                stream = stream.replace(old_text.encode(), new_text.encode())
            doc.update_stream(xref, stream)
    doc.save(dst_path, garbage=3, deflate=True)
    doc.close()


def generate_gdh_pdfs(count=20):
    """Genere des PDFs GDH avec des numeros BDC uniques."""
    src = os.path.join(DOCS_DIR, "Modèle_bdc_GDH.pdf")
    if not os.path.exists(src):
        print(f"ERREUR: {src} introuvable")
        return

    for i in range(1, count + 1):
        new_numero = f"{500000 + i}"  # 500001 a 500020
        dst = os.path.join(OUTPUT_DIR, f"GDH_test_{new_numero}.pdf")
        replacements = [
            ("450056", new_numero),
        ]
        replace_in_content_streams(src, dst, replacements)
        print(f"  GDH #{i:02d} -> numero_bdc={new_numero} -> {os.path.basename(dst)}")


def generate_erilia_pdfs(count=20):
    """Genere des PDFs ERILIA avec des numeros BDC uniques."""
    src = os.path.join(DOCS_DIR, "Modèle_bdc_ERILIA.pdf")
    if not os.path.exists(src):
        print(f"ERREUR: {src} introuvable")
        return

    for i in range(1, count + 1):
        new_numero_suffix = f"{30000 + i}"  # 30001 a 30020
        new_recl = f"{16000 + i}"
        dst = os.path.join(OUTPUT_DIR, f"ERILIA_test_2026_{new_numero_suffix}.pdf")
        replacements = [
            ("20205", new_numero_suffix),
            ("15635", new_recl),
        ]
        replace_in_content_streams(src, dst, replacements)
        print(f"  ERILIA #{i:02d} -> numero_bdc=2026 {new_numero_suffix} -> {os.path.basename(dst)}")


if __name__ == "__main__":
    # Nettoyer l'ancien dossier si existant
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    print(f"Dossier de sortie: {OUTPUT_DIR}\n")

    print("Generation des PDFs GDH...")
    generate_gdh_pdfs(20)

    print("\nGeneration des PDFs ERILIA...")
    generate_erilia_pdfs(20)

    print(f"\nTermine! 40 PDFs generes dans {OUTPUT_DIR}")
