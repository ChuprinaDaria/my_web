import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle

article = ProcessedArticle.objects.get(id=114)
print('Після оновлення:')
print(f'EN: "{article.title_en}"')
print(f'PL: "{article.title_pl}"')
print(f'UK: "{article.title_uk}"')

print('\nПереклади через get_title:')
print(f'get_title("en"): {article.get_title("en")}')
print(f'get_title("pl"): {article.get_title("pl")}')
print(f'get_title("uk"): {article.get_title("uk")}')
