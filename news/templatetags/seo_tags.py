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
            image_url = f"https://lazysoft.pl{article.ai_image_url}"
    
    # Формуємо абсолютний URL статті
    article_url = ""
    if request:
        article_url = request.build_absolute_uri(article.get_absolute_url())
    else:
        article_url = f"https://lazysoft.pl{article.get_absolute_url()}"
    
    # Отримуємо заголовок статті
    title = article.get_title('uk') if hasattr(article, 'get_title') else str(article.title)
    
    # Базова структура Schema.org NewsArticle
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title[:110],  # Google максимум 110 символів
        "datePublished": article.published_at.isoformat() if article.published_at else article.created_at.isoformat(),
        "dateModified": article.updated_at.isoformat() if article.updated_at else article.created_at.isoformat(),
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
    if hasattr(article, 'meta_description') and article.meta_description:
        schema["description"] = article.meta_description[:160]
    elif hasattr(article, 'get_summary') and article.get_summary('uk'):
        schema["description"] = article.get_summary('uk')[:160]
    else:
        schema["description"] = title[:160]
    
    # Додаємо категорію якщо є
    if hasattr(article, 'category') and article.category:
        if hasattr(article.category, 'get_name'):
            schema["articleSection"] = article.category.get_name('uk')
        else:
            schema["articleSection"] = str(article.category)
    
    return {
        'schema_json': json.dumps(schema, ensure_ascii=False, indent=2)
    }
