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
    
    # Формуємо абсолютний URL зображення (завжди потрібен для схеми)
    image_url = ""
    if hasattr(article, 'ai_image_url') and article.ai_image_url:
        if request:
            image_url = request.build_absolute_uri(article.ai_image_url)
        else:
            image_url = article.ai_image_url  # ai_image_url вже містить повний URL
    elif hasattr(article, 'featured_image') and article.featured_image:
        if request:
            image_url = request.build_absolute_uri(article.featured_image.url)
        else:
            image_url = f"https://lazysoft.pl{article.featured_image.url}"
    else:
        # Fallback до default зображення
        image_url = "https://lazysoft.pl/static/images/default-news.png"
    
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
            "name": "LAZYSOFT",
            "url": "https://lazysoft.pl",
            "@id": "https://lazysoft.pl/#organization"
        },
        "publisher": {
            "@type": "Organization",
            "name": "LAZYSOFT",
            "url": "https://lazysoft.pl",
            "logo": {
                "@type": "ImageObject",
                "url": "https://lazysoft.pl/static/images/logo.png",
                "width": 200,
                "height": 60
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": article_url
        }
    }
    
    # Додаємо зображення (завжди обов'язкове для NewsArticle)
    schema["image"] = image_url
    
    # Додаємо URL статті
    schema["url"] = article_url
    
    # Додаємо мову
    schema["inLanguage"] = current_language
    
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
