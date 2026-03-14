from decimal import Decimal, InvalidOperation

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

NBSP = "\u00a0"  # espace insecable
EM_DASH = "\u2014"  # tiret cadratin


@register.filter
def montant(value):
    """Formate un nombre en montant : 3509.43 -> 3 509,43 € (avec espaces insecables)."""
    if value is None or value == "":
        return mark_safe(EM_DASH)

    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return mark_safe(EM_DASH)

    # Partie entiere et decimale
    sign = "-" if d < 0 else ""
    d = abs(d)
    entier = int(d)
    decimale = f"{d - entier:.2f}"[2:]  # 2 chiffres apres la virgule

    # Separateur de milliers avec espace insecable
    s = f"{entier:,}".replace(",", NBSP)

    return mark_safe(f"{sign}{s},{decimale}{NBSP}\u20ac")
