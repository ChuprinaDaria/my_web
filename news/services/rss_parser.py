import hashlib
import logging
import requests
import feedparser
import time
from datetime import datetime, timezone, time as datetime_time
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone as django_timezone
from django.db import transaction
from ..models import RSSSource, RawArticle

logger = logging.getLogger(__name__)


@dataclass
class ParsedArticle:
    """Структура распарсеної статті"""
    title: str
    content: str
    summary: str
    url: str
    author: str
    published_at: datetime
    content_hash: str
    
    def __post_init__(self):
        """Генеруємо хеш після ініціалізації"""
        if not self.content_hash:
            self.content_hash = self._generate_content_hash()
    
    def _generate_content_hash(self) -> str:
        """Генеруємо SHA-256 хеш для детекції дублікатів"""
        content_for_hash = f"{self.title}{self.content}{self.url}"
        return hashlib.sha256(content_for_hash.encode('utf-8')).hexdigest()


class RSSParserError(Exception):
    """Базова помилка RSS парсера"""
    pass


class RSSFetchError(RSSParserError):
    """Помилка завантаження RSS фіду"""
    pass


class RSSParseError(RSSParserError):
    """Помилка парсингу RSS контенту"""
    pass


class RSSParser:
    """Головний RSS парсер для новинних джерел"""
    
    def __init__(self):
        self.session = requests.Session()
        self.target_date = None  
        self.date_filter_enabled = True  
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36 LAZYSOFT-NewsBot/1.0'
            )
        })
        self.session.timeout = 30
        
        # Налаштування логування
        self.logger = logging.getLogger(__name__)
        
        # Статистика парсингу
        self.stats = {
            'total_sources': 0,
            'successful_sources': 0,
            'failed_sources': 0,
            'total_articles': 0,
            'new_articles': 0,
            'duplicate_articles': 0,
            'errors': []
        }
    
    def parse_all_sources(self, language: Optional[str] = None, 
                         category: Optional[str] = None,
                         active_only: bool = True) -> Dict:
        """
        Парсить всі RSS джерела з фільтрацією
        
        Args:
            language: Фільтр по мові ('en', 'pl', 'uk')
            category: Фільтр по категорії
            active_only: Тільки активні джерела
            
        Returns:
            Dict з статистикою парсингу
        """
        self.logger.info("🚀 Початок парсингу RSS джерел")
        
        # Фільтруємо джерела
        sources_queryset = RSSSource.objects.all()
        
        if active_only:
            sources_queryset = sources_queryset.filter(is_active=True)
        if language:
            sources_queryset = sources_queryset.filter(language=language)
        if category:
            sources_queryset = sources_queryset.filter(category=category)
        
        sources = list(sources_queryset)
        self.stats['total_sources'] = len(sources)
        
        self.logger.info(f"📊 Знайдено {len(sources)} джерел для парсингу")
        
        # Парсимо кожне джерело
        for source in sources:
            try:
                result = self.parse_single_source(source)
                self.stats['successful_sources'] += 1
                self.stats['total_articles'] += result['total_articles']
                self.stats['new_articles'] += result['new_articles']
                self.stats['duplicate_articles'] += result['duplicate_articles']
                
                self.logger.info(
                    f"✅ {source.name}: {result['new_articles']} нових, "
                    f"{result['duplicate_articles']} дублікатів"
                )
                
            except Exception as e:
                self.stats['failed_sources'] += 1
                error_msg = f"❌ {source.name}: {str(e)}"
                self.stats['errors'].append(error_msg)
                self.logger.error(error_msg, exc_info=True)
        
        self.logger.info(
            f"🏁 Парсинг завершено: {self.stats['successful_sources']}/{self.stats['total_sources']} "
            f"джерел, {self.stats['new_articles']} нових статей"
        )
        
        return self.stats
    
    def set_date_filter(self, target_date):
        """
        Встановлює фільтр по даті для парсингу статей
        
        Args:
            target_date: datetime.date - дата для фільтрації статей
        """
        self.target_date = target_date
        self.date_filter_enabled = True
        self.logger.info(f"📅 Встановлено фільтр по даті: {target_date}")

    def disable_date_filter(self):
        """Вимикає фільтр по даті - парсить всі статті"""
        self.date_filter_enabled = False
        self.target_date = None
        self.logger.info("🚫 Фільтр по даті вимкнений")

    def is_article_date_valid(self, published_date):
        """
        Перевіряє чи стаття відповідає фільтру по даті
        
        Args:
            published_date: datetime - дата публікації статті
            
        Returns:
            bool: True якщо стаття проходить фільтр
        """
        # Якщо фільтр вимкнений - всі статті проходять
        if not self.date_filter_enabled:
            return True
        
        # Якщо не задана цільова дата - використовуємо вчорашню
        if not self.target_date:
            from datetime import timedelta
            yesterday = django_timezone.now().date() - timedelta(days=1)
            self.target_date = yesterday
        
        if not published_date:
            # Якщо дата невідома - пропускаємо
            return False
        
        article_date = published_date.date()
        return article_date == self.target_date
    
    def parse_single_source(self, source: RSSSource, enhance_with_fulltext: bool = False) -> Dict:
        """
        Парсить одне RSS джерело з опціональним витягуванням повного тексту
        
        Args:
            source: RSS джерело
            enhance_with_fulltext: Чи витягувати повний текст через FiveFilters
        """
        self.logger.info(f"📡 Парсинг джерела: {source.name}")
        start_time = time.time()
        
        try:
            # 1. Завантажуємо та парсимо RSS
            feed = self._fetch_rss_feed(source.url)
            
            # 2. Парсимо статті з RSS
            parsed_articles = self._parse_feed_content(feed, source)
            
            if not parsed_articles:
                self.logger.warning(f"⚠️ Не знайдено статей у {source.name}")
                return self._empty_result()
            
            # 3. Фільтруємо по даті якщо потрібно
            if self.date_filter_enabled and self.target_date:
                filtered_articles = self._filter_articles_by_date(parsed_articles)
                filtered_count = len(parsed_articles) - len(filtered_articles)
                if filtered_count > 0:
                    self.logger.info(f"⏭️ Відфільтровано {filtered_count} статей за датою")
                parsed_articles = filtered_articles
            
            # 4. НОВИЙ КРОК: Збагачення повним текстом
            if enhance_with_fulltext and parsed_articles:
                self.logger.info("🔍 Збагачення повним текстом через FiveFilters...")
                parsed_articles = self.enhance_articles_with_fulltext(parsed_articles, source)
            
            # 5. Конвертуємо в RawArticles і зберігаємо
            result = self._save_articles_to_db(parsed_articles, source)
            new_articles = result.get('new_articles', 0)
            duplicate_count = result.get('duplicates', 0)
            
            # 6. Оновлюємо статистику джерела
            self._update_source_stats(source)
            
            processing_time = time.time() - start_time
            
            result = {
                'total_articles': len(parsed_articles),
                'new_articles': new_articles,
                'duplicate_articles': duplicate_count,
                'errors': 0,
                'processing_time': processing_time
            }
            
            if self.date_filter_enabled:
                result['filtered_articles'] = filtered_count
            
            self.logger.info(
                f"✅ Парсинг завершено: {new_articles} нових, "
                f"{duplicate_count} дублікатів за {processing_time:.1f}с"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Помилка парсингу {source.name}: {str(e)}")
            return {'total_articles': 0, 'new_articles': 0, 'duplicate_articles': 0, 'errors': 1}

    
    def _fetch_rss_feed(self, url: str) -> feedparser.FeedParserDict:
        """
        Завантажує RSS фід з URL
        
        Args:
            url: URL RSS фіду
            
        Returns:
            Parsed feed data
        """
        try:
            self.logger.debug(f"📡 Завантаження RSS: {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Перевіряємо Content-Type
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' not in content_type and 'rss' not in content_type and 'atom' not in content_type:
                self.logger.warning(f"⚠️ Підозрілий Content-Type: {content_type} для {url}")
            
            # Парсимо фід
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                self.logger.warning(f"⚠️ RSS має помилки парсингу: {url}")
            
            if not feed.entries:
                raise RSSFetchError(f"RSS фід пустий або невалідний: {url}")
            
            self.logger.debug(f"📄 Знайдено {len(feed.entries)} записів в RSS")
            
            return feed
            
        except requests.exceptions.RequestException as e:
            raise RSSFetchError(f"Не вдалося завантажити RSS {url}: {str(e)}")
        except Exception as e:
            raise RSSParseError(f"Помилка парсингу RSS {url}: {str(e)}")
    
    def _parse_feed_content(self, feed: feedparser.FeedParserDict, 
                          source: RSSSource) -> List[ParsedArticle]:
        """
        Парсить контент RSS фіду
        
        Args:
            feed: Parsed feed data
            source: RSS джерело
            
        Returns:
            Список ParsedArticle об'єктів
        """
        articles = []
        
        for entry in feed.entries:
            try:
                article = self._parse_single_entry(entry, source)
                if article:
                    articles.append(article)
            except Exception as e:
                self.logger.warning(f"⚠️ Пропуск статті через помилку: {str(e)}")
                continue
        
        self.logger.debug(f"✅ Успішно парсено {len(articles)} статей")
        return articles
    
    def _parse_single_entry(self, entry, source: RSSSource) -> Optional[ParsedArticle]:
        """
        Парсить одну статтю з RSS entry
        
        Args:
            entry: RSS entry
            source: RSS джерело
            
        Returns:
            ParsedArticle або None
        """
        try:
            # Заголовок (обов'язково)
            title = self._extract_text(entry, 'title')
            if not title:
                raise ValueError("Відсутній заголовок статті")
            
            # URL (обов'язково)
            url = self._extract_link(entry)
            if not url:
                raise ValueError("Відсутнє посилання на статтю")
            
            # Контент (з різних полів)
            content = self._extract_content(entry)
            
            # Короткий опис
            summary = self._extract_text(entry, 'summary') or content[:500]
            
            # Автор
            author = self._extract_author(entry)
            
            # Дата публікації
            published_at = self._extract_date(entry)
            
            # Створюємо ParsedArticle
            article = ParsedArticle(
                title=title.strip(),
                content=content.strip() if content else "",
                summary=summary.strip() if summary else "",
                url=url,
                author=author.strip() if author else "",
                published_at=published_at,
                content_hash=""  # Буде згенеровано автоматично
            )
            
            return article
            
        except Exception as e:
            self.logger.debug(f"⚠️ Помилка парсингу entry: {str(e)}")
            return None
    
    def _extract_text(self, entry, field_name: str) -> str:
        """Витягує текст з RSS поля з очищенням HTML"""
        try:
            value = getattr(entry, field_name, '')
            if isinstance(value, dict) and 'value' in value:
                value = value['value']
            elif isinstance(value, list) and value:
                value = value[0]
            
            if value:
                # Очищення HTML тегів (базове)
                import re
                value = re.sub(r'<[^>]+>', '', str(value))
                value = re.sub(r'\s+', ' ', value)
                return value.strip()
            
            return ""
        except Exception:
            return ""
    
    def _extract_link(self, entry) -> str:
        """Витягує посилання на статтю"""
        # Пробуємо різні поля для URL
        url = getattr(entry, 'link', '') or getattr(entry, 'guid', '')
        
        if isinstance(url, dict):
            url = url.get('href', '')
        
        # Валідація URL
        if url and self._is_valid_url(url):
            return url
        
        return ""
    
    def _extract_content(self, entry) -> str:
        """Витягує основний контент статті"""
        # Пробуємо різні поля для контенту
        content_fields = ['content', 'description', 'summary']
        
        for field in content_fields:
            content = getattr(entry, field, '')
            
            if isinstance(content, list) and content:
                content = content[0]
            
            if isinstance(content, dict):
                content = content.get('value', '')
            
            if content and len(str(content).strip()) > 50:  # Мінімальна довжина контенту
                return self._extract_text(entry, field)
        
        return ""
    
    def _extract_author(self, entry) -> str:
        """Витягує автора статті"""
        author_fields = ['author', 'dc_creator', 'author_detail']
        
        for field in author_fields:
            author = getattr(entry, field, '')
            if isinstance(author, dict):
                author = author.get('name', '') or author.get('email', '')
            if author:
                return str(author)
        
        return ""
    
    def _extract_date(self, entry) -> datetime:
        """Витягує та парсить дату публікації"""
        date_fields = ['published_parsed', 'updated_parsed']
        
        for field in date_fields:
            date_tuple = getattr(entry, field, None)
            if date_tuple:
                try:
                    return datetime(*date_tuple[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    continue
        
        # Якщо не знайшли дату, використовуємо поточну
        return django_timezone.now()
    
    def _is_valid_url(self, url: str) -> bool:
        """Перевіряє валідність URL"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _save_articles_to_db(self, articles: List[ParsedArticle], 
                           source: RSSSource) -> Dict:
        """
        Зберігає статті в базу даних з перевіркою дублікатів
        
        Args:
            articles: Список ParsedArticle
            source: RSS джерело
            
        Returns:
            Dict з результатами збереження
        """
        result = {
            'total_articles': len(articles),
            'new_articles': 0,
            'duplicate_articles': 0,
            'errors': 0
        }
        
        self.logger.debug(f"💾 Збереження {len(articles)} статей для {source.name}")
        
        # Отримуємо існуючі хеші для швидкої перевірки дублікатів
        existing_hashes = set(
            RawArticle.objects.filter(source=source)
            .values_list('content_hash', flat=True)
        )
        
        with transaction.atomic():
            for article in articles:
                try:
                    # Перевіряємо дублікат
                    if article.content_hash in existing_hashes:
                        result['duplicate_articles'] += 1
                        continue
                    
                    # Створюємо нову статтю
                    raw_article = RawArticle.objects.create(
                        source=source,
                        title=article.title[:2000],  # Обмеження довжини
                        content=article.content,
                        summary=article.summary,
                        original_url=article.url,
                        author=article.author[:200],  # Обмеження довжини
                        published_at=article.published_at,
                        content_hash=article.content_hash,
                        fetched_at=django_timezone.now(),
                        is_processed=False,
                        is_duplicate=False
                    )
                    
                    result['new_articles'] += 1
                    existing_hashes.add(article.content_hash)
                    
                    self.logger.debug(f"✅ Збережено: {article.title[:50]}...")
                    
                except Exception as e:
                    result['errors'] += 1
                    self.logger.error(f"❌ Помилка збереження статті: {str(e)}")
        
        self.logger.info(
            f"💾 Збереження завершено: {result['new_articles']} нових, "
            f"{result['duplicate_articles']} дублікатів, {result['errors']} помилок"
        )
        
        return result
    
    def cleanup_old_articles(self, days_old: int = 30) -> int:
        """
        Видаляє старі необроблені статті
        
        Args:
            days_old: Вік статей в днях
            
        Returns:
            Кількість видалених статей
        """
        cutoff_date = django_timezone.now() - django_timezone.timedelta(days=days_old)
        
        deleted_count, _ = RawArticle.objects.filter(
            fetched_at__lt=cutoff_date,
            is_processed=False
        ).delete()
        
        self.logger.info(f"🧹 Видалено {deleted_count} старих необроблених статей")
        return deleted_count
    

    

    def _save_articles_to_db(self, articles: List[ParsedArticle], source: RSSSource) -> Dict:
        """
        ОНОВЛЕНА версія збереження з урахуванням фільтру по даті
        """
        result = {
            'total_articles': len(articles),
            'new_articles': 0,
            'duplicate_articles': 0,
            'filtered_articles': 0,  # Відфільтровано по даті
            'errors': 0
        }
        
        self.logger.debug(f"💾 Збереження {len(articles)} статей для {source.name}")
        
        # Отримуємо існуючі хеші для швидкої перевірки дублікатів
        existing_hashes = set(
            RawArticle.objects.filter(source=source)
            .values_list('content_hash', flat=True)
        )
        
        with transaction.atomic():
            for article in articles:
                try:
                    # НОВИЙ ФІЛЬТР: перевіряємо дату
                    if not self.is_article_date_valid(article.published_at):
                        result['filtered_articles'] += 1
                        self.logger.debug(f"⏭️ Відфільтровано по даті: {article.title[:50]}...")
                        continue
                    
                    # Перевіряємо дублікат
                    if article.content_hash in existing_hashes:
                        result['duplicate_articles'] += 1
                        continue
                    
                    # Створюємо нову статтю
                    raw_article = RawArticle.objects.create(
                        source=source,
                        title=article.title[:2000],
                        content=article.content,
                        summary=article.summary,
                        original_url=article.url,
                        author=article.author[:200],
                        published_at=article.published_at,
                        content_hash=article.content_hash,
                        fetched_at=django_timezone.now(),
                        is_processed=False,
                        is_duplicate=False
                    )
                    
                    result['new_articles'] += 1
                    existing_hashes.add(article.content_hash)
                    
                    self.logger.debug(f"✅ Збережено: {article.title[:50]}...")
                    
                except Exception as e:
                    result['errors'] += 1
                    self.logger.error(f"❌ Помилка збереження статті: {str(e)}")
        
        # Логування результатів
        self.logger.info(
            f"💾 Збереження завершено: {result['new_articles']} нових, "
            f"{result['duplicate_articles']} дублікатів"
        )
        
        if result['filtered_articles'] > 0:
            filter_info = f"цільова дата: {self.target_date}" if self.target_date else "фільтр вимкнений"
            self.logger.info(
                f"📅 Відфільтровано {result['filtered_articles']} статей ({filter_info})"
            )
        
        return result


    def get_parsing_statistics(self) -> Dict:
        """Повертає статистику парсера"""
        return self.stats.copy()



    def enhance_articles_with_fulltext(self, articles: List[ParsedArticle], source: RSSSource) -> List[ParsedArticle]:
        """Збагачує статті повним текстом через FiveFilters"""
        from .fulltext_extractor import FullTextExtractor
        
        if not articles:
            return articles
            
        enhanced_articles = []
        extractor = FullTextExtractor()
        
        self.logger.info(f"🔍 Витягування повного тексту для {len(articles)} статей...")
        
        for i, article in enumerate(articles, 1):
            self.logger.debug(f"[{i}/{len(articles)}] {article.title[:50]}...")
            
            try:
                # Витягуємо повний текст
                full_content = extractor.extract_article(article.url)
                
                if full_content and len(full_content) > len(article.content or ""):
                    # Якщо повний текст кращий - замінюємо
                    original_length = len(article.content or "")
                    article.content = full_content
                    
                    # Оновлюємо summary якщо він був коротший
                    if len(full_content) > 500:
                        article.summary = full_content[:500] + "..."
                        
                    improvement = len(full_content) - original_length
                    self.logger.info(f"✅ [{i}] Full-text: +{improvement} символів ({len(full_content)} total)")
                else:
                    # Залишаємо оригінальний RSS контент
                    self.logger.debug(f"⚠️ [{i}] RSS контент кращий або full-text порожній")
                
                enhanced_articles.append(article)
                
            except Exception as e:
                self.logger.warning(f"❌ [{i}] Помилка full-text для {article.url}: {e}")
                # Додаємо оригінальну статтю навіть при помилці
                enhanced_articles.append(article)
                continue
        
        success_rate = len([a for a in enhanced_articles if len(a.content or "") > 1000]) / len(articles) * 100
        self.logger.info(f"📊 Full-text успішність: {success_rate:.1f}% ({len(enhanced_articles)}/{len(articles)} статей)")
        
        return enhanced_articles
    
    def _filter_articles_by_date(self, articles: List[ParsedArticle]) -> List[ParsedArticle]:
        """Фільтрує статті по даті публікації"""
        if not self.target_date:
            return articles
        
        filtered_articles = []
        target_date = self.target_date
        
        for article in articles:
            # Порівнюємо тільки дату, без часу
            article_date = article.published_at.date()
            if article_date == target_date:
                filtered_articles.append(article)
        
        return filtered_articles
    
    def _update_source_stats(self, source: RSSSource):
        """Оновлює статистику джерела"""
        try:
            # Просто зберігаємо джерело (без неіснуючого поля last_parsed)
            source.save()
        except Exception as e:
            self.logger.warning(f"Помилка оновлення статистики джерела {source.name}: {e}")