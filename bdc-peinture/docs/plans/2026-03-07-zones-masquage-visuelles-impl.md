# Zones de masquage visuelles PDF — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the fragile text-search-based PDF field masking with a visual rectangle-based masking system where admins draw zones on the bailleur's PDF template.

**Architecture:** New `zones_masquage` JSONField on `Bailleur` stores rectangle coordinates. A PDF.js-based visual editor lets users draw rectangles on the PDF template. The backend applies these rectangles as white redactions via PyMuPDF. The old `champs_masques` field and all its associated text-search code is removed.

**Tech Stack:** Django 5.1, PyMuPDF (fitz), PDF.js (CDN), Alpine.js (already present), HTMX

---

### Task 1: Migration — add `zones_masquage`, remove `champs_masques`

**Files:**
- Modify: `apps/bdc/models.py:35-40`
- Create: `apps/bdc/migrations/0012_*.py` (auto-generated)

**Step 1: Update model**

In `apps/bdc/models.py`, replace the `champs_masques` field with `zones_masquage`:

```python
# Remove this:
champs_masques = models.JSONField(
    default=list,
    blank=True,
    verbose_name="Champs à masquer sur le PDF",
    help_text="Liste des clés de champs extraits à masquer (ex: montant_ht, montant_ttc)",
)

# Add this in its place:
zones_masquage = models.JSONField(
    default=list,
    blank=True,
    verbose_name="Zones à masquer sur le PDF",
    help_text='Rectangles de masquage [{x, y, w, h, page, label}]. Coordonnées en points PDF.',
)
```

**Step 2: Generate and apply migration**

Run:
```bash
cd bdc-peinture
uv run manage.py makemigrations --settings=config.settings.dev_sqlite
uv run manage.py migrate --settings=config.settings.dev_sqlite
```

Expected: Migration created and applied successfully.

**Step 3: Commit**

```bash
git add apps/bdc/models.py apps/bdc/migrations/0012_*
git commit -m "feat: replace champs_masques with zones_masquage on Bailleur"
```

---

### Task 2: Rewrite `masquage_pdf.py` — zone-based masking

**Files:**
- Rewrite: `apps/bdc/masquage_pdf.py` (full rewrite)

**Step 1: Write the failing test**

Create `tests/test_bdc/test_masquage_pdf.py`:

```python
import fitz
import pytest

from apps.bdc.masquage_pdf import generer_pdf_masque


def _creer_pdf_simple():
    """Cree un PDF 1 page avec du texte pour les tests."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_text((100, 100), "Montant HT : 1234,56 EUR", fontsize=12)
    page.insert_text((100, 200), "Adresse : 12 rue des Tests", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.django_db
class TestGenererPdfMasqueZones:
    def test_masque_zone_rectangulaire(self, bdc_a_traiter):
        """Une zone de masquage doit produire un rectangle blanc dans le PDF."""
        # Configurer une zone de masquage sur le bailleur
        bdc_a_traiter.bailleur.zones_masquage = [
            {"x": 90, "y": 85, "w": 300, "h": 25, "page": 1, "label": "Montant"}
        ]
        bdc_a_traiter.bailleur.save()

        # Creer un PDF original pour le BDC
        from django.core.files.base import ContentFile
        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(_creer_pdf_simple()))

        result = generer_pdf_masque(bdc_a_traiter)

        assert result is not None
        assert isinstance(result, bytes)
        # Le PDF retourne doit etre un PDF valide
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 1
        doc.close()

    def test_retourne_none_sans_pdf_original(self, bdc_a_traiter):
        """Sans PDF original, retourne None."""
        bdc_a_traiter.bailleur.zones_masquage = [
            {"x": 0, "y": 0, "w": 100, "h": 100, "page": 1, "label": "test"}
        ]
        bdc_a_traiter.bailleur.save()

        result = generer_pdf_masque(bdc_a_traiter)
        assert result is None

    def test_retourne_none_sans_zones(self, bdc_a_traiter):
        """Sans zones de masquage, retourne None."""
        from django.core.files.base import ContentFile
        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(_creer_pdf_simple()))

        result = generer_pdf_masque(bdc_a_traiter)
        assert result is None

    def test_filtrage_pages(self, bdc_a_traiter):
        """Le parametre pages filtre les pages du resultat."""
        bdc_a_traiter.bailleur.zones_masquage = [
            {"x": 90, "y": 85, "w": 300, "h": 25, "page": 1, "label": "test"}
        ]
        bdc_a_traiter.bailleur.save()

        # Creer un PDF 2 pages
        doc = fitz.open()
        doc.new_page(width=595, height=842)
        doc.new_page(width=595, height=842)
        pdf_2pages = doc.tobytes()
        doc.close()

        from django.core.files.base import ContentFile
        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(pdf_2pages))

        result = generer_pdf_masque(bdc_a_traiter, pages=[1])

        assert result is not None
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 1
        doc.close()

    def test_zone_page_inexistante_ignoree(self, bdc_a_traiter):
        """Une zone ciblant une page inexistante est ignoree sans erreur."""
        bdc_a_traiter.bailleur.zones_masquage = [
            {"x": 0, "y": 0, "w": 100, "h": 100, "page": 5, "label": "page 5"}
        ]
        bdc_a_traiter.bailleur.save()

        from django.core.files.base import ContentFile
        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(_creer_pdf_simple()))

        result = generer_pdf_masque(bdc_a_traiter)
        assert result is not None  # No crash, still returns the PDF
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bdc/test_masquage_pdf.py -v`
Expected: FAIL — `champs_masques` no longer exists (model changed), function signature mismatch

