import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle

article = ProcessedArticle.objects.get(id=116)
print('=== СТАТЯ 116 ПІСЛЯ ОНОВЛЕННЯ ===')
print(f'Title EN: {article.title_en}')
print(f'Title PL: {article.title_pl}')  
print(f'Title UK: {article.title_uk}')
print()
print(f'Summary EN (перші 150 символів): {article.summary_en[:150]}...')
print(f'Summary PL (перші 150 символів): {article.summary_pl[:150]}...')
print(f'Summary UK (перші 150 символів): {article.summary_uk[:150]}...')
