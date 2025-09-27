import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle

# Перевіряємо останні статті
articles = ProcessedArticle.objects.filter(status='published').order_by('-created_at')[:5]

print("Перевірка перекладів заголовків:")
print("=" * 50)

for article in articles:
    print(f"\nСтаття ID {article.id}:")
    print(f"  EN: {article.title_en[:80]}...")
    print(f"  PL: {article.title_pl[:80]}...")  
    print(f"  UK: {article.title_uk[:80]}...")
    
    # Перевіряємо, чи є переклади
    has_translations = (
        article.title_en != article.title_pl and 
        article.title_en != article.title_uk and
        article.title_pl != article.title_uk
    )
    
    if has_translations:
        print("  ✅ Має переклади")
    else:
        print("  ❌ Переклади відсутні або ідентичні")

print(f"\n🎯 Резюме: Перевірено {len(articles)} статей")