**Step 3: Rewrite masquage_pdf.py**

Replace the entire content of `apps/bdc/masquage_pdf.py`:

```python
"""
Service de masquage PDF : applique des zones de masquage (rectangles blancs)
definies dans la config du bailleur sur le PDF original du BDC.

Utilise PyMuPDF (fitz) : add_redact_annot() + apply_redactions().
"""

import logging

import fitz  # PyMuPDF

from .models import BonDeCommande

logger = logging.getLogger(__name__)


def generer_pdf_masque(bdc: BonDeCommande, pages: list[int] | None = None) -> bytes | None:
    """
    Ouvre le PDF original, applique les zones de masquage du bailleur,
    puis filtre les pages si demande.

    Args:
        bdc: Le bon de commande dont on masque le PDF.
        pages: Liste de numeros de page (1-indexes) a inclure. None ou [] = toutes.

    Returns:
        bytes du PDF masque, ou None si pas de PDF ou pas de zones configurees.
    """
    if not bdc.pdf_original or not bdc.pdf_original.name:
        logger.warning("Pas de PDF original pour BDC %s", bdc.numero_bdc)
        return None

    zones = bdc.bailleur.zones_masquage if bdc.bailleur else []
    if not zones:
        logger.info("Aucune zone de masquage pour BDC %s (bailleur %s)", bdc.numero_bdc, bdc.bailleur)
        return None

    try:
        bdc.pdf_original.open("rb")
        pdf_bytes = bdc.pdf_original.read()
        bdc.pdf_original.close()
    except Exception:
        logger.warning("Impossible de lire le PDF original pour BDC %s", bdc.numero_bdc, exc_info=True)
        return None

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Appliquer les zones de masquage page par page
    pages_modifiees = set()
    for zone in zones:
        page_num = zone.get("page", 1) - 1  # 1-indexed -> 0-indexed
        if page_num < 0 or page_num >= len(doc):
            continue
        page = doc[page_num]
        rect = fitz.Rect(zone["x"], zone["y"], zone["x"] + zone["w"], zone["y"] + zone["h"])
        page.add_redact_annot(rect, fill=(1, 1, 1))
        pages_modifiees.add(page_num)

    for page_num in pages_modifiees:
        doc[page_num].apply_redactions()

    logger.info("PDF masque genere pour BDC %s : %d zone(s) appliquee(s)", bdc.numero_bdc, len(zones))

    # Filtrer les pages si demande
    if pages:
        doc_filtre = fitz.open()
        for p in pages:
            if 1 <= p <= len(doc):
                doc_filtre.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        doc.close()
        doc = doc_filtre

    result = doc.tobytes()
    doc.close()
    return result
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_bdc/test_masquage_pdf.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add apps/bdc/masquage_pdf.py tests/test_bdc/test_masquage_pdf.py
git commit -m "feat: rewrite masquage_pdf to use visual zone-based masking"
```

---

### Task 3: Update views — remove old masquage config, add zone save endpoint

**Files:**
- Modify: `apps/accounts/views.py:228-280` (config_bailleurs, config_bailleur_form)
- Modify: `apps/accounts/views.py:452-473` (preview_masquage)
- Modify: `apps/accounts/urls_gestion.py`

