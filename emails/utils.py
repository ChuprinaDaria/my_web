from typing import Tuple, Optional, List
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import override


def render_quote_email_bodies(context: dict) -> Tuple[str, str]:
    """Render HTML and plain-text email bodies for the quote email using i18n."""
    language = (context.get('language') or getattr(settings, 'LANGUAGE_CODE', 'uk')).lower()
    with override(language):
        html_body = render_to_string('emails/quote_email.html', context)
        text_body = render_to_string('emails/quote_email.txt', context)
    return html_body, text_body


def send_email_with_pdf(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    reply_to: Optional[List[str]] = None,
    bcc_admin: bool = True,
) -> bool:
    """Send an email with HTML + plain text alternative and optional PDF attachment."""
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost')
    admin_email = getattr(settings, 'SALES_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)

    if not text_body:
        # Fallback plain text if not provided
        text_body = 'Please see the attached PDF for your quote.'

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[to_email],
            bcc=[admin_email] if (bcc_admin and admin_email) else None,
            reply_to=reply_to or None,
        )
        message.attach_alternative(html_body, 'text/html')
        if pdf_bytes:
            message.attach('proposal.pdf', pdf_bytes, 'application/pdf')
        message.send(fail_silently=False)
        return True
    except Exception:
        return False
