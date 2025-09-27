import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle

# Підраховуємо статті з різними заголовками
articles = ProcessedArticle.objects.all()
total = articles.count()
translated = 0

print(f"Загальна кількість статей: {total}")

for article in articles[:5]:  # Перевіримо перші 5
    print(f"\nID {article.id}:")
    print(f"  EN: \"{article.title_en[:60]}...\"")
    print(f"  PL: \"{article.title_pl[:60]}...\"")
    print(f"  UK: \"{article.title_uk[:60]}...\"")

    if (article.title_en and article.title_en != article.title_uk and
        article.title_pl and article.title_pl != article.title_uk):
        translated += 1
        print("  ✅ Має переклади")
    else:
        print("  ❌ Немає перекладів")

print(f"\nЗ перевірених статей {translated}/5 мають переклади")