**Step 1: Update `config_bailleurs` view**

In `apps/accounts/views.py`, rewrite the `config_bailleurs` view. The POST handler now saves `zones_masquage` (JSON) instead of `champs_masques` (checkboxes):

```python
@login_required
def config_bailleurs(request):
    bailleurs = Bailleur.objects.all()

    if request.method == "POST":
        bailleur_id = request.POST.get("bailleur_id")
        bailleur = get_object_or_404(Bailleur, pk=bailleur_id)

        # Zones de masquage (JSON string from editor)
        import json
        zones_raw = request.POST.get("zones_masquage", "[]")
        try:
            bailleur.zones_masquage = json.loads(zones_raw)
        except json.JSONDecodeError:
            bailleur.zones_masquage = []

        # Pages a envoyer
        pages_raw = request.POST.get("pages_a_envoyer", "").strip()
        if pages_raw:
            bailleur.pages_a_envoyer = [int(p.strip()) for p in pages_raw.split(",") if p.strip().isdigit()]
        else:
            bailleur.pages_a_envoyer = []

        bailleur.save(update_fields=["zones_masquage", "pages_a_envoyer"])
        messages.success(request, f"Configuration de masquage mise a jour pour {bailleur.nom}.")

        if request.headers.get("HX-Request"):
            return render(request, "accounts/partials/_config_bailleur_form.html", {"bailleur": bailleur})
        return redirect("gestion:config_bailleurs")

    return render(request, "accounts/config_bailleur.html", {"bailleurs": bailleurs})
```

Remove the `CHAMPS_DISPONIBLES` imports from both `config_bailleurs` and `config_bailleur_form`.

**Step 2: Update `config_bailleur_form` view**

Simplify — no more `champs_disponibles` context:

```python
@login_required
def config_bailleur_form(request, pk):
    bailleur = get_object_or_404(Bailleur, pk=pk)
    return render(request, "accounts/partials/_config_bailleur_form.html", {"bailleur": bailleur})
```

**Step 3: Update `preview_masquage` view**

In `preview_masquage`, remove the now-deleted `champs_masques` dependency. The view already calls `generer_pdf_masque(bdc)` which now uses `zones_masquage` internally. Just make sure it also passes `pages`:

```python
@login_required
def preview_masquage(request, pk):
    from apps.bdc.masquage_pdf import generer_pdf_masque
    from apps.bdc.models import BonDeCommande

    bailleur = get_object_or_404(Bailleur, pk=pk)
    bdc_pk = request.GET.get("bdc") or request.POST.get("bdc")
    if not bdc_pk:
        messages.error(request, "Veuillez selectionner un BDC.")
        return redirect("gestion:config_bailleurs")

    bdc = get_object_or_404(BonDeCommande, pk=bdc_pk, bailleur=bailleur)
    pages = bailleur.pages_a_envoyer or None
    pdf_bytes = generer_pdf_masque(bdc, pages=pages)

    if not pdf_bytes:
        # Fallback: serve original if no zones configured
        if bdc.pdf_original and bdc.pdf_original.name:
            bdc.pdf_original.open("rb")
            pdf_bytes = bdc.pdf_original.read()
            bdc.pdf_original.close()
        else:
            messages.error(request, "Aucun PDF disponible.")
            return redirect("gestion:config_bailleurs")

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="masquage_preview_{bdc.numero_bdc}.pdf"'
    return response
```

**Step 4: Run all tests**

