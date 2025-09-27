import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle

articles = ProcessedArticle.objects.filter(status='published').order_by('-created_at')[:3]
for article in articles:
    print(f'ID: {article.id}')
    print(f'Title EN: {article.title_en}')
    print(f'Title PL: {article.title_pl}')
    print(f'Title UK: {article.title_uk}')
    print(f'get_title(uk): {article.get_title("uk")}')
    print(f'get_title(pl): {article.get_title("pl")}')
    print(f'get_title(en): {article.get_title("en")}')
    print('---')