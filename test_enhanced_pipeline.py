#!/usr/bin/env python3
"""
Тестуємо новий Enhanced Pipeline: Smart Selection → FiveFilters → AI
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import RawArticle
from news.services.fulltext_extractor import FullTextExtractor

def test_smart_selection():
    """Тестуємо smart selection"""
    print("📊 Тест Smart Selection")
    print("=" * 30)
    
    # Беремо необроблені статті
    unprocessed = RawArticle.objects.filter(
        is_processed=False,
        is_duplicate=False
    ).select_related('source').order_by('-published_at')[:20]
    
    print(f"📄 Необроблених статей: {len(unprocessed)}")
    
    if not unprocessed:
        print("❌ Немає статей для тестування")
        return []
    
    # Показуємо статті з оцінками
    scored_articles = []
    
    for i, article in enumerate(unprocessed[:10], 1):
        # Простий алгоритм оцінки
        score = 0
        content_length = len(article.content or article.summary or "")
        
        if content_length > 1000:
            score += 3
        elif content_length > 500:
            score += 2
        elif content_length > 200:
            score += 1
        
        # Свіжість
        from django.utils import timezone
        hours_old = (timezone.now() - article.published_at).total_seconds() / 3600
        if hours_old < 6:
            score += 2
        elif hours_old < 24:
            score += 1
        
        # Англійські джерела
        if article.source.language == 'en':
            score += 1
        
        scored_articles.append((article, score, content_length))
        
        print(f"[{i}] Скор: {score} | {content_length} симв | {article.title[:50]}...")
    
    # Сортуємо по скору
    scored_articles.sort(key=lambda x: x[1], reverse=True)
    top_5 = scored_articles[:5]
    
    print(f"\n🏆 ТОП-5 статей для FiveFilters:")
    for i, (article, score, length) in enumerate(top_5, 1):
        print(f"{i}. [{score} балів] {article.title[:60]}...")
    
    return [article for article, score, length in top_5]

def test_fivefilters_on_top_articles(top_articles):
    """Тестуємо FiveFilters на топ статтях"""
    print(f"\n🔍 Тест FiveFilters на {len(top_articles)} статтях")
    print("=" * 50)
    
    if not top_articles:
        print("❌ Немає статей для тестування")
        return
    
    extractor = FullTextExtractor()
    results = []
    
    for i, article in enumerate(top_articles, 1):
        print(f"\n[{i}/{len(top_articles)}] {article.title[:50]}...")
        print(f"🔗 URL: {article.original_url}")
        
        original_length = len(article.content or article.summary or "")
        print(f"📏 RSS контент: {original_length} символів")
        
        try:
            # Витягуємо повний текст
            full_content = extractor.extract_article(article.original_url)
            
            if full_content:
                improvement = len(full_content) - original_length
                percentage = (improvement / original_length * 100) if original_length > 0 else 999
                
                print(f"✅ FiveFilters: {len(full_content)} символів")
                print(f"📈 Покращення: +{improvement} символів (+{percentage:.1f}%)")
                
                if improvement > 1000:
                    quality = "🔥 ВІДМІННО"
                elif improvement > 500:
                    quality = "✅ ДОБРЕ"
                elif improvement > 0:
                    quality = "⚠️ НЕВЕЛИКЕ"
                else:
                    quality = "❌ БЕЗ ПОКРАЩЕННЯ"
                
                print(f"💎 Якість: {quality}")
                
                results.append({
                    'article': article,
                    'original_length': original_length,
                    'enhanced_length': len(full_content),
                    'improvement': improvement,
                    'success': True
                })
            else:
                print("❌ FiveFilters не зміг витягти контент")
                results.append({
                    'article': article,
                    'original_length': original_length,
                    'enhanced_length': 0,
                    'improvement': 0,
                    'success': False
                })
                
        except Exception as e:
            print(f"❌ Помилка: {e}")
            results.append({
                'article': article,
                'original_length': original_length,
                'enhanced_length': 0,
                'improvement': 0,
                'success': False
            })
    
    return results

def analyze_pipeline_results(results):
    """Аналізуємо результати пайплайна"""
    print(f"\n📊 АНАЛІЗ РЕЗУЛЬТАТІВ PIPELINE")
    print("=" * 40)
    
    if not results:
        print("❌ Немає результатів для аналізу")
        return
    
    successful = [r for r in results if r['success']]
    success_rate = len(successful) / len(results) * 100
    
    print(f"✅ Успішність FiveFilters: {success_rate:.1f}% ({len(successful)}/{len(results)})")
    
    if successful:
        total_improvement = sum(r['improvement'] for r in successful)
        avg_improvement = total_improvement / len(successful)
        
        print(f"📈 Середнє покращення: {avg_improvement:.0f} символів")
        print(f"📊 Загальне покращення: {total_improvement} символів")
        
        # Показуємо найкращий результат
        best = max(successful, key=lambda x: x['improvement'])
        print(f"\n🏆 Найкращий результат:")
        print(f"   📰 {best['article'].title[:50]}...")
        print(f"   📈 {best['original_length']} → {best['enhanced_length']} символів")
        print(f"   🎯 Покращення: +{best['improvement']} символів")
    
    # Рекомендації
    print(f"\n💡 РЕКОМЕНДАЦІЇ:")
    if success_rate >= 80:
        print("🎉 Відмінна якість! Готові до AI обробки!")
    elif success_rate >= 60:
        print("✅ Хороша якість. Можна покращити фільтри джерел.")
    elif success_rate >= 40:
        print("⚠️ Середня якість. Варто перевірити налаштування FiveFilters.")
    else:
        print("❌ Низька якість. Потрібна діагностика проблем.")

def test_ai_readiness(results):
    """Перевіряємо готовність для AI обробки"""
    print(f"\n🤖 ГОТОВНІСТЬ ДО AI ОБРОБКИ")
    print("=" * 30)
    
    successful = [r for r in results if r['success'] and r['enhanced_length'] > 800]
    
    print(f"📊 Статей готових до AI: {len(successful)}")
    
    if successful:
        avg_length = sum(r['enhanced_length'] for r in successful) / len(successful)
        print(f"📏 Середня довжина: {avg_length:.0f} символів")
        
        if avg_length > 2000:
            print("🔥 Відмінно! AI матиме багато контенту для роботи")
        elif avg_length > 1000:
            print("✅ Добре! Достатньо контенту для якісних інсайтів")
        else:
            print("⚠️ Мало контенту. AI працюватиме з обмеженою інформацією")

def main():
    print("🧪 ТЕСТ ENHANCED PIPELINE")
    print("=" * 50)
    
    # 1. Smart Selection
    top_articles = test_smart_selection()
    
    if not top_articles:
        print("❌ Немає статей. Спочатку запусти RSS парсинг!")
        return
    
    # 2. FiveFilters Enhancement
    results = test_fivefilters_on_top_articles(top_articles)
    
    # 3. Аналіз результатів
    analyze_pipeline_results(results)
    
    # 4. Готовність до AI
    test_ai_readiness(results)
    
    print(f"\n🎯 НАСТУПНІ КРОКИ:")
    print("1. Якщо результати добрі → інтегруй в основний код")
    print("2. Потім оновлюй AI промпт для роботи з повним текстом")
    print("3. Тестуй повний pipeline: RSS → Selection → FiveFilters → AI")

if __name__ == "__main__":
    main()