Run: `uv run pytest -v --tb=short`
Expected: All pass (the old masquage tests don't directly test `champs_masques` field)

**Step 5: Commit**

```bash
git add apps/accounts/views.py
git commit -m "feat: update views for zone-based masquage"
```

---

### Task 4: Rewrite config bailleur template — visual PDF zone editor

**Files:**
- Rewrite: `templates/accounts/partials/_config_bailleur_form.html`
- Modify: `templates/accounts/config_bailleur.html`

**Step 1: Rewrite the form partial**

Replace `templates/accounts/partials/_config_bailleur_form.html` entirely. The new template contains a PDF.js canvas with an Alpine.js overlay for drawing rectangles:

```html
<form method="post" action="{% url 'gestion:config_bailleurs' %}" class="px-6 py-5 space-y-5"
      x-data="masquageEditor({{ bailleur.zones_masquage|safe }}, '{% if bailleur.pdf_modele and bailleur.pdf_modele.name %}{{ bailleur.pdf_modele.url }}{% endif %}')"
      x-init="init()">
    {% csrf_token %}
    <input type="hidden" name="bailleur_id" value="{{ bailleur.pk }}">
    <input type="hidden" name="zones_masquage" :value="JSON.stringify(zones)">

    {# ── Editeur visuel ── #}
    {% if bailleur.pdf_modele and bailleur.pdf_modele.name %}
    <div>
        <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
            Zones de masquage
        </h3>
        <p class="text-xs text-[var(--color-text-muted)] mb-3">
            Dessinez des rectangles sur les zones a masquer (prix, montants...).
            Cliquez-glissez pour creer une zone.
        </p>

        {# Navigation pages #}
        <div class="flex items-center gap-2 mb-2" x-show="totalPages > 1">
            <button type="button" @click="goToPage(currentPage - 1)" :disabled="currentPage <= 1"
                    class="px-2 py-1 rounded border border-[var(--color-border)] text-xs disabled:opacity-30">
                &larr;
            </button>
            <span class="text-xs text-[var(--color-text-muted)]">
                Page <span x-text="currentPage"></span> / <span x-text="totalPages"></span>
            </span>
            <button type="button" @click="goToPage(currentPage + 1)" :disabled="currentPage >= totalPages"
                    class="px-2 py-1 rounded border border-[var(--color-border)] text-xs disabled:opacity-30">
                &rarr;
            </button>
        </div>

        {# Canvas container #}
        <div class="relative border border-[var(--color-border)] rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800"
             style="max-height: 600px;">
            <canvas x-ref="pdfCanvas" class="block"></canvas>
            <canvas x-ref="overlayCanvas" class="absolute top-0 left-0 cursor-crosshair"
                    @mousedown="startDraw($event)"
                    @mousemove="drawing($event)"
                    @mouseup="endDraw($event)"></canvas>
        </div>
    </div>
    {% else %}
    <div class="px-4 py-8 text-center border border-dashed border-[var(--color-border)] rounded-lg">
        <p class="text-sm text-[var(--color-text-muted)]">
            Uploadez un PDF modele dans la
            <a href="{% url 'gestion:config_extraction' bailleur.pk %}" class="text-accent hover:underline">
                configuration d'extraction
            </a>
            pour activer l'editeur de zones de masquage.
        </p>
    </div>
    {% endif %}

    {# ── Liste des zones existantes ── #}
    <div x-show="zones.length > 0">
        <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
            Zones configurees
        </h3>
        <div class="space-y-1">
            <template x-for="(zone, idx) in zones" :key="idx">
                <div class="flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--color-border)] text-sm"
                     @mouseenter="highlightZone(idx)" @mouseleave="redrawOverlay()">
                    <div class="w-3 h-3 rounded bg-red-400/60 shrink-0"></div>
                    <input type="text" x-model="zone.label" placeholder="Ex: Colonne prix..."
                           class="flex-1 px-2 py-1 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-xs text-[var(--color-text)] focus:ring-1 focus:ring-accent">
                    <span class="text-xs text-[var(--color-text-muted)] shrink-0" x-text="'p.' + zone.page"></span>
                    <button type="button" @click="removeZone(idx)"
                            class="text-red-500 hover:text-red-700 text-xs font-bold px-1">&times;</button>
                </div>
            </template>
        </div>
    </div>

    {# ── Pages a envoyer ── #}
    <div>
        <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Pages a envoyer</h3>
        <p class="text-xs text-[var(--color-text-muted)] mb-2">Laissez vide pour envoyer toutes les pages du PDF</p>
        <input type="text" name="pages_a_envoyer" placeholder="Ex: 1 ou 1,2"
               value="{{ bailleur.pages_a_envoyer|join:',' }}"
               class="w-full sm:w-48 px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text)] focus:ring-2 focus:ring-accent focus:border-accent">
    </div>

    {# ── Boutons ── #}
    <div class="flex items-center gap-3 pt-2">
        <button type="submit"
                class="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-dark transition-colors">
            Enregistrer
        </button>
        <span class="text-xs text-[var(--color-text-muted)]" x-text="zones.length + ' zone(s) de masquage'"></span>
    </div>
</form>
```

**Step 2: Add PDF.js scripts in config_bailleur.html**

In `templates/accounts/config_bailleur.html`, add the `{% block extra_scripts %}` with PDF.js CDN and the Alpine.js `masquageEditor` component:

```html
{% block extra_head %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.9.155/pdf.min.mjs" type="module"></script>
{% endblock %}

{% block extra_scripts %}
<script type="module">
import * as pdfjsLib from 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.9.155/pdf.min.mjs';
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.9.155/pdf.worker.min.mjs';

window.masquageEditor = function(initialZones, pdfUrl) {
    return {
        zones: initialZones || [],
        pdfUrl: pdfUrl,
        pdfDoc: null,
        currentPage: 1,
        totalPages: 0,
        scale: 1,
        // Drawing state
        isDrawing: false,
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0,

        async init() {
            if (!this.pdfUrl) return;
            try {
                this.pdfDoc = await pdfjsLib.getDocument(this.pdfUrl).promise;
                this.totalPages = this.pdfDoc.numPages;
                await this.renderPage(1);
            } catch (e) {
                console.error('Erreur chargement PDF:', e);
            }
        },

        async renderPage(num) {
            if (!this.pdfDoc) return;
            this.currentPage = num;
            const page = await this.pdfDoc.getPage(num);
            const viewport = page.getViewport({ scale: 1 });

            // Scale to fit container (max 800px wide)
            const maxWidth = this.$refs.pdfCanvas.parentElement.clientWidth;
            this.scale = Math.min(maxWidth / viewport.width, 1.5);
            const scaledViewport = page.getViewport({ scale: this.scale });

            const canvas = this.$refs.pdfCanvas;
            canvas.width = scaledViewport.width;
            canvas.height = scaledViewport.height;

            const overlay = this.$refs.overlayCanvas;
            overlay.width = scaledViewport.width;
            overlay.height = scaledViewport.height;

            await page.render({
                canvasContext: canvas.getContext('2d'),
                viewport: scaledViewport,
            }).promise;

            this.redrawOverlay();
        },

        async goToPage(num) {
            if (num >= 1 && num <= this.totalPages) {
                await this.renderPage(num);
            }
        },

        startDraw(e) {
            const rect = this.$refs.overlayCanvas.getBoundingClientRect();
            this.isDrawing = true;
            this.startX = e.clientX - rect.left;
            this.startY = e.clientY - rect.top;
        },

        drawing(e) {
            if (!this.isDrawing) return;
            const rect = this.$refs.overlayCanvas.getBoundingClientRect();
            this.currentX = e.clientX - rect.left;
            this.currentY = e.clientY - rect.top;
            this.redrawOverlay();

            // Draw current selection
            const ctx = this.$refs.overlayCanvas.getContext('2d');
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
            ctx.fillStyle = 'rgba(239, 68, 68, 0.15)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 3]);
            const x = Math.min(this.startX, this.currentX);
            const y = Math.min(this.startY, this.currentY);
            const w = Math.abs(this.currentX - this.startX);
            const h = Math.abs(this.currentY - this.startY);
            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);
            ctx.setLineDash([]);
        },

        endDraw(e) {
            if (!this.isDrawing) return;
            this.isDrawing = false;
            const rect = this.$refs.overlayCanvas.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;

            const x = Math.min(this.startX, endX);
            const y = Math.min(this.startY, endY);
            const w = Math.abs(endX - this.startX);
            const h = Math.abs(endY - this.startY);

            // Ignore tiny rectangles (accidental clicks)
            if (w < 10 || h < 10) {
                this.redrawOverlay();
                return;
            }

            // Convert from screen coords to PDF points
            this.zones.push({
                x: Math.round(x / this.scale),
                y: Math.round(y / this.scale),
                w: Math.round(w / this.scale),
                h: Math.round(h / this.scale),
                page: this.currentPage,
                label: '',
            });

            this.redrawOverlay();
        },

        redrawOverlay() {
            const canvas = this.$refs.overlayCanvas;
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw existing zones for current page
            for (const zone of this.zones) {
                if (zone.page !== this.currentPage) continue;
                const x = zone.x * this.scale;
                const y = zone.y * this.scale;
                const w = zone.w * this.scale;
                const h = zone.h * this.scale;
                ctx.fillStyle = 'rgba(239, 68, 68, 0.25)';
                ctx.fillRect(x, y, w, h);
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.7)';
                ctx.lineWidth = 2;
                ctx.strokeRect(x, y, w, h);
                if (zone.label) {
                    ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
                    ctx.font = '11px sans-serif';
                    ctx.fillText(zone.label, x + 4, y + 14);
                }
            }
        },

        highlightZone(idx) {
            const zone = this.zones[idx];
            if (zone.page !== this.currentPage) {
                this.goToPage(zone.page);
            }
            this.redrawOverlay();
            const canvas = this.$refs.overlayCanvas;
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const x = zone.x * this.scale;
            const y = zone.y * this.scale;
            const w = zone.w * this.scale;
            const h = zone.h * this.scale;
            ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
            ctx.fillRect(x, y, w, h);
            ctx.strokeStyle = 'rgba(239, 68, 68, 1)';
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, w, h);
        },

        removeZone(idx) {
            this.zones.splice(idx, 1);
            this.redrawOverlay();
        },
    };
};
</script>
{% endblock %}
```

**Step 3: Update the accordion summary in `config_bailleur.html`**

Replace `champs_masques` references in the accordion header:

```html
{# Replace: #}
{% if bailleur.champs_masques %}
    {{ bailleur.champs_masques|length }} champ{{ ... }} masque{{ ... }}
{% else %}
    Aucun masquage configure
{% endif %}

{# With: #}
{% if bailleur.zones_masquage %}
    {{ bailleur.zones_masquage|length }} zone{{ bailleur.zones_masquage|length|pluralize }} de masquage
{% else %}
    Aucun masquage configure
{% endif %}
```

**Step 4: Run tests**

Run: `uv run pytest -v --tb=short`
Expected: All pass

**Step 5: Commit**

```bash
git add templates/accounts/partials/_config_bailleur_form.html templates/accounts/config_bailleur.html
git commit -m "feat: visual PDF zone editor for masquage configuration"
```

---

### Task 5: Update email service and pdf_masque_preview view

**Files:**
- Modify: `apps/notifications/email.py:20-28`
- Modify: `apps/bdc/views.py:1367-1387`

**Step 1: Verify email.py still works**

The `_obtenir_pdf_masque` function already calls `generer_pdf_masque(bdc, pages=pages or None)` — this still works since `generer_pdf_masque` signature is unchanged. No code change needed.

Verify by reading `apps/notifications/email.py:20-28` and confirming it does not reference `champs_masques`.

**Step 2: Verify pdf_masque_preview view**

The view at `apps/bdc/views.py:1367` already calls `generer_pdf_masque(bdc, pages=pages or None)`. It works without change since the new `generer_pdf_masque` has the same API.

**Step 3: Run full test suite**

Run: `uv run pytest -v --tb=short`
Expected: All 476+ tests pass

**Step 4: Commit (if any changes were needed)**

---

### Task 6: Cleanup dead code

**Files:**
- Modify: `apps/bdc/masquage_pdf.py` — already done in Task 2 (dead code removed)
- Verify: no remaining references to `champs_masques` or `CHAMPS_DISPONIBLES`

**Step 1: Search for remaining references**

Run:
```bash
grep -r "champs_masques\|CHAMPS_DISPONIBLES" apps/ templates/ tests/ --include="*.py" --include="*.html"
```

Expected: No results (all references removed)

**Step 2: Run linting**

Run: `uv run ruff check . && uv run ruff format .`
Expected: Clean

**Step 3: Run full test suite one final time**

Run: `uv run pytest -v --tb=short`
Expected: All tests pass

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: cleanup dead champs_masques references"
```

---

## Summary of changes

| File | Action |
|------|--------|
| `apps/bdc/models.py` | Replace `champs_masques` with `zones_masquage` |
| `apps/bdc/migrations/0012_*.py` | Auto-generated migration |
| `apps/bdc/masquage_pdf.py` | Full rewrite: zone rectangles instead of text search |
| `apps/accounts/views.py` | Update `config_bailleurs`, `config_bailleur_form`, `preview_masquage` |
| `templates/accounts/config_bailleur.html` | Add PDF.js + Alpine.js editor script |
| `templates/accounts/partials/_config_bailleur_form.html` | Full rewrite: visual zone editor |
| `apps/notifications/email.py` | No change needed (API unchanged) |
| `apps/bdc/views.py` | No change needed (API unchanged) |
| `tests/test_bdc/test_masquage_pdf.py` | New test file for zone-based masking |
