# news/management/commands/post_telegram.py
from django.core.management.base import BaseCommand
from django.utils.translation import override
from django.utils.html import escape
from django.conf import settings
from news.models import ProcessedArticle
from news.services.telegram import tg_send_photo, tg_send_message

SITE_URL = getattr(settings, "SITE_URL", "https://lazysoft.dev")

def clamp(s: str, n: int) -> str:
    if not s:
        return ""
    s = str(s).strip()
    return (s[: n - 1] + "…") if len(s) > n else s

def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "\n".join(str(x).strip() for x in value if x is not None and str(x).strip())
    if isinstance(value, dict):
        return "\n".join(f"{k}: {as_text(v).strip()}" for k, v in value.items() if k or v)
    return str(value)

def first_nonempty(*values) -> str:
    for v in values:
        t = as_text(v).strip()
        if t:
            return t
    return ""

def bullets(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(f"• {ln}" for ln in lines) if lines else ""

def get_localized(article, base: str, lang: str, strict: bool) -> str:
    # Якщо strict=True — беремо ТІЛЬКИ поточну мову (інакше — з фолбеком)
    primary = as_text(getattr(article, f"{base}_{lang}", None)).strip()
    if strict:
        return primary  # без фолбеків
    return first_nonempty(
        primary,
        getattr(article, "title_uk" if base == "title" else f"{base}_uk", None),
        getattr(article, "title_en" if base == "title" else f"{base}_en", None),
        getattr(article, "title_pl" if base == "title" else f"{base}_pl", None),
    )

class Command(BaseCommand):
    help = "Публікує останню (або обрану) статтю в Telegram красивим постом"

    def add_arguments(self, parser):
        parser.add_argument("--lang", default="uk", help="Мова публікації: uk/en/pl")
        parser.add_argument("--id", type=int, help="ID статті (опц.)")
        parser.add_argument("--uuid", type=str, help="UUID статті (опц.)")
        parser.add_argument("--strict-lang", action="store_true",
                            help="Публікувати ТІЛЬКИ якщо є контент саме цією мовою (без фолбеків).")

    def handle(self, *args, **opts):
        lang = opts["lang"]
        strict = bool(opts.get("strict_lang"))

        qs = ProcessedArticle.objects.filter(status="published")
        if opts.get("id"):
            qs = qs.filter(id=opts["id"])
        if opts.get("uuid"):
            qs = qs.filter(uuid=opts["uuid"])

        article = qs.order_by("-published_at", "-created_at").first()
        if not article:
            self.stdout.write(self.style.ERROR("Немає опублікованих статей під умови відбору"))
            return

        # Локалізовані поля
        title = get_localized(article, "title", lang, strict)
        summary = get_localized(article, "summary", lang, strict)
        insight_text = get_localized(article, "insight", lang, strict)
        takeaways_text = get_localized(article, "key_takeaways", lang, strict)

        if strict:
            missing = []
            if not title: missing.append("title")
            if not summary: missing.append("summary")
            # insight/takeaways — опційні
            if missing:
                self.stdout.write(self.style.ERROR(
                    f"❌ Відсутні поля для мови '{lang}': {', '.join(missing)}. Публікацію скасовано (strict-lang)."
                ))
                return

        if takeaways_text:
            takeaways_text = bullets(takeaways_text)

        with override(lang):
            path = article.get_absolute_url(lang)
        url = f"{SITE_URL}{path}"

        # Формуємо caption з правильним форматуванням
        title_part = f"🔥 *{escape(clamp(title, 140))}*\n\n" if title else ""
        summary_part = f"{escape(clamp(summary, 400))}\n\n" if summary else ""
        footer = "— Lazysoft AI News"
        caption = f"{title_part}{summary_part}{footer}"

        # Кнопка (посилання тільки в кнопці)
        button = {"inline_keyboard": [[{"text": "📖 Читати далі", "url": url}]]}

        # Фото: перевіряємо кілька джерел і логумо стан
        photo = getattr(article, "ai_image_url", None) or getattr(article, "image_url", None)
        if not photo:
            self.stdout.write(self.style.WARNING("⚠️ У статті немає зображення (ai_image_url / image_url порожні)."))

        if photo:
            msg_id = tg_send_photo(photo, caption, language=lang, reply_markup=button, unpin=True)
        else:
            # надсилаємо без сирого URL у тексті — лише з кнопкою
            msg_id = tg_send_message(caption, language=lang, reply_markup=button, unpin=True)

        self.stdout.write(self.style.SUCCESS(f"✅ Опубліковано в Telegram (msg_id={msg_id})"))
