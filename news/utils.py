import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
from django.utils import timezone
from django.conf import settings


def clean_html_text(text: str) -> str:
    """
    Очищає HTML теги з тексту та нормалізує пробіли
    
    Args:
        text: Текст з HTML тегами
        
    Returns:
        Очищений текст
    """
    if not text:
        return ""
    
    # Видаляємо HTML теги
    text = re.sub(r'<[^>]+>', '', str(text))
    
    # Декодуємо HTML entities
    import html
    text = html.unescape(text)
    
    # Нормалізуємо пробіли
    text = re.sub(r'\s+', ' ', text)
    
    # Видаляємо пробіли на початку та кінці
    return text.strip()


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Нормалізує URL (додає схему, домен тощо)
    
    Args:
        url: Оригінальний URL
        base_url: Базовий URL для відносних посилань
        
    Returns:
        Нормалізований URL
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Якщо URL відносний і є базовий URL
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Додаємо схему якщо відсутня
    if url.startswith('//'):
        url = 'https:' + url
    elif not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


def generate_content_hash(*args) -> str:
    """
    Генерує SHA-256 хеш для контенту
    
    Args:
        *args: Аргументи для хешування
        
    Returns:
        Хеш рядок
    """
    content = ''.join(str(arg) for arg in args)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def extract_domain_from_url(url: str) -> str:
    """
    Витягує домен з URL
    
    Args:
        url: URL адреса
        
    Returns:
        Домен
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def is_recent_article(published_date: datetime, max_age_days: int = 7) -> bool:
    """
    Перевіряє чи стаття свіжа
    
    Args:
        published_date: Дата публікації
        max_age_days: Максимальний вік в днях
        
    Returns:
        True якщо стаття свіжа
    """
    if not published_date:
        return True  # Якщо дата невідома, вважаємо свіжою
    
    cutoff_date = timezone.now() - timedelta(days=max_age_days)
    return published_date >= cutoff_date


def detect_article_language(text: str) -> str:
    """
    Простий детектор мови статті
    
    Args:
        text: Текст статті
        
    Returns:
        Код мови ('en', 'uk', 'pl', 'unknown')
    """
    if not text:
        return 'unknown'
    
    text_lower = text.lower()
    
    # Українські слова-маркери
    ukrainian_words = [
        'україна', 'український', 'київ', 'львів', 'одеса', 'дніпро',
        'що', 'який', 'може', 'буде', 'має', 'його', 'неї', 'цей',
        'компанія', 'бізнес', 'технології', 'розробка'
    ]
    
    # Польські слова-маркери  
    polish_words = [
        'polska', 'polski', 'warszawa', 'kraków', 'gdańsk', 'wrocław',
        'która', 'które', 'może', 'będzie', 'jego', 'jej', 'tego',
        'firma', 'biznes', 'technologie', 'rozwój'
    ]
    
    # Англійські слова-маркери
    english_words = [
        'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you',
        'this', 'but', 'his', 'from', 'they', 'she', 'her', 'been',
        'company', 'business', 'technology', 'development', 'market'
    ]
    
    # Підраховуємо збіги
    ukrainian_count = sum(1 for word in ukrainian_words if word in text_lower)
    polish_count = sum(1 for word in polish_words if word in text_lower)
    english_count = sum(1 for word in english_words if word in text_lower)
    
    # Визначаємо мову
    if ukrainian_count > polish_count and ukrainian_count > english_count:
        return 'uk'
    elif polish_count > english_count:
        return 'pl'
    elif english_count > 0:
        return 'en'
    else:
        return 'unknown'


def sanitize_filename(filename: str) -> str:
    """
    Очищає назву файлу від небезпечних символів
    
    Args:
        filename: Оригінальна назва файлу
        
    Returns:
        Безпечна назва файлу
    """
    # Видаляємо небезпечні символи
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Замінюємо пробіли на підкреслення
    filename = re.sub(r'[\s_-]+', '_', filename)
    # Обмежуємо довжину
    return filename[:100].strip('_')


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Обрізає текст до максимальної довжини
    
    Args:
        text: Оригінальний текст
        max_length: Максимальна довжина
        suffix: Суфікс для обрізаного тексту
        
    Returns:
        Обрізаний текст
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].strip() + suffix


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Витягує ключові слова з тексту (простий алгоритм)
    
    Args:
        text: Текст для аналізу
        max_keywords: Максимальна кількість ключових слів
        
    Returns:
        Список ключових слів
    """
    if not text:
        return []
    
    # Очищаємо текст
    text = clean_html_text(text).lower()
    
    # Стоп-слова (базовий набір)
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'a', 'an', 'as', 'it', 'its', 'he', 'she', 'him', 'her', 'his',
        'їх', 'він', 'вона', 'вони', 'який', 'яка', 'які', 'що', 'де',
        'коли', 'як', 'чому', 'тому', 'але', 'або', 'та', 'і', 'в', 'на',
        'za', 'w', 'i', 'a', 'o', 'z', 'do', 'od', 'po', 'przez', 'dla'
    }
    
    # Витягуємо слова
    words = re.findall(r'\b[a-zA-Zа-яїієґА-ЯЇІЄҐ]{3,}\b', text)
    
    # Фільтруємо та підраховуємо
    word_count = {}
    for word in words:
        if word.lower() not in stop_words and len(word) >= 3:
            word_count[word.lower()] = word_count.get(word.lower(), 0) + 1
    
    # Сортуємо за частотою
    keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    return [keyword[0] for keyword in keywords[:max_keywords]]


