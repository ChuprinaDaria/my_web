#!/usr/bin/env python
import os
import sys
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle, RawArticle
from django.utils import timezone

def test_homepage_logic():
    print("=== ТЕСТ ЛОГІКИ ГОЛОВНОЇ СТОРІНКИ ===")
    
    # Перевіряємо топ-статті з повним контентом
    top_articles = ProcessedArticle.objects.filter(
        status='published',
        is_top_article=True,
        top_selection_date=timezone.now().date(),
        raw_article__has_full_content=True
    ).order_by('article_rank')[:5]
    
    print(f"Топ-статті з повним контентом: {top_articles.count()}")
    for article in top_articles:
        word_count = article.get_word_count()
        print(f"- {article.title_uk[:50]}... | Ранг: {article.article_rank} | Слів: {word_count} | Повний контент: {article.raw_article.has_full_content}")
    
    # Перевіряємо дайджест
    from news.models import DailyDigest
    try:
        daily_digest = DailyDigest.objects.get(date=timezone.now().date())
        digest_articles = daily_digest.articles.count()
        print(f"Дайджест (з DailyDigest): {digest_articles} статей")
    except DailyDigest.DoesNotExist:
        # Якщо немає дайджесту, беремо з ProcessedArticle
        digest_articles = ProcessedArticle.objects.filter(
            status='published',
            is_top_article=False
        )[:10].count()
        print(f"Дайджест (з ProcessedArticle): {digest_articles} статей")
    
    # Загальна статистика
    print(f"\n=== ЗАГАЛЬНА СТАТИСТИКА ===")
    print(f"RawArticle з has_full_content=True: {RawArticle.objects.filter(has_full_content=True).count()}")
    print(f"ProcessedArticle з is_top_article=True: {ProcessedArticle.objects.filter(is_top_article=True).count()}")
    print(f"ProcessedArticle з is_top_article=True та has_full_content=True: {ProcessedArticle.objects.filter(is_top_article=True, raw_article__has_full_content=True).count()}")

if __name__ == "__main__":
    test_homepage_logic()
