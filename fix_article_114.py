import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle

article = ProcessedArticle.objects.get(id=114)
raw = article.raw_article

# Встановлюємо правильний оригінальний заголовок
correct_en_title = raw.title
article.title_en = correct_en_title

print(f'Оригінальний заголовок: {correct_en_title}')
print(f'Поточний PL: {article.title_pl}')
print(f'Поточний UK: {article.title_uk}')

# Якщо польський та український заголовки правильні, залишаємо їх
# Інакше встановлюємо оригінальний заголовок для всіх
if article.title_pl == article.title_en:  # Якщо польський = англійському (помилка)
    article.title_pl = correct_en_title
if article.title_uk == correct_en_title:  # Якщо український = англійському (не перекладений)
    article.title_uk = correct_en_title

article.save()

print('\nПісля виправлення:')
print(f'EN: {article.title_en}')
print(f'PL: {article.title_pl}')
print(f'UK: {article.title_uk}')
