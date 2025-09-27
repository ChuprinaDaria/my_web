import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle
from django.utils.translation import activate

article = ProcessedArticle.objects.get(id=114)

print('Тестуємо get_title() з різними мовами:')
print(f'get_title(): {article.get_title()}')  # За замовчуванням
print(f'get_title("uk"): {article.get_title("uk")}')
print(f'get_title("pl"): {article.get_title("pl")}')
print(f'get_title("en"): {article.get_title("en")}')

print('\nТестуємо з активацією мов:')
activate('uk')
print(f'Після activate("uk"): {article.get_title()}')
activate('pl')
print(f'Після activate("pl"): {article.get_title()}')
activate('en')
print(f'Після activate("en"): {article.get_title()}')
