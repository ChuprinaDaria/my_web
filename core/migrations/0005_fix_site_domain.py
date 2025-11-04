from django.db import migrations


def fix_site_domain(apps, schema_editor):
    """Виправляємо домен сайту з example.com на lazysoft.pl"""
    Site = apps.get_model('sites', 'Site')

    try:
        site = Site.objects.get(pk=1)
        site.domain = 'lazysoft.pl'
        site.name = 'LAZYSOFT'
        site.save()
        print(f"✓ Site domain updated to: {site.domain}")
    except Site.DoesNotExist:
        # Створюємо сайт, якщо його немає
        Site.objects.create(
            pk=1,
            domain='lazysoft.pl',
            name='LAZYSOFT'
        )
        print("✓ Created new site: lazysoft.pl")


def reverse_fix(apps, schema_editor):
    """Зворотна міграція - повертаємо example.com (якщо потрібно)"""
    Site = apps.get_model('sites', 'Site')

    try:
        site = Site.objects.get(pk=1)
        site.domain = 'example.com'
        site.name = 'example.com'
        site.save()
    except Site.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_homehero'),
        ('sites', '0001_initial'),  # Залежність від Sites framework
    ]

    operations = [
        migrations.RunPython(fix_site_domain, reverse_fix),
    ]
