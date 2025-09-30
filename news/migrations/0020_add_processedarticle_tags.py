# Generated manually on 2025-09-30
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Залежність від Tag моделі
        ('news', '0019_auto_20250930_0949'),
    ]

    operations = [
        migrations.AddField(
            model_name='processedarticle',
            name='tags',
            field=models.ManyToManyField(
                blank=True,
                help_text='Внутрішні теги для крос-видачі з проєктами та сервісами',
                related_name='articles',
                to='core.tag'
            ),
        ),
    ]
