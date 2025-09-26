#!/usr/bin/env python
import os
import sys
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle, RawArticle
from news.services.smart_news_pipeline import SmartNewsPipeline
from django.utils import timezone

def test_top_articles_pipeline():
    print("=== ТЕСТ ПАЙПЛАЙНУ ТОП-СТАТЕЙ ===")
    
    # Очищаємо попередні топ-статті
    ProcessedArticle.objects.filter(is_top_article=True).update(
        is_top_article=False,
        article_rank=None,
        top_selection_date=None
    )
    
    # Запускаємо пайплайн
    pipeline = SmartNewsPipeline()
    result = pipeline.run_daily_pipeline(dry_run=False)
    
    print(f"Результат пайплайну: {result.articles_processed > 0}")
    print(f"Оброблено статей: {result.articles_processed}")
    print(f"Помилки: {len(result.errors)}")
    
    # Перевіряємо топ-статті
    top_articles = ProcessedArticle.objects.filter(
        is_top_article=True,
        top_selection_date=timezone.now().date()
    ).order_by('article_rank')
    
    print(f"\n=== ТОП-СТАТТІ ===")
    print(f"Кількість топ-статей: {top_articles.count()}")
    
    for article in top_articles:
        print(f"\n--- Стаття {article.article_rank} ---")
        print(f"Заголовок: {article.title_uk[:50]}...")
        print(f"Повний контент (EN): {len(article.full_content_en)} символів")
        print(f"Повний контент (PL): {len(article.full_content_pl)} символів")
        print(f"Повний контент (UK): {len(article.full_content_uk)} символів")
        print(f"Повний контент спарсений: {article.full_content_parsed}")
        print(f"Кількість слів оригіналу: {article.original_word_count}")
        print(f"Час читання: {article.reading_time} хв")
        print(f"Має повний контент (RawArticle): {article.raw_article.has_full_content}")
        print(f"Кількість слів (get_word_count): {article.get_word_count()}")
        print(f"Статус: {article.status}")
        print(f"Пріоритет: {article.priority}")

if __name__ == "__main__":
    test_top_articles_pipeline()
