# Generated migration to update article slugs from English titles
from django.db import migrations
from django.utils.text import slugify


def update_slugs_from_english_title(apps, schema_editor):
    """Update all article slugs to be based on English title."""
    ProcessedArticle = apps.get_model('news', 'ProcessedArticle')
    
    for article in ProcessedArticle.objects.all():
        # Пріоритет: title_en → title_uk → title_pl
        base = (article.title_en or article.title_uk or article.title_pl or '')[:180]
        if base:
            candidate = slugify(base)
            # Перевірка унікальності
            if candidate:
                existing = ProcessedArticle.objects.filter(slug=candidate).exclude(pk=article.pk).exists()
                if existing:
                    # Додаємо 8 символів UUID для унікальності
                    candidate = f"{candidate}-{str(article.uuid)[:8]}"
                article.slug = candidate
                article.save(update_fields=['slug'])


def reverse_migration(apps, schema_editor):
    """Reverse migration - do nothing, slugs will remain."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0021_add_implementation_steps_fields'),
    ]

    operations = [
        migrations.RunPython(update_slugs_from_english_title, reverse_migration),
    ]

