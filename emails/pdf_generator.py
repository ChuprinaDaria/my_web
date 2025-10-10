from typing import Tuple
from django.conf import settings
from django.template.loader import render_to_string


def generate_quote_pdf(context: dict) -> Tuple[str, bytes | None]:
    """Render 'quotes/proposal.html' and convert to PDF.
    Tries WeasyPrint first; if it fails, falls back to a minimal ReportLab PDF,
    so the email always includes a valid PDF attachment.
    Returns (html_for_reference, pdf_bytes).
    """
    html = render_to_string('quotes/proposal.html', context)
    pdf_bytes: bytes | None = None
    # Try WeasyPrint (best fidelity with HTML/CSS)
    try:
        from weasyprint import HTML  # type: ignore
        pdf_bytes = HTML(string=html, base_url=getattr(settings, 'SITE_URL', None)).write_pdf()
        if pdf_bytes:
            return html, pdf_bytes
    except Exception:
        pdf_bytes = None

    # Fallback: generate a simple PDF via ReportLab
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        from reportlab.lib.enums import TA_LEFT

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        title = str(context.get('language') == 'pl' and 'Propozycja komercyjna' or context.get('language') == 'en' and 'Commercial Proposal' or 'Комерційна пропозиція')
        name = context.get('name') or ''
        email = context.get('email') or ''

        c.setFont('Helvetica-Bold', 16)
        c.drawString(20*mm, height - 25*mm, title)
        c.setFont('Helvetica', 11)
        c.drawString(20*mm, height - 35*mm, f"Client: {name}")
        c.drawString(20*mm, height - 42*mm, f"Email: {email}")

        y = height - 55*mm
        items = context.get('items') or []
        if items:
            c.setFont('Helvetica-Bold', 12)
            c.drawString(20*mm, y, 'Items:')
            y -= 7*mm
            c.setFont('Helvetica', 10)
            for it in items[:6]:  # limit to avoid overflow
                line = f"- {it.get('title','')} — {it.get('pkg','')} — {it.get('price','')} {it.get('currency','')}"
                c.drawString(22*mm, y, line[:100])
                y -= 6*mm
                if y < 20*mm:
                    c.showPage()
                    y = height - 20*mm

        notes = context.get('notes')
        if notes and y > 40*mm:
            c.setFont('Helvetica-Bold', 12)
            c.drawString(20*mm, y, 'Notes:')
            y -= 7*mm
            c.setFont('Helvetica', 10)
            # Simple wrapping for notes
            import textwrap
            for line in textwrap.wrap(str(notes), width=90):
                c.drawString(22*mm, y, line)
                y -= 6*mm
                if y < 20*mm:
                    c.showPage()
                    y = height - 20*mm

        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
    except Exception:
        pdf_bytes = None

    return html, pdf_bytes
