from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag
def news_json_ld(article, language='uk'):
    """
    Генерує JSON-LD розмітку для Google News
    Критично важливо для Google News індексації!
    """
    try:
        # Отримуємо базові дані статті
        title = article.get_title(language)
        summary = article.get_summary(language)
        published_date = article.published_at or article.updated_at
        
        # Конвертуємо дату в UTC ISO формат
        if published_date:
            published_iso = published_date.astimezone(timezone.utc).isoformat()
        else:
            published_iso = timezone.now().astimezone(timezone.utc).isoformat()
        
        # Підготовляємо JSON-LD структуру
        json_ld = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": summary,
            "datePublished": published_iso,
            "dateModified": published_iso,
            "author": {
                "@type": "Organization",
                "name": "LazySoft",
                "url": "https://lazysoft.pl"
            },
            "publisher": {
                "@type": "Organization",
                "name": "LazySoft",
                "url": "https://lazysoft.pl",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://lazysoft.pl/static/images/logo.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"https://lazysoft.pl/news/article/{article.uuid}/"
            },
            "articleSection": "Technology",
            "keywords": _get_article_keywords(article, language),
            "inLanguage": language,
            "isAccessibleForFree": True,
            "copyrightYear": published_date.year if published_date else timezone.now().year,
            "copyrightHolder": {
                "@type": "Organization",
                "name": "LazySoft"
            }
        }
        
        # Додаємо зображення якщо є
        if hasattr(article, 'ai_image_url') and article.ai_image_url:
            json_ld["image"] = {
                "@type": "ImageObject",
                "url": article.ai_image_url,
                "width": 1200,
                "height": 630
            }
        
        # Додаємо категорію якщо є
        if article.category:
            json_ld["articleSection"] = article.category.get_name(language)
        
        # Додаємо теги якщо є
        if hasattr(article, 'tags') and article.tags.exists():
            tags = [tag.get_name(language) for tag in article.tags.all()]
            json_ld["keywords"] = ", ".join(tags)
        
        # Конвертуємо в JSON з правильним форматуванням
        json_str = json.dumps(json_ld, indent=2, ensure_ascii=False)
        
        return mark_safe(f'<script type="application/ld+json">\n{json_str}\n</script>')
        
    except Exception as e:
        print(f"Error generating JSON-LD for article {article.uuid}: {e}")
        return ""


def _get_article_keywords(article, language='uk'):
    """Отримує ключові слова для статті"""
    keywords = []
    
    # Додаємо категорію
    if article.category:
        keywords.append(article.category.get_name(language))
    
    # Додаємо теги
    if hasattr(article, 'tags') and article.tags.exists():
        keywords.extend([tag.get_name(language) for tag in article.tags.all()])
    
    # Додаємо базові ключові слова
    base_keywords = {
        'uk': ['AI', 'технології', 'автоматизація', 'бізнес', 'інновації'],
        'pl': ['AI', 'technologie', 'automatyzacja', 'biznes', 'innowacje'],
        'en': ['AI', 'technology', 'automation', 'business', 'innovation']
    }
    
    keywords.extend(base_keywords.get(language, base_keywords['uk']))
    
    # Видаляємо дублікати та обмежуємо кількість
    unique_keywords = list(dict.fromkeys(keywords))[:10]
    return ", ".join(unique_keywords)


@register.simple_tag
def news_organization_json_ld():
    """
    Генерує JSON-LD розмітку для організації (LazySoft)
    """
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "LazySoft",
        "url": "https://lazysoft.pl",
        "logo": "https://lazysoft.pl/static/images/logo.png",
        "description": "AI-powered business automation and technology solutions",
        "foundingDate": "2024",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "PL"
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "url": "https://lazysoft.pl/contacts/"
        },
        "sameAs": [
            "https://www.linkedin.com/company/lazysoft",
            "https://twitter.com/lazysoft"
        ]
    }
    
    json_str = json.dumps(json_ld, indent=2, ensure_ascii=False)
    return mark_safe(f'<script type="application/ld+json">\n{json_str}\n</script>')


@register.simple_tag
def news_website_json_ld():
    """
    Генерує JSON-LD розмітку для веб-сайту
    """
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "LazySoft",
        "url": "https://lazysoft.pl",
        "description": "AI-powered business automation and technology solutions",
        "publisher": {
            "@type": "Organization",
            "name": "LazySoft"
        },
        "potentialAction": {
            "@type": "SearchAction",
            "target": "https://lazysoft.pl/search/?q={search_term_string}",
            "query-input": "required name=search_term_string"
        }
    }
    
    json_str = json.dumps(json_ld, indent=2, ensure_ascii=False)
    return mark_safe(f'<script type="application/ld+json">\n{json_str}\n</script>')