def validate_rss_url(url: str) -> bool:
    """
    Перевіряє чи URL схожий на RSS фід
    
    Args:
        url: URL для перевірки
        
    Returns:
        True якщо URL схожий на RSS
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Типові патерни RSS URL
    rss_patterns = [
        'rss', 'feed', 'atom', 'xml',
        '/rss/', '/feed/', '/atom/', '/xml/',
        'rss.xml', 'feed.xml', 'atom.xml'
    ]
    
    return any(pattern in url_lower for pattern in rss_patterns)


def get_article_reading_time(content: str, words_per_minute: int = 200) -> int:
    """
    Оцінює час читання статті
    
    Args:
        content: Контент статті
        words_per_minute: Слів за хвилину (середня швидкість читання)
        
    Returns:
        Час читання в хвилинах
    """
    if not content:
        return 0
    
    # Підраховуємо кількість слів
    words = len(re.findall(r'\b\w+\b', clean_html_text(content)))
    
    # Розраховуємо час
    minutes = max(1, round(words / words_per_minute))
    
    return minutes


def format_article_summary(title: str, summary: str, max_length: int = 300) -> str:
    """
    Форматує короткий опис статті
    
    Args:
        title: Заголовок статті
        summary: Оригінальний опис
        max_length: Максимальна довжина
        
    Returns:
        Відформатований опис
    """
    if not summary:
        # Якщо немає опису, використовуємо початок заголовка
        summary = title
    
    # Очищаємо HTML
    summary = clean_html_text(summary)
    
    # Обрізаємо до потрібної довжини
    summary = truncate_text(summary, max_length)
    
    # Переконуємося що закінчується крапкою
    if summary and not summary.endswith('.'):
        summary += '.'
    
    return summary


def get_rss_source_stats() -> Dict:
    """
    Повертає статистику RSS джерел
    
    Returns:
        Словник зі статистикою
    """
    from .models import RSSSource, RawArticle
    from django.db.models import Count, Q
    
    total_sources = RSSSource.objects.count()
    active_sources = RSSSource.objects.filter(is_active=True).count()
    
    # Статистика по мовах
    language_stats = RSSSource.objects.values('language').annotate(
        count=Count('id'),
        active_count=Count('id', filter=Q(is_active=True))
    )
    
    # Статистика по категоріях
    category_stats = RSSSource.objects.values('category').annotate(
        count=Count('id'),
        active_count=Count('id', filter=Q(is_active=True))
    )
    
    # Статистика статей
    total_articles = RawArticle.objects.count()
    processed_articles = RawArticle.objects.filter(is_processed=True).count()
    
    return {
        'total_sources': total_sources,
        'active_sources': active_sources,
        'inactive_sources': total_sources - active_sources,
        'language_distribution': list(language_stats),
        'category_distribution': list(category_stats),
        'total_articles': total_articles,
        'processed_articles': processed_articles,
        'pending_articles': total_articles - processed_articles,
        'processing_rate': round((processed_articles / total_articles * 100), 2) if total_articles > 0 else 0
    }