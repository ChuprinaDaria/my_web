from django import template
import json
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('news/json_ld.html', takes_context=True)
def news_json_ld(context, article):
    """
    Генерує JSON-LD розмітку для новинної статті
    """
    request = context.get('request')
    
    # Формуємо абсолютний URL зображення
    image_url = ""
    if hasattr(article, 'ai_image_url') and article.ai_image_url:
        if request:
            image_url = request.build_absolute_uri(article.ai_image_url)
        else:
            image_url = article.ai_image_url  # ai_image_url вже містить повний URL
    
    # Формуємо абсолютний URL статті
    article_url = ""
    if request:
        article_url = request.build_absolute_uri(article.get_absolute_url())
    else:
        article_url = f"https://lazysoft.pl{article.get_absolute_url()}"
    
    # Отримуємо заголовок статті для поточної мови
    from django.utils.translation import get_language
    current_language = get_language() or 'uk'
    title = article.get_title(current_language)
    
    # Базова структура Schema.org NewsArticle
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title[:110],  # Google максимум 110 символів
        "datePublished": article.published_at.isoformat() if article.published_at else article.created_at.isoformat(),
        "dateModified": article.updated_at.isoformat(),
        "author": {
            "@type": "Organization",
            "name": "LazySoft",
            "url": "https://lazysoft.pl"
        },
        "publisher": {
            "@type": "Organization",
            "name": "LazySoft",
            "logo": {
                "@type": "ImageObject",
                "url": "https://lazysoft.pl/static/images/logo.svg",  # Логотип LazySoft
                "width": 600,
                "height": 60
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": article_url
        }
    }
    
    # Додаємо зображення якщо є
    if image_url:
        schema["image"] = [image_url]
    
    # Додаємо опис якщо є
    meta_description = article.get_meta_description(current_language)
    if meta_description:
        schema["description"] = meta_description[:160]
    else:
        summary = article.get_summary(current_language)
        schema["description"] = summary[:160] if summary else title[:160]
    
    # Додаємо категорію якщо є
    if hasattr(article, 'category') and article.category:
        if hasattr(article.category, 'get_name'):
            schema["articleSection"] = article.category.get_name(current_language)
        else:
            schema["articleSection"] = str(article.category)
    
    return {
        'schema_json': json.dumps(schema, ensure_ascii=False, indent=2)
    }